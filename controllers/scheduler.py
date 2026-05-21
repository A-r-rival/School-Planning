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
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(BASE_DIR, "database"))
import curriculum_data
from controllers.scheduler_services import (
    CourseRepository, CurriculumResolver, CourseMerger, 
    SchedulableCourseBuilder, CourseRole
)

DIAG_DIR = os.path.join(BASE_DIR, "logs", "diagnostics")
os.makedirs(DIAG_DIR, exist_ok=True)

# Constants
SLOTS_PER_DAY = 18  # 30-min slots from 08:30 to 17:30

def to_minutes(time_str: str) -> int:
    """Convert HH:MM string to minutes since midnight."""
    try:
        if not time_str or ':' not in time_str:
            return 0
        h, m = map(int, time_str.split(':'))
        return h * 60 + m
    except ValueError:
        return 0

class SolutionPrinter(cp_model.CpSolverSolutionCallback):
    """Callback to print intermediate solutions."""
    def __init__(self):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.__solution_count = 0

    def OnSolutionCallback(self):
        self.__solution_count += 1
        print(f"DEBUG: Found intermediate Feasible Solution #{self.__solution_count} at {self.WallTime():.2f}s", flush=True)

    def SolutionCount(self):
        return self.__solution_count

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
        self.semester_filter = "Güz" # Default

    def load_data(self, semester_filter: Optional[str] = None):
        """Load necessary data from database. Called once."""
        self.semester_filter = semester_filter
        # 1. Load Rooms
        self.rooms = self.db_model.aktif_derslikleri_getir() 
        self.rooms.sort(key=lambda x: x[0]) # Deterministic Sort by ID
        print(f"Loaded {len(self.rooms)} rooms.")
        
        # 2. Load Courses 
        self.courses = self._fetch_all_course_instances()
        
        # Filter: Project Courses (Existing + Expanded for SDP)
        skip_keywords = [
            'bitirme projesi', 'tasarım projesi', 'capstone', 'tez',
            'seçmeli proje', 'elective project',
            'robotik projesi', 'robotics project',
            'üretim projesi', 'production auto. project',
            'akıllı sis. proj.', 'intelligent sys. project',
            'mekatronik projesi', 'mechatronics project'
        ]
        
        filtered_courses = []
        for c in self.courses:
            name = c.get('name', '').lower()
            code = str(c.get('code', '')).upper()
            
            if any(kw in name for kw in skip_keywords) or 'MEC319' in code:
                continue
            filtered_courses.append(c)
            
        self.courses = filtered_courses
        
        # Filter: Semester (using semester_lookup from curriculum_data)
        if semester_filter and semester_filter not in ("Hepsi", "Yaz"):
            print(f"DEBUG: Filtering courses for semester: {semester_filter}")
            semester_courses = []
            lookup = getattr(self.db_model, 'semester_lookup', {})
            
            for c in self.courses:
                code = str(c.get('code', '')).strip()
                name = str(c.get('name', '')).strip()
                
                valid_groups = []
                has_any_match = False
                
                lookup_by_dept = getattr(self.db_model, 'semester_lookup_by_dept', {})
                lookup = getattr(self.db_model, 'semester_lookup', {})
                
                if 'program_contexts' in c and c['program_contexts']:
                    for ctx in c['program_contexts']:
                        dept = str(ctx.department).strip() if hasattr(ctx, 'department') else ""
                        
                        sem_set = set()
                        if dept and (dept, code) in lookup_by_dept:
                            sem_set = lookup_by_dept[(dept, code)]
                        elif dept and (dept, name) in lookup_by_dept:
                            sem_set = lookup_by_dept[(dept, name)]
                        elif code and code in lookup:
                            sem_set = lookup[code]
                        elif name and name in lookup:
                            sem_set = lookup[name]
                            
                        # Include if ONLY for selected semester OR if it explicitly spans BOTH
                        if semester_filter in sem_set or ("Güz" in sem_set and "Bahar" in sem_set):
                            if hasattr(ctx, 'group_id'):
                                valid_groups.append(ctx.group_id)
                            has_any_match = True
                else:
                    # Fallback for old tests or edge cases without program_contexts
                    dept = str(c.get('department', '')).strip()
                    sem_set = set()
                    if dept and (dept, code) in lookup_by_dept:
                        sem_set = lookup_by_dept[(dept, code)]
                    elif dept and (dept, name) in lookup_by_dept:
                        sem_set = lookup_by_dept[(dept, name)]
                    elif code and code in lookup:
                        sem_set = lookup[code]
                    elif name and name in lookup:
                        sem_set = lookup[name]
                        
                    if semester_filter in sem_set or ("Güz" in sem_set and "Bahar" in sem_set):
                        has_any_match = True
                        valid_groups = c.get('groups', [])
                        
                if has_any_match:
                    # PRUNE: Mathematically strip cohorts that do NOT belong to this semester
                    c['groups'] = valid_groups
                    semester_courses.append(c)
            
            self.courses = semester_courses
            print(f"DEBUG: Loaded {len(self.courses)} courses after Semester Filter ({semester_filter}).")
        else:
            print(f"DEBUG: Loaded {len(self.courses)} schedulable courses (after filtering projects).")
        
        # 3. Load Teachers
        self.teachers = self.db_model.get_all_teachers_with_ids()
        
        # 4. Define Time Slots (30-minute blocks)
        self.time_slots = []
        days = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma"]
        
        # Start: 08:30
        # End: 17:30 (18 slots * 30 mins = 9 hours)
        # 08:30, 09:00, 09:30, 10:00 ... 17:00, 17:30
        
        start_hour = 8
        start_minute = 30
        self.slots_per_day = SLOTS_PER_DAY # GLOBAL for class usage
        
        # Override global constant if possible, or just use local logic
        # We need to ensure SLOTS_PER_DAY constant is updated or ignored
        # For now, let's redefine internal logic to rely on calculated slots
        
        current_id = 0
        for d_idx, day in enumerate(days):
            # Reset time for each day
            h = start_hour
            m = start_minute
            
            for s_idx in range(self.slots_per_day):
                # Format Start
                start_str = f"{h:02d}:{m:02d}"
                start_min = h * 60 + m
                
                # Calculate End (Start + 30 mins)
                m += 30
                if m >= 60:
                    m -= 60
                    h += 1
                
                end_str = f"{h:02d}:{m:02d}"
                end_min = h * 60 + m
                
                self.time_slots.append({
                    'id': current_id,
                    'day': day,
                    'day_idx': d_idx,
                    'slot_idx': s_idx, 
                    'start_time_string': start_str,
                    'end_time_string': end_str,
                    'start_min': start_min,
                    'end_min': end_min
                })
                current_id += 1
                
        print(f"DEBUG: Initialized {len(self.time_slots)} time slots (30-min intervals).")

        self.course_faculties = self.db_model.get_course_faculty_map()

        # Teacher Day Span Preferences
        self.teacher_day_spans = {}
        for t_id, span in self.db_model.get_all_teacher_day_spans():
            self.teacher_day_spans[t_id] = span
        print(f"DEBUG: Loaded {len(self.teacher_day_spans)} teachers with day span preferences.")

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

    def create_variables(self, ignore_fixed_rooms=False, optional_indices=None, active_indices=None, fixed_assignments=None):
        """Create CP variables and initialize model logic with strict contiguity."""
        if optional_indices is None:
            optional_indices = set()
        else:
            optional_indices = set(optional_indices)
            
        if active_indices is not None:
            active_indices = set(active_indices)
            
        if fixed_assignments is None:
            fixed_assignments = {}

        self.vars = {} 
        self.room_vars = {}
        self.starts = {} # (c_idx, r_id, s_id) -> bool_var
        
        capacity_filtered_count = 0
        symmetry_filtered_count = 0
        
        active_count = len(active_indices) if active_indices is not None else len(self.courses)
        print(f"DEBUG: Creating variables for {active_count} courses...", flush=True)
        if hasattr(self, 'cp_model') and self.cp_model:
             print("DEBUG: CP Model exists.", flush=True)
        else:
             print("CRITICAL ERROR: CP Model is None in create_variables!", flush=True)

        count = 0
        for c_idx, course in enumerate(self.courses):
            allowed_theory_pool_seed = None
            
            # Optimization: Skip variable creation for courses not in active phase
            if active_indices is not None and c_idx not in active_indices:
                continue
                
            duration = course['duration']
            
            # Duration Safety Check
            if duration > self.slots_per_day:
                 print(f"CRITICAL WARNING: Course {course['name']} duration ({duration}) exceeds SLOTS_PER_DAY ({self.slots_per_day}). It will verify be infeasible.")
                 # We could skip it to avoid breaking the solver, or let it fail.
                 # Let's skip creating variables for it so it doesn't crash calculations
                 continue

            # PHASE 2 OPTIMIZATION: If course was fixed in Phase 1, ONLY build the assigned path!
            if c_idx in fixed_assignments:
                r_assigned, s_assigned_start = fixed_assignments[c_idx]
                r_var = self.cp_model.NewBoolVar(f'c{c_idx}_r{r_assigned}')
                self.room_vars[(c_idx, r_assigned)] = r_var
                self.cp_model.Add(r_var == 1)
                
                s_var = self.cp_model.NewBoolVar(f'start_c{c_idx}_r{r_assigned}_s{s_assigned_start}')
                self.starts[(c_idx, r_assigned, s_assigned_start)] = s_var
                self.cp_model.Add(s_var == 1)
                
                for t in self.time_slots:
                    t_id = t['id']
                    if s_assigned_start <= t_id < s_assigned_start + duration:
                        occ_var = self.cp_model.NewBoolVar(f'c{c_idx}_r{r_assigned}_s{t_id}')
                        self.vars[(c_idx, r_assigned, t_id)] = occ_var
                        self.cp_model.Add(occ_var == 1)
                continue

            # 1. Create Room Variables
            possible_rooms = []
            viable_rooms_count = 0
            
            # Determine if fixed_room is actually a valid room in our current list
            is_fixed_room_valid = False
            if not ignore_fixed_rooms and course['fixed_room']:
                is_fixed_room_valid = any(r[0] == course['fixed_room'] for r in self.rooms)
                if not is_fixed_room_valid:
                    print(f"DEBUG WARNING: Course {course['name']} has invalid fixed_room ID {course['fixed_room']}. Ignoring fixed room constraint.")

            # HASH POOLING: Determine course's allowed sub-pool (Symmetry breaking)
            # Only apply generic sub-pooling if there are lots of rooms and no fixed room
            allowed_theory_pool = None
            if not is_fixed_room_valid and len(self.rooms) > 20: # If school has more than 20 rooms total
                # Use Course Name + Instance to deterministically hash it to a chunk of 12 rooms
                h_val = hash(course['name'] + str(course.get('instance', '1')))
                pool_size = 12
                # We will just modulo the room ID against a shift based on h_val, or use a list.
                # Since we don't have a contiguous list of theory rooms here, we will filter below.
                allowed_theory_pool_seed = h_val % max(1, len(self.rooms) // pool_size)

            for r in self.rooms:
                r_id = r[0]
                
                # Filter rooms logic
                if is_fixed_room_valid and course['fixed_room'] != r_id:
                     continue
                
                # Room Type Logic
                # Strict matching based on course 'type' provided by Builder
                # --- ROBUST ROOM TYPE LOGIC ---
                
                # 1. Normalize Room Type & Name
                room_type_str = ""
                # r[2] is technically 'floor' in current DB schema, but check it anyway
                if len(r) > 2 and r[2]:
                    room_type_str = str(r[2]).lower()
                
                room_name = str(r[1]).lower() if len(r) > 1 and r[1] else ""
                
                # Check capabilities (Robust check against Name OR Type/Floor)
                is_lab_keywords = ["laboratuvar", "lab"]
                is_lab_room = any(k in room_name for k in is_lab_keywords) or \
                              any(k in room_type_str for k in is_lab_keywords)
                
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
                
                
                # Rule A: Lab Courses -> ONLY in Lab Rooms
                if is_lab_course:
                    if not is_lab_room:
                        continue # Skip non-lab rooms
                        
                # Rule B: Non-Lab Courses (Teori/Uygulama) -> NEVER in Lab Rooms
                # (Unless strictly overridden by fixed_room, but that's handled above)
                else:
                    if is_lab_room:
                        continue
                        
                # Rule C: Capacity Pre-Filtering (RAM Optimization)
                course_capacity = course.get('student_count', 0)
                room_capacity = r[3] if len(r) > 3 else 0
                if course_capacity > 0 and room_capacity > 0:
                    if course_capacity > room_capacity * 1.20:
                        capacity_filtered_count += 1
                        continue
                        
                # Rule D: Symmetry Breaking Room Sub-Pooling (RAM Optimization)
                # Severely limit identical generic room assignments to avoid 3.1 Million variable tree bloat
                if allowed_theory_pool_seed is not None and not is_lab_course:
                    # Deterministically distribute courses across rooms using their hash seed
                    # e.g., allow room if its index modulo (TotalRooms / PoolSize) matches the seed
                    # This guarantees every generic course gets exactly ~12 rooms to choose from.
                    total_generic_chunks = max(1, len(self.rooms) // 12)
                    if r_id % total_generic_chunks != allowed_theory_pool_seed:
                        symmetry_filtered_count += 1
                        continue
                
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
                    start_day = start_id // self.slots_per_day
                    end_day = end_id // self.slots_per_day
                    
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

                # 3. Create Occupancy Vars (self.vars) linked to Starts
                # Occ[t] = Sum(Start[s]) for all s where s <= t < s+dur
                for t in self.time_slots:
                    t_id = t['id']
                    
                    # Fix: Ensure bleeding does not cross days
                    t_day = t_id // self.slots_per_day
                    
                    relevant_starts = []
                    min_s = max(0, t_id - duration + 1)
                    max_s = t_id
                    
                    for s_id in range(min_s, max_s + 1):
                        # Ensure the start slot 's' is on the SAME DAY as 't'
                        if (s_id // self.slots_per_day) == t_day:
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
                     # Extract departments for better identification of generic course names
                     course_depts = ", ".join(set([ctx.department for ctx in self.courses[c_idx].get('program_contexts', [])]))
                     course_name = self.courses[c_idx]['name']
                     if course_depts:
                          course_name = f"{course_name} ({course_depts})"
                     
                     reason = f"Duration ({self.courses[c_idx]['duration']}) > Slots Per Day ({self.slots_per_day})"
                     if capacity_filtered_count > 0 and capacity_filtered_count >= len(self.rooms):
                         reason = f"Kapasite Sorunu: Dersi alacak öğrenci sayısı ({course.get('student_count', 0)}) okulun en büyük dersliğinden daha büyük!"
                     
                     msg = f"CRITICAL WARNING: Course {course_name} (ID {c_idx}) has NO VIABLE ROOMS! Reason: {reason}\n"
                     print(msg, flush=True)
                     with open(os.path.join(DIAG_DIR, "debug_infeasibility_report.txt"), "a", encoding="utf-8") as f:
                         f.write(msg)
            
            if possible_rooms:
                if c_idx in optional_indices:
                     self.cp_model.Add(sum(possible_rooms) <= 1)
                else:
                     self.cp_model.Add(sum(possible_rooms) == 1)
            if not possible_rooms:
                print(f"CRITICAL ERROR: No possible rooms found for course {course['name']} (duration {duration}). Capacity Filtered {capacity_filtered_count} rooms.", flush=True)
        
        print(f"DEBUG: Created {len(self.starts)} start variables, {len(self.vars)} occupancy variables. Pruned {capacity_filtered_count} (Cap), {symmetry_filtered_count} (Symmetry).", flush=True)

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
                    unavail = self.db_model.get_teacher_unavailability(t_id, donem=self.semester_filter)
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
                                        # if t_id == 87: # Debug only for Abdullah Şahin
                                        #    print(f"DEBUG_CONST: Blocking Slot {s['day']} {s['start_time_string']}-{s['end_time_string']} for Teacher {t_id} due to unavail {u_start}-{u_end}", flush=True)
                                        
                                        for var in teacher_slot_vars[(t_id, s['id'])]:
                                            self.cp_model.Add(var == 0)
            except Exception as e:
                import traceback
                print(f"CRITICAL ERROR in Teacher Unavailability: {e}", flush=True)
                traceback.print_exc()

        # 5. Teacher Day Span Optimization
        self.add_teacher_day_span_constraints()

        # 6. Student Group Conflict (Refactored)
        self.add_student_group_conflicts()
        print("DEBUG: Executed add_student_group_conflicts", flush=True)

        # 7. Lunch Break Constraint (NEW)
        self.add_lunch_break_constraints()
        print("DEBUG: Executed add_lunch_break_constraints", flush=True)
        print(f"DEBUG: add_hard_constraints DONE.", flush=True)


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

            # --- DIAGNOSTIC: Total Core Demand per Semantic Group ---
            group_core_demand = collections.defaultdict(set)
            for (g_id, s_id), items in group_slot_vars.items():
                g_desc = self.group_metadata.get(g_id)
                g_dept, g_year = g_desc if isinstance(g_desc, tuple) else (g_desc, None)
                for var, course in items:
                    role = self.get_role_for_group(course, g_dept, g_year)
                    if role == CourseRole.CORE:
                        # Use parent_key to avoid counting parts multiple times if we just want course count
                        # But wait, we want total duration. Since each physical course is a unique c_idx
                        # and has a duration, we should just sum the duration of unique physical courses.
                        # Wait, the items array already has valid physical courses.
                        group_core_demand[(g_dept, g_year)].add((course['name'], course.get('instance', '')))
            
            course_duration_map = {(c['name'], c.get('instance', '')): c.get('duration', 0) for c in self.courses}
            for (g_dept, g_year), courses in group_core_demand.items():
                 # O(1) duration lookup instead of O(N) per course
                 total_hours = sum([course_duration_map.get(c_name, 0) for c_name in courses])
                 if total_hours > 50:
                     course_list_str = ", ".join(sorted(list(courses)))
                     print(f"WARNING: Group {g_dept}-{g_year} has VERY HIGH Core Demand: {total_hours} slots ({len(courses)} courses).", flush=True)
                     print(f"  -> Courses causing demand: {course_list_str}", flush=True)

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
        

    def add_lunch_break_constraints(self):
        """
        Enforce at least one empty slot between 11:30 and 14:00 for every student group.
        Time window: 11:30 (690 min) to 14:00 (840 min).
        Slots contained in this window must not be fully occupied.
        Max occupied slots = Total Lunch Slots - 1.
        """
        print("DEBUG: Starting add_lunch_break_constraints...", flush=True)
        
        # 1. Identify Lunch Slots per Day
        lunch_start_min = 11 * 60 + 30 # 690
        lunch_end_min = 14 * 60        # 840
        
        lunch_slots_by_day = collections.defaultdict(list)
        lunch_slots_set = set() # O(1) lookup map
        
        for s in self.time_slots:
            if s['start_min'] >= lunch_start_min and s['end_min'] <= lunch_end_min:
                lunch_slots_by_day[s['day_idx']].append(s['id'])
                lunch_slots_set.add(s['id'])
                
        # Debug: Print identified slots
        for d_idx, slots in lunch_slots_by_day.items():
            print(f"DEBUG_LUNCH: Day {d_idx} Lunch Slots: {slots}", flush=True)

        # 2. Group Variables by Semantic Group (Dept, Year) and Slot ID
        # Mapping: (Dept, Year, DayIdx, SlotID) -> [List of BoolVars in Lunch Window]
        group_slot_lunch_vars = collections.defaultdict(list)
        
        for key, var in self.vars.items():
            c_idx, r_id, s_id = key
            
            # Optimization check against pre-built set
            if s_id not in lunch_slots_set:
                continue
            
            s_day = s_id // self.slots_per_day
            course = self.courses[c_idx]
            
            for g_id in course['group_ids']:
                if g_id in self.group_metadata:
                    g_desc = self.group_metadata[g_id]
                    g_dept, g_year = g_desc if isinstance(g_desc, tuple) else (g_desc, None)
                    
                    group_slot_lunch_vars[(g_dept, g_year, s_day, s_id)].append(var)

        # 3. Apply Constraints
        # For each Group + Day, we want the number of OCCUPIED slots to be <= Max-1
        # A slot is occupied if ANY of the courses in it for that group are active.
        
        # Map (Dept, Year, DayIdx) -> list of occupied bools
        day_occupancy = collections.defaultdict(list)
        
        # We need a stable string representation for variable names to avoid invalid chars
        def safe_name(text):
            return "".join(c for c in str(text) if c.isalnum())
            
        for (g_dept, g_year, s_day, s_id), vars_list in group_slot_lunch_vars.items():
            if vars_list:
                # Deduplicate vars (in case course belongs to multiple groups mapping to same semantic group)
                unique_vars = list(set(vars_list))
                
                # Check if we have multiple courses that could be co-scheduled (e.g. parallel electives)
                if len(unique_vars) > 1:
                    # Create an OR variable: is ANY class scheduled in this slot for this group?
                    slot_occupied = self.cp_model.NewBoolVar(f'lunch_occ_{safe_name(g_dept)}_{g_year}_d{s_day}_s{s_id}')
                    self.cp_model.AddMaxEquality(slot_occupied, unique_vars)
                    day_occupancy[(g_dept, g_year, s_day)].append(slot_occupied)
                else:
                    # Optimized: just use the single var directly!
                    day_occupancy[(g_dept, g_year, s_day)].append(unique_vars[0])
                    
        print(f"DEBUG_LUNCH: Applying constraints for {len(day_occupancy)} group-day combinations.", flush=True)
        
        if not hasattr(self, 'soft_penalties'):
            self.soft_penalties = []
            
        for (g_dept, g_year, s_day), occ_vars in day_occupancy.items():
            lunch_slots_count = len(lunch_slots_by_day[s_day])
            max_allowed = lunch_slots_count - 1
            if occ_vars:
                # Add a slack variable to softly enforce max_allowed. 
                # If they are scheduled for all lunch_slots_count slots, lunch_missed must be > 0.
                lunch_missed = self.cp_model.NewIntVar(0, lunch_slots_count, f'lunch_missed_{safe_name(g_dept)}_{g_year}_d{s_day}')
                
                # sum(occ_vars) - max_allowed <= lunch_missed
                self.cp_model.Add(sum(occ_vars) - max_allowed <= lunch_missed)
                
                # Severely penalize missing lunch (High Penalty like 200)
                self.soft_penalties.append(lunch_missed * 200)

        


    def add_teacher_room_preferences(self):
        """
        Apply constraints based on teacher room requests.
        Keywords: 'zemin', 'giriş', 'k1', 'k2', 'lab', or specific room names.
        
        DEBUG VERSION: Logs viable room counts to identify infeasibility.
        """
        debug_log = []
        debug_log.append("=== ROOM PREFERENCE DEBUG LOG ===\n")
        if not hasattr(self, 'soft_penalties'):
            self.soft_penalties = []
        
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
                debug_log.append(f"\nTeacher ID={t_id}, Request=\"{request}\"\n")
                debug_log.append(f"  Courses: {len(teacher_course_indices)}\n")
                
                # Count viable rooms BEFORE applying constraints for each course
                # DETAILED LOGGING: Show WHY courses have limited room options
                viable_before = {}
                for c_idx in teacher_course_indices:
                    # Check if variables exist for this course (skip if inactive/elective in Phase 1)
                    has_vars = any((c_idx, r[0]) in self.room_vars for r in self.rooms)
                    if not has_vars:
                         continue

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
                        course = self.courses[c_idx]
                        course_type = course.get('type', '').lower()
                        
                        # User Request: Labs should ignore teacher floor preferences,
                        # and ANY course with a fixed_room should ignore teacher preferences
                        # to avoid creating an infeasible model.
                        if 'lab' in course_type or course.get('fixed_room'):
                            debug_log.append(f"    Skipping Floor Constraint for Course {c_idx} (Type: {course_type}, Fixed Room: {bool(course.get('fixed_room'))})\n")
                            continue

                        # Check viability to prevent INFEASIBILITY
                        viable_after = 0
                        for r in self.rooms:
                            r_floor = r[4] if len(r) > 4 else 0
                            if r_floor == target_floor:
                                if (c_idx, r[0]) in self.room_vars:
                                    viable_after += 1
                        
                        if viable_after > 0:
                            for r in self.rooms:
                                r_id = r[0]
                                r_floor = r[4] if len(r) > 4 else 0
                                
                                if r_floor != target_floor:
                                    if (c_idx, r_id) in self.room_vars:
                                        self.soft_penalties.append(self.room_vars[(c_idx, r_id)] * 60)
                                        banned_rooms_count += 1
                        else:
                            debug_log.append(f"    WARNING: Skipping Floor Constraint for Course {c_idx} because no viable rooms on Floor {target_floor}!\n")
                
                # Logic 2: Lab Constraint
                # IMPORTANT: Teacher lab preference should ONLY apply to lab-type courses
                # If teacher requests "Lab" but teaches theory courses, don't force theory into labs!
                if 'lab' in req_lower:
                    debug_log.append(f"  Detected Lab Request\n")
                    lab_rooms = [r for r in self.rooms if 'lab' in r[1].lower()]
                    debug_log.append(f"  Lab Rooms: {len(lab_rooms)}\n")
                    
                    for c_idx in teacher_course_indices:
                        course = self.courses[c_idx]
                        course_type = course.get('type', '').lower()
                        
                        # Check if THIS specific course is a lab course
                        is_lab_course = 'lab' in course_type
                        
                        if not is_lab_course or course.get('fixed_room'):
                            # This is a theory course, OR has a fixed room - teacher lab preference doesn't apply
                            debug_log.append(f"    Skipping Course {c_idx} (theory course or fixed room)\n")
                            continue
                        
                        # This IS a lab course - apply teacher's lab room preference
                        viable_after = 0
                        for r in self.rooms:
                            if 'lab' in r[1].lower():
                                if (c_idx, r[0]) in self.room_vars:
                                    viable_after += 1
                        
                        if viable_after > 0:
                            for r in self.rooms:
                                r_id = r[0]
                                r_name = r[1].lower()
                                is_lab_room = 'lab' in r_name
                                if not is_lab_room:
                                     if (c_idx, r_id) in self.room_vars:
                                        self.soft_penalties.append(self.room_vars[(c_idx, r_id)] * 80)
                                        banned_rooms_count += 1
                        else:
                            debug_log.append(f"    WARNING: Skipping Lab Constraint for Course {c_idx} because no viable lab rooms available!\n")

                # Logic 3: Specific Room Name
                valid_room_ids = []
                for r in self.rooms:
                    if r[1].lower() in req_lower:
                         valid_room_ids.append(r[0])
                
                if valid_room_ids:
                    debug_log.append(f"  Detected Specific Room Request: {[r[1] for r in self.rooms if r[0] in valid_room_ids]}\n")
                    for c_idx in teacher_course_indices:
                        if self.courses[c_idx].get('fixed_room'):
                            continue # Skip courses with fixed rooms
                            
                        # Check viability
                        viable_after = 0
                        for r_id in valid_room_ids:
                            if (c_idx, r_id) in self.room_vars:
                                viable_after += 1
                        
                        if viable_after > 0:
                            for r in self.rooms:
                                 r_id = r[0]
                                 if r_id not in valid_room_ids:
                                     if (c_idx, r_id) in self.room_vars:
                                         self.soft_penalties.append(self.room_vars[(c_idx, r_id)] * 100)
                                         banned_rooms_count += 1
                        else:
                            debug_log.append(f"    WARNING: Skipping Specific Room Constraint for Course {c_idx} because valid rooms are too small or unavailable!\n")

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
                            # Only enforce lab match if course is Lab type
                            course_type = self.courses[c_idx].get('type', '').lower()
                            if 'lab' in course_type:
                                if 'lab' not in r[1].lower():
                                    matches = False
                            # Else: Theory course ignores teacher lab preference for logging too
                        
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
        with open(os.path.join(DIAG_DIR, "room_preference_debug.txt"), "w", encoding="utf-8") as f:
            f.writelines(debug_log)
        
        print("DEBUG: Room preference constraints applied. Log written to logs/diagnostics/room_preference_debug.txt", flush=True)



    def add_teacher_day_span_constraints(self):
        """
        Soft Constraint: Penalize teachers being scheduled on more days than their
        preferred_day_span. Uses penalty variables added to self.soft_penalties.
        """
        if not self.teacher_day_spans:
            print("DEBUG: No teacher day span preferences found. Skipping.", flush=True)
            return

        print(f"DEBUG: Adding day span constraints for {len(self.teacher_day_spans)} teachers...", flush=True)

        if not hasattr(self, 'soft_penalties'):
            self.soft_penalties = []
        if not hasattr(self, 'teacher_span_penalties'):
            self.teacher_span_penalties = []

        # Pre-group vars by (teacher_id, day_idx) to avoid O(T * D * V) loops
        teacher_day_vars = collections.defaultdict(list)
        for (c_idx, r_id, s_id), var in self.vars.items():
            d_idx = s_id // self.slots_per_day
            for t_id in self.courses[c_idx].get('teacher_ids', []):
                teacher_day_vars[(t_id, d_idx)].append(var)

        for t_id, preferred_span in self.teacher_day_spans.items():
            day_active_vars = []
            for d_idx in range(5):
                t_day_vars = teacher_day_vars.get((t_id, d_idx), [])
                if t_day_vars:
                    active = self.cp_model.NewBoolVar(f'tspan_t{t_id}_d{d_idx}')
                    self.cp_model.AddMaxEquality(active, t_day_vars)
                    day_active_vars.append(active)

            # Penalize each active day beyond the preferred span
            if len(day_active_vars) > preferred_span:
                total_active = sum(day_active_vars)
                excess = self.cp_model.NewIntVar(0, 5, f'tspan_excess_{t_id}')
                self.cp_model.Add(excess >= total_active - preferred_span)
                self.cp_model.Add(excess >= 0)
                self.teacher_span_penalties.append(excess)

        print(f"DEBUG: Teacher day span constraints added. {len(self.teacher_span_penalties)} penalty vars.", flush=True)

    def add_soft_constraints_consecutive(self):
        """
        Soft Constraint: Encourage different session types (T/U/L) to be on DIFFERENT days.
        Groups courses by parent_key and penalizes parts of the same course on the same day.
        Penalties are stored in self.soft_penalties for the objective function.
        """
        if not hasattr(self, 'soft_penalties'):
            self.soft_penalties = []

        # Group courses by parent_key
        course_parts = collections.defaultdict(list)
        for c_idx, course in enumerate(self.courses):
            if 'parent_key' in course:
                course_parts[course['parent_key']].append(c_idx)

        # Optimization 1: Identify courses that ACTUALLY need day-separation checks (multi-part courses)
        # Avoid generating 7.5 million SWIG constraints for single-block courses!
        multi_part_c_indices = set()
        for p_key, indices in course_parts.items():
            if len(indices) >= 2:
                multi_part_c_indices.update(indices)

        if not multi_part_c_indices:
            print("DEBUG: add_soft_constraints_consecutive skipped (No multi-part courses).", flush=True)
            return

        # Optimization 2: Pre-group vars by (course_idx, day_idx) ONLY for multi-part courses
        course_day_starts = collections.defaultdict(list)
        for (c_idx, r_id, s_id), s_var in self.starts.items():
            if c_idx in multi_part_c_indices:
                d_idx = s_id // self.slots_per_day
                course_day_starts[(c_idx, d_idx)].append(s_var)

        # Pre-calculate active day flag per course to avoid duplicate MaxEquality clauses
        course_day_active = {}
        for (c_idx, d_idx), start_vars in course_day_starts.items():
            if start_vars:
                # Use a single dedicated variable representing "does this course start on this day?"
                active_var = self.cp_model.NewBoolVar(f'c_{c_idx}_day_{d_idx}_active')
                self.cp_model.AddMaxEquality(active_var, start_vars)
                course_day_active[(c_idx, d_idx)] = active_var

        penalty_count = 0
        for p_key, indices in course_parts.items():
            if len(indices) < 2:
                continue

            for i in range(len(indices)):
                for j in range(i + 1, len(indices)):
                    idx1, idx2 = indices[i], indices[j]
                    for d_idx in range(5):
                        b1 = course_day_active.get((idx1, d_idx))
                        b2 = course_day_active.get((idx2, d_idx))

                        if b1 is not None and b2 is not None:
                            conflict = self.cp_model.NewBoolVar(f'dd_c_{idx1}_{idx2}_{d_idx}')
                            self.cp_model.AddBoolOr([b1.Not(), b2.Not(), conflict])
                            self.soft_penalties.append(conflict)
                            penalty_count += 1

        print(f"DEBUG: add_soft_constraints_consecutive added {penalty_count} day-separation penalties.", flush=True)
        


    def generate_schedule(self, semester_filter: Optional[str] = None):
        """Solve with 2-Phase Strategy (Core then Elective) and Fallbacks."""
        self.load_data(semester_filter)
        
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
                if dur is None:
                    print(f"CRITICAL: Course {i} '{course.get('name')}' duration is None!")
                elif not isinstance(dur, int):
                    print(f"CRITICAL: Course {i} '{course.get('name')}' duration is not int: {dur} type {type(dur)}")
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
        # Create Variables
        # User requested to FORCE use of fixed rooms.
        # So ignore_fixed_rooms=False
        self.create_variables(ignore_fixed_rooms=False, optional_indices=elective_indices, active_indices=core_indices)
        
        # Force electives OFF in Phase 1
        for idx in elective_indices:
            for r_id in [r[0] for r in self.rooms]:
                if (idx, r_id) in self.room_vars:
                    self.cp_model.Add(self.room_vars[(idx, r_id)] == 0)
        
        self.soft_penalties = []  # Reset for Phase 1
        self.teacher_span_penalties = [] # Reset for Phase 1
        self.add_hard_constraints(include_teacher_unavailability=True)
        self.add_soft_constraints_consecutive()
        
        # Phase 1 Objective: Minimize soft penalties
        objective_p1 = 0
        if hasattr(self, 'soft_penalties') and self.soft_penalties:
            objective_p1 += sum(self.soft_penalties)
        if hasattr(self, 'teacher_span_penalties') and self.teacher_span_penalties:
            objective_p1 += sum(self.teacher_span_penalties)
            
        if type(objective_p1) is not int:
            self.cp_model.Minimize(objective_p1)
            print(f"DEBUG: Phase 1 objective: minimize soft penalties.", flush=True)
        
        try:
            if not self._run_solver("PHASE1_CORE", timeout=120.0, save_to_db=False):
                print("FAILED to schedule Core courses within time limit. Schedule is overconstrained. Aborting.")
                return False
        except Exception as e:
            import traceback
            with open(os.path.join(DIAG_DIR, "scheduler_crash.txt"), "w", encoding="utf-8") as f:
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
        
        # Re-Map Stable Keys to New Indices
        course_index_map = {}
        for c_idx, course in enumerate(self.courses):
            stable_key = (course['name'], course['instance'], course['type'])
            course_index_map[stable_key] = c_idx
            
        fixed_cores = {}
        for (stable_key, r_id, s_id) in core_assignments_stable:
            c_idx = course_index_map.get(stable_key)
            if c_idx is not None:
                fixed_cores[c_idx] = (r_id, s_id)
            else:
                msg = f"CRITICAL: Could not map Phase 1 core assignment {stable_key} in Phase 2! Variables missing. Falling back to Phase 1 schedule."
                print(msg)
                fallback_assignments = []
                for (sk, rid, sid) in core_assignments_stable:
                    cidx = course_index_map.get(sk)
                    if cidx is not None:
                        fallback_assignments.append((cidx, rid, sid))
                
                if fallback_assignments:
                    self.save_manual_assignments(fallback_assignments)
                    return True
                return False

        # MATCH Phase 1: Enforce fixed rooms + Only expand combinatorial arrays for electives!
        self.create_variables(ignore_fixed_rooms=False, optional_indices=elective_indices, fixed_assignments=fixed_cores)
        
        self.soft_penalties = []  # Reset for Phase 2
        self.teacher_span_penalties = [] # Reset for Phase 2
        self.add_hard_constraints(include_teacher_unavailability=True)
        self.add_soft_constraints_consecutive()
        
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
                
                # OPTIMIZATION: Pre-calculate active flags for each pool to avoid duplicating MaxEquality
                pool_active_vars = {}
                for pool_key in pools:
                    p_vars = data['pools'][pool_key]
                    if p_vars:
                        active_var = self.cp_model.NewBoolVar(f'penalty_g{g_id}_s{s_id}_{pool_key}')
                        self.cp_model.AddMaxEquality(active_var, p_vars)
                        pool_active_vars[pool_key] = active_var
                
                for i, pool_a in enumerate(pools):
                    for pool_b in pools[i+1:]:
                        a_active = pool_active_vars.get(pool_a)
                        b_active = pool_active_vars.get(pool_b)
                        
                        if a_active is not None and b_active is not None:
                            overlap = self.cp_model.NewBoolVar(f'overlap_{g_id}_{s_id}_{pool_a}_{pool_b}')
                            self.cp_model.AddBoolOr([a_active.Not(), b_active.Not(), overlap])
                            penalty_vars.append(overlap)
        
        if elective_vars:
            objective = sum(elective_vars)
            if penalty_vars:
                objective = objective - 10 * sum(penalty_vars)
            
            # Penalize Core-Elective Conflicts (Soft Constraint)
            if hasattr(self, 'core_elective_penalties') and self.core_elective_penalties:
                objective = objective - 1000 * sum(self.core_elective_penalties) # High penalty
            
            # Integrate soft penalties (day separation)
            if hasattr(self, 'soft_penalties') and self.soft_penalties:
                objective = objective - 5 * sum(self.soft_penalties)
                
            # Teacher Day Span Penalty (User request: -15)
            if hasattr(self, 'teacher_span_penalties') and self.teacher_span_penalties:
                objective = objective - 100 * sum(self.teacher_span_penalties)
            
            self.cp_model.Maximize(objective)
        
        # Solve Phase 2
        if self._run_solver("PHASE2_ELECTIVES", timeout=150.0, save_to_db=True):
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
        Optimized with an in-memory session cache to avoid O(N) queries.
        """
        if getattr(self, '_ensured_courses', None) is None:
            self._ensured_courses = set()
            
        course_key = (course['name'], course['instance'])
        if course_key in self._ensured_courses:
            return
            
        try:
            # Check existence
            self.db_model.c.execute('SELECT 1 FROM Dersler WHERE ders_adi = ? AND ders_instance = ?', 
                                  (course['name'], course['instance']))
            if self.db_model.c.fetchone():
                self._ensured_courses.add(course_key)
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
            self._ensured_courses.add(course_key)
            
        except Exception as e:
            print(f"ERROR ensuring course in DB: {e}")
            print(f"  Course: {course.get('name', 'UNKNOWN')} (inst {course.get('instance', '?')}), Type: {course.get('type', '?')}")
            raise

    def _run_solver(self, mode_name: str, timeout: float = 120.0, save_to_db: bool = False) -> bool:
        """Helper to run solver and handle results."""
        # Create a fresh solver instance to avoid state corruption
        self.solver = cp_model.CpSolver()
        self.solver.parameters.log_search_progress = os.environ.get('DEBUG_SOLVER') == '1' # Enable via env var
        # self.solver.parameters.log_to_stdout = False # Already False by default if log_search_progress is False?
        self.solver.parameters.max_time_in_seconds = timeout
        # Enable Randomization for different results on retry
        import time
        self.solver.parameters.random_seed = int(time.time() * 10) % 2147483647 # Dynamic varying seed, valid int32
        self.solver.parameters.linearization_level = 0 # Encourages diversity
        
        try:
            print(f"DEBUG: Starting Solve ({mode_name})...", flush=True)
            # print(f"DEBUG: Model Stats:\n{self.cp_model.ModelStats()}", flush=True) 
            
            # Dump Model for Debugging Infeasible states
            DUMP_MODEL = True
            if DUMP_MODEL:
                with open(os.path.join(DIAG_DIR, f"model_dump_{mode_name}.txt"), "w", encoding="utf-8") as f:
                    f.write(str(self.cp_model.Proto()))
                print(f"DEBUG: Model dumped to logs/diagnostics/model_dump_{mode_name}.txt", flush=True)
            
            solution_printer = SolutionPrinter()
            status = self.solver.Solve(self.cp_model, solution_printer)
            print(f"DEBUG: Solve returned status: {status}. Total feasible solutions found: {solution_printer.SolutionCount()}", flush=True)
        except Exception as e:
            print(f"CRITICAL ERROR in Solve ({mode_name}): {e}", flush=True)
            import traceback
            traceback.print_exc()
            return False
            
        print(f"[{mode_name}] Solver Status: {self.solver.StatusName(status)}", flush=True)
        
        if status == cp_model.INFEASIBLE:
            print(f"CRITICAL: Model is INFEASIBLE. Dumping model for diagnostics.", flush=True)
            try:
                # Basic validation
                print(f"Model Validation: {self.cp_model.Validate()}", flush=True)
            except Exception as e:
                pass
                
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            print(f"SUCCESS: Solution found in {mode_name} mode!")
            # Explicitly controlled save to DB to avoid destroying live data during debug
            if save_to_db:
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
            
            # Robust slot mapping to avoid index out of bounds
            slot_by_id = {s['id']: s for s in self.time_slots}
            
            # Build local room map to safely resolve Names and Capacities
            room_by_id = {r[0]: {'name': r[1], 'capacity': r[3] if len(r) > 3 else 0} for r in self.rooms}
            
            for c_idx, r_id, s_id in assignments:
                course = self.courses[c_idx]
                self._ensure_course_in_db(course)
                
                duration = course['duration']
                start_slot = slot_by_id.get(s_id)
                if not start_slot:
                    print(f"WARNING: Invalid start slot ID {s_id} for course {course['name']}, skipping")
                    continue
                
                # Capacity Filter (for logging/debugging purposes during commit, though filtering should happen earlier)
                room_data = room_by_id.get(r_id)
                if room_data:
                    r_capacity = room_data.get('capacity', 0)
                    course_size = course.get('student_count', 0)
                    if course_size > 0 and r_capacity > 0 and r_capacity < course_size:
                        print(f"WARNING: Course '{course['name']}' (size {course_size}) assigned to room '{room_data.get('name', r_id)}' (capacity {r_capacity}) which is too small. This assignment might be infeasible due to capacity.")
                
                # Defensive: Ensure end index is valid
                end_idx = s_id + duration - 1
                end_slot = slot_by_id.get(end_idx)
                if not end_slot:
                    print(f"WARNING: Invalid end slot ID {end_idx} for course {course['name']}, skipping")
                    continue
                
                # Use FIRST teacher ID if available (schema limitation)
                main_teacher_id = course['teacher_ids'][0] if course['teacher_ids'] else None
                
                # Insert into DB
                self.db_model.c.execute('''
                    INSERT INTO Ders_Programi (ders_adi, ders_instance, ogretmen_id, derslik_id, gun, baslangic, bitis, ders_tipi)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (course['name'], course['instance'], main_teacher_id, r_id, 
                      start_slot['day'], start_slot['start_time_string'], end_slot['end_time_string'], course['type']))
                
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
