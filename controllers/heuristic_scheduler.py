
# -*- coding: utf-8 -*-
import random
from typing import List, Dict, Optional, Tuple, Set

class HeuristicScheduler:
    def __init__(self, model):
        self.db_model = model
        self.courses = []
        self.rooms = []
        self.teachers = []
        self.time_slots = []
        self.assignments = [] # List of (course_idx, room_id, slot_id)
        
        # Caches for fast checking
        self.room_schedule = {} # (room_id, slot_id) -> course_idx
        self.teacher_schedule = {} # (teacher_id, slot_id) -> course_idx
        self.group_schedule = {} # (group_id, slot_id) -> course_idx
        self.assigned_courses = set()

    def load_data(self):
        # 1. Load Rooms
        self.rooms = self.db_model.aktif_derslikleri_getir() # [(id, name, type, capacity), ...]
        print(f"Loaded {len(self.rooms)} rooms.")
        
        # 2. Load Courses
        self.courses = self._fetch_all_course_instances()
        
        # 3. Load Teachers (just needed for checks)
        self.teachers = self.db_model.get_all_teachers_with_ids()
        
        # 4. Time Slots
        days = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma']
        hours = ['09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00']
        self.time_slots = []
        for d_idx, day in enumerate(days):
            for h_idx, hour in enumerate(hours):
                self.time_slots.append({
                    'id': d_idx * 8 + h_idx,
                    'day': day,
                    'start': hour,
                    'end': f"{int(hour[:2])+1}:00"
                })
        
        # 5. Teacher Unavailability Cache
        self.teacher_unavailability = {} # teacher_id -> set of slot_ids
        for t in self.teachers:
            t_id = t[0]
            unavail = self.db_model.get_teacher_unavailability(t_id)
            if unavail:
                self.teacher_unavailability[t_id] = set()
                for u in unavail:
                    u_day, u_start, u_end, _ = u
                    # Find slots covering this range
                    for s in self.time_slots:
                        if s['day'] == u_day:
                            if (u_start < s['end'] and u_end > s['start']):
                                self.teacher_unavailability[t_id].add(s['id'])

    def _fetch_all_course_instances(self) -> List[Dict]:
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
        
        courses = []
        for row in rows:
            ders_adi, instance, teori, lab, teacher_id, group_id = row
            courses.append({
                'name': ders_adi,
                'instance': instance,
                'teacher_id': teacher_id,
                'group_id': group_id,
                'fixed_room': teori if teori else lab,
                'duration': 1
            })
        print(f"Loaded {len(courses)} courses.")
        return courses

    def solve(self):
        print("Starting Heuristic Schedule Generation...")
        
        # Sort courses to handle difficult ones first
        # 1. Fixed rooms
        # 2. Most conflicts (heuristic: shared groups)
        # For now, simplistic sort: Fixed Room first
        self.courses.sort(key=lambda x: (x['fixed_room'] is None, x['group_id'] or ''))
        
        unscheduled = []
        
        for c_idx, course in enumerate(self.courses):
            assigned = False
            
            # Determine potential rooms
            valid_rooms = []
            if course['fixed_room']:
                # Find the room object with this ID
                for r in self.rooms:
                    if r[0] == course['fixed_room']:
                        valid_rooms.append(r)
                        break
            else:
                valid_rooms = self.rooms # Any room (ignore capacity/type for now, assumption: all fit)
            
            if not valid_rooms:
                print(f"Warning: No valid room for {course['name']}")
                unscheduled.append(course)
                continue

            # Try to find a slot
            # Shuffle slots/rooms to randomize?
            # User invited randomization.
            time_indices = list(range(len(self.time_slots)))
            random.shuffle(time_indices)
            
            for s_id in time_indices:
                if assigned: break
                
                # Check teacher constraints
                t_id = course['teacher_id']
                if t_id:
                    # Check unavailability
                    if t_id in self.teacher_unavailability and s_id in self.teacher_unavailability[t_id]:
                        continue
                    # Check overlap
                    if (t_id, s_id) in self.teacher_schedule:
                        continue
                
                # Check group constraints
                g_id = course['group_id']
                if g_id:
                    if (g_id, s_id) in self.group_schedule:
                        continue
                        
                # Check Room availability
                for r in valid_rooms:
                    r_id = r[0]
                    if (r_id, s_id) in self.room_schedule:
                        continue
                    
                    # FOUND A SLOT!
                    self._assign(c_idx, r_id, s_id)
                    assigned = True
                    break
            
            if not assigned:
                unscheduled.append(course)
        
        print(f"Scheduled: {len(self.assignments)}/{len(self.courses)}")
        if unscheduled:
            print(f"Unscheduled: {len(unscheduled)}")
            # print([c['name'] for c in unscheduled[:10]])
            
        return len(unscheduled) == 0

    def _assign(self, c_idx, r_id, s_id):
        course = self.courses[c_idx]
        self.assignments.append((c_idx, r_id, s_id))
        
        self.room_schedule[(r_id, s_id)] = c_idx
        
        if course['teacher_id']:
            self.teacher_schedule[(course['teacher_id'], s_id)] = c_idx
            
        if course['group_id']:
            self.group_schedule[(course['group_id'], s_id)] = c_idx
            
    def extract_schedule(self):
        print("Saving schedule...")
        course_room_map = {}
        
        for c_idx, r_id, s_id in self.assignments:
            course = self.courses[c_idx]
            slot = self.time_slots[s_id]
            
            self.db_model.c.execute('''
                INSERT INTO Ders_Programi (ders_adi, ders_instance, ogretmen_id, gun, baslangic, bitis)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (course['name'], course['instance'], course['teacher_id'], slot['day'], slot['start'], slot['end']))
            
            course_room_map[(course['name'], course['instance'])] = r_id
            
        # Update rooms in Dersler
        for (ders_adi, ders_instance), r_id in course_room_map.items():
            self.db_model.c.execute('''
                UPDATE Dersler SET teori_odasi = ? WHERE ders_adi = ? AND ders_instance = ?
            ''', (r_id, ders_adi, ders_instance))
            
        self.db_model.conn.commit()
