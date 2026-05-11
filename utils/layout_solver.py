# -*- coding: utf-8 -*-
"""
📐 CP-SAT Layout Solver for Calendar Event Positioning
=======================================================
Uses OR-Tools CP-SAT to find optimal horizontal positions for overlapping
calendar events. Replaces heuristic midpoint-based positioning.

A slot is

RULES (in priority order):
  1. HARD: No two events in the same slot may overlap horizontally.
  2. HARD: Every event must be at least MIN_WIDTH_BRANCH wide.
  3. HARD: Multi-slot events must overlap by at least MIN_WIDTH_BRANCH between adjacent slots.
  4. HARD: Symmetry breaking — leftmost event in each slot anchored to x=0.
  5. HARD: Once slot of a lesson starts to shrink, slots after that can't exceed boundaries of their one prior slot
  6. SOFT (+500):    Overlap reward — reward large overlap between adjacent slots.
  7. SOFT (+3000):   Every event should be able to write its lesson code  [CODE only]
  8. SOFT (+700):    Every event should be able to write its full lesson title [word-wrappable]
  9. SOFT (+300):    Every event should be able to write its teacher
  10. SOFT (+100):   Every event should be able to write its room

  Rewards 7-10 are BOOLEAN: the block earns the reward when its pixel width
  (= w_var * widget_width / PRECISION) meets the per-event minimum pixel width
  for that info piece measured by QFontMetrics at fixed font sizes (TITLE_PT / DETAIL_PT).
  Fallback: continuous capped_w proxy when px_reqs is not supplied.

  Also calendar doesn't need to write "teacher" or "room" or "lesson name" just the values.
  However hovertip should write in that manner.


RETURNS: Fractional positions {sig: {slot_idx: (left_frac, right_frac)}}
         Re-run on every resize (widget_width changes).
"""
from ortools.sat.python import cp_model
import time

PRECISION = 1000       # Discretize 0.0–1.0 into 0–1000
MIN_WIDTH_BRANCH = 30  # 3% absolute minimum width for any event in any slot


def _get_sig(e):
    """Event signature — must match DayCanvas.get_sig()"""
    d = e['course_data']
    return (d['course'], str(d['extra']).strip(), d['start_str'], d['end_str'])


def solve_layout(events, slot_occupants, widget_width=None, px_reqs=None):
    """
    Solve optimal horizontal positions for calendar events using CP-SAT.
    """
    t0 = time.perf_counter()
    model = cp_model.CpModel()
    vc = 0  # global variable counter — never reset
    
    # ──────────────────────────────────────────────────────────────
    # STEP 1: Create L/R variables for every (event, slot) pair
    # ──────────────────────────────────────────────────────────────
    left_vars = {}
    right_vars = {}
    objective_terms = []
    
    for slot_idx in range(18):
        occupants = slot_occupants.get(slot_idx, [])
        if not occupants:
            continue
        
        # Deduplicate by signature (same event may appear multiple times)
        seen = set()
        unique_occs = []
        for e in sorted(occupants, key=lambda x: x['base_center']):
            sig = _get_sig(e)
            if sig not in seen:
                seen.add(sig)
                unique_occs.append(e)
        
        K = len(unique_occs)
        
        for j, e in enumerate(unique_occs):
            sig = _get_sig(e)
            key = (sig, slot_idx)
            if key in left_vars:
                continue
            
            left_vars[key] = model.NewIntVar(0, PRECISION, f'L{vc}')
            right_vars[key] = model.NewIntVar(0, PRECISION, f'R{vc}')
            vc += 1
            
            # CP-SAT Search Hint: Start from the perfectly distributed heuristic!
            # If the solver times out, it will return this beautifully spaced layout 
            # (or something even better), guaranteeing NO slivers!
            left_bound = 0.0 if j == 0 else (unique_occs[j-1]['base_center'] + e['base_center']) / 2.0
            right_bound = 1.0 if j == K - 1 else (e['base_center'] + unique_occs[j+1]['base_center']) / 2.0
            model.AddHint(left_vars[key], int(left_bound * PRECISION))
            model.AddHint(right_vars[key], int(right_bound * PRECISION))
            
            w_var = model.NewIntVar(0, PRECISION, f'w{vc}')
            model.Add(w_var == right_vars[key] - left_vars[key])
            vc += 1
            
            # HARD Rule 2: Minimum width
            model.Add(w_var >= MIN_WIDTH_BRANCH)
            
            # SOFT Rules 7-10: Pixel-based boolean text-fitting rewards
            if widget_width and widget_width > 0 and px_reqs and sig in px_reqs:
                req = px_reqs[sig]
                def _t(px):  # pixel → PRECISION units (clamped)
                    return min(PRECISION, max(MIN_WIDTH_BRANCH,
                               int(px * PRECISION / widget_width) + 1))
                
                for reward, field in [(3000, 'code'), (700, 'name'),
                                      (300, 'teacher'), (100, 'room')]:
                    req = px_reqs[sig].get(field)
                    if not req or req['max'] == 0:
                        continue
                        
                    min_thresh = _t(req['min'])
                    max_thresh = _t(req['max'])
                    
                    if min_thresh <= MIN_WIDTH_BRANCH:
                        min_thresh = MIN_WIDTH_BRANCH
                    
                    if max_thresh <= min_thresh:
                        # Just a boolean reward if min and max are the same
                        bv = model.NewBoolVar(f'b_{field}_{vc}')
                        model.Add(w_var >= min_thresh).OnlyEnforceIf(bv)
                        model.Add(w_var < min_thresh).OnlyEnforceIf(bv.Not())
                        objective_terms.append(reward * bv)
                        vc += 1
                    else:
                        # Base reward for reaching min_thresh (50% of the points)
                        base_reward = reward // 2
                        
                        bv = model.NewBoolVar(f'b_{field}_{vc}')
                        model.Add(w_var >= min_thresh).OnlyEnforceIf(bv)
                        model.Add(w_var < min_thresh).OnlyEnforceIf(bv.Not())
                        objective_terms.append(base_reward * bv)
                        vc += 1
                        
                        # Continuous reward for expanding up to max_thresh
                        capped_w = model.NewIntVar(0, PRECISION, f'cw_{field}_{vc}')
                        model.AddMinEquality(capped_w, [w_var, max_thresh])
                        vc += 1
                        
                        earned_w = model.NewIntVar(0, PRECISION, f'ew_{field}_{vc}')
                        model.Add(earned_w == capped_w).OnlyEnforceIf(bv)
                        model.Add(earned_w == 0).OnlyEnforceIf(bv.Not())
                        vc += 1
                        
                        scaled_reward = model.NewIntVar(0, reward, f'sr_{field}_{vc}')
                        # scaled_reward = floor(earned_w * (reward - base_reward) / max_thresh)
                        model.Add(max_thresh * scaled_reward <= earned_w * (reward - base_reward))
                        objective_terms.append(scaled_reward)
                        vc += 1
            else:
                # Fallback: continuous proxy (no pixel info available)
                capped_w = model.NewIntVar(0, 300, f'cw{vc}')
                model.AddMinEquality(capped_w, [w_var, 300])
                objective_terms.append(14 * capped_w)
                vc += 1
    
    if not left_vars:
        return None
    
    # ──────────────────────────────────────────────────────────────
    # STEP 2: Per-slot tiling
    # ──────────────────────────────────────────────────────────────
    for slot_idx in range(18):
        occupants = slot_occupants.get(slot_idx, [])
        if not occupants:
            continue
        
        seen = set()
        sigs = []
        for e in sorted(occupants, key=lambda x: x['base_center']):
            s = _get_sig(e)
            if s not in seen:
                seen.add(s)
                sigs.append(s)
        
        intervals = []
        total_width = []
        
        for sig in sigs:
            key = (sig, slot_idx)
            if key not in left_vars:
                continue
            w = model.NewIntVar(0, PRECISION, f'wi{vc}')
            model.Add(w == right_vars[key] - left_vars[key])
            iv = model.NewIntervalVar(left_vars[key], w, right_vars[key], f'iv{vc}')
            vc += 1
            intervals.append(iv)
            total_width.append(w)
        
        if intervals:
            # HARD Rule 1: NoOverlap
            model.AddNoOverlap(intervals)
            
            # HARD Rule 1.5: Relative Fairness Pruning
            # Prevent solver from starving blocks to 30px to feed others.
            # Max width can be at most 3.0x the min width in the same slot.
            if len(total_width) > 1:
                for w1 in total_width:
                    for w2 in total_width:
                        model.Add(10 * w1 <= 30 * w2)
            
            # Single slack = unused space in this slot
            slack = model.NewIntVar(0, PRECISION, f'sk{vc}')
            vc += 1
            model.Add(sum(total_width) + slack == PRECISION)
            objective_terms.append(-1000 * slack)
            
            # HARD Rule 4: Symmetry breaking
            first_key = (sigs[0], slot_idx)
            if first_key in left_vars:
                model.Add(left_vars[first_key] == 0)
            
            # HARD Rule: Ordering Hints (L_i <= L_j)
            prev_key = None
            for sig in sigs:
                key = (sig, slot_idx)
                if key in left_vars:
                    if prev_key is not None and prev_key in left_vars:
                        model.Add(left_vars[prev_key] <= left_vars[key])
                    prev_key = key
    
    # ──────────────────────────────────────────────────────────────
    # STEP 3: Cross-slot constraints
    # ──────────────────────────────────────────────────────────────
    overlap_terms = []
    processed_sigs = set()
    
    for e in events:
        sig = _get_sig(e)
        if sig in processed_sigs:
            continue
        processed_sigs.add(sig)
        
        start_slot = int(e['start_slot'])
        end_slot = int(e['end_slot'])
        
        L_list, R_list = [], []
        for s in range(start_slot, end_slot):
            key = (sig, s)
            if key in left_vars and key in right_vars:
                L_list.append(left_vars[key])
                R_list.append(right_vars[key])
        
        has_shrunk_prev = None
        
        for i in range(1, len(L_list)):
            lp, rp = L_list[i-1], R_list[i-1]
            lc, rc = L_list[i], R_list[i]
            
            # HARD Rule 3: Minimum overlap
            max_left = model.NewIntVar(0, PRECISION, f'ml{vc}')
            min_right = model.NewIntVar(0, PRECISION, f'mr{vc}')
            model.AddMaxEquality(max_left, [lp, lc])
            model.AddMinEquality(min_right, [rp, rc])
            model.Add(max_left + MIN_WIDTH_BRANCH <= min_right)
            vc += 2
            
            # SOFT Rule 6: Overlap reward
            overlap_terms.append(min_right - max_left)
            
            # ──────────────────────────────────────────────────────────────
            # HARD Rule 5: Unimodal Hourglass Prevention
            # "Once it starts to shrink, slots after that can't exceed prior boundaries"
            # ──────────────────────────────────────────────────────────────
            l_in = model.NewBoolVar(f'lin_{vc}')
            model.Add(lc > lp).OnlyEnforceIf(l_in)
            model.Add(lc <= lp).OnlyEnforceIf(l_in.Not())
            
            r_in = model.NewBoolVar(f'rin_{vc}')
            model.Add(rc < rp).OnlyEnforceIf(r_in)
            model.Add(rc >= rp).OnlyEnforceIf(r_in.Not())
            
            is_shrinking_now = model.NewBoolVar(f'snow_{vc}')
            model.AddBoolOr([l_in, r_in]).OnlyEnforceIf(is_shrinking_now)
            model.AddBoolAnd([l_in.Not(), r_in.Not()]).OnlyEnforceIf(is_shrinking_now.Not())
            
            has_shrunk_curr = model.NewBoolVar(f'hsc_{vc}')
            if has_shrunk_prev is not None:
                model.AddBoolOr([has_shrunk_prev, is_shrinking_now]).OnlyEnforceIf(has_shrunk_curr)
                model.AddBoolAnd([has_shrunk_prev.Not(), is_shrinking_now.Not()]).OnlyEnforceIf(has_shrunk_curr.Not())
                
                # If it had shrunk PREVIOUSLY, it cannot expand at all NOW
                model.Add(lc >= lp).OnlyEnforceIf(has_shrunk_prev)
                model.Add(rc <= rp).OnlyEnforceIf(has_shrunk_prev)
            else:
                model.Add(has_shrunk_curr == is_shrinking_now)
            
            has_shrunk_prev = has_shrunk_curr
            
            # ──────────────────────────────────────────────────────────────
            # HARD Rule: Staircase Prevention (Ultra-fast continuous math)
            # ──────────────────────────────────────────────────────────────
            lmr = model.NewIntVar(0, PRECISION, f'lmr_{vc}')
            model.AddMaxEquality(lmr, [lc - lp, 0])
            rmr = model.NewIntVar(0, PRECISION, f'rmr_{vc}')
            model.AddMaxEquality(rmr, [rc - rp, 0])
            stair_r = model.NewIntVar(0, PRECISION, f'str_{vc}')
            model.AddMinEquality(stair_r, [lmr, rmr])
            model.Add(stair_r == 0) # Forbid right staircase
            
            lml = model.NewIntVar(0, PRECISION, f'lml_{vc}')
            model.AddMaxEquality(lml, [lp - lc, 0])
            rml = model.NewIntVar(0, PRECISION, f'rml_{vc}')
            model.AddMaxEquality(rml, [rp - rc, 0])
            stair_l = model.NewIntVar(0, PRECISION, f'stl_{vc}')
            model.AddMinEquality(stair_l, [lml, rml])
            model.Add(stair_l == 0) # Forbid left staircase
            
            # ──────────────────────────────────────────────────────────────
            # SOFT Rule 12: Visual Edge Misalignment Penalty (Rectangularity)
            # ──────────────────────────────────────────────────────────────
            # A perfect rectangle has 4 edges. Any shift creates extra edges.
            # We strongly penalize any shift to squash 1-5px misalignments.
            # Using 5000 weight to overpower up to 50 units of fairness or 10 units of overlap.
            is_l_diff = model.NewBoolVar(f'ldiff_{vc}')
            model.Add(lc != lp).OnlyEnforceIf(is_l_diff)
            model.Add(lc == lp).OnlyEnforceIf(is_l_diff.Not())
            
            is_r_diff = model.NewBoolVar(f'rdiff_{vc}')
            model.Add(rc != rp).OnlyEnforceIf(is_r_diff)
            model.Add(rc == rp).OnlyEnforceIf(is_r_diff.Not())
            
            objective_terms.append(-5000 * is_l_diff)
            objective_terms.append(-5000 * is_r_diff)
            
            vc += 14
    
    # ──────────────────────────────────────────────────────────────
    # STEP 4: Objective terms
    # ──────────────────────────────────────────────────────────────
    OVERLAP_WEIGHT = 500
    for ow in overlap_terms:
        objective_terms.append(OVERLAP_WEIGHT * ow)
    
    # ──────────────────────────────────────────────────────────────
    # STEP 5: Solve
    # ──────────────────────────────────────────────────────────────
    if objective_terms:
        model.Maximize(sum(objective_terms))
    
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 2.0
    solver.parameters.log_search_progress = False
    solver.parameters.linearization_level = 0 
    solver.parameters.num_search_workers = 8
    
    status = solver.Solve(model)
    elapsed = (time.perf_counter() - t0) * 1000
    
    if status == cp_model.MODEL_INVALID:
        print("Validation Error:", model.Validate())
    
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        result = {}
        for (sig, slot_idx), lv in left_vars.items():
            if sig not in result:
                result[sig] = {}
            result[sig][slot_idx] = (
                solver.Value(lv) / PRECISION,
                solver.Value(right_vars[(sig, slot_idx)]) / PRECISION
            )
        status_name = "OPTIMAL" if status == cp_model.OPTIMAL else "FEASIBLE"
        print(f"[LayoutSolver] {status_name} in {elapsed:.1f}ms | {vc} vars | {len(result)} events")
        return result
    else:
        print(f"[LayoutSolver] FAILED ({status}) in {elapsed:.1f}ms — falling back to heuristic")
        return None

