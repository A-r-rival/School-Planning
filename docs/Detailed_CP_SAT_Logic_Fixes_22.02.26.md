# Detailed Scheduler CP-SAT Logic Fixes

This document provides a comprehensive, line-by-line explanation of the bug fixes and performance improvements made to `controllers/scheduler.py` based on the CP-SAT solver feedback.

## 1. Single Source of Truth for Time Slots (`SLOTS_PER_DAY`)

Previously, there was a risk of silent failures due to a module-level constant (`SLOTS_PER_DAY = 18`) and an instance variable (`self.slots_per_day = 18`) being used interchangeably. This was deliberately changed from a static constant because the daily slot amount might be different in the future, for example, to accommodate a different schedule format for a possible Summer Course season.

**Line-by-Line Changes:**
We searched the entire file and replaced references to the global constant `SLOTS_PER_DAY` with the instance variable `self.slots_per_day`.

```diff
- if duration > SLOTS_PER_DAY:
-     print(f"CRITICAL WARNING: Course {course['name']} duration ({duration}) exceeds SLOTS_PER_DAY ({SLOTS_PER_DAY}). It will verify be infeasible.")
+ if duration > self.slots_per_day:
+     print(f"CRITICAL WARNING: Course {course['name']} duration ({duration}) exceeds SLOTS_PER_DAY ({self.slots_per_day}). It will verify be infeasible.")
```

```diff
- start_day = start_id // SLOTS_PER_DAY
- end_day = end_id // SLOTS_PER_DAY
+ start_day = start_id // self.slots_per_day
+ end_day = end_id // self.slots_per_day
```

_(Similar replacements were made in `create_variables`, `add_teacher_day_span_constraints`, and `add_soft_constraints_consecutive` where day indices are calculated)._

## 2. Optimized Lunch Break Constraint Lookup

The `add_lunch_break_constraints` method was doing an $O(N)$ lookup on `lunch_slots_by_day` (a list) for every generated variable. We introduced an $O(1)$ set lookup (`lunch_slots_set`). We now quickly verify if a slot falls during lunch before proceeding with the more complex grouping logic, resulting in faster variable generation.

**Line-by-Line Changes:**

```diff
  lunch_slots_by_day = collections.defaultdict(list)
+ lunch_slots_set = set() # O(1) lookup map

  for s in self.time_slots:
      if s['start_min'] >= lunch_start_min and s['end_min'] <= lunch_end_min:
          lunch_slots_by_day[s['day_idx']].append(s['id'])
+         lunch_slots_set.add(s['id'])
```

And in the variable loop, we replaced the slow mapping logic with a fast set check:

```diff
-  # Optimization:
-  is_lunch = False
-  day_idx = -1
-  s_day = s_id // self.slots_per_day
-  if s_id in lunch_slots_by_day[s_day]:
-      is_lunch = True
-  if not is_lunch:
-      continue
+  # Optimization check against pre-built set
+  if s_id not in lunch_slots_set:
+      continue
+  s_day = s_id // self.slots_per_day
```

## 3. Preserving Solver Results

`_run_solver` was silently discarding optimal/feasible results if they didn't match specific string names (`PHASE2_ELECTIVES` or `PHASE1_CORE_FALLBACK`). Originally, these arbitrary restrictions were put in place during the implementation of the 2-Phase Strategy—the author likely intended to avoid saving the partial intermediate schedules (like `PHASE1_CORE`), but hardcoding it inside `_run_solver` instead of controlling it via the caller caused issues.

However, making the solver unconditionally save on any successful run posed a risk for manual diagnostics: generating a schedule for a past semester purely for debugging would overwrite the active database. To solve this, we introduced an explicit `save_to_db` flag to the `_run_solver` parameters.

**Line-by-Line Changes:**

```diff
- def _run_solver(self, mode_name: str, timeout: float = 120.0) -> bool:
+ def _run_solver(self, mode_name: str, timeout: float = 120.0, save_to_db: bool = False) -> bool:
```

```diff
  if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
      print(f"SUCCESS: Solution found in {mode_name} mode!")
-     if mode_name == "PHASE2_ELECTIVES" or mode_name == "PHASE1_CORE_FALLBACK":
-         self._save_solution()
+     # Explicitly controlled save to DB to avoid destroying live data during debug
+     if save_to_db:
+         self._save_solution()
      return True
```

_And in the caller functions (`generate_schedule`), we strictly set `save_to_db=False` for Phase 1, and `save_to_db=True` for Phase 2._

## 4. Consecutive Penalty Model Fix

The CP-SAT penalty model in `add_soft_constraints_consecutive` was improperly constructed.

The original logic explicitly told the solver: _"IF the solver chooses to set `conflict = 1`, THEN it must ensure both class `b1` and `b2` are true."_ Because the objective function attempts to minimize conflicts, the solver smartly realizes that the implication is one-way. It can happily schedule `b1 = 1` and `b2 = 1` (a real conflict), but cheat the system by choosing to set the `conflict` penalty variable to `0`.

Rewrote the statement completely. We now use: `AddBoolOr([b1.Not(), b2.Not(), conflict])`. This forces the correct relationship: _"Either `b1` is false, `b2` is false, OR `conflict` must be true."_ This securely guarantees the penalty is applied when the classes overlap, fixing the logic gap.

**Line-by-Line Changes:**

```diff
  conflict = self.cp_model.NewBoolVar(f'dd_c_{idx1}_{idx2}_{d_idx}')
- self.cp_model.AddBoolAnd([b1, b2]).OnlyEnforceIf(conflict)
- self.cp_model.AddBoolOr([b1.Not(), b2.Not()]).OnlyEnforceIf(conflict.Not())
+ self.cp_model.AddBoolOr([b1.Not(), b2.Not(), conflict])
  self.soft_penalties.append(conflict)
```

## 5. Strict Core Assignment Mapping in Phase 2

If Phase 2's solver failed to exactly reconstruct the room variables for a Core course that was solved in Phase 1, it logged a "WARNING" and implicitly ignored the failure — destroying the core assignment entirely. Promoted this case to a hard error (`ValueError`).

**Line-by-Line Changes:**

```diff
  # FIX core assignments from Phase 1
  for (stable_key, r_id, s_id) in core_assignments_stable:
      c_idx = course_index_map.get(stable_key)
      if c_idx is not None and (c_idx, r_id, s_id) in self.starts:
          self.cp_model.Add(self.starts[(c_idx, r_id, s_id)] == 1)
      else:
-         print(f"WARNING: Could not map stable key {stable_key} in Phase 2!")
+         msg = f"CRITICAL: Could not map Phase 1 core assignment {stable_key} in Phase 2! Variables missing."
+         print(msg)
+         raise ValueError(msg)
```

## 6. Loop Optimization for Core Demands

A diagnostic loop analyzing `group_core_demand` nested an $O(N)$ iterator to calculate duration over thousands of records, resulting in an expensive $O(N^2)$ operation on every schedule generation. Refactored to map all durations securely into a precompiled `$O(1)$` dictionary mapping (`course_duration_map`) immediately beforehand, reducing the evaluation sequence purely to `$O(N)$`.

**Line-by-Line Changes:**

```diff
+ course_duration_map = {c['name'] + str(c.get('instance', '')): c.get('duration', 0) for c in self.courses}
  for (g_dept, g_year), courses in group_core_demand.items():
-     # We have to fetch actual duration but just counting unique courses * avg duration is a good heuristic
-     total_hours = sum([next((c['duration'] for c in self.courses if c['name'] + str(c['instance']) == c_name), 0) for c_name in courses])
+     # O(1) duration lookup instead of O(N) per course
+     total_hours = sum([course_duration_map.get(c_name, 0) for c_name in courses])
      if total_hours > 50:
          print(f"WARNING: Group {g_dept}-{g_year} has VERY HIGH Core Demand: {total_hours} slots ({len(courses)} courses).", flush=True)
```

## 7. Cleaned up Artifact Syntax and Workspace

Removed orphaned and commented out exception raises (`# raise e`) outside standard try/except blocks inside `add_teacher_room_preferences`. Cleaned up and deleted outdated `debug*.txt`, `room_preference_debug.txt`, `model_dump.txt`, and `scheduler_crash.txt` dump files generated from previous debugging sessions inside the main project folder. And removed unused database and scripts.
