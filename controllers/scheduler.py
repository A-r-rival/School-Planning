# -*- coding: utf-8 -*-
"""
Scheduler Module using Google OR-Tools
Handles automatic schedule generation with hard and soft constraints
"""
from ortools.sat.python import cp_model
from typing import List, Dict, Tuple, Optional
import collections
import re
import sys
import os
# curriculum_data is in database/
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database"))
import curriculum_data
from controllers.scheduler_services import (
    CourseRepository, CurriculumResolver, CourseMerger, 
    SchedulableCourseBuilder, CourseRole
)

# Constants
SLOTS_PER_DAY = 9  # Hours per day (08:00-17:00)

def to_minutes(time_str: str) -> int:
    """Convert HH:MM string to minutes since midnight."""
    try:
        if not time_str or ':' not in time_str:
            return 0
        h, m = map(int, time_str.split(':'))
        return h * 60 + m
    except ValueError:
        return 0

class ORToolsScheduler:
    def __init__(self, model):
        """
        Initialize the scheduler with the data model
        Args:
            model: The ScheduleModel instance containing database connections
        """
        self.db_model = model
        # Parameters (State)
        self.courses = []
        self.rooms = []
        self.teachers = []
        self.time_slots = []
        
        # Solver Components
        self.cp_model = None
        self.solver = cp_model.CpSolver()
        self.vars = {}      # (c_idx, r_id, s_id) -> bool_var
        self.room_vars = {} # (c_idx, r_id) -> bool_var

    def load_data(self):
        """Load necessary data from database. Called once."""
        # 1. Load Rooms
        self.rooms = self.db_model.aktif_derslikleri_getir() 
        self.rooms.sort(key=lambda x: x[0]) # Deterministic Sort by ID
        print(f"Loaded {len(self.rooms)} rooms.")
        
        # 2. Load Courses 
        self.courses = self._fetch_all_course_instances()
        
        # 3. Load Teachers
        self.teachers = self.db_model.get_all_teachers_with_ids()
        
        # 4. Define Time Slots
        # 4. Define Time Slots
        days = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma']
        # Added 08:00
        hours = ['08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00']
        self.time_slots = []
        for d_idx, day in enumerate(days):
            for h_idx, hour in enumerate(hours):
                end_hour = f"{int(hour[:2])+1}:00"
                self.time_slots.append({
                    'id': d_idx * SLOTS_PER_DAY + h_idx,
                    'day': day,
                    'start_str': hour,
                    'end_str': end_hour,
                    'start_min': to_minutes(hour),
                    'end_min': to_minutes(end_hour)
                })
        
        # 5. Load Course Faculty Map
        self.course_faculties = self.db_model.get_course_faculty_map()

    def _fetch_all_course_instances(self):
        """
        Refactored Fetching Pipeline using separated services.
        1. Repository: Fetch Raw Data
        2. Resolver: Determine Contexts (Core vs Elective)
        3. Merger: Create Physical Courses
        4. Builder: Create Schedulable Blocks
        """
        # 1. Instantiate Services
        repo = CourseRepository(self.db_model)
        resolver = CurriculumResolver()
        merger = CourseMerger()
        builder = SchedulableCourseBuilder()
        
        # 2. Fetch Raw Data
        raw_rows = repo.fetch_course_rows()
        
        # 3. Populate Metadata (Required for Constraints)
        self.group_metadata = {}
        for r in raw_rows:
            if r.group_id and r.department:
                self.group_metadata[r.group_id] = (r.department, r.class_year)
        
        # 4. Merge & Build
        physical_courses = merger.merge(raw_rows, resolver)
        print(f"DEBUG: Merged into {len(physical_courses)} physical courses.")
        
        self.courses = builder.build_blocks(physical_courses)
        
        # FIX: Sort courses deterministically for index stability
        self.courses.sort(key=lambda x: (x['name'], x['instance'], x['type']))
        
        print(f"DEBUG: Pipeline generated {len(self.courses)} schedulable blocks.")
        
        if not self.courses:
            print("CRITICAL DEBUG: No courses found! Checking repositories...")
            print(f"Raw Rows: {len(raw_rows)}")
            if raw_rows:
                print(f"Sample Row: {raw_rows[0]}")
            
        return self.courses

    def create_variables(self, ignore_fixed_rooms=False, optional_indices=None, active_indices=None):
        """Create CP variables and initialize model logic with strict contiguity."""
        if optional_indices is None:
            optional_indices = set()
        else:
            optional_indices = set(optional_indices)
            
        if active_indices is not None:
            active_indices = set(active_indices)

        self.vars = {} 
        self.room_vars = {}
        self.starts = {} # (c_idx, r_id, s_id) -> bool_var (Is this the START slot?)
        
        print(f"DEBUG: Creating variables for {len(self.courses)} courses...", flush=True)
        if hasattr(self, 'cp_model') and self.cp_model:
             print("DEBUG: CP Model exists.", flush=True)
        else:
             print("CRITICAL ERROR: CP Model is None in create_variables!", flush=True)

        count = 0
        for c_idx, course in enumerate(self.courses):
            # Optimization: Skip variable creation for courses not in active phase
            if active_indices is not None and c_idx not in active_indices:
                continue
                
            duration = course['duration']
            
            # Duration Safety Check
            if duration > SLOTS_PER_DAY:
                 print(f"CRITICAL WARNING: Course {course['name']} duration ({duration}) exceeds SLOTS_PER_DAY ({SLOTS_PER_DAY}). It will verify be infeasible.")
                 # We could skip it to avoid breaking the solver, or let it fail.
                 # Let's skip creating variables for it so it doesn't crash calculations
                 continue

            # 1. Create Room Variables
            possible_rooms = []
            viable_rooms_count = 0
            
            for r in self.rooms:
                r_id = r[0]
                
                # Filter rooms logic
                if not ignore_fixed_rooms and course['fixed_room'] and course['fixed_room'] != r_id:
                     continue
                
                # Room Type Logic
                # Strict matching based on course 'type' provided by Builder
                # --- ROBUST ROOM TYPE LOGIC ---
                
                # 1. Normalize Room Type
                room_type_str = ""
                if len(r) > 2 and r[2]:
                    room_type_str = str(r[2]).lower()
                
                # Check capabilities
                is_lab_room = any(k in room_type_str for k in ["laboratuvar", "lab"])
                is_amfi = "amfi" in room_type_str
                
                # 2. Normalize Course Type
                raw_type = course.get('type')
                course_type_norm = str(raw_type).lower() if raw_type else "teori"
                
                # Check requirements
                is_lab_course = "lab" in course_type_norm
                
                # DEBUG: Trace specifically for Derslik-1 or questionable assignments
                if r[1] == "Derslik-1" and is_lab_course:
                     # This should theoretically NEVER happen if logic works
                     pass

                # 3. Apply Usage Rules
                
                # Rule A: Lab Courses -> ONLY in Lab Rooms, NEVER in Amfi
                if is_lab_course:
                    if not is_lab_room:
                        continue # Skip non-lab rooms
                    if is_amfi:
                        continue # Skip amfis (even if named 'Lab Amfi' etc)
                        
                # Rule B: Non-Lab Courses (Teori/Uygulama) -> NEVER in Lab Rooms
                # (Unless strictly overridden by fixed_room, but that's handled above)
                else:
                    if is_lab_room:
                        continue # Keep classrooms for theory
                
                # Create Room Var
                r_var = self.cp_model.NewBoolVar(f'c{c_idx}_r{r_id}')
                self.room_vars[(c_idx, r_id)] = r_var
                possible_rooms.append(r_var)

                # 2. Identify Valid Start Slots (Enforce Same Day & Contiguity)
                valid_start_vars = []
                
                for s in self.time_slots:
                    start_id = s['id']
                    end_id = start_id + duration - 1
                    
                    # Check 1: Must end within total slots
                    if end_id >= len(self.time_slots):
                        continue
                        
                    # Check 2: Must be on SAME DAY
                    # Slots 0-8 (Day 0), 9-17 (Day 1)...
                    start_day = start_id // SLOTS_PER_DAY
                    end_day = end_id // SLOTS_PER_DAY
                    
                    if start_day == end_day:
                        # This is a valid start slot
                        s_var = self.cp_model.NewBoolVar(f'start_c{c_idx}_r{r_id}_s{start_id}')
                        self.starts[(c_idx, r_id, start_id)] = s_var
                        valid_start_vars.append(s_var)
                
                # Constraint: If assigned to room R, MUST have exactly ONE start time
                if valid_start_vars:
                    self.cp_model.Add(sum(valid_start_vars) == r_var)
                    viable_rooms_count += 1
                else:
                    # Duration too long for any day? Disable room
                    self.cp_model.Add(r_var == 0)
                    # print(f"DEBUG: Course {c_idx} Room {r_id} has NO valid start slots.", flush=True)

                # 3. Create Occupancy Vars (self.vars) linked to Starts
                # Occ[t] = Sum(Start[s]) for all s where s <= t < s+dur
                for t in self.time_slots:
                    t_id = t['id']
                    
                    # Fix: Ensure bleeding does not cross days
                    t_day = t_id // SLOTS_PER_DAY
                    
                    relevant_starts = []
                    min_s = max(0, t_id - duration + 1)
                    max_s = t_id
                    
                    for s_id in range(min_s, max_s + 1):
                        # Ensure the start slot 's' is on the SAME DAY as 't'
                        if (s_id // SLOTS_PER_DAY) == t_day:
                            if (c_idx, r_id, s_id) in self.starts:
                                relevant_starts.append(self.starts[(c_idx, r_id, s_id)])
                    
                    occ_var = self.cp_model.NewBoolVar(f'c{c_idx}_r{r_id}_s{t_id}')
                    self.vars[(c_idx, r_id, t_id)] = occ_var
                    
                    if relevant_starts:
                        self.cp_model.Add(occ_var == sum(relevant_starts))
                    else:
                        self.cp_model.Add(occ_var == 0)
                        
                    # Note: We don't need 'AddImplication' anymore, it's covered by the sum structure.
                    # If r_var is 0, valid_starts is 0, so relevant_starts is 0, so occ_var is 0.

            # Constraint: Each course must be assigned to EXACTLY ONE room
            if viable_rooms_count == 0:
                if c_idx not in optional_indices:
                     msg = f"CRITICAL WARNING: Course {self.courses[c_idx]['name']} (ID {c_idx}) has NO VIABLE ROOMS (Duration/Slot Issue)! Duration: {self.courses[c_idx]['duration']}. Slots Per Day: {SLOTS_PER_DAY}\n"
                     print(msg, flush=True)
                     with open("debug_infeasibility_report.txt", "a", encoding="utf-8") as f:
                         f.write(msg)
            
            if possible_rooms:
                if c_idx in optional_indices:
                     self.cp_model.Add(sum(possible_rooms) <= 1)
                else:
                     self.cp_model.Add(sum(possible_rooms) == 1)
        
        print(f"DEBUG: Created {len(self.starts)} start variables, {len(self.vars)} occupancy variables")

    def add_hard_constraints(self, include_teacher_unavailability=True):
        """Add system-wide hard constraints."""
        
        # 1. Room Conflict
        for r in self.rooms:
            r_id = r[0]
            for s in self.time_slots:
                s_id = s['id']
                active_vars = []
                for c_idx in range(len(self.courses)):
                    if (c_idx, r_id, s_id) in self.vars:
                        active_vars.append(self.vars[(c_idx, r_id, s_id)])
                if active_vars:
                    self.cp_model.Add(sum(active_vars) <= 1)

        # 2. Teacher Conflict
        teacher_slot_vars = collections.defaultdict(list)
        for key, var in self.vars.items():
            c_idx, r_id, s_id = key
            for t_id in self.courses[c_idx]['teacher_ids']:
                teacher_slot_vars[(t_id, s_id)].append(var)
        
        for vars_list in teacher_slot_vars.values():
            self.cp_model.Add(sum(vars_list) <= 1)
            
        # 3. Teacher Room Preferences (NEW)
        # Apply constraints based on room_request
        print("DEBUG: Calling add_teacher_room_preferences...", flush=True)
        self.add_teacher_room_preferences()
        print("DEBUG: add_teacher_room_preferences DONE.", flush=True)

        # 4. Teacher Unavailability
        if include_teacher_unavailability:
            print("DEBUG: Starting Teacher Unavailability constraints...", flush=True)
            try:
                # Use DB Model service which handles mapping correctly
                for t in self.teachers:
                    t_id = t[0]
                    unavail = self.db_model.get_teacher_unavailability(t_id)
                    # unavail comes as list of (day, start, end, ...?)
                    # Assuming get_teacher_unavailability returns usable data or we fallback
                    
                    if unavail:
                         for u in unavail:
                            # u format: (day, start, end, ...) 
                            # We need to map this to slots
                            u_day, u_start, u_end = u[0], u[1], u[2]
                            # Convert to minutes for overlap check
                            try:
                                u_start_min = to_minutes(u_start)
                                u_end_min = to_minutes(u_end)
                            except Exception as e:
                                print(f"ERROR: Invalid time format for teacher {t_id}: {u_start}-{u_end} ({e})", flush=True)
                                continue
                            
                            for s in self.time_slots:
                                if s['day'] == u_day:
                                    # Check time overlap
                                    if (u_start_min < s['end_min'] and u_end_min > s['start_min']):
                                        # Block this slot for this teacher
                                        if (t_id, s['id']) in teacher_slot_vars:
                                            for var in teacher_slot_vars[(t_id, s['id'])]:
                                                self.cp_model.Add(var == 0)
            except Exception as e:
                import traceback
                print(f"CRITICAL ERROR in Teacher Unavailability: {e}", flush=True)
                traceback.print_exc()

        # 4. Teacher Day Span Optimization (Sliding Window)
        print("DEBUG: Teacher Day Span Optimization DONE (SKIPPED).", flush=True)

        # 5. Student Group Conflict (Refactored)
        self.add_student_group_conflicts()
        print("DEBUG: Executed add_student_group_conflicts", flush=True)
        
        # 6. OPTIONAL: Different Days Soft Constraint
        ENABLE_DIFFERENT_DAYS_CONSTRAINT = False
        if ENABLE_DIFFERENT_DAYS_CONSTRAINT:
            print("DEBUG: Adding Soft Constraints (Different Days)...")
            course_parts = collections.defaultdict(list)
            for c_idx, course in enumerate(self.courses):
                if 'parent_key' in course:
                    course_parts[course['parent_key']].append(c_idx)
            
            penalties = []
            for p_key, indices in course_parts.items():
                if len(indices) < 2: continue
                
                for i in range(len(indices)):
                    for j in range(i + 1, len(indices)):
                        idx1, idx2 = indices[i], indices[j]
                        for d_idx in range(5):
                            days_slots = [s for s in self.time_slots if s['id'] // SLOTS_PER_DAY == d_idx]
                            
                            vars1 = [self.vars[(idx1, r_id, s['id'])] for s in days_slots for r_id in [r[0] for r in self.rooms] if (idx1, r_id, s['id']) in self.vars]
                            vars2 = [self.vars[(idx2, r_id, s['id'])] for s in days_slots for r_id in [r[0] for r in self.rooms] if (idx2, r_id, s['id']) in self.vars]
                            
                            if vars1 and vars2:
                                b1, b2 = self.cp_model.NewBoolVar(f'p{idx1}d{d_idx}'), self.cp_model.NewBoolVar(f'p{idx2}d{d_idx}')
                                self.cp_model.Add(sum(vars1) > 0).OnlyEnforceIf(b1)
                                self.cp_model.Add(sum(vars1) == 0).OnlyEnforceIf(b1.Not())
                                self.cp_model.Add(sum(vars2) > 0).OnlyEnforceIf(b2)
                                self.cp_model.Add(sum(vars2) == 0).OnlyEnforceIf(b2.Not())
                                
                                conflict = self.cp_model.NewBoolVar(f'c_{idx1}_{idx2}_{d_idx}')
                                self.cp_model.AddBoolAnd([b1, b2]).OnlyEnforceIf(conflict)
                                self.cp_model.AddBoolOr([b1.Not(), b2.Not()]).OnlyEnforceIf(conflict.Not())
                                penalties.append(conflict)
            
            if penalties:
                self.cp_model.Minimize(sum(penalties))


    def get_role_for_group(self, course, group_dept: str, group_year: int) -> CourseRole:
        """Determines the role of a course for a specific student group context."""
        for ctx in course['program_contexts']:
            if ctx.department == group_dept and ctx.year == group_year:
                return ctx.role
        return CourseRole.CORE

    def add_student_group_conflicts(self):
        """
        Refactored Student Group Conflicts Logic.
        Uses ProgramContexts to distinguish Core vs Elective roles per group.
        Populates self.group_slot_data for use in other soft constraints.
        """
        print("DEBUG: Starting add_student_group_conflicts...", flush=True)
        try:
            # 1. Structure vars by Group & Slot
            group_slot_vars = collections.defaultdict(list)
            for key, var in self.vars.items():
                c_idx, r_id, s_id = key
                course = self.courses[c_idx]
                for g_id in course['group_ids']:
                    if g_id in self.group_metadata:
                        group_slot_vars[(g_id, s_id)].append((var, course))

            print(f"DEBUG: Processed vars into {len(group_slot_vars)} group-slot entries.", flush=True)

            # 2. Reset and Populate Group Slot Data (Metadata for soft constraints)
            self.group_slot_data = collections.defaultdict(lambda: {'cores': [], 'pools': collections.defaultdict(list)})

            # 3. Apply Constraints & Categories
            print("DEBUG: Applying constraints...", flush=True)

            # Refactor: Aggregate items by (Dept, Year) to handle split Group IDs
            # This fixes the issue where Service Courses (Separate Group ID) don't conflict with Dept Courses
            semantic_group_vars = collections.defaultdict(list)
            
            for (g_id, s_id), items in group_slot_vars.items():
                g_desc = self.group_metadata[g_id]
                g_dept, g_year = g_desc if isinstance(g_desc, tuple) else (g_desc, None)
                
                # Key by (Dept, Year, Slot)
                semantic_key = (g_dept, g_year, s_id)
                # Store items along with their original group_id for reference if needed
                for item in items:
                    semantic_group_vars[semantic_key].append((item[0], item[1], g_id))

            print(f"DEBUG: Aggregated into {len(semantic_group_vars)} semantic group-slots.", flush=True)

            count = 0
            for (g_dept, g_year, s_id), items in semantic_group_vars.items():
                count += 1
                if count % 1000 == 0:
                     print(f"DEBUG: Processing semantic group-slot {count}/{len(semantic_group_vars)}", flush=True)
                
                core_vars = []
                elective_vars = []
                
                # Deduplication set (to avoid adding same var twice if it belongs to multiple group_ids mapped to same semantic group)
                seen_vars = set()

                for var, course, origin_g_id in items:
                    if var in seen_vars:
                         continue
                    seen_vars.add(var)

                    role = self.get_role_for_group(course, g_dept, g_year)
                    
                    if role == CourseRole.CORE:
                        core_vars.append(var)
                        # We map back to origin_g_id for data storage? 
                        # Or maybe we need to store it under ALL group IDs?
                        # Soft constraints use group_slot_data which is keyed by g_id.
                        # So we should populate group_slot_data here too?
                        # Actually group_slot_data is populated based on raw g_id earlier?
                        # Re-populating here might be complex.
                        # Let's rely on the raw g_id loop for populating group_slot_data if needed?
                        # Wait, group_slot_data logic was inside the loop I'm removing.
                        # I must re-implement group_slot_data population.
                        pass # See below
                    else:
                        elective_vars.append(var)
                
                # Populate group_slot_data for Soft Constraints
                # We need to broadcast this decision back to the individual group_ids?
                # Actually, soft constraints iterate group_slot_data.
                # If we aggregate here, we should populate group_slot_data for each origin_g_id found?
                # Let's do it inside the loop.
                for var, course, origin_g_id in items:
                     # Identify pool logic...
                     role = self.get_role_for_group(course, g_dept, g_year)
                     if role == CourseRole.CORE:
                         self.group_slot_data[(origin_g_id, s_id)]['cores'].append(var)
                     else:
                         # Pool logic
                         pool_code = "UNKNOWN"
                         for ctx in course['program_contexts']:
                             if ctx.department == g_dept and ctx.year == g_year and ctx.role == CourseRole.ELECTIVE:
                                 pool_code = ctx.pool_code
                                 break
                         if pool_code:
                             self.group_slot_data[(origin_g_id, s_id)]['pools'][pool_code].append(var)


                
                # Constraint A: Strict Core Conflict (Max 1 Core)
                # Now applies across ALL groups for this Dept/Year
                if len(core_vars) > 1:
                    # FIX: Changed back to HARD Constraint
                    self.cp_model.Add(sum(core_vars) <= 1)
                
                # Constraint B: Core vs Any Elective Conflict
                if core_vars and elective_vars:
                    # Sanitize name to prevent encoding/length issues
                    safe_dept = "".join(x for x in str(g_dept) if x.isalnum())
                    ae_name = f'ae_{safe_dept}_{g_year}_{s_id}'
                    any_elec = self.cp_model.NewBoolVar(ae_name)
                    self.cp_model.AddMaxEquality(any_elec, elective_vars)
                    
                    # FIX: Changed back to HARD Constraint
                    # Core + Any Elective <= 1
                    self.cp_model.Add(sum(core_vars) + any_elec <= 1)

        except Exception as e:
            import traceback
            print(f"CRITICAL ERROR in add_student_group_conflicts: {e}", flush=True)
            traceback.print_exc()

        print("DEBUG: add_student_group_conflicts DONE.", flush=True)
        


    def add_teacher_room_preferences(self):
        """
        Apply constraints based on teacher room requests.
        Keywords: 'zemin', 'giriş', 'k1', 'k2', 'lab', or specific room names.
        
        DEBUG VERSION: Logs viable room counts to identify infeasibility.
        """
        debug_log = []
        debug_log.append("=== ROOM PREFERENCE DEBUG LOG ===\n")
        
        for t in self.teachers:
            t_id = t[0]
            if len(t) < 3: 
                continue
            
            request = t[2]
            if not request: 
                continue
            
            req_lower = request.lower()
            
            # Identify courses taught by this teacher
            teacher_course_indices = []
            try:
                for c_idx, course in enumerate(self.courses):
                    if 'teacher_ids' not in course:
                         continue
                    if t_id in course['teacher_ids']:
                        teacher_course_indices.append(c_idx)
            except Exception as e:
                debug_log.append(f"ERROR in course lookup for teacher {t_id}: {e}\n")
                continue
            
            if not teacher_course_indices: 
                continue
            
            try:
                t_name = f"Teacher {t_id}"
                if len(t) > 1:
                    t_name = f"{t[1]}" + (f" {t[2]}" if len(t) > 2 and isinstance(t[2], str) and t[2] != request else "")
                
                debug_log.append(f"\nTeacher ID={t_id}, Request=\"{request}\"\n")
                debug_log.append(f"  Courses: {len(teacher_course_indices)}\n")
                
                # Count viable rooms BEFORE applying constraints for each course
                # DETAILED LOGGING: Show WHY courses have limited room options
                viable_before = {}
                for c_idx in teacher_course_indices:
                    course = self.courses[c_idx]
                    course_name = course.get('name', f'Course{c_idx}')
                    course_type = course.get('type', 'Unknown')
                    course_capacity = course.get('group_size', 'Unknown')
                    
                    # Find which rooms are viable for this course
                    viable_rooms = [(r[0], r[1], r[3], r[4]) for r in self.rooms if (c_idx, r[0]) in self.room_vars]
                    viable_count = len(viable_rooms)
                    viable_before[c_idx] = viable_count
                    
                    debug_log.append(f"    Course {c_idx} ({course_name}):\n")
                    debug_log.append(f"      Type: {course_type}, Capacity Need: {course_capacity}\n")
                    debug_log.append(f"      Viable rooms BEFORE teacher pref: {viable_count}\n")
                    
                    if viable_count <= 3:
                        # Show details for courses with very limited options
                        debug_log.append(f"      Viable room details:\n")
                        for r_id, r_name, r_cap, r_floor in viable_rooms:
                            debug_log.append(f"        - {r_name} (Cap={r_cap}, Floor={r_floor})\n")
                
                # Track which rooms we're banning
                banned_rooms_count = 0
                
                # Logic 1: Floor Constraints
                target_floor = None
                if any(k in req_lower for k in ['zemin', 'giriş', 'kat 0', '0. kat']):
                    target_floor = 0
                elif any(k in req_lower for k in ['kat 1', '1. kat']):
                    target_floor = 1
                elif any(k in req_lower for k in ['kat 2', '2. kat']):
                    target_floor = 2
                elif any(k in req_lower for k in ['kat 3', '3. kat']):
                    target_floor = 3
                    
                if target_floor is not None:
                    debug_log.append(f"  Detected Floor Request: {target_floor}\n")
                    # Count how many rooms are on this floor
                    floor_rooms = [r for r in self.rooms if (r[4] if len(r) > 4 else 0) == target_floor]
                    debug_log.append(f"  Rooms on Floor {target_floor}: {len(floor_rooms)}\n")
                    
                    for c_idx in teacher_course_indices:
                        for r in self.rooms:
                            r_id = r[0]
                            r_floor = r[4] if len(r) > 4 else 0
                            
                            if r_floor != target_floor:
                                if (c_idx, r_id) in self.room_vars:
                                    self.cp_model.Add(self.room_vars[(c_idx, r_id)] == 0)
                                    banned_rooms_count += 1
                
                # Logic 2: Lab Constraint
                # IMPORTANT: Teacher lab preference should ONLY apply to lab-type courses
                # If teacher requests "Lab" but teaches theory courses, don't force theory into labs!
                if 'lab' in req_lower:
                    debug_log.append(f"  Detected Lab Request\n")
                    lab_rooms = [r for r in self.rooms if 'lab' in r[1].lower()]
                    debug_log.append(f"  Lab Rooms: {len(lab_rooms)}\n")
                    
                    for c_idx in teacher_course_indices:
                        # Check if THIS specific course is a lab course
                        course_type = self.courses[c_idx].get('type', '').lower()
                        is_lab_course = 'lab' in course_type
                        
                        if not is_lab_course:
                            # This is a theory course - teacher lab preference doesn't apply
                            debug_log.append(f"    Skipping Course {c_idx} (theory course, teacher lab pref doesn't apply)\n")
                            continue
                        
                        # This IS a lab course - apply teacher's lab room preference
                        for r in self.rooms:
                            r_id = r[0]
                            r_name = r[1].lower()
                            is_lab_room = 'lab' in r_name
                            if not is_lab_room:
                                 if (c_idx, r_id) in self.room_vars:
                                    self.cp_model.Add(self.room_vars[(c_idx, r_id)] == 0)
                                    banned_rooms_count += 1

                # Logic 3: Specific Room Name
                valid_room_ids = []
                for r in self.rooms:
                    if r[1].lower() in req_lower:
                         valid_room_ids.append(r[0])
                
                if valid_room_ids:
                    debug_log.append(f"  Detected Specific Room Request: {[r[1] for r in self.rooms if r[0] in valid_room_ids]}\n")
                    for c_idx in teacher_course_indices:
                        for r in self.rooms:
                             r_id = r[0]
                             if r_id not in valid_room_ids:
                                 if (c_idx, r_id) in self.room_vars:
                                     self.cp_model.Add(self.room_vars[(c_idx, r_id)] == 0)
                                     banned_rooms_count += 1

                debug_log.append(f"  Total room-course combinations banned: {banned_rooms_count}\n")
                
                # Count viable rooms AFTER applying constraints
                for c_idx in teacher_course_indices:
                    # We can't directly count viable rooms after adding constraints,
                    # but we can calculate based on floor matching
                    viable_after = 0
                    for r in self.rooms:
                        r_id = r[0]
                        if (c_idx, r_id) not in self.room_vars:
                            continue
                        
                        # Check if this room matches the preference
                        matches = True
                        if target_floor is not None:
                            r_floor = r[4] if len(r) > 4 else 0
                            if r_floor != target_floor:
                                matches = False
                        if 'lab' in req_lower:
                            if 'lab' not in r[1].lower():
                                matches = False
                        if valid_room_ids:
                            if r_id not in valid_room_ids:
                                matches = False
                        
                        if matches:
                            viable_after += 1
                    
                    course_name = self.courses[c_idx].get('name', f'Course{c_idx}')
                    if viable_after == 0:
                        debug_log.append(f"    *** CRITICAL: Course {c_idx} ({course_name}) has ZERO viable rooms after constraint! ***\n")
                    else:
                        debug_log.append(f"    Course {c_idx} ({course_name}): {viable_after} viable rooms AFTER constraint\n")

            except Exception as e:
                import traceback
                debug_log.append(f"ERROR processing teacher {t_id}: {e}\n")
                debug_log.append(traceback.format_exc())
        
        # Write debug log to file
        with open("room_preference_debug.txt", "w", encoding="utf-8") as f:
            f.writelines(debug_log)
        
        print("DEBUG: Room preference constraints applied. Log written to room_preference_debug.txt", flush=True)

                # raise e 



    def add_soft_constraints_consecutive(self):
        """
        Soft Constraint: Encourage different session types (T/U/L) to be on DIFFERENT days.
        Simplified version using day-level granularity to avoid variable explosion.
        """
        return
        


    def solve(self):
        """Solve with 2-Phase Strategy (Core then Elective) and Fallbacks."""
        self.load_data()
        
        # --- Pre-Solve Capacity Check ---
        total_demand = sum(c['duration'] for c in self.courses)
        total_capacity = len(self.rooms) * len(self.time_slots)
        
        # Room Type Capacity Check
        lab_rooms = [r for r in self.rooms if any(k in (str(r[2]) if len(r)>2 else "").lower() for k in ["lab", "laboratuvar"])]
        std_rooms = [r for r in self.rooms if r not in lab_rooms]
        
        lab_courses = [c for c in self.courses if c.get('type') == 'Lab']
        std_courses = [c for c in self.courses if c not in lab_courses]
        
        lab_demand = sum(c['duration'] for c in lab_courses)
        std_demand = sum(c['duration'] for c in std_courses)
        
        lab_capacity = len(lab_rooms) * len(self.time_slots)
        std_capacity = len(std_rooms) * len(self.time_slots)
        
        print(f"\n[DIAGNOSTIC] Capacity Check:")
        print(f"  - Total: Needed {total_demand} / Cap {total_capacity}")
        print(f"  - Labs : Needed {lab_demand} / Cap {lab_capacity} (Rooms: {len(lab_rooms)})")
        print(f"  - Theory: Needed {std_demand} / Cap {std_capacity} (Rooms: {len(std_rooms)})")
        
        if total_demand > total_capacity:
            print(f"CRITICAL WARNING: Demand exceeds Capacity!")
        if lab_demand > lab_capacity:
             print(f"CRITICAL WARNING: LAB Demand exceeds LAB Capacity!")
             
        # Check Fixed Room Overbooking
        fixed_room_demand = collections.defaultdict(int)
        for c in self.courses:
            if c.get('fixed_room'):
                fixed_room_demand[c['fixed_room']] += c['duration']
        
        for r in self.rooms:
            r_id = r[0]
            demand = fixed_room_demand.get(r_id, 0)
            capacity = len(self.time_slots) # 45
            if demand > capacity:
                 print(f"CRITICAL WARNING: Room {r[1]} (ID {r_id}) is OVERBOOKED by Fixed Courses! Demand {demand} > Cap {capacity}", flush=True)
            
        # Segregate for diagnostics and optional handling
        # --- AGGRESSIVE DATA VALIDATION (DEBUGGING CRASH) ---
        print("\n=== DATA VALIDATION START ===", flush=True)
        try:
            print(f"Total Courses: {len(self.courses)}")
            print(f"Total Rooms: {len(self.rooms)}")
            print(f"Total Slots: {len(self.time_slots)}")
            
            # 1. Validate Time Slots
            for i, slot in enumerate(self.time_slots):
                if not isinstance(slot.get('id'), int):
                    print(f"CRITICAL: Slot {i} has non-int ID: {slot.get('id')} type {type(slot.get('id'))}")
                if slot.get('id') < 0:
                     print(f"CRITICAL: Slot {i} has negative ID: {slot.get('id')}")

            # 2. Validate Rooms
            for i, room in enumerate(self.rooms):
                # room is tuple (id, name, type?)
                if not isinstance(room[0], int):
                    print(f"CRITICAL: Room {i} at index 0 (ID) is not int: {room[0]} type {type(room[0])}")
                
            # 3. Validate Courses
            for i, course in enumerate(self.courses):
                # duration
                dur = course.get('duration')
                if not isinstance(dur, int):
                    print(f"CRITICAL: Course {i} '{course.get('name')}' duration is not int: {dur} type {type(dur)}")
                elif dur is None:
                    print(f"CRITICAL: Course {i} '{course.get('name')}' duration is None!")
                elif dur > 100: # Heuristic limit
                    print(f"CRITICAL: Course {i} '{course.get('name')}' duration is HUGE: {dur}")
                elif dur < 0:
                     print(f"CRITICAL: Course {i} '{course.get('name')}' duration is NEGATIVE: {dur}")
                
                # property types
                name = course.get('name')
                if not isinstance(name, str):
                     print(f"WARNING: Course {i} name is not string: {name} type {type(name)}")
                
                # check fixed_room
                fr = course.get('fixed_room')
                if fr is not None and not isinstance(fr, int):
                     print(f"CRITICAL: Course {i} '{name}' fixed_room is not int: {fr} type {type(fr)}")

        except Exception as e:
            print(f"CRITICAL ERROR DURING VALIDATION: {e}", flush=True)
            import traceback
            traceback.print_exc()
            
        print("=== DATA VALIDATION END ===\n", flush=True)

        core_indices = []
        elective_indices = []
        
        for i, c in enumerate(self.courses):
            # Determine Phase based on Contexts
            # If a course is CORE for ANY group, it belongs in Phase 1.
            # It is only "Elective Phase" if it is Elective for EVERYONE.
            is_elective = True
            contexts = c.get('program_contexts', [])
            if not contexts:
                is_elective = False # Default to Core if undefined
            else:
                for ctx in contexts:
                    if ctx.role == CourseRole.CORE:
                        is_elective = False
                        break
            
            if is_elective:
                elective_indices.append(i)
            else:
                core_indices.append(i)
                
        print(f"DEBUG: {len(core_indices)} Core, {len(elective_indices)} Elective")
        
        # --- PHASE 1: CORE COURSES ONLY ---
        print("\n=== PHASE 1: CORE COURSES ===")
        
        self.cp_model = cp_model.CpModel()
        # Only create variables for cores
        self.create_variables(ignore_fixed_rooms=False, optional_indices=elective_indices, active_indices=core_indices)
        
        # Force electives OFF in Phase 1
        for idx in elective_indices:
            for r_id in [r[0] for r in self.rooms]:
                if (idx, r_id) in self.room_vars:
                    self.cp_model.Add(self.room_vars[(idx, r_id)] == 0)
        
        self.add_hard_constraints(include_teacher_unavailability=False)
        # print("DEBUG: Phase 1 add_hard_constraints SKIPPED.", flush=True)
        # self.add_soft_constraints_consecutive()
        print("DEBUG: Phase 1 add_soft_constraints_consecutive SKIPPED.", flush=True)
        
        try:
            if not self._run_solver("PHASE1_CORE", timeout=180.0):
                print("FAILED to schedule Core courses. Aborting.")
                return False
        except Exception as e:
            import traceback
            with open("scheduler_crash.txt", "w", encoding="utf-8") as f:
                f.write(f"CRASH IN PHASE 1 SOLVER: {e}\n")
                traceback.print_exc(file=f)
            print(f"CRASH IN PHASE 1 SOLVER: {e}")
            raise
        
        # Retrieve core assignments using STABLE KEYS
        core_assignments_stable = []
        for idx in core_indices:
            course = self.courses[idx]
            for r in self.rooms:
                r_id = r[0]
                if (idx, r_id) in self.room_vars and self.solver.Value(self.room_vars[(idx, r_id)]) == 1:
                    for s in self.time_slots:
                        s_id = s['id']
                        if (idx, r_id, s_id) in self.starts and self.solver.Value(self.starts[(idx, r_id, s_id)]) == 1:
                            # Use Stable Key: (Name, Instance, Type)
                            stable_key = (course['name'], course['instance'], course['type'])
                            core_assignments_stable.append((stable_key, r_id, s_id))
                            break
        
        print(f"Phase 1 SUCCESS: {len(core_assignments_stable)} core courses scheduled")
        
        # --- PHASE 2: ADD ELECTIVES (Fix Cores) ---
        print("\n=== PHASE 2: ELECTIVES (Cores Fixed) ===")
        
        self.cp_model = cp_model.CpModel()
        # Create variables for all courses, electives optional
        self.create_variables(ignore_fixed_rooms=False, optional_indices=elective_indices)
        
        # Re-Map Stable Keys to New Indices
        course_index_map = {}
        for idx, course in enumerate(self.courses):
            stable_key = (course['name'], course['instance'], course['type'])
            course_index_map[stable_key] = idx
            
        # FIX core assignments from Phase 1
        for (stable_key, r_id, s_id) in core_assignments_stable:
            c_idx = course_index_map.get(stable_key)
            if c_idx is not None and (c_idx, r_id, s_id) in self.starts:
                self.cp_model.Add(self.starts[(c_idx, r_id, s_id)] == 1)
            else:
                print(f"WARNING: Could not map stable key {stable_key} in Phase 2!")
        
        self.add_hard_constraints(include_teacher_unavailability=True)
        # print("DEBUG: Phase 2 add_hard_constraints SKIPPED.", flush=True)
        self.add_soft_constraints_consecutive()
        # print("DEBUG: Phase 2 add_soft_constraints_consecutive SKIPPED.", flush=True)
        
        # OBJECTIVE: Maximize electives - penalty for pool overlaps
        elective_vars = []
        for idx in elective_indices:
            for r in self.rooms:
                r_id = r[0]
                if (idx, r_id) in self.room_vars:
                    elective_vars.append(self.room_vars[(idx, r_id)])
        
        # Soft penalty for different-pool overlaps
        penalty_vars = []
        if hasattr(self, 'group_slot_data'):
            for (g_id, s_id), data in self.group_slot_data.items():
                pools = list(data['pools'].keys())
                
                for i, pool_a in enumerate(pools):
                    for pool_b in pools[i+1:]:
                        vars_a = data['pools'][pool_a]
                        vars_b = data['pools'][pool_b]
                        
                        if vars_a and vars_b:
                            a_active = self.cp_model.NewBoolVar(f'penalty_g{g_id}_s{s_id}_{pool_a}')
                            self.cp_model.AddMaxEquality(a_active, vars_a)
                            
                            b_active = self.cp_model.NewBoolVar(f'penalty_g{g_id}_s{s_id}_{pool_b}')
                            self.cp_model.AddMaxEquality(b_active, vars_b)
                            
                            overlap = self.cp_model.NewBoolVar(f'overlap_{g_id}_{s_id}_{pool_a}_{pool_b}')
                            self.cp_model.AddBoolAnd([a_active, b_active]).OnlyEnforceIf(overlap)
                            self.cp_model.AddBoolOr([a_active.Not(), b_active.Not()]).OnlyEnforceIf(overlap.Not())
                            
                            penalty_vars.append(overlap)
        
        if elective_vars:
            objective = sum(elective_vars)
            if penalty_vars:
                objective = objective - 10 * sum(penalty_vars)
            
            # Penalize Core-Elective Conflicts (Soft Constraint)
            if hasattr(self, 'core_elective_penalties') and self.core_elective_penalties:
                objective = objective - 1000 * sum(self.core_elective_penalties) # High penalty
            self.cp_model.Maximize(objective)
        
        # Solve Phase 2
        if self._run_solver("PHASE2_ELECTIVES", timeout=300.0):
            return True
        else:
            print("WARNING: Phase 2 failed. Saving Phase 1 (cores only) as fallback.")
            
            # Re-convert stable keys to indices for saving
            fallback_assignments = []
            c_map = { (c['name'], c['instance'], c['type']): i for i, c in enumerate(self.courses) }
            
            for (stable_key, r_id, s_id) in core_assignments_stable:
                if stable_key in c_map:
                    fallback_assignments.append((c_map[stable_key], r_id, s_id))
            
            self.save_manual_assignments(fallback_assignments)
            return True


    def _ensure_course_in_db(self, course):
        """
        Check if course exists in Dersler table (based on name and instance).
        If not (e.g. actualized elective), insert it to satisfy Foreign Key.
        """
        try:
            # Check existence
            self.db_model.c.execute('SELECT 1 FROM Dersler WHERE ders_adi = ? AND ders_instance = ?', 
                                  (course['name'], course['instance']))
            if self.db_model.c.fetchone():
                return

            # Insert new course with correct type-based hour distribution
            duration = course.get('duration', 0)
            course_type = course.get('type', 'Teori')
            
            # Map duration to correct column based on type
            if course_type == 'Teori':
                t, u, l = duration, 0, 0
            elif course_type == 'Uygulama':
                t, u, l = 0, duration, 0
            elif course_type == 'Lab':
                t, u, l = 0, 0, duration
            else:
                # Fallback for unknown types
                t, u, l = duration, 0, 0
            
            self.db_model.c.execute('''
                INSERT INTO Dersler (ders_adi, ders_instance, ders_kodu, akts, teori_saati, uygulama_saati, lab_saati)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (course['name'], course['instance'], course.get('code', ''), 
                  course.get('akts', 0), t, u, l))
            
            print(f"DEBUG: Inserted new course: {course['name']} (inst {course['instance']}) - Type: {course_type}, Hours: T={t}, U={u}, L={l}")
            
        except Exception as e:
            print(f"ERROR ensuring course in DB: {e}")
            print(f"  Course: {course.get('name', 'UNKNOWN')} (inst {course.get('instance', '?')}), Type: {course.get('type', '?')}")
            raise

    def _run_solver(self, mode_name: str, timeout: float = 120.0) -> bool:
        """Helper to run solver and handle results."""
        # Create a fresh solver instance to avoid state corruption
        self.solver = cp_model.CpSolver()
        self.solver.parameters.log_search_progress = False # Fix crash
        # self.solver.parameters.log_to_stdout = False # Already False by default if log_search_progress is False?
        self.solver.parameters.max_time_in_seconds = timeout
        # Enable Randomization for different results on retry
        self.solver.parameters.random_seed = int(timeout * 100) # Simple varying seed
        self.solver.parameters.linearization_level = 0 # Encourages diversity
        
        try:
            print(f"DEBUG: Starting Solve ({mode_name})...", flush=True)
            # print(f"DEBUG: Model Stats:\n{self.cp_model.ModelStats()}", flush=True) 
            
            # Dump Model
            # with open(f"model_dump_{mode_name}.txt", "w", encoding="utf-8") as f:
            #     f.write(str(self.cp_model.Proto()))
            # print(f"DEBUG: Model dumped to model_dump_{mode_name}.txt", flush=True)
            
            status = self.solver.Solve(self.cp_model)
            print(f"DEBUG: Solve returned status: {status}", flush=True)
        except Exception as e:
            print(f"CRITICAL ERROR in Solve ({mode_name}): {e}", flush=True)
            import traceback
            traceback.print_exc()
            return False
            
        print(f"[{mode_name}] Solver Status: {self.solver.StatusName(status)}", flush=True)
        
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            print(f"SUCCESS: Solution found in {mode_name} mode!")
            if mode_name == "PHASE2_ELECTIVES" or mode_name == "PHASE1_CORE_FALLBACK": 
                self._save_solution()
            return True
        return False

    def _save_solution(self):
        try:
            self.clear_previous_schedule()
            self.extract_schedule()
            print("Schedule successfully generated and saved to database.")
        except Exception as e:
            print(f"Error saving schedule: {e}")
            raise
    
    def clear_previous_schedule(self):
        """Clear existing schedule from database"""
        try:
            self.db_model.c.execute("DELETE FROM Ders_Programi")
            self.db_model.conn.commit()
            print("Existing schedule cleared.")
        except Exception as e:
            print(f"Error clearing schedule: {e}")
            raise
            
    def _commit_assignments(self, assignments):
        """
        Shared logic to commit assignments to the database.
        assignments: List of (c_idx, r_id, s_id)
        """
        try:
            course_room_map = collections.defaultdict(dict)
            count = 0
            
            for c_idx, r_id, s_id in assignments:
                course = self.courses[c_idx]
                self._ensure_course_in_db(course)
                
                duration = course['duration']
                start_slot = self.time_slots[s_id]
                
                # Defensive: Ensure end index is valid
                end_idx = s_id + duration - 1
                if end_idx >= len(self.time_slots):
                    print(f"WARNING: Invalid end index {end_idx} for course {course['name']}, skipping")
                    continue
                end_slot = self.time_slots[end_idx]
                
                # Use FIRST teacher ID if available (schema limitation)
                main_teacher_id = course['teacher_ids'][0] if course['teacher_ids'] else None
                
                # Insert into DB
                self.db_model.c.execute('''
                    INSERT INTO Ders_Programi (ders_adi, ders_instance, ogretmen_id, derslik_id, gun, baslangic, bitis, ders_tipi)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (course['name'], course['instance'], main_teacher_id, r_id, 
                      start_slot['day'], start_slot['start_str'], end_slot['end_str'], course['type']))
                
                # Store room assignments separately for T and L
                if course['type'] == 'Teori' or course['type'] == 'Uygulama':
                    course_room_map[course['parent_key']]['T'] = r_id
                elif course['type'] == 'Lab':
                    course_room_map[course['parent_key']]['L'] = r_id
                count += 1
            
            print(f"Committed {count} schedule items to database.")
            
            # Update Dersler table with assigned rooms
            for key, val in course_room_map.items():
                ders_adi, ders_instance = key
                
                if 'T' in val:
                     self.db_model.c.execute('''
                        UPDATE Dersler SET teori_odasi = ? WHERE ders_adi = ? AND ders_instance = ?
                    ''', (val['T'], ders_adi, ders_instance))
                
                if 'L' in val:
                     self.db_model.c.execute('''
                        UPDATE Dersler SET lab_odasi = ? WHERE ders_adi = ? AND ders_instance = ?
                    ''', (val['L'], ders_adi, ders_instance))
            
            self.db_model.conn.commit()
            
        except Exception as e:
            print(f"ERROR: Failed to commit assignments - {e}")
            self.db_model.conn.rollback()
            raise

    def save_manual_assignments(self, assignments):
        """
        Manually save assignments to database when solver fails to produce a model solution
        assignments: List of (c_idx, r_id, s_id)
        """
        print("Saving manual assignments (Fallback)...")
        self.clear_previous_schedule()
        self._commit_assignments(assignments)
        print("Fallback schedule saved successfully.")
    
    def extract_schedule(self):
        """Extract the schedule from the solved model and save to database"""
        print("Extracting schedule from solver...")
        assignments = []
        for key, start_var in self.starts.items():
            if self.solver.Value(start_var) == 1:
                assignments.append(key)
        
        if assignments:
            self._commit_assignments(assignments)
        else:
            print("WARNING: No assignments found in solution!")
