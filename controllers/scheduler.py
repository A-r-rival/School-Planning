# -*- coding: utf-8 -*-
"""
Scheduler Module using Google OR-Tools
Handles automatic schedule generation with hard and soft constraints
"""
from ortools.sat.python import cp_model
from typing import List, Dict, Tuple, Optional
import collections

class ORToolsScheduler:
    def __init__(self, model):
        """
        Initialize the scheduler with the data model
        Args:
            model: The ScheduleModel instance containing database connections
        """
        self.db_model = model
        self.cp_model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()
        
        # Data caches
        self.courses = []
        self.rooms = []
        self.teachers = []
        self.time_slots = []
        
        # Decision variables
        self.vars = {} # (course_id, room_id, slot_id) -> bool_var

    def load_data(self):
        """Load necessary data from database"""
        # 1. Load Rooms
        self.rooms = self.db_model.aktif_derslikleri_getir() # [(id, name, type, capacity), ...]
        
        # 2. Load Courses (that need scheduling)
        # For now, let's assume we schedule ALL courses in the database
        # In reality, we might filter by semester or department
        # We need a method to get all course instances with their metadata
        self.courses = self._fetch_all_course_instances()
        
        # 3. Load Teachers
        self.teachers = self.db_model.get_all_teachers_with_ids()
        
        # 4. Define Time Slots
        # Mon-Fri, 09:00 to 17:00 (8 slots per day)
        days = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma']
        hours = ['09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00']
        self.time_slots = []
        for d_idx, day in enumerate(days):
            for h_idx, hour in enumerate(hours):
                # Calculate end time (assuming 50 min blocks + 10 min break)
                # For simplicity, let's say slots are indices 0..39
                self.time_slots.append({
                    'id': d_idx * 8 + h_idx,
                    'day': day,
                    'start': hour,
                    'end': f"{int(hour[:2])+1}:00" # Simple +1 hour
                })

    def _fetch_all_course_instances(self) -> List[Dict]:
        """
        Fetch all course instances that need to be scheduled.
        Returns a list of dicts with course details.
        """
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
            LIMIT 50
        '''
        self.db_model.c.execute(query)
        rows = self.db_model.c.fetchall()
        
        courses = []
        for row in rows:
            ders_adi, instance, teori, lab, teacher_id, group_id = row
            courses.append({
                'name': ders_adi,
                'instance': instance,
                'teacher_id': teacher_id,
                'group_id': group_id,
                'fixed_room': teori if teori else lab,
                'duration': 1 # Default 1 hour
            })
            
        print(f"Loaded {len(courses)} courses to schedule.")
        return courses

    def create_variables(self):
        """Create CP variables"""
        # 1. Slot assignment variables: vars[(c_idx, r_id, s_id)]
        # 2. Room assignment variables: room_vars[(c_idx, r_id)]
        self.room_vars = {}

        for c_idx, course in enumerate(self.courses):
            # Create Room Variables
            possible_rooms = []
            for r in self.rooms:
                r_id = r[0]
                # Check if room matches course requirements
                if course['fixed_room'] and course['fixed_room'] != r_id:
                    continue
                
                self.room_vars[(c_idx, r_id)] = self.cp_model.NewBoolVar(f'c{c_idx}_r{r_id}')
                possible_rooms.append(self.room_vars[(c_idx, r_id)])
                
                # Create Slot Variables for this room
                for s in self.time_slots:
                    s_id = s['id']
                    self.vars[(c_idx, r_id, s_id)] = self.cp_model.NewBoolVar(
                        f'c{c_idx}_r{r_id}_s{s_id}'
                    )
            
            # Constraint: Each course must have exactly one room assigned
            if possible_rooms:
                self.cp_model.Add(sum(possible_rooms) == 1)
            else:
                print(f"Error: No valid room for course {course['name']}")

    def add_hard_constraints(self):
        """Add hard constraints"""
        
        # 1. Link Slot Variables to Room Variables
        # If a course is assigned to a slot in a room, that room must be the chosen room for the course
        for (c_idx, r_id, s_id), var in self.vars.items():
            # var implies room_vars[(c_idx, r_id)]
            self.cp_model.AddImplication(var, self.room_vars[(c_idx, r_id)])

        # 2. Each course must be assigned exactly 'duration' slots
        for c_idx, course in enumerate(self.courses):
            all_course_slots = []
            for r_id in [r[0] for r in self.rooms]:
                for s in self.time_slots:
                    s_id = s['id']
                    if (c_idx, r_id, s_id) in self.vars:
                        all_course_slots.append(self.vars[(c_idx, r_id, s_id)])
            
            if all_course_slots:
                self.cp_model.Add(sum(all_course_slots) == course['duration'])

        # 3. No two courses in the same room at the same time
        # for r in self.rooms:
        #     r_id = r[0]
        #     for s in self.time_slots:
        #         s_id = s['id']
        #         room_slot_vars = []
        #         for c_idx in range(len(self.courses)):
        #             if (c_idx, r_id, s_id) in self.vars:
        #                 room_slot_vars.append(self.vars[(c_idx, r_id, s_id)])
        #         if room_slot_vars:
        #             self.cp_model.Add(sum(room_slot_vars) <= 1)

        # 4. No two courses for the same teacher at the same time
        # teacher_slot_vars = collections.defaultdict(list)
        # for (c_idx, r_id, s_id), var in self.vars.items():
        #     teacher_id = self.courses[c_idx]['teacher_id']
        #     if teacher_id:
        #         teacher_slot_vars[(teacher_id, s_id)].append(var)
        
        # for (t_id, s_id), vars_list in teacher_slot_vars.items():
        #     self.cp_model.Add(sum(vars_list) <= 1)

        # 5. No two courses for the same student group at the same time
        # group_slot_vars = collections.defaultdict(list)
        # for (c_idx, r_id, s_id), var in self.vars.items():
        #     group_id = self.courses[c_idx]['group_id']
        #     if group_id:
        #         group_slot_vars[(group_id, s_id)].append(var)
                
        # for (g_id, s_id), vars_list in group_slot_vars.items():
        #     self.cp_model.Add(sum(vars_list) <= 1)

        # 6. Teacher Unavailability
        # for t in self.teachers:
        #     t_id = t[0]
        #     unavail = self.db_model.get_teacher_unavailability(t_id)
        #     for u in unavail:
        #         u_day, u_start, u_end, _ = u
        #         for s in self.time_slots:
        #             if s['day'] == u_day:
        #                 if (u_start < s['end'] and u_end > s['start']):
        #                     if (t_id, s['id']) in teacher_slot_vars:
        #                         # Teacher is unavailable at this slot, prohibit all courses assigned to this teacher
        #                         for var in teacher_slot_vars[(t_id, s['id'])]:
        #                             self.cp_model.Add(var == 0)

    def solve(self):
        """Solve the scheduling problem"""
        print("Solving...")
        status = self.solver.Solve(self.cp_model)
        print(f"Solver Status: {self.solver.StatusName(status)}")
        
        if status == cp_model.INFEASIBLE:
            print("Problem is INFEASIBLE. Checking conflicts...")
            # We could add IIS computation here or relax constraints
        
        return status
    
    def extract_schedule(self):
        """Extract the schedule from the solved model and save to database"""
        # Track which room was assigned to which course to update Dersler table
        course_room_map = {} # (ders_adi, ders_instance) -> room_id
        
        for (c_idx, r_id, s_id), var in self.vars.items():
            if self.solver.Value(var) == 1:
                course = self.courses[c_idx]
                slot = next(s for s in self.time_slots if s['id'] == s_id)
                
                # Add to schedule
                self.db_model.c.execute('''
                    INSERT INTO Ders_Programi (ders_adi, ders_instance, ogretmen_id, gun, baslangic, bitis)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (course['name'], course['instance'], course['teacher_id'], slot['day'], slot['start'], slot['end']))
                
                # Record room assignment
                course_room_map[(course['name'], course['instance'])] = r_id
        
        # Update rooms in Dersler table
        for (ders_adi, ders_instance), room_id in course_room_map.items():
            # We assume it's a theory room for now. If it was a lab course, we might need to update lab_odasi.
            # But since we don't distinguish yet, let's update teori_odasi.
            self.db_model.c.execute('''
                UPDATE Dersler SET teori_odasi = ? WHERE ders_adi = ? AND ders_instance = ?
            ''', (room_id, ders_adi, ders_instance))
            
        self.db_model.conn.commit()
