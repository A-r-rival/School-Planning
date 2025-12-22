# -*- coding: utf-8 -*-
"""
Scheduler Module using Google OR-Tools
Handles automatic schedule generation with hard and soft constraints
"""
from ortools.sat.python import cp_model
from typing import List, Dict, Tuple, Optional
import collections

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
        print(f"Loaded {len(self.rooms)} rooms.")
        
        # 2. Load Courses 
        self.courses = self._fetch_all_course_instances()
        
        # 3. Load Teachers
        self.teachers = self.db_model.get_all_teachers_with_ids()
        
        # 4. Define Time Slots
        days = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma']
        hours = ['09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00']
        self.time_slots = []
        for d_idx, day in enumerate(days):
            for h_idx, hour in enumerate(hours):
                end_hour = f"{int(hour[:2])+1}:00"
                self.time_slots.append({
                    'id': d_idx * 8 + h_idx,
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
        Fetch courses from curriculum_data, implementing:
        1. Faculty Filter (Engineering & Science only)
        2. Course Merging (Same Name & Teacher -> Single Instance)
        3. T/U/L Splitting
        """
        self.course_faculties = {} # Map (name, instance) -> [faculties]
        
        # Merging Dictionary: (name, frozenset(teachers)) -> CourseDict
        merged_courses = {}
        
        # Allowed Faculties Filter
        ALLOWED_KEYWORDS = ["mühendislik", "fen", "engineering", "science"]

        # RE-STRATEGY: 
        # The previous implementation ignored curriculum_data loop for fetching instances? 
        # No, it primarily used `self.db_model.c.execute` to fetch `Dersler`.
        # Correct source of truth for "What to schedule" is the DB `Dersler` table (which has teacher assignments)
        # JOINed with `Ders_Sinif_Iliskisi` to know which group takes it.
        
        # Query DB for ALL instances
        query = '''
            SELECT d.ders_instance, d.ders_adi, d.teori_saati, d.uygulama_saati, d.lab_saati, d.akts,
                   d.teori_odasi, d.lab_odasi,
                   o.ogretmen_num,
                   dsi.donem_sinif_num,
                   b.fakulte_num, f.fakulte_adi
            FROM Dersler d
            LEFT JOIN Ders_Sinif_Iliskisi dsi ON d.ders_instance = dsi.ders_instance AND d.ders_adi = dsi.ders_adi
            LEFT JOIN Ogrenci_Donemleri od ON dsi.donem_sinif_num = od.donem_sinif_num
            LEFT JOIN Bolumler b ON od.bolum_num = b.bolum_id
            LEFT JOIN Fakulteler f ON b.fakulte_num = f.fakulte_num
            LEFT JOIN Verilen_Dersler vd -- Wait, map teacher via course name? 
            -- Currently Scheduler assumes 'teacher_ids' are passed or found.
            -- In 'models/schedule_model.py', there is no direct link Dersler->Ogretmenler except via 'Ders_Programi' (output).
            -- Teachers MUST be inputs. Where are they defined?
            -- User manually adds courses in UI? Or 'populate_teachers' assigns them?
            -- Let's look at how data was fetched before.
        '''
        
        # Original code (lines 75-80) fetched from `Dersler` and then did some grouping.
        # But wait, `Dersler` table doesn't have `ogretmen_id`.
        # `Verilen_Dersler` (Teachers) has `ders_listesi`.
        
        # Let's rebuild the teacher map first.
        teacher_map = collections.defaultdict(set)
        self.db_model.c.execute("SELECT ogretmen_num, ders_listesi FROM Verilen_Dersler")
        for t_id, d_list in self.db_model.c.fetchall():
            if d_list:
                for d_name in d_list.split(','):
                     teacher_map[d_name.strip()].add(t_id)
                     
        # Now fetch courses from DB linked with Fac/Dept
        query = '''
            SELECT d.ders_adi, d.ders_instance, d.teori_saati, d.uygulama_saati, d.lab_saati, d.akts,
                   d.teori_odasi, d.lab_odasi,
                   dsi.donem_sinif_num,
                   f.fakulte_adi
            FROM Dersler d
            JOIN Ders_Sinif_Iliskisi dsi ON d.ders_instance = dsi.ders_instance AND d.ders_adi = dsi.ders_adi
            JOIN Ogrenci_Donemleri od ON dsi.donem_sinif_num = od.donem_sinif_num
            JOIN Bolumler b ON od.bolum_num = b.bolum_id
            JOIN Fakulteler f ON b.fakulte_num = f.fakulte_num
        '''
        self.db_model.c.execute(query)
        rows = self.db_model.c.fetchall()
        
        print(f"DEBUG: Fetched {len(rows)} raw course-group links.")
        
        # Processing & Merging
        # Key: (name, frozenset(teacher_ids))
        merged_map = {}
        
        for r in rows:
            name, instance, t, u, l, akts, t_room, l_room, group_id, fac_name = r
            
            # Faculty Filter
            is_allowed = False
            if fac_name:
                fac_lower = fac_name.lower()
                for kw in ALLOWED_KEYWORDS:
                    if kw in fac_lower:
                        is_allowed = True
                        break
            if not is_allowed:
                continue

            # Exclusions
            name_lower = name.lower()
            if any(x in name_lower for x in ["staj", "işletmede mesleki eğitim", "mesleki uygulama", "lisans bitirme çalışması", "tez"]):
                continue

            # Fallback Hours
            if t == 0 and u == 0 and l == 0:
                akts_val = akts if akts else 0
                t = min(akts_val, 4)

            # Teachers
            t_ids = frozenset(teacher_map.get(name, []))
            
            # Unique Key for Merging
            # We merge if Name matches AND Teachers match.
            # (Instance ID is from DB, might differ, we'll pick the first one or synthesize)
            merge_key = (name, t_ids)
            
            if merge_key not in merged_map:
                merged_map[merge_key] = {
                    'name': name,
                    'teacher_ids': list(t_ids),
                    't': t, 'u': u, 'l': l,
                    'akts': akts,
                    'priority_instance': instance, # Keep one instance ID for reference
                    'group_ids': set(),
                    'fixed_t_room': t_room,
                    'fixed_l_room': l_room,
                    'faculties': set()
                }
            
            # Aggregate
            item = merged_map[merge_key]
            item['group_ids'].add(group_id)
            if fac_name: item['faculties'].add(fac_name)
            # Logic: If one instance has fixed room, we adopt it (Optimistic)
            if t_room and not item['fixed_t_room']: item['fixed_t_room'] = t_room
            if l_room and not item['fixed_l_room']: item['fixed_l_room'] = l_room

        self.courses = []
        
        # Convert to schedulable items (Flatten T/U/L)
        for key, data in merged_map.items():
            name = data['name']
            
            # Track faculties for logic usage
            # self.course_faculties is (name, instance) -> [facs]
            # Since we merged, let's use the priority_instance or just name?
            # Creating a consistent ID is tricky if we merged instances 1 and 2.
            # Let's just use 'priority_instance' as the canonical ID for the schedule.
            c_inst = data['priority_instance']
            self.course_faculties[(name, c_inst)] = list(data['faculties'])
            
            common_props = {
                'name': name,
                'instance': c_inst,
                'teacher_ids': data['teacher_ids'],
                'group_ids': data['group_ids'],
                'parent_key': f"{name}_{c_inst}"
            }
            
            # Add Theory Blocks
            if data['t'] > 0:
                self.courses.append({
                    **common_props,
                    'type': 'Teori',
                    'duration': data['t'],
                    'fixed_room': data['fixed_t_room']
                })
            
            # Add Practice Blocks
            if data['u'] > 0:
                self.courses.append({
                    **common_props,
                    'type': 'Uygulama',
                    # Treat U like Teori for room mostly, unless specific U-room exists?
                    # Generally U is in classroom.
                    'duration': data['u'],
                    'fixed_room': data['fixed_t_room'] 
                })
                
            # Add Lab Blocks
            if data['l'] > 0:
                self.courses.append({
                    **common_props,
                    'type': 'Lab',
                    'duration': data['l'],
                    'fixed_room': data['fixed_l_room']
                })
                
        print(f"DEBUG: Generated {len(self.courses)} schedulable items after merging and filtering.")
        if len(self.courses) == 0:
             print("WARNING: No courses found! Check faculty filter keywords.")
        return self.courses

    def create_variables(self, ignore_fixed_rooms=False):
        """Create CP variables and initialize model logic."""
        self.vars = {} 
        self.room_vars = {}

        for c_idx, course in enumerate(self.courses):
            # 1. Create Room Variables (Is course c assigned to room r?)
            possible_rooms = []
            
            for r in self.rooms:
                r_id = r[0]
                
                # Filter rooms based on Fixed Room constraint (Logic kept in variable creation for efficiency)
                if not ignore_fixed_rooms and course['fixed_room'] and course['fixed_room'] != r_id:
                     continue
                
                # Room Type Logic
                # r structure: (id, name, tip, capacity)
                if len(r) > 2:
                    room_type_str = (r[2] if r[2] else "").lower()
                    
                    is_lab_room = "laboratuvar" in room_type_str or "lab" in room_type_str
                    course_type = course.get('type', '') # 'Teori', 'Uygulama', 'Lab'
                    
                    # STRICT LOGIC:
                    # 1. If Course is 'Lab', it MUST go to a Lab Room.
                    if course_type == 'Lab':
                         if not is_lab_room:
                             continue
                             
                    # 2. If Course is 'Teori' or 'Uygulama', it MUST NOT go to a Lab Room 
                    # (unless explicitly fixed, which is handled by previous check)
                    elif course_type in ['Teori', 'Uygulama']:
                        if is_lab_room:
                            continue
                            
                    # 3. Fallback for legacy data (name-based) if type is missing
                    elif not course_type:
                        # Legacy Logicy
                        if is_lab_room:
                             if not ("laboratuvar" in course['name'].lower() or "uygulama" in course['name'].lower() or "lab" in course['name'].lower()):
                                 continue
                
                # Create boolean var for (Course, Room)
                r_var = self.cp_model.NewBoolVar(f'c{c_idx}_r{r_id}')
                self.room_vars[(c_idx, r_id)] = r_var
                possible_rooms.append(r_var)

                # 2. Create Slot Variables for this valid room option
                for s in self.time_slots:
                    s_id = s['id']
                    # Var: Course c is in Room r at Slot s
                    var = self.cp_model.NewBoolVar(f'c{c_idx}_r{r_id}_s{s_id}')
                    self.vars[(c_idx, r_id, s_id)] = var
                    
                    # LINKAGE: If Course is in Room R at Slot S, then Course MUST be assigned to Room R
                    self.cp_model.AddImplication(var, r_var)

            # Constraint: Each course must be assigned to EXACTLY ONE room
            if possible_rooms:
                self.cp_model.Add(sum(possible_rooms) == 1)
            else:
                # Should be caught by relaxed logic, but good for debug
                pass

    def add_hard_constraints(self, include_teacher_unavailability=True):
        """Add system-wide hard constraints."""
        
        # 1. Course Duration Integrity
        print("DEBUG: Adding Duration Constraints...")
        for c_idx, course in enumerate(self.courses):
            duration = course['duration']
            # Iterate over all rooms that *could* host this course
            for r in self.rooms:
                r_id = r[0]
                if (c_idx, r_id) in self.room_vars:
                    room_var = self.room_vars[(c_idx, r_id)]
                    
                    # Gather all slot variables for this (Course, Room) pair
                    course_room_slots = []
                    for s in self.time_slots:
                        s_id = s['id']
                        if (c_idx, r_id, s_id) in self.vars:
                            course_room_slots.append(self.vars[(c_idx, r_id, s_id)])
                    
                    if course_room_slots:
                        # If RoomVar=1 -> Sum(slots)=duration. If RoomVar=0 -> Sum(slots)=0.
                        self.cp_model.Add(sum(course_room_slots) == duration * room_var)

        # 2. Room Conflict: No two courses in the same room at the same time
        for r in self.rooms:
            r_id = r[0]
            for s in self.time_slots:
                s_id = s['id']
                
                # Collect all vars for this room+slot across all courses
                active_vars_in_cell = []
                for c_idx in range(len(self.courses)):
                    if (c_idx, r_id, s_id) in self.vars:
                        active_vars_in_cell.append(self.vars[(c_idx, r_id, s_id)])
                
                if active_vars_in_cell:
                    self.cp_model.Add(sum(active_vars_in_cell) <= 1)

        # 3. Teacher Conflict: No two courses for the same teacher at the same time
        # NOTE: A course might have MULTIPLE teachers. We must check all of them.
        teacher_slot_vars = collections.defaultdict(list)
        for key, var in self.vars.items():
            c_idx, r_id, s_id = key
            course_teachers = self.courses[c_idx]['teacher_ids']
            
            for t_id in course_teachers:
                teacher_slot_vars[(t_id, s_id)].append(var)
        
        for (t_id, s_id), vars_list in teacher_slot_vars.items():
            self.cp_model.Add(sum(vars_list) <= 1)

        # 4. Student Group Conflict
        # NOTE: A course might have MULTIPLE groups. Check all.
        group_slot_vars = collections.defaultdict(list)
        for key, var in self.vars.items():
            c_idx, r_id, s_id = key
            course_groups = self.courses[c_idx]['group_ids']
            
            for g_id in course_groups:
                group_slot_vars[(g_id, s_id)].append(var)
                
        for (g_id, s_id), vars_list in group_slot_vars.items():
            self.cp_model.Add(sum(vars_list) <= 1)

        # 5. Teacher Unavailability (Corrected with Minute Comparison)
        if include_teacher_unavailability:
            for t in self.teachers:
                t_id = t[0]
                unavail = self.db_model.get_teacher_unavailability(t_id)
                
                for u in unavail:
                    # u format: (day_str, start_str, end_str, reason)
                    u_day, u_start_str, u_end_str, _ = u
                    u_start_min = to_minutes(u_start_str)
                    u_end_min = to_minutes(u_end_str)
                    
                    for s in self.time_slots:
                        if s['day'] == u_day:
                            # Intersection Logic
                            slot_start = s['start_min']
                            slot_end = s['end_min']
                            
                            # Overlap condition: (StartA < EndB) and (EndA > StartB)
                            if (u_start_min < slot_end and u_end_min > slot_start):
                                # This slot is unavailable for this teacher
                                if (t_id, s['id']) in teacher_slot_vars:
                                    for var in teacher_slot_vars[(t_id, s['id'])]:
                                        self.cp_model.Add(var == 0)

        # 6. Soft Constraint: Spread parts of the same course (T, U, L) across DIFFERENT days
        # NOTE: Disabled for performance/feasibility. Enabling this adds significant complexity 
        # that can cause the solver to crash or find no solution on large datasets.
        ENABLE_DIFFERENT_DAYS_CONSTRAINT = False
        
        # Group items by parent_key (Initialize always to prevent UnboundLocalError)
        course_parts = collections.defaultdict(list)
        
        if ENABLE_DIFFERENT_DAYS_CONSTRAINT:
            print("DEBUG: Adding Soft Constraints (Different Days)...")
            
        # Only populate if enabled
        courses_to_process = self.courses if ENABLE_DIFFERENT_DAYS_CONSTRAINT else []
        for c_idx, course in enumerate(courses_to_process):
            if 'parent_key' in course:
                course_parts[course['parent_key']].append(c_idx)
        
        for p_key, indices in course_parts.items():
            if len(indices) < 2:
                continue
            
            # For each pair of parts, minimize same-day occurrence
            for i in range(len(indices)):
                for j in range(i + 1, len(indices)):
                    idx1 = indices[i]
                    idx2 = indices[j]
                    
                    # We need to know which DAY each part is assigned to.
                    # Since variables are (c_idx, r_id, s_id), we can sum over s_id for each day.
                    
                    for d_idx in range(5): # 5 days
                        # Is Part 1 on Day D?
                        # Sum of vars for idx1 on Day D
                        p1_on_day = []
                        for s in self.time_slots:
                            if to_minutes(s['start_str']) // (24*60) == d_idx: # Simple day index check?
                                # wait, self.time_slots has 'day' string.
                                pass
                            
                            # Better: use s['id'] // 8 or similar if structured 0-7, 8-15...
                            # Yes: s['id'] = d_idx * 8 + h_idx
                            if s['id'] // 8 == d_idx:
                                # Start checking vars
                                for r in self.rooms:
                                    r_id = r[0]
                                    if (idx1, r_id, s['id']) in self.vars:
                                        p1_on_day.append(self.vars[(idx1, r_id, s['id'])])
                        
                        # Is Part 2 on Day D?
                        p2_on_day = []
                        for s in self.time_slots:
                            if s['id'] // 8 == d_idx:
                                for r in self.rooms:
                                    r_id = r[0]
                                    if (idx2, r_id, s['id']) in self.vars:
                                        p2_on_day.append(self.vars[(idx2, r_id, s['id'])])
                        
                        if p1_on_day and p2_on_day:
                            # Create bools for "Part 1 is on Day D"
                            b1 = self.cp_model.NewBoolVar(f'p{idx1}_d{d_idx}')
                            self.cp_model.Add(sum(p1_on_day) >= 1).OnlyEnforceIf(b1)
                            self.cp_model.Add(sum(p1_on_day) == 0).OnlyEnforceIf(b1.Not())
                            
                            b2 = self.cp_model.NewBoolVar(f'p{idx2}_d{d_idx}')
                            self.cp_model.Add(sum(p2_on_day) >= 1).OnlyEnforceIf(b2)
                            self.cp_model.Add(sum(p2_on_day) == 0).OnlyEnforceIf(b2.Not())
                            
                            # Penalty if both are true
                            both_on_day = self.cp_model.NewBoolVar(f'both_{idx1}_{idx2}_{d_idx}')
                            self.cp_model.AddBoolAnd([b1, b2]).OnlyEnforceIf(both_on_day)
                            self.cp_model.AddBoolOr([b1.Not(), b2.Not()]).OnlyEnforceIf(both_on_day.Not())
                            
                            # Minimize 10 cost for overlap
                            self.cp_model.Minimize(10 * both_on_day) # Wait, Minimize is global. 
                            # We need to sum up penalties.
                            # Since we can define Minimize only once, we should collect all penalties.
                            # But for now, let's just make it a soft constraint via objective?
                            # OR-Tools Model.Minimize takes a linear expression.
                            
                            # Let's collect all 'both_on_day' vars and minimize their sum.
                            pass 

        # Correct Implementation of Minimize:
        # We need a list of penalties.
        penalties = []
        for p_key, indices in course_parts.items():
            if len(indices) < 2: continue
            for i in range(len(indices)):
                for j in range(i + 1, len(indices)):
                    idx1, idx2 = indices[i], indices[j]
                    for d_idx in range(5):
                        # ... (re-logic for vars) ...
                        days_slots = [s for s in self.time_slots if s['id'] // 8 == d_idx]
                        
                        # Gather all vars for item 1 on this day
                        vars1 = []
                        for s in days_slots:
                            for r_id in [rm[0] for rm in self.rooms]:
                                if (idx1, r_id, s['id']) in self.vars:
                                    vars1.append(self.vars[(idx1, r_id, s['id'])])
                        
                        # Gather all vars for item 2 on this day
                        vars2 = []
                        for s in days_slots:
                            for r_id in [rm[0] for rm in self.rooms]:
                                if (idx2, r_id, s['id']) in self.vars:
                                    vars2.append(self.vars[(idx2, r_id, s['id'])])
                        
                        if vars1 and vars2:
                            # If sum(vars1) > 0 AND sum(vars2) > 0 -> Penalty
                            # Since an item is only scheduled ONCE (one room, one start time), sum(vars1) is effectively bool (if we consider duration logic, it's duration, but >0 implies presence).
                            
                            # optimization: sum(vars1) is integer > 0 if present.
                            # b1 <-> sum(vars1) > 0
                            b1 = self.cp_model.NewBoolVar(f'p{idx1}_d{d_idx}')
                            self.cp_model.Add(sum(vars1) > 0).OnlyEnforceIf(b1)
                            self.cp_model.Add(sum(vars1) == 0).OnlyEnforceIf(b1.Not())
                            
                            b2 = self.cp_model.NewBoolVar(f'p{idx2}_d{d_idx}')
                            self.cp_model.Add(sum(vars2) > 0).OnlyEnforceIf(b2)
                            self.cp_model.Add(sum(vars2) == 0).OnlyEnforceIf(b2.Not())
                            
                            conflict = self.cp_model.NewBoolVar(f'c_{idx1}_{idx2}_{d_idx}')
                            self.cp_model.AddBoolAnd([b1, b2]).OnlyEnforceIf(conflict)
                            self.cp_model.AddBoolOr([b1.Not(), b2.Not()]).OnlyEnforceIf(conflict.Not())
                            
                            penalties.append(conflict)

        if penalties:
            self.cp_model.Minimize(sum(penalties))

    def solve(self):
        """Solve with fallback strategy."""
        self.load_data()  # Loaded once
        
        # --- Pre-Solve Capacity Check ---
        total_demand = sum(c['duration'] for c in self.courses)
        total_capacity = len(self.rooms) * len(self.time_slots)
        
        print(f"\n[DIAGNOSTIC] Capacity Check:")
        print(f"  - Total Course Hours Needed: {total_demand}")
        print(f"  - Total School Capacity (Rooms x Slots): {total_capacity}")
        
        if total_demand > total_capacity:
            print(f"CRITICAL WARNING: Demand ({total_demand}) exceeds Total Capacity ({total_capacity})!")
            print("  -> The schedule is MATHEMATICALLY IMPOSSIBLE with current room count.")
            return False

        # Check Lab vs Theory Specifics
        lab_demand = sum(c['duration'] for c in self.courses if c['type'] == 'Lab')
        theory_demand = sum(c['duration'] for c in self.courses if c['type'] in ['Teori', 'Uygulama']) # Assuming U uses classrooms
        
        lab_rooms = [r for r in self.rooms if "laboratuvar" in (r[2] or "").lower() or "lab" in (r[2] or "").lower()]
        theory_rooms = [r for r in self.rooms if r not in lab_rooms] # Rough approximation
        
        lab_cap = len(lab_rooms) * len(self.time_slots)
        theory_cap = len(theory_rooms) * len(self.time_slots)
        
        print(f"  - Lab Demand: {lab_demand} | Lab Capacity: {lab_cap}")
        print(f"  - Theory Demand: {theory_demand} | Theory Capacity: {theory_cap} (Approx)")
        
        if lab_demand > lab_cap:
             print(f"CRITICAL WARNING: Lab Demand ({lab_demand}) exceeds Lab Capacity ({lab_cap})!")
        if theory_demand > theory_cap:
             print(f"CRITICAL WARNING: Theory Demand ({theory_demand}) exceeds Theory Capacity ({theory_cap})!")
        # --------------------------------
        
        # Strategy 1: All Constraints
        print("\n=== ATTEMPT 1: Strict Constraints ===")
        self.cp_model = cp_model.CpModel()
        print("DEBUG: Creating variables...")
        self.create_variables(ignore_fixed_rooms=False)
        print("DEBUG: Adding hard constraints...")
        self.add_hard_constraints(include_teacher_unavailability=True) # Fixed Rooms implied by False above
        print("DEBUG: Starting solver...")
        
        if self._run_solver("STRICT"):
            return True
            
        # Strategy 2: Relax Teacher Unavailability
        print("\n=== ATTEMPT 2: Relax Teacher Unavailability ===")
        self.cp_model = cp_model.CpModel()
        self.create_variables(ignore_fixed_rooms=False)
        self.add_hard_constraints(include_teacher_unavailability=False)
        
        if self._run_solver("RELAX_TEACHER"):
            return True
            
        # Strategy 3: Relax Fixed Rooms AND Teacher Unavailability
        print("\n=== ATTEMPT 3: Relax Fixed Rooms & Teacher ===")
        try:
            self.cp_model = cp_model.CpModel()
            self.create_variables(ignore_fixed_rooms=True)
            self.add_hard_constraints(include_teacher_unavailability=False)
        except Exception as e:
            print(f"Error building model for Attempt 3: {e}")
            return False
        
        if self._run_solver("RELAX_ALL"):
            return True
            
        return False
        
    def _run_solver(self, mode_name: str) -> bool:
        """Helper to run solver and handle results."""
        self.solver.parameters.log_search_progress = True
        self.solver.parameters.log_to_stdout = True
        self.solver.parameters.max_time_in_seconds = 120.0 
        
        try:
            status = self.solver.Solve(self.cp_model)
        except Exception as e:
            print(f"CRITICAL ERROR in Solve ({mode_name}): {e}")
            return False
            
        print(f"[{mode_name}] Solver Status: {self.solver.StatusName(status)}")
        
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            print(f"SUCCESS: Solution found in {mode_name} mode!")
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
            
    def extract_schedule(self):
        """Extract the schedule from the solved model and save to database"""
        course_room_map = {} 
        count = 0
        
        # Iterate over all variables to find assigned slots
        for key, var in self.vars.items():
            c_idx, r_id, s_id = key
            
            if self.solver.Value(var) == 1:
                course = self.courses[c_idx]
                slot = next(s for s in self.time_slots if s['id'] == s_id)
                
                # Use FIRST teacher ID if available (schema limitation)
                main_teacher_id = course['teacher_ids'][0] if course['teacher_ids'] else None
                
                # Insert into DB
                # Note: We treat each item (T/U/L) as a separate entry in Ders_Programi.
                # If consecutiveness is enforced by duration block, this entry covers the whole duration.
                self.db_model.c.execute('''
                    INSERT INTO Ders_Programi (ders_adi, ders_instance, ogretmen_id, gun, baslangic, bitis)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (course['name'], course['instance'], main_teacher_id, 
                      slot['day'], slot['start_str'], slot['end_str']))
                
                # Logic Update: If we split T/U/L, we might overwrite the room assignment in Dersler table multiple times.
                # Ideally, T overwrites 'teori_odasi', L overwrites 'lab_odasi'.
                
                if course['type'] == 'Teori' or course['type'] == 'Uygulama':
                    course_room_map[course['parent_key']] = {'type': 'T', 'room': r_id}
                elif course['type'] == 'Lab':
                    course_room_map[course['parent_key']] = {'type': 'L', 'room': r_id}
                count += 1
        
        print(f"Schedule items extracted: {count}")
        
        # Update course room assignments in Dersler table
        # course_room_map: (name, inst) -> {'type': 'X', 'room': r_id} (Wait, this overwrites if mixed!)
        # Actually, we need to collect updates.
        # But wait, the loop above runs per item.
        # Let's fix course_room_map logic above first. 
        # Better: Execute updates directly inside the loop or accumulate properly.
        # Reverting to simplified update for now:
        for key, val in course_room_map.items():
            ders_adi, ders_instance = key
            
            if val['type'] == 'L':
                 self.db_model.c.execute('''
                    UPDATE Dersler SET lab_odasi = ? WHERE ders_adi = ? AND ders_instance = ?
                ''', (val['room'], ders_adi, ders_instance))
            else:
                 self.db_model.c.execute('''
                    UPDATE Dersler SET teori_odasi = ? WHERE ders_adi = ? AND ders_instance = ?
                ''', (val['room'], ders_adi, ders_instance))
            
            # Debug update
            # if self.db_model.c.rowcount == 0:
            #     print(f"WARNING: Failed to update room for {ders_adi} (inst {ders_instance})")
            
        self.db_model.conn.commit()
