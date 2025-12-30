# -*- coding: utf-8 -*-
"""
Scheduler Module using Google OR-Tools
Handles automatic schedule generation with hard and soft constraints
"""
from ortools.sat.python import cp_model
from typing import List, Dict, Tuple, Optional
import collections
from scripts import curriculum_data

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
        Fetch courses from curriculum_data, implementing:
        1. Faculty Filter (Engineering & Science only)
        2. Course Merging (Same Name & Teacher -> Single Instance)
        3. T/U/L Splitting
        """
        self.course_faculties = {} # Map (name, instance) -> [faculties]
        
        # Merging Dictionary: (name, frozenset(teachers)) -> CourseDict
        # merged_courses removed - was unused
        
        # Allowed Faculties Filter (TEMP: Engineering only for testing)
        ALLOWED_KEYWORDS = ["mühendislik", "engineering"]

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
        # Use Ders_Ogretmen_Iliskisi (Teacher-Course Relationship) table
        teacher_map = collections.defaultdict(set)
        self.db_model.c.execute("""
            SELECT ogretmen_id, ders_adi 
            FROM Ders_Ogretmen_Iliskisi
        """)
        for t_id, d_name in self.db_model.c.fetchall():
            if d_name:
                teacher_map[d_name.strip()].add(t_id)
                     
        # Now fetch courses from DB linked with Fac/Dept
        query = '''
            SELECT d.ders_adi, d.ders_instance, d.teori_saati, d.uygulama_saati, d.lab_saati, d.akts,
                   d.teori_odasi, d.lab_odasi,
                   dsi.donem_sinif_num,
                   f.fakulte_adi,
                   d.ders_kodu,
                   b.bolum_adi
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
            name, instance, t, u, l, akts, t_room, l_room, group_id, fac_name, code, dept_name = r
            
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

            # --- ACTUALIZATION LOGIC ---
            items_to_process = []
            is_expanded = False
            
            # Check Curriculum Data for Pools
            if dept_name and code:
                dept_data = curriculum_data.DEPARTMENTS_DATA.get(dept_name.strip())
                if dept_data and 'pools' in dept_data:
                    # Match code to pool keys (e.g. ZSDI -> ZSD)
                    for pool_key, pool_courses in dept_data['pools'].items():
                        # If the course code starts with the pool key (Simple Heuristic)
                        # e.g. code="ZSDI", pool_key="ZSD" -> Match
                        # e.g. code="SDII", pool_key="SD" -> Match
                        if code.startswith(pool_key):
                            is_expanded = True
                            # Generate items for each course in the pool
                            for p_code, p_name, p_akts, p_t, p_u, p_l in pool_courses:
                                items_to_process.append({
                                    'name': p_name,
                                    't': p_t, 'u': p_u, 'l': p_l, 'akts': p_akts,
                                    'code': pool_key, # USE POOL KEY AS CODE FOR OVERLAP logic
                                    'real_code': p_code,
                                    'is_pool': True
                                })
                            break
            
            if not is_expanded:
                items_to_process.append({
                    'name': name,
                    't': t, 'u': u, 'l': l, 'akts': akts,
                    'code': code,
                    'real_code': code,
                    'is_pool': False
                })

            for item_data in items_to_process:
                i_name = item_data['name']
                
                
                # Exclusions (Apply to expanded names too)
                name_lower = i_name.lower()
                
                # Generic exclusions
                if any(x in name_lower for x in ["staj", "işletmede mesleki eğitim", "mesleki uygulama", "lisans bitirme çalışması", "tez"]):
                    continue
                
                # Pool placeholder exclusions (SDUx, USD000, ZSD000, etc.)
                # These are student curriculum placeholders, not actual schedulable courses
                if any(x in name_lower for x in [
                    "seçmeli ders havuzu", "elective pool", "elective course pool",
                    "uzmanlık a, b, c", "specialization a, b, c"
                ]):
                    continue
                
                # Also check course codes for placeholders
                i_code = item_data.get('code', '')  # Get code from item_data
                if i_code:
                    code_upper = i_code.upper()
                    # SDUx, USD000, GSD000, ZSD000, etc. (ends with x or 000)
                    if code_upper.endswith('X') or code_upper.endswith('000'):
                        if any(code_upper.startswith(prefix) for prefix in ['SDU', 'USD', 'GSD', 'ZSD', 'SD', 'ÜSD']):
                            continue
                
                # Specific project exclusions (not regular courses)
                if any(x in name_lower for x in [
                    "proje i", "proje ii",  # Bitirme projeleri
                    "bitirme projesi",
                    "seçmeli alan - proje", "seçmeli ders alanı - proje",
                    "yazılım projesi", "donanım projesi", "endüstri projesi",
                    "mekatronik projesi", "elektrik-elektronik müh. projesi",
                    "yazılım mühendisliği projesi", "elektrik ve elektronik mühendisliği projesi",
                    "interdisipliner proje", "uygulamalı proje"
                ]):
                    continue

                # Fallback Hours
                i_t, i_u, i_l = item_data['t'], item_data['u'], item_data['l']
                if i_t == 0 and i_u == 0 and i_l == 0:
                    akts_val = item_data['akts'] if item_data['akts'] else 0
                    i_t = min(akts_val, 4)

                # Teachers
                # Try getting teacher for the specific course name, else fallback?
                # For expanded courses, we likely don't have teacher in DB.
                # In that case, teacher_map returning empty set is fine (User will see "Atanmamış").
                t_ids = frozenset(teacher_map.get(i_name, []))
                
                # Unique Key for Merging
                merge_key = (i_name, t_ids)
                
                if merge_key not in merged_map:
                    merged_map[merge_key] = {
                        'name': i_name,
                        'teacher_ids': list(t_ids),
                        't': i_t, 'u': i_u, 'l': i_l,
                        'akts': item_data['akts'],
                        'priority_instance': instance, # Inherit original instance ID (useful for group linking)
                        'group_ids': set(),
                        'fixed_t_room': t_room if not is_expanded else None, # Don't enforce room on expanded items unless specific?
                        'fixed_l_room': l_room if not is_expanded else None,
                        'faculties': set(),
                        'code': item_data['code'], # This is key for overlap
                        'pool_codes': set() # Track for coloring
                    }
                
                # Aggregate
                item = merged_map[merge_key]
                item['group_ids'].add(group_id)
                if fac_name: item['faculties'].add(fac_name)
                if item_data['is_pool']:
                     item['pool_codes'].add(item_data['code'])
                # Logic: If one instance has fixed room, we adopt it (Optimistic)
                if not is_expanded:
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
                'parent_key': (name, c_inst),  # Tuple for unpacking in extract_schedule
                'code': data['code'],
                'is_elective': "seçmeli" in name.lower() or "sdi" in data['code'].lower() or "gsd" in data['code'].lower() or len(data.get('pool_codes', [])) > 0,
                'pool_codes': list(data.get('pool_codes', []))
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
        
        print(f"DEBUG: Creating variables for {len(self.courses)} courses...")

        for c_idx, course in enumerate(self.courses):
            # Optimization: Skip variable creation for courses not in active phase
            if active_indices is not None and c_idx not in active_indices:
                continue
                
            duration = course['duration']
            
            # 1. Create Room Variables
            possible_rooms = []
            
            for r in self.rooms:
                r_id = r[0]
                
                # Filter rooms logic
                if not ignore_fixed_rooms and course['fixed_room'] and course['fixed_room'] != r_id:
                     continue
                
                # Room Type Logic
                if len(r) > 2:
                    room_type_str = (r[2] if r[2] else "").lower()
                    is_lab_room = "laboratuvar" in room_type_str or "lab" in room_type_str
                    course_type = course.get('type', '')
                    
                    if course_type == 'Lab':
                         if not is_lab_room: continue
                    elif course_type in ['Teori', 'Uygulama']:
                        if is_lab_room: continue
                    elif not course_type:
                        if is_lab_room:
                             if not ("laboratuvar" in course['name'].lower() or "uygulama" in course['name'].lower() or "lab" in course['name'].lower()):
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
                else:
                    # Duration too long for any day? Disable room
                    self.cp_model.Add(r_var == 0)

                # 3. Create Occupancy Vars (self.vars) linked to Starts
                # Occ[t] = Sum(Start[s]) for all s where s <= t < s+dur
                for t in self.time_slots:
                    t_id = t['id']
                    
                    # Find all starts that would cover time t
                    # A start at s covers t if: s <= t AND s + duration > t
                    # => s <= t AND s > t - duration
                    # => s in [t - duration + 1, t]
                    
                    relevant_starts = []
                    min_s = max(0, t_id - duration + 1)
                    max_s = t_id
                    
                    for s_id in range(min_s, max_s + 1):
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
            if possible_rooms:
                if c_idx in optional_indices:
                     self.cp_model.Add(sum(possible_rooms) <= 1)
                else:
                     self.cp_model.Add(sum(possible_rooms) == 1)
        
        print(f"DEBUG: Created {len(self.starts)} start variables, {len(self.vars)} occupancy variables")

    def add_hard_constraints(self, include_teacher_unavailability=True):
        """Add system-wide hard constraints."""
        
        # 1. Course Duration Integrity
        # [REMOVED] - Intrinsic to the variable creation logic now.
        pass

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

        # 4. Student Group Conflict (Intra-Pool Overlap Allowed)
        # Structure: (group_id, slot_id) -> { 'cores': [], 'electives': { 'pool_code': [vars] } }
        group_slot_data = collections.defaultdict(lambda: {'cores': [], 'electives': collections.defaultdict(list)})
        
        for key, var in self.vars.items():
            c_idx, r_id, s_id = key
            course = self.courses[c_idx]
            groups = course['group_ids']
            
            is_elective = course.get('is_elective', False)
            pool_code = course.get('code', 'UNKNOWN_POOL')
            
            for g_id in groups:
                entry = group_slot_data[(g_id, s_id)]
                if is_elective:
                    entry['electives'][pool_code].append(var)
                else:
                    entry['cores'].append(var)

        # Store for later use in soft constraints
        self.group_slot_data = group_slot_data
        
        for (g_id, s_id), data in group_slot_data.items():
            # NEW: Allow all elective overlaps, only prevent Core + Elective
            constraints_terms = list(data['cores'])
            
            # Aggregate ALL elective vars (ignore pool separation)
            all_elective_vars = []
            for pool_vars in data['electives'].values():
                all_elective_vars.extend(pool_vars)
            
            if all_elective_vars:
                # Single indicator: ANY elective active?
                elective_active = self.cp_model.NewBoolVar(f'elec_active_g{g_id}_s{s_id}')
                self.cp_model.AddMaxEquality(elective_active, all_elective_vars)
                constraints_terms.append(elective_active)
            
            if constraints_terms:
                # At most core OR elective (not both)
                self.cp_model.Add(sum(constraints_terms) <= 1)

        # 5. Teacher Unavailability (Corrected with Minute Comparison)
        if include_teacher_unavailability:
            for t in self.teachers:
                t_id = t[0]
                unavail = self.db_model.get_teacher_unavailability(t_id)
                
                for u in unavail:
                    # u format: (day, start, end, id, desc, span) - unpacking first 3 safely
                    u_day, u_start_str, u_end_str = u[0], u[1], u[2]
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
                                    for var in teacher_slot_vars[(t_id, s['id'])]:
                                        self.cp_model.Add(var == 0)

        # 6. Teacher Day Span Constraint (Sliding Window)
        print("Model: Applying Teacher Day Span Constraints...")
        # Define days and indices
        days_lookup = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma']
        num_days = 5
        
        for t in self.teachers:
            t_id = t[0]
            # Fetch preference
            span = self.db_model.get_teacher_span(t_id)
            
            if span > 0 and span < num_days:
                # 1. Create Active Day Variables
                day_active_vars = []
                for d_idx in range(num_days):
                    # Gather all slot vars for this day for this teacher
                    day_vars = []
                    for s in self.time_slots:
                        if s['day'] == days_lookup[d_idx]: 
                            if (t_id, s['id']) in teacher_slot_vars:
                                day_vars.extend(teacher_slot_vars[(t_id, s['id'])])
                    
                    d_act = self.cp_model.NewBoolVar(f't{t_id}_day{d_idx}_active')
                    day_active_vars.append(d_act)
                    
                    if day_vars:
                        # d_act is TRUE if ANY class is assigned on this day
                        self.cp_model.AddMaxEquality(d_act, day_vars)
                    else:
                        self.cp_model.Add(d_act == 0)

                # 2. Sliding Window Logic
                # Valid windows start at index 0 to (num_days - span)
                window_vars = []
                for start_day in range(num_days - span + 1):
                    w_var = self.cp_model.NewBoolVar(f't{t_id}_window{start_day}')
                    window_vars.append(w_var)
                
                # Must select exactly one window
                if window_vars:
                    self.cp_model.Add(sum(window_vars) == 1)
                    
                    # 3. Link Days to Windows
                    # day_active[d] <= Sum(windows covering d)
                    for d_idx in range(num_days):
                        covering_windows = []
                        for w_idx in range(len(window_vars)):
                            # Window starts at w_idx, covers [w_idx, w_idx + span - 1]
                            if w_idx <= d_idx < w_idx + span:
                                covering_windows.append(window_vars[w_idx])
                        
                        if covering_windows:
                            self.cp_model.Add(day_active_vars[d_idx] <= sum(covering_windows))
                        else:
                            # Day not covered by ANY valid window
                            self.cp_model.Add(day_active_vars[d_idx] == 0)

        # 6. OPTIONAL: Soft Constraint to spread T/U/L across different days
        # NOTE: Disabled by default for performance. Enable with caution on small datasets.
        ENABLE_DIFFERENT_DAYS_CONSTRAINT = False
        
        if ENABLE_DIFFERENT_DAYS_CONSTRAINT:
            print("DEBUG: Adding Soft Constraints (Different Days)...")
            course_parts = collections.defaultdict(list)
            
            # Populate course parts
            for c_idx, course in enumerate(self.courses):
                if 'parent_key' in course:
                    course_parts[course['parent_key']].append(c_idx)
            
            # Build penalty variables
            penalties = []
            for p_key, indices in course_parts.items():
                if len(indices) < 2:
                    continue
                    
                for i in range(len(indices)):
                    for j in range(i + 1, len(indices)):
                        idx1, idx2 = indices[i], indices[j]
                        for d_idx in range(5):
                            days_slots = [s for s in self.time_slots if s['id'] // SLOTS_PER_DAY == d_idx]
                            
                            # Gather vars for both courses on this day
                            vars1 = [self.vars[(idx1, r_id, s['id'])] 
                                    for s in days_slots 
                                    for r_id in [rm[0] for rm in self.rooms] 
                                    if (idx1, r_id, s['id']) in self.vars]
                            
                            vars2 = [self.vars[(idx2, r_id, s['id'])] 
                                    for s in days_slots 
                                    for r_id in [rm[0] for rm in self.rooms] 
                                    if (idx2, r_id, s['id']) in self.vars]
                            
                            if vars1 and vars2:
                                # Create indicators for presence on this day
                                b1 = self.cp_model.NewBoolVar(f'p{idx1}_d{d_idx}')
                                self.cp_model.Add(sum(vars1) > 0).OnlyEnforceIf(b1)
                                self.cp_model.Add(sum(vars1) == 0).OnlyEnforceIf(b1.Not())
                                
                                b2 = self.cp_model.NewBoolVar(f'p{idx2}_d{d_idx}')
                                self.cp_model.Add(sum(vars2) > 0).OnlyEnforceIf(b2)
                                self.cp_model.Add(sum(vars2) == 0).OnlyEnforceIf(b2.Not())
                                
                                # Conflict = both present on same day
                                conflict = self.cp_model.NewBoolVar(f'c_{idx1}_{idx2}_{d_idx}')
                                self.cp_model.AddBoolAnd([b1, b2]).OnlyEnforceIf(conflict)
                                self.cp_model.AddBoolOr([b1.Not(), b2.Not()]).OnlyEnforceIf(conflict.Not())
                                
                                penalties.append(conflict)
            
            if penalties:
                self.cp_model.Minimize(sum(penalties))
                print(f"DEBUG: Added {len(penalties)} penalty terms for different-day soft constraint")

    def add_soft_constraints_consecutive(self):
        """
        Soft Constraint: Encourage different session types (T/U/L) to be on DIFFERENT days.
        Simplified version using day-level granularity to avoid variable explosion.
        """
        # print("DEBUG: Adding Different-Day Soft Constraint for T/U/L...")
        # penalties = []
        # 
        # # Group courses by parent_key (name, instance)
        # course_groups = collections.defaultdict(list)
        # for c_idx, course in enumerate(self.courses):
        #     parent_key = course['parent_key']
        #     course_groups[parent_key].append((c_idx, course))
        pass
        


    def solve(self):
        """Solve with 2-Phase Strategy (Core then Elective) and Fallbacks."""
        self.load_data()
        
        # --- Pre-Solve Capacity Check ---
        total_demand = sum(c['duration'] for c in self.courses)
        total_capacity = len(self.rooms) * len(self.time_slots)
        
        print(f"\n[DIAGNOSTIC] Capacity Check:")
        print(f"  - Total Course Hours Needed: {total_demand}")
        print(f"  - Total School Capacity (Rooms x Slots): {total_capacity}")
        
        if total_demand > total_capacity:
            print(f"CRITICAL WARNING: Demand exceeds Capacity!")
            
        # Segregate for diagnostics and optional handling
        core_indices = []
        elective_indices = []
        
        for i, c in enumerate(self.courses):
            is_elective = c.get('is_elective', False)
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
        
        self.add_hard_constraints(include_teacher_unavailability=True)
        self.add_soft_constraints_consecutive()
        
        if not self._run_solver("PHASE1_CORE", timeout=180.0):
            print("FAILED to schedule Core courses. Aborting.")
            return False
        
        # Retrieve core assignments
        core_assignments = []
        for idx in core_indices:
            for r in self.rooms:
                r_id = r[0]
                if (idx, r_id) in self.room_vars and self.solver.Value(self.room_vars[(idx, r_id)]) == 1:
                    for s in self.time_slots:
                        s_id = s['id']
                        if (idx, r_id, s_id) in self.starts and self.solver.Value(self.starts[(idx, r_id, s_id)]) == 1:
                            core_assignments.append((idx, r_id, s_id))
                            break
        
        print(f"Phase 1 SUCCESS: {len(core_assignments)} core courses scheduled")
        
        # --- PHASE 2: ADD ELECTIVES (Fix Cores) ---
        print("\n=== PHASE 2: ELECTIVES (Cores Fixed) ===")
        
        self.cp_model = cp_model.CpModel()
        # Create variables for all courses, electives optional
        self.create_variables(ignore_fixed_rooms=False, optional_indices=elective_indices)
        
        # FIX core assignments from Phase 1
        for (c_idx, r_id, s_id) in core_assignments:
            if (c_idx, r_id, s_id) in self.starts:
                self.cp_model.Add(self.starts[(c_idx, r_id, s_id)] == 1)
        
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
                pools = list(data['electives'].keys())
                
                for i, pool_a in enumerate(pools):
                    for pool_b in pools[i+1:]:
                        vars_a = data['electives'][pool_a]
                        vars_b = data['electives'][pool_b]
                        
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
            self.cp_model.Maximize(objective)
        
        # Solve Phase 2
        if self._run_solver("PHASE2_ELECTIVES", timeout=300.0):
            return True
        else:
            print("WARNING: Phase 2 failed. Saving Phase 1 (cores only) as fallback.")
            self.save_manual_assignments(core_assignments)
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
        self.solver.parameters.log_search_progress = True
        self.solver.parameters.log_to_stdout = True
        self.solver.parameters.max_time_in_seconds = timeout
        
        try:
            status = self.solver.Solve(self.cp_model)
        except Exception as e:
            print(f"CRITICAL ERROR in Solve ({mode_name}): {e}")
            return False
            
        print(f"[{mode_name}] Solver Status: {self.solver.StatusName(status)}")
        
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
            
    def save_manual_assignments(self, assignments):
        """
        Manually save assignments to database when solver fails to produce a model solution
        assignments: List of (c_idx, r_id, s_id)
        """
        try:
            self.clear_previous_schedule()
            course_room_map = collections.defaultdict(dict)  # Fix: Use defaultdict(dict) like extract_schedule
            count = 0
            
            for c_idx, r_id, s_id in assignments:
                course = self.courses[c_idx]
                self._ensure_course_in_db(course)
                
                # Fix: Calculate duration for correct end time
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
                
                self.db_model.c.execute('''
                    INSERT INTO Ders_Programi (ders_adi, ders_instance, ogretmen_id, derslik_id, gun, baslangic, bitis, ders_tipi)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (course['name'], course['instance'], main_teacher_id, r_id, 
                      start_slot['day'], start_slot['start_str'], end_slot['end_str'], course['type']))
                
                # Fix: Store room assignments separately for T and L
                if course['type'] == 'Teori' or course['type'] == 'Uygulama':
                    course_room_map[course['parent_key']]['T'] = r_id
                elif course['type'] == 'Lab':
                    course_room_map[course['parent_key']]['L'] = r_id
                count += 1
            
            print(f"Fallback Schedule: {count} core items extracted.")
            
            # Fix: Update logic matching extract_schedule
            for key, val in course_room_map.items():
                ders_adi, ders_instance = key
                
                # Update theory room if exists
                if 'T' in val:
                     self.db_model.c.execute('''
                        UPDATE Dersler SET teori_odasi = ? WHERE ders_adi = ? AND ders_instance = ?
                    ''', (val['T'], ders_adi, ders_instance))
                
                # Update lab room if exists
                if 'L' in val:
                     self.db_model.c.execute('''
                        UPDATE Dersler SET lab_odasi = ? WHERE ders_adi = ? AND ders_instance = ?
                    ''', (val['L'], ders_adi, ders_instance))
            
            self.db_model.conn.commit()
            print("Fallback schedule saved successfully.")
            
        except Exception as e:
            print(f"Error saving fallback schedule: {e}")
            raise
    
    def extract_schedule(self):
        """Extract the schedule from the solved model and save to database"""
        course_room_map = collections.defaultdict(dict)  # {parent_key: {'T': room_id, 'L': room_id}}
        count = 0
        
        # Iterate over START variables only to prevent duplicate INSERTs
        for key, start_var in self.starts.items():
            c_idx, r_id, s_id = key
            
            if self.solver.Value(start_var) == 1:
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
                
                # Insert into DB with correct start and end times
                self.db_model.c.execute('''
                    INSERT INTO Ders_Programi (ders_adi, ders_instance, ogretmen_id, derslik_id, gun, baslangic, bitis, ders_tipi)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (course['name'], course['instance'], main_teacher_id, r_id, 
                      start_slot['day'], start_slot['start_str'], end_slot['end_str'], course['type']))
                
                # Store room assignments separately for T and L to prevent overwrite
                if course['type'] == 'Teori' or course['type'] == 'Uygulama':
                    course_room_map[course['parent_key']]['T'] = r_id
                elif course['type'] == 'Lab':
                    course_room_map[course['parent_key']]['L'] = r_id
                count += 1
        
        print(f"Schedule items extracted: {count}")
        
        # Update course room assignments in Dersler table
        # course_room_map: (name, inst) -> {'type': 'X', 'room': r_id} (Wait, this overwrites if mixed!)
        # Actually, we need to collect updates.
        # But wait, the loop above runs per item.
        # Let's fix course_room_map logic above first. 
        # Better: Execute updates directly inside the loop or accumulate properly.
        # Reverting to simplified update for now:
        try:
            for key, val in course_room_map.items():
                print(f"DEBUG: Processing key={key}, val={val}")  # Debug line
                ders_adi, ders_instance = key
                
                # Update theory room if exists
                if 'T' in val:
                     self.db_model.c.execute('''
                        UPDATE Dersler SET teori_odasi = ? WHERE ders_adi = ? AND ders_instance = ?
                    ''', (val['T'], ders_adi, ders_instance))
                
                # Update lab room if exists
                if 'L' in val:
                     self.db_model.c.execute('''
                        UPDATE Dersler SET lab_odasi = ? WHERE ders_adi = ? AND ders_instance = ?
                    ''', (val['L'], ders_adi, ders_instance))
                
                # Debug update
                # if self.db_model.c.rowcount == 0:
                #     print(f"WARNING: Failed to update room for {ders_adi} (inst {ders_instance})")
        except ValueError as e:
            print(f"ERROR: Unpacking failed - {e}")
            print(f"Problematic key: {key}")
            raise
            
        self.db_model.conn.commit()
