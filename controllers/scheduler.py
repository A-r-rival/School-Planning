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

    def _fetch_all_course_instances(self) -> List[Dict]:
        """Fetch course instances, deduplicating multiple rows into teacher/group lists."""
        query = '''
            SELECT 
                d.ders_adi, 
                d.ders_instance, 
                d.teori_odasi, 
                d.lab_odasi,
                doi.ogretmen_id,
                dsi.donem_sinif_num
            FROM Dersler d
            LEFT JOIN Ders_Ogretmen_Iliskisi doi ON d.ders_adi = doi.ders_adi AND d.ders_instance = doi.ders_instance
            LEFT JOIN Ders_Sinif_Iliskisi dsi ON d.ders_adi = dsi.ders_adi AND d.ders_instance = dsi.ders_instance
        '''
        self.db_model.c.execute(query)
        rows = self.db_model.c.fetchall()
        
        # Deduplicate Logic
        # (ders_adi, instance) -> { 'teori':..., 'lab':..., 'teachers': set(), 'groups': set() }
        course_map = {}
        
        for row in rows:
            ders_adi, instance, teori, lab, teacher_id, group_id = row
            key = (ders_adi, instance)
            
            if key not in course_map:
                course_map[key] = {
                    'name': ders_adi,
                    'instance': instance,
                    'fixed_room': teori if teori else lab,
                    'teacher_ids': set(),
                    'group_ids': set(),
                    'duration': 1
                }
            
            if teacher_id:
                course_map[key]['teacher_ids'].add(teacher_id)
            if group_id:
                course_map[key]['group_ids'].add(group_id)
                
        # Convert to list
        courses = []
        for key, val in course_map.items():
            # Convert sets to lists for stability (optional)
            val['teacher_ids'] = list(val['teacher_ids'])
            val['group_ids'] = list(val['group_ids'])
            courses.append(val)
            
        print(f"Loaded {len(courses)} unique course instances to schedule (aggregated from {len(rows)} rows).")
        return courses

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
                    room_type = r[2] if r[2] else ""
                    # If Room is a Lab
                    if "Laboratuvar" in room_type or "Lab" in room_type:
                        # 1. Heuristic: Course name must imply Lab need
                        if not ("Laboratuvar" in course['name'] or "Uygulama" in course['name'] or "Lab" in course['name']):
                            continue
                        
                        # 2. Faculty Constraint: Only Science, Engineering, Architecture can use Labs
                        facs = self.course_faculties.get((course['name'], course['instance']), [])
                        # Check if ANY associated faculty is allowed
                        allowed_facs = ["Mühendislik", "Fen", "Mimarlık", "Engineering", "Science", "Architecture"]
                        
                        # If we have faculty info, enforce restriction
                        if facs:
                            is_allowed = False
                            for f_name in facs:
                                for allowed in allowed_facs:
                                    if allowed in f_name:
                                        is_allowed = True
                                        break
                                if is_allowed: break
                            
                            if not is_allowed:
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

    def solve(self):
        """Solve with fallback strategy."""
        self.load_data()  # Loaded once
        
        # Strategy 1: All Constraints
        print("\n=== ATTEMPT 1: Strict Constraints ===")
        self.cp_model = cp_model.CpModel()
        self.create_variables(ignore_fixed_rooms=False)
        self.add_hard_constraints(include_teacher_unavailability=True) # Fixed Rooms implied by False above
        
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
        self.solver.parameters.log_search_progress = False
        self.solver.parameters.log_to_stdout = False
        self.solver.parameters.max_time_in_seconds = 30.0 
        
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
                self.db_model.c.execute('''
                    INSERT INTO Ders_Programi (ders_adi, ders_instance, ogretmen_id, gun, baslangic, bitis)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (course['name'], course['instance'], main_teacher_id, 
                      slot['day'], slot['start_str'], slot['end_str']))
                
                course_room_map[(course['name'], course['instance'])] = r_id
                count += 1
        
        print(f"Schedule items extracted: {count}")
        
        # Update course room assignments in Dersler table
        for (ders_adi, ders_instance), room_id in course_room_map.items():
            self.db_model.c.execute('''
                UPDATE Dersler SET teori_odasi = ? WHERE ders_adi = ? AND ders_instance = ?
            ''', (room_id, ders_adi, ders_instance))
            
            # Debug update
            if self.db_model.c.rowcount == 0:
                print(f"WARNING: Failed to update room for {ders_adi} (inst {ders_instance})")
            
        self.db_model.conn.commit()
