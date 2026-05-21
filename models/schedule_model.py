# -*- coding: utf-8 -*-
"""
Schedule Model - MVC Pattern
Handles all data operations and business logic

Sections:
    1.  INIT & CONNECTION
    2.  SCHEDULE CRUD
    3.  CALENDAR QUERIES
    4.  TEACHER-COURSE ASSIGNMENT
    5.  CURRICULUM MANAGEMENT
    6.  TEACHER & CLASSROOM LOOKUPS
    7.  FACULTY & DEPARTMENT
    8.  STUDENT & STUDENT-NUMBER HELPERS
    9.  CLASSROOM CRUD
    10. TEACHER AVAILABILITY & UNAVAILABILITY
    11. STUDENT QUERIES & GRADES
    12. MASTER VIEW & SNAPSHOTS
"""
import os
import sqlite3
import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from PyQt5.QtCore import QObject, pyqtSignal

# Import type-safe entities
from models.entities import ScheduleSlot, CourseInput, ScheduledCourse
from models.services.exceptions import ScheduleConflictError, CourseCreationError




class ScheduleModel(QObject):
    """
    Model class for schedule management
    Handles data operations and business logic
    """
    
    # Signals for view updates
    course_added = pyqtSignal(str)  # Emits course info when added
    course_removed = pyqtSignal(str)  # Emits course info when removed
    error_occurred = pyqtSignal(str)  # Emits error messages
    
    # ════════════════════════════════════════════════════════════════
    # INIT & CONNECTION
    # ════════════════════════════════════════════════════════════════

    def __init__(self, db_path: str = None):
        super().__init__()
        
        # Initialize database path
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if db_path is None:
            db_path = os.path.join(script_dir, "database", "okul_veritabani.db")
        self.db_path = db_path
        
        # Initialize Semester Lookup
        self.semester_lookup = {}
        self._build_semester_lookup()

        # Initialize Connection
        self.initialize_connection()
        
        # Initialize ID Seeding Service (Auto-seed faculties/departments)
        from models.services.faculty_and_department_id_seeder import IDSeedingService
        seeder = IDSeedingService(self.conn)
        seeder.seed()
        
        # Initialize repositories
        from models.repositories import TeacherRepository, ScheduleRepository, CourseRepository
        self.teacher_repo = TeacherRepository(self.c, self.conn)
        self.schedule_repo = ScheduleRepository(self.c, self.conn)
        self.course_repo = CourseRepository(self.c)  # Course repo doesn't need conn
        
        # Initialize service layer
        from models.services import ScheduleService
        self.schedule_service = ScheduleService(
            self.conn,
            self.teacher_repo,
            self.course_repo,
            self.schedule_repo
        )
        
        # Auto-patch Ders_Havuz_Iliskisi sinif_duzeyi if missing from old migration
        self._patch_pool_sinif_duzeyi()

    def _patch_pool_sinif_duzeyi(self):
        """Fix for migration 012 where sinif_duzeyi might be 0 for existing pool courses.
        Updates them to the correct value based on curriculum_data.
        
        Key fix: If a pool code (e.g. 'ZSD') appears in multiple years for the same
        department, sinif_duzeyi stays 0 (= universal/all years). The query uses
        'sinif_duzeyi = ? OR sinif_duzeyi = 0' so 0 means 'show to all years'.
        Single-year pools get their specific year value set.
        """
        try:
            import re
            from database import curriculum_data
            data = getattr(curriculum_data, 'DEPARTMENTS_DATA', {})
            
            # Map (bolum_adi, havuz_kodu) -> SET of years it appears in
            pool_years: dict = {}  # (dept_name, pool_code) -> set of int years
            for dept_name, details in data.items():
                curr = details.get('curriculum', {})
                for sem_key, courses in curr.items():
                    year_match = re.search(r'(\d+)\.\s*Y[ıi]l', sem_key)
                    if not year_match: continue
                    sinif_duzeyi = int(year_match.group(1))
                    
                    if isinstance(courses, list):
                        for course in courses:
                            if isinstance(course, list) and len(course) >= 2:
                                key = (dept_name, course[0])
                                pool_years.setdefault(key, set()).add(sinif_duzeyi)

            # Resolve: single year -> use it; multiple years -> 0 (universal, skip update)
            # Build map of ONLY single-year pools that need updating (target: nonzero)
            single_year_map = {}  # (dept_name, pool_code) -> specific_year
            for key, years in pool_years.items():
                if len(years) == 1:
                    single_year_map[key] = min(years)
            # Multi-year pools intentionally stay at 0, no update needed.

            # Get bolum_id dictionary
            self.c.execute("SELECT bolum_id, bolum_adi FROM Bolumler")
            bolum_dict = {row[1]: row[0] for row in self.c.fetchall()}

            # Count only the single-year pool entries that still have sinif_duzeyi = 0
            # (multi-year = 0 is intentional and should not trigger the patch)
            count = 0
            for (dept_name, pool_code), sinif in single_year_map.items():
                if dept_name in bolum_dict:
                    bolum_id = bolum_dict[dept_name]
                    self.c.execute(
                        "SELECT COUNT(*) FROM Ders_Havuz_Iliskisi WHERE bolum_id = ? AND havuz_kodu = ? AND sinif_duzeyi = 0",
                        (bolum_id, pool_code)
                    )
                    count += self.c.fetchone()[0]

            if count == 0:
                return

            print(f"[DB Patch] Found {count} pool courses with missing sinif_duzeyi. Patching...")

            # Apply updates only for single-year pools
            for (dept_name, pool_code), sinif in single_year_map.items():
                if dept_name in bolum_dict:
                    bolum_id = bolum_dict[dept_name]
                    self.c.execute('''
                        UPDATE Ders_Havuz_Iliskisi 
                        SET sinif_duzeyi = ? 
                        WHERE bolum_id = ? AND havuz_kodu = ? AND sinif_duzeyi = 0
                    ''', (sinif, bolum_id, pool_code))
            
            self.conn.commit()
            print("[DB Patch] Successfully updated Ders_Havuz_Iliskisi.")
        except Exception as e:
            print(f"[DB Patch] Error patching pool courses: {e}")

    def _build_semester_lookup(self):
        """Builds a lookup map for course semesters from curriculum_data.py"""
        try:
            self.semester_lookup = {}
            self.semester_lookup_by_dept = {} # NEW: Keep track per department
            from database import curriculum_data
            data = getattr(curriculum_data, 'DEPARTMENTS_DATA', {})
            
            for dept, details in data.items():
                curr = details.get('curriculum', {})
                for sem_key, courses in curr.items():
                    # sem_key format is like "1. Dönem / 1. Yıl Güz Dönemi" or "1"
                    try:
                        # Extract the first number from the string
                        match = re.search(r'\d+', sem_key)
                        if match:
                            sem_num = int(match.group())
                            is_odd = (sem_num % 2 != 0)
                            semester = "Güz" if is_odd else "Bahar"
                            
                            for course in courses:
                                # course: [Code, Name, T, U, L, AKTS]
                                if len(course) >= 2:
                                    code = str(course[0]).strip()
                                    name = str(course[1]).strip()
                                    
                                    if code:
                                        if code not in self.semester_lookup:
                                            self.semester_lookup[code] = set()
                                        if (dept, code) not in self.semester_lookup_by_dept:
                                            self.semester_lookup_by_dept[(dept, code)] = set()
                                            
                                        self.semester_lookup[code].add(semester)
                                        self.semester_lookup_by_dept[(dept, code)].add(semester)
                                        
                                    if name:
                                        if name not in self.semester_lookup:
                                            self.semester_lookup[name] = set()
                                        if (dept, name) not in self.semester_lookup_by_dept:
                                            self.semester_lookup_by_dept[(dept, name)] = set()
                                            
                                        self.semester_lookup[name].add(semester)
                                        self.semester_lookup_by_dept[(dept, name)].add(semester)
                                        
                                        # If this code is a pool reference, expand all pool sub-courses
                                        pools = details.get('pools', {})
                                        if code in pools:
                                            for pool_course in pools[code]:
                                                if len(pool_course) >= 2:
                                                    pool_code = str(pool_course[0]).strip()
                                                    pool_name = str(pool_course[1]).strip()
                                                    
                                                    if pool_code:
                                                        if pool_code not in self.semester_lookup:
                                                            self.semester_lookup[pool_code] = set()
                                                        if (dept, pool_code) not in self.semester_lookup_by_dept:
                                                            self.semester_lookup_by_dept[(dept, pool_code)] = set()
                                                            
                                                        self.semester_lookup[pool_code].add(semester)
                                                        self.semester_lookup_by_dept[(dept, pool_code)].add(semester)
                                                        
                                                    if pool_name:
                                                        if pool_name not in self.semester_lookup:
                                                            self.semester_lookup[pool_name] = set()
                                                        if (dept, pool_name) not in self.semester_lookup_by_dept:
                                                            self.semester_lookup_by_dept[(dept, pool_name)] = set()
                                                            
                                                        self.semester_lookup[pool_name].add(semester)
                                                        self.semester_lookup_by_dept[(dept, pool_name)].add(semester)
                    except Exception as parse_e:
                        print(f"Warning: Failed to parse semester key '{sem_key}': {parse_e}")
                        continue
        except Exception as e:
            print(f"Warning: Could not build semester lookup: {e}")
            
    def initialize_connection(self):
        """Initializes the database connection and runs migrations."""
        try:
            # Enable cross-thread usage for the solver background thread
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.c = self.conn.cursor()
            
            # Run migrations
            from models.repositories.migration import DatabaseMigration
            migration = DatabaseMigration(self.conn)
            migration.run_all()
            
        except Exception as e:
            print(f"Database initialization error: {e}")
            raise

    # ════════════════════════════════════════════════════════════════
    # SCHEDULE CRUD
    # ════════════════════════════════════════════════════════════════

    def add_course(self, course_data: CourseInput) -> bool:
        """
        Add a new course to the schedule.
        Delegates to service layer for business logic.
        
        Args:
            course_data: Validated course input
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Delegate to service layer - returns entity
            scheduled_course = self.schedule_service.add_course(course_data)
            
            # Format entity for UI display
            from models.formatters import ScheduleFormatter
            course_info = ScheduleFormatter.from_scheduled_course(scheduled_course)
            
            # Emit signal with formatted string
            self.course_added.emit(course_info)
            return True
            
        except ScheduleConflictError as e:
            self.error_occurred.emit(str(e))
            return False
        except (CourseCreationError, Exception) as e:
            self.error_occurred.emit(f"Failed to add course: {e}")
            return False
    
    def remove_course_by_id(self, program_id: int) -> bool:
        """
        Remove a course by its database ID.
        Uses transaction for safety.
        
        Args:
            program_id: Database ID from Ders_Programi table
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self.conn:  # Transaction
                success = self.schedule_repo.remove_by_id(program_id)
                # Commits automatically if successful
            return success
        except Exception as e:
            error_msg = f"Ders silinirken hata: {str(e)}"
            self.error_occurred.emit(error_msg)
            print(f"[ERROR] {error_msg}")
            return False
    
    def get_all_schedule_items(self, semester_filter: Optional[str] = None) -> List[Dict]:
        """
        Get all scheduled items with structured data for Table View.
        semester_filter: 'Güz' (Odd semesters), 'Bahar' (Even semesters), 'Yaz' (Empty)
        Returns:
            List[Dict]: List of course data objects with fields:
            id (list of ints for merged), pool, code, name, teacher, day, start, end, classes,
            metadata: faculty_ids, dept_ids, years (lists of ints)
        """
        try:
            query = '''
                SELECT dp.program_id, dp.ders_adi, COALESCE(o.ad || ' ' || o.soyad, 'Atanmamış'), dp.gun, dp.baslangic, dp.bitis, d.ders_kodu,
                       GROUP_CONCAT(DISTINCT b.bolum_adi || ' ' || od.sinif_duzeyi || '. Sınıf'),
                       GROUP_CONCAT(DISTINCT dhi.havuz_kodu),
                       GROUP_CONCAT(DISTINCT b.fakulte_num),
                       GROUP_CONCAT(DISTINCT od.bolum_num),
                       GROUP_CONCAT(DISTINCT od.sinif_duzeyi)
                FROM Ders_Programi dp
                LEFT JOIN Ogretmenler o ON dp.ogretmen_id = o.ogretmen_num
                LEFT JOIN Dersler d ON dp.ders_adi = d.ders_adi AND dp.ders_instance = d.ders_instance
                LEFT JOIN Ders_Sinif_Iliskisi dsi ON d.ders_adi = dsi.ders_adi AND d.ders_instance = dsi.ders_instance
                LEFT JOIN Ogrenci_Donemleri od ON dsi.donem_sinif_num = od.donem_sinif_num
                LEFT JOIN Bolumler b ON od.bolum_num = b.bolum_id
                LEFT JOIN Ders_Havuz_Iliskisi dhi ON d.ders_adi = dhi.ders_adi AND d.ders_instance = dhi.ders_instance
                GROUP BY dp.program_id, dp.ders_adi, o.ad, o.soyad, dp.gun, dp.baslangic, dp.bitis, d.ders_kodu, d.ders_instance
            '''
            self.c.execute(query)
            rows = self.c.fetchall()
            
            items = []
            for pid, ders, hoca, gun, start, end, kodu, siniflar, havuzlar, fac_ids, dept_ids, years in rows:
                
                # Format pool codes
                pool_str = ""
                if havuzlar:
                     pool_codes = sorted(set(p.strip() for p in havuzlar.split(',') if p.strip()))
                     pool_str = ", ".join(pool_codes)
                
                # Parse metadata
                f_ids = [int(x) for x in fac_ids.split(',')] if fac_ids else []
                d_ids = [int(x) for x in dept_ids.split(',')] if dept_ids else []
                y_ids = [int(x) for x in years.split(',')] if years else []

                # --- 1. Filter by Semester (Inference) ---
                if semester_filter:
                    # Yaz: Strictly empty for now
                    if semester_filter == "Yaz":
                        continue

                    # Determine Course Semester (Priority: Lookup -> Name-Based)
                    is_fall = False
                    is_spring = False
                    
                    code_str = str(kodu).strip()
                    
                    # 1. Lookup from Curriculum Data (Source of Truth)
                    if code_str and code_str in self.semester_lookup:
                        sem_set = self.semester_lookup[code_str]
                        if "Güz" in sem_set: is_fall = True
                        if "Bahar" in sem_set: is_spring = True
                    
                    # 2. Fallback: Default to BOTH (Safe availability)
                    # User requested removing "I/II" logic.
                    if not is_fall and not is_spring:
                        is_fall = True
                        is_spring = True

                    if semester_filter == "Güz":
                        if not is_fall: continue
                    elif semester_filter == "Bahar":
                        if not is_spring: continue

                items.append({
                    'id': pid,
                    'pool': pool_str,
                    'code': kodu if kodu else "",
                    'name': ders,
                    'teacher': hoca,
                    'day': gun,
                    'start': start,
                    'end': end,
                    'classes': siniflar if siniflar else "",
                    'faculty_ids': f_ids,
                    'dept_ids': d_ids,
                    'years': y_ids
                })
            return items
        except Exception as e:
            self.error_occurred.emit(f"Dersler yüklenirken hata: {str(e)}")
            return []

    
    # ════════════════════════════════════════════════════════════════
    # CALENDAR QUERIES (used by CalendarScheduleBuilder)
    # ════════════════════════════════════════════════════════════════

    def get_teachers(self):
        """
        Get all unique teacher names
        
        Returns:
            List[str]: List of teacher names
        """
        try:
            self.c.execute("SELECT ad || ' ' || soyad FROM Ogretmenler ORDER BY ad, soyad")
            return [row[0] for row in self.c.fetchall()]
        except Exception as e:
            self.error_occurred.emit(f"Error fetching teachers: {str(e)}")
            return []


    


    def get_schedule_by_teacher(self, teacher_id: int) -> List[tuple]:
        """Get schedule for a specific teacher"""
        try:
            query = '''
                SELECT dp.gun, dp.baslangic, dp.bitis, dp.ders_adi, 
                       (SELECT derslik_adi FROM Derslikler WHERE derslik_num = dp.derslik_id) as oda,
                       COALESCE(d.ders_kodu, 'CUSTOM') as ders_kodu, dp.ders_tipi
                FROM Ders_Programi dp
                LEFT JOIN Dersler d ON dp.ders_adi = d.ders_adi AND dp.ders_instance = d.ders_instance
                WHERE dp.ogretmen_id = ?
            '''
            self.c.execute(query, (teacher_id,))
            return self.c.fetchall()
        except Exception as e:
            print(f"Error fetching teacher schedule: {e}")
            return []

    # ════════════════════════════════════════════════════════════════
    # TEACHER-COURSE ASSIGNMENT
    # ════════════════════════════════════════════════════════════════

    def assign_teacher_to_course(self, teacher_id: int, course_name: str, instance: int = 1) -> bool:
        """
        Assign a teacher to a specific course instance (section).
        Persists to Ders_Ogretmen_Iliskisi.
        """
        try:
            with self.conn:
                self.c.execute("""
                    INSERT OR REPLACE INTO Ders_Ogretmen_Iliskisi (ders_adi, ders_instance, ogretmen_id)
                    VALUES (?, ?, ?)
                """, (course_name, instance, teacher_id))
            return True
        except Exception as e:
            self.error_occurred.emit(f"Hoca ataması başarısız: {str(e)}")
            return False

    def get_courses_assigned_to_teacher(self, teacher_id: int) -> List[tuple]:
        """
        Get courses assigned to a teacher in the CURRICULUM (not schedule).
        Returns: List of (Course Name, Instance) tuples.
        """
        try:
            self.c.execute("""
                SELECT ders_adi, ders_instance
                FROM Ders_Ogretmen_Iliskisi
                WHERE ogretmen_id = ?
                ORDER BY ders_adi, ders_instance
            """, (teacher_id,))
            return self.c.fetchall()
        except Exception as e:
            print(f"Error fetching assigned courses: {e}")
            return []

    def get_all_courses_assigned_to_teachers(self) -> List[tuple]:
        """
        Get all courses assigned to any teacher
        Returns: List of (ders_adi, ders_instance, ogretmen_adi_soyadi, ogretmen_id)
        """
        try:
            query = """
                SELECT i.ders_adi, i.ders_instance, (o.ad || ' ' || o.soyad) as hoca, o.ogretmen_num
                FROM Ders_Ogretmen_Iliskisi i
                JOIN Ogretmenler o ON i.ogretmen_id = o.ogretmen_num
                ORDER BY i.ders_adi, i.ders_instance
            """
            self.c.execute(query)
            return self.c.fetchall()
        except Exception as e:
            print(f"Error fetching all assigned: {e}")
            return []

    def get_unassigned_courses(self) -> List[tuple]:
        """
        Get all course instances that do NOT have any teacher assigned in Ders_Ogretmen_Iliskisi.
        Returns: List of (ders_adi, ders_instance)
        """
        try:
            query = """
                SELECT DISTINCT d.ders_adi, d.ders_instance
                FROM Dersler d
                WHERE NOT EXISTS (
                    SELECT 1 FROM Ders_Ogretmen_Iliskisi doi
                    WHERE doi.ders_adi = d.ders_adi AND doi.ders_instance = d.ders_instance
                )
                ORDER BY d.ders_adi, d.ders_instance
            """
            self.c.execute(query)
            return self.c.fetchall()
        except Exception as e:
            print(f"Error fetching unassigned courses: {e}")
            return []

    # ════════════════════════════════════════════════════════════════
    # CURRICULUM MANAGEMENT
    # ════════════════════════════════════════════════════════════════

    def delete_curriculum_course(self, course_name: str) -> bool:
        """
        Delete a course from the curriculum + all related tables.
        """
        try:
            with self.conn:
                # 1. Delete from Curriculum (Dersler)
                self.c.execute("DELETE FROM Dersler WHERE ders_adi = ?", (course_name,))
                
                # 2. Delete Relations
                self.c.execute("DELETE FROM Ders_Sinif_Iliskisi WHERE ders_adi = ?", (course_name,))
                self.c.execute("DELETE FROM Ders_Havuz_Iliskisi WHERE ders_adi = ?", (course_name,))
                
                # 3. Delete from Schedule (Cascade logically)
                self.c.execute("DELETE FROM Ders_Programi WHERE ders_adi = ?", (course_name,))
                self.c.execute("DELETE FROM Ders_Ogretmen_Iliskisi WHERE ders_adi = ?", (course_name,))
                
            self.course_removed.emit(course_name)
            return True
        except Exception as e:
            print(f"Error deleting curriculum course: {e}")
            self.error_occurred.emit(f"Ders silinirken hata: {e}")
            return False


    def add_curriculum_course_as_template(self, data: Dict) -> bool:
        """
        Add a course template to the curriculum (Dersler + Ders_Sinif_Iliskisi).
        This is for the 'Template' button.
        
        Args:
            data: {
                'code': str, 'name': str, 'dept_id': int, 'year': int,
                't': int, 'u': int, 'l': int, 'akts': int,
                'type': str (Core/Elective) - currently ignored, logic is implicit
            }
        """
        try:
            # 1. Determine Instance ID (Auto-increment logic)
            # Find max instance for this course name to separate sections if name exists
            self.c.execute("SELECT MAX(ders_instance) FROM Dersler WHERE ders_adi = ?", (data['name'],))
            row = self.c.fetchone()
            instance = 1
            if row and row[0]:
                instance = row[0] + 1
            
            # 2. Add to Dersler
            with self.conn:
                self.c.execute("""
                    INSERT INTO Dersler (ders_kodu, ders_instance, ders_adi, teori_saati, uygulama_saati, lab_saati, akts)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (data['code'], instance, data['name'], data['t'], data['u'], data['l'], data['akts']))
                
                is_pool = data.get('is_pool', False)
                
                if is_pool:
                    # 3a. Add to Ders_Havuz_Iliskisi (Pool Course)
                    # Schema: (ders_instance, ders_adi, bolum_num, havuz_kodu)
                    pool_code = data.get('pool_code', 'GENEL')
                    
                    # Resolve bolum_num from dept_id
                    self.c.execute("SELECT bolum_num FROM Bolumler WHERE bolum_id = ?", (data['dept_id'],))
                    row_bn = self.c.fetchone()
                    if not row_bn:
                        raise ValueError(f"Bölüm bulunamadı (ID: {data['dept_id']})")
                    bolum_num = row_bn[0]
                    
                    self.c.execute("""
                        INSERT INTO Ders_Havuz_Iliskisi (ders_instance, ders_adi, bolum_id, havuz_kodu)
                        VALUES (?, ?, ?, ?)
                    """, (instance, data['name'], bolum_num, pool_code))
                    
                    self.course_added.emit(f"[Havuz] {data['name']} (Şube {instance}, Havuz: {pool_code}) eklendi.")
                    
                else:
                    # 3b. Add to Ders_Sinif_Iliskisi (Class Course)
                    # Resolve donem_sinif_num from dept_id + year
                    
                    # First get department info to find donem_sinif_num
                    self.c.execute("""
                        SELECT donem_sinif_num FROM Ogrenci_Donemleri 
                        WHERE bolum_num = ? AND sinif_duzeyi = ?
                    """, (data['dept_id'], data['year']))
                    
                    rows = self.c.fetchall()
                    if not rows:
                         raise ValueError(f"Bu bölüm/sınıf için dönem kaydı bulunamadı (Bölüm: {data['dept_id']}, Sınıf: {data['year']})")
                    
                    # Add for ALL matching periods
                    for r in rows:
                        ds_num = r[0]
                        self.c.execute("""
                            INSERT INTO Ders_Sinif_Iliskisi (ders_adi, ders_instance, donem_sinif_num)
                            VALUES (?, ?, ?)
                        """, (data['name'], instance, ds_num))
                        
                    self.course_added.emit(f"[Template] {data['name']} (Şube {instance}) eklendi.")

            return True
            
        except Exception as e:
            self.error_occurred.emit(f"Şablon ders eklenirken hata: {str(e)}")
            return False


    def get_schedule_by_classroom(self, classroom_id: int) -> List[tuple]:
        """Get schedule for a specific classroom"""
        try:
            query = '''
                SELECT dp.gun, dp.baslangic, dp.bitis, dp.ders_adi,
                       (SELECT ad || ' ' || soyad FROM Ogretmenler WHERE ogretmen_num = dp.ogretmen_id) as hoca,
                       GROUP_CONCAT(DISTINCT COALESCE(d.ders_kodu, 'CUSTOM')), dp.ders_tipi
                FROM Ders_Programi dp
                LEFT JOIN Dersler d ON dp.ders_adi = d.ders_adi AND dp.ders_instance = d.ders_instance
                WHERE dp.derslik_id = ?
                GROUP BY dp.gun, dp.baslangic, dp.bitis, dp.ders_adi, dp.ogretmen_id, dp.ders_tipi
            '''
#SQL kuralı: GROUP BY kullanırken, SELECT'teki aggregate olmayan (örn: SUM, COUNT, GROUP_CONCAT gibi fonksiyon kullanmayan) tüm sütunlar GROUP BY'da da olmalı
            self.c.execute(query, (classroom_id,))
            return self.c.fetchall()
        except Exception as e:
            print(f"Error fetching classroom schedule: {e}")
            return []

    def get_schedule_by_student_group(self, bolum_id: int, sinif_duzeyi: int) -> List[tuple]:
        """Get schedule for a specific student group (Department + Year)"""
        try:
            query = '''
                SELECT dp.gun, dp.baslangic, dp.bitis, dp.ders_adi,
                       (SELECT ad || ' ' || soyad FROM Ogretmenler WHERE ogretmen_num = dp.ogretmen_id) as hoca,
                       (SELECT derslik_adi FROM Derslikler WHERE derslik_num = dp.derslik_id) as oda,
                       COALESCE(d.ders_kodu, 'CUSTOM') as ders_kodu, dp.ders_tipi,
                       NULL as havuz_kodu,
                       0 as is_pool,
                       dp.ders_instance
                FROM Ders_Programi dp
                LEFT JOIN Dersler d ON dp.ders_adi = d.ders_adi AND dp.ders_instance = d.ders_instance
                JOIN Ders_Sinif_Iliskisi dsi ON d.ders_adi = dsi.ders_adi AND d.ders_instance = dsi.ders_instance
                JOIN Ogrenci_Donemleri od ON dsi.donem_sinif_num = od.donem_sinif_num
                WHERE od.bolum_num = ? AND od.sinif_duzeyi = ?
                
                UNION ALL
                
                SELECT dp.gun, dp.baslangic, dp.bitis, dp.ders_adi,
                       (SELECT ad || ' ' || soyad FROM Ogretmenler WHERE ogretmen_num = dp.ogretmen_id) as hoca,
                       (SELECT derslik_adi FROM Derslikler WHERE derslik_num = dp.derslik_id) as oda,
                       COALESCE(d.ders_kodu, 'CUSTOM') as ders_kodu, dp.ders_tipi,
                       (SELECT GROUP_CONCAT(dhi2.havuz_kodu) FROM Ders_Havuz_Iliskisi dhi2 
                        WHERE dhi2.ders_adi = dp.ders_adi AND dhi2.bolum_id = ? 
                        AND (dhi2.sinif_duzeyi = ? OR dhi2.sinif_duzeyi = 0)) as havuz_kodu,
                       1 as is_pool,
                       dp.ders_instance
                FROM Ders_Programi dp
                LEFT JOIN Dersler d ON dp.ders_adi = d.ders_adi AND dp.ders_instance = d.ders_instance
                WHERE EXISTS (
                    SELECT 1 FROM Ders_Havuz_Iliskisi dhi
                    WHERE dhi.ders_adi = dp.ders_adi
                    AND dhi.bolum_id = ?
                    AND (dhi.sinif_duzeyi = ? OR dhi.sinif_duzeyi = 0)
                )
            '''
            self.c.execute(query, (bolum_id, sinif_duzeyi, bolum_id, sinif_duzeyi, bolum_id, sinif_duzeyi))
            return self.c.fetchall()
        except Exception as e:
            print(f"Error fetching student schedule: {e}")
            return []

    def get_all_curriculum_details(self, dept_id: Optional[int] = None, year: Optional[int] = None, faculty_id: Optional[int] = None, semester_filter: Optional[str] = None) -> List[tuple]:
        """
        Fetch detailed curriculum list, merging Class-Specific and Pool courses.
        Returns list of tuples:
        (Code, Name, T, U, L, AKTS, Type, Dept/Pool Info, SortKey_Year, IsPool, PoolCode)
        
        Note: semester_filter is currently ignored due to database limitations (no semester column).
        """
        results = []
        try:
            # 1. Fetch Class-Specific Courses
            query_class = """
                SELECT DISTINCT 
                    d.ders_kodu, d.ders_adi, d.teori_saati, d.uygulama_saati, d.lab_saati, d.akts,
                    'Bölüm Dersi' as tip,
                    b.bolum_adi || ' - ' || od.sinif_duzeyi || '. Sınıf' as detay,
                    od.sinif_duzeyi as sort_year,
                    0 as is_pool,
                    NULL as pool_code
                FROM Dersler d
                JOIN Ders_Sinif_Iliskisi dsi ON d.ders_adi = dsi.ders_adi AND d.ders_instance = dsi.ders_instance
                JOIN Ogrenci_Donemleri od ON dsi.donem_sinif_num = od.donem_sinif_num
                JOIN Bolumler b ON od.bolum_num = b.bolum_id
                WHERE 1=1
            """
            params_class = []
            if dept_id:
                 query_class += " AND od.bolum_num = ?"
                 params_class.append(dept_id)
            if faculty_id:
                 query_class += " AND b.fakulte_num = ?"
                 params_class.append(faculty_id)
            if year:
                 query_class += " AND od.sinif_duzeyi = ?"
                 params_class.append(year)
                 
            self.c.execute(query_class, tuple(params_class))
            results.extend(self.c.fetchall())
            
            # 2. Fetch Pool Courses
            query_pool = """
                SELECT DISTINCT
                    d.ders_kodu, d.ders_adi, d.teori_saati, d.uygulama_saati, d.lab_saati, d.akts,
                    'Havuz Dersi' as tip,
                    'Havuz: ' || dhi.havuz_kodu,
                    99 as sort_year,
                    1 as is_pool,
                    dhi.havuz_kodu as pool_code
                FROM Dersler d
                JOIN Ders_Havuz_Iliskisi dhi ON d.ders_adi = dhi.ders_adi AND d.ders_instance = dhi.ders_instance
                LEFT JOIN Bolumler b ON dhi.bolum_id = b.bolum_id
                WHERE 1=1
            """
            params_pool = []
            if dept_id:
                query_pool += " AND b.bolum_id = ?"
                params_pool.append(dept_id)
            if faculty_id:
                query_pool += " AND b.fakulte_num = ?"
                params_pool.append(faculty_id)
            
            if year is None or year == 99: # 99 for Havuz filter
                 self.c.execute(query_pool, tuple(params_pool))
                 results.extend(self.c.fetchall())
                 
            # Sort by: 
            # 1. Year (ASC)
            # 2. IsPool (ASC)
            # 3. Pool Code (ASC) - Ensure string & stripped
            # 4. Name (ASC)
            results.sort(key=lambda x: (
                x[8], 
                x[9], 
                str(x[10]).strip().upper() if x[10] else "ZZZZZ", 
                x[1]
            ))
            # --- Semester Filtering & Column Injection (Always Run) ---
            # Always run to ensure the "Semester" column is added at index 6
            filtered_results = []
            for row in results:
                # Row: 0:Code, 1:Name, ... 8:Year, 9:IsPool
                
                if semester_filter == "Yaz":
                    # We don't support Yaz yet in DB, just skip or show empty?
                    # For now, let's just filtering logic handle it.
                    pass

                code = row[0] # Fix: Define code
                name = row[1]
                code_str = str(code).strip()
                detay = row[7] # Contains dept info e.g. "Makine Müh - 1. Sınıf"
                
                sem_str = "Belirsiz" # Default if unknown
                
                # Extract dept from detay string if it's a department course
                bolum_adi = None
                if detay and " - " in detay and not str(detay).startswith("Havuz:"):
                    bolum_adi = str(detay).split(" - ")[0].strip()
                    
                # 1. Lookup from Curriculum Data (Strict Source of Truth)
                sem_set = None
                
                # Prioritize department-specific timing over global timing
                if bolum_adi and hasattr(self, 'semester_lookup_by_dept') and (bolum_adi, code_str) in self.semester_lookup_by_dept:
                    sem_set = self.semester_lookup_by_dept[(bolum_adi, code_str)]
                
                # Fallback to global if unmapped or pool
                if not sem_set and hasattr(self, 'semester_lookup') and code_str in self.semester_lookup:
                    sem_set = self.semester_lookup[code_str]
                    
                if sem_set:
                    if "Güz" in sem_set and "Bahar" in sem_set:
                        sem_str = "Güz / Bahar"
                    elif "Güz" in sem_set:
                        sem_str = "Güz"
                    elif "Bahar" in sem_set:
                        sem_str = "Bahar"
                
                # Apply Filter for View
                show_row = False
                if semester_filter == "Güz":
                    if "Güz" in sem_str or sem_str == "Belirsiz": show_row = True
                elif semester_filter == "Bahar":
                    if "Bahar" in sem_str or sem_str == "Belirsiz": show_row = True
                elif semester_filter == "Hepsi" or not semester_filter:
                     show_row = True
                     
                if show_row:
                    # Construct new row tuple with Semester Column at index 6
                    # Original: Code, Name, T, U, L, AKTS, Type, Detail, SortKey, IsPool, PoolCode
                    # New:      Code, Name, T, U, L, AKTS, Sem,  Type, Detail, SortKey, IsPool, PoolCode
                    
                    new_row = list(row)
                    new_row.insert(6, sem_str)
                    filtered_results.append(tuple(new_row))
            
            results = filtered_results

            return results
            
        except Exception as e:
            print(f"Error fetching curriculum details: {e}")
            return []

    def get_curriculum_courses(self) -> List[str]:
        """Get unique course names from curriculum"""
        try:
            self.c.execute("SELECT DISTINCT ders_adi FROM Dersler ORDER BY ders_adi")
            return [r[0] for r in self.c.fetchall()]
        except Exception as e:
            print(f"Error fetching curriculum courses: {e}")
            return []


    # ════════════════════════════════════════════════════════════════
    # TEACHER & CLASSROOM LOOKUPS
    # ════════════════════════════════════════════════════════════════

    def get_all_teachers_with_ids(self) -> List[Tuple[int, str, Optional[str]]]:
        """Get all teachers with their IDs and room preferences"""
        try:
            # Check if column exists first to be safe (migration should have added it)
            self.c.execute("SELECT ogretmen_num, ad || ' ' || soyad, room_request FROM Ogretmenler ORDER BY ad")
            return self.c.fetchall()
        except Exception as e:
            print(f"Error fetching teachers: {e}")
            return []
            
    def get_all_classrooms_with_ids(self) -> List[Tuple[int, str, int]]:
        """
        Get all classrooms with their IDs and Floor info sorted naturally.
        Returns: List of (id, name, floor)
        """
        try:
            # Try to fetch floor, if column doesn't exist yet (before migration runs), handle gracefully
            try:
                self.c.execute("SELECT derslik_num, derslik_adi, floor FROM Derslikler WHERE silindi = 0")
            except Exception:
                # Fallback
                self.c.execute("SELECT derslik_num, derslik_adi, 0 as floor FROM Derslikler WHERE silindi = 0")
                
            rows = self.c.fetchall()
            
            # Natural sort helper - sorts "Derslik 2" before "Derslik 10"
            def natural_keys(classroom_tuple):
                classroom_name = classroom_tuple[1]  # Get name from (id, name, floor) tuple
                parts = re.split(r'(\d+)', classroom_name)  # Split into text and numbers
                
                # Convert number strings to integers, keep text as lowercase
                converted_parts = []
                for part in parts:
                    if part.isdigit():
                        converted_parts.append(int(part))  # "10" -> 10
                    else:
                        converted_parts.append(part.lower())  # "Derslik " -> "derslik "
                
                return converted_parts
                
            return sorted(rows, key=natural_keys)
        except Exception as e:
            print(f"Error fetching classrooms: {e}")
            return []

    # ════════════════════════════════════════════════════════════════
    # FACULTY & DEPARTMENT
    # ════════════════════════════════════════════════════════════════

    def get_departments_by_faculty(self, faculty_id: int) -> List[Tuple[int, str]]:
        """Get departments for a faculty"""
        try:
            self.c.execute("SELECT bolum_id, bolum_adi FROM Bolumler WHERE fakulte_num = ? ORDER BY bolum_adi", (faculty_id,))
            return self.c.fetchall()
        except Exception as e:
            print(f"Error fetching departments: {e}")
            return []  # Return True to be safe

    def get_courses_by_faculty(self, faculty_id: int, year: str = None, day: str = None) -> List[str]:
        """Fetch all scheduled courses for a faculty from Ders_Programi""" 
        try:
            from models.services.query_builder import ScheduleQueryBuilder, ScheduleQueryFilter
            
            # Build query using DRY builder
            filters = ScheduleQueryFilter(
                faculty_id=faculty_id,
                year=int(year) if year and str(year).isdigit() else None,
                day=day
            )
            sql, params = ScheduleQueryBuilder().build(filters)
            
            self.c.execute(sql, params)
            rows = self.c.fetchall()
            
            # Format: [CODE] Name - Teacher (Day Time) [Classes]
            result = []
            for r in rows:
                ders_adi, codes, hoca, gun, baslangic, bitis, siniflar = r
                hoca = hoca if hoca else "Belirsiz"
                saat = f"{baslangic}-{bitis}"
                classes_str = f" [{siniflar}]" if siniflar else ""
                result.append(f"[{codes}] {ders_adi} - {hoca} ({gun} {saat}){classes_str}")
            return result
        except Exception as e:
            print(f"Error fetching faculty courses: {e}")
            return []

    def get_courses_by_department(self, dept_id: int, year: str = None, day: str = None) -> List[str]:
        """Fetch scheduled courses for a specific department from Ders_Programi"""
        try:
            from models.services.query_builder import ScheduleQueryBuilder, ScheduleQueryFilter
            
            # Build query using DRY builder
            filters = ScheduleQueryFilter(
                department_id=dept_id,
                year=int(year) if year and str(year).isdigit() else None,
                day=day
            )
            sql, params = ScheduleQueryBuilder().build(filters)
            
            self.c.execute(sql, params)
            rows = self.c.fetchall()
            
            # Format: [CODE] Name - Teacher (Day Time) [Classes]
            result = []
            for r in rows:
                ders_adi, codes, hoca, gun, baslangic, bitis, siniflar = r
                hoca = hoca if hoca else "Belirsiz"
                saat = f"{baslangic}-{bitis}"
                classes_str = f" [{siniflar}]" if siniflar else ""
                result.append(f"[{codes}] {ders_adi} - {hoca} ({gun} {saat}){classes_str}")
            return result
        except Exception as e:
            print(f"Error fetching dept courses: {e}")
            return []
            
    def get_schedule_for_faculty_common(self, faculty_id: int, year: int) -> List[Tuple]:
        """Get schedule for Common Courses of a faculty, including pool courses."""
        try:
            query = """
                SELECT dp.gun, dp.baslangic, dp.bitis, dp.ders_adi, 
                       (o.ad || ' ' || o.soyad) as hoca, 
                       (SELECT derslik_adi FROM Derslikler WHERE derslik_num = dp.derslik_id) as oda,
                       GROUP_CONCAT(DISTINCT d.ders_kodu) as ders_kodu,
                       dp.ders_tipi,
                       NULL as havuz_kodu,
                       0 as is_pool
                FROM Ders_Programi dp
                JOIN Dersler d ON dp.ders_adi = d.ders_adi AND dp.ders_instance = d.ders_instance
                LEFT JOIN Ogretmenler o ON dp.ogretmen_id = o.ogretmen_num
                JOIN Ders_Sinif_Iliskisi dsi ON dsi.ders_instance = d.ders_instance AND dsi.ders_adi = d.ders_adi
                JOIN Ogrenci_Donemleri od ON dsi.donem_sinif_num = od.donem_sinif_num
                JOIN Bolumler b ON od.bolum_num = b.bolum_id
                WHERE b.fakulte_num = ? AND od.sinif_duzeyi = ?
                GROUP BY dp.gun, dp.baslangic, dp.bitis, dp.ders_adi, o.ad, o.soyad, dp.derslik_id, dp.ders_tipi
                
                UNION ALL
                
                SELECT dp.gun, dp.baslangic, dp.bitis, dp.ders_adi, 
                       (o.ad || ' ' || o.soyad) as hoca, 
                       (SELECT derslik_adi FROM Derslikler WHERE derslik_num = dp.derslik_id) as oda,
                       COALESCE(d.ders_kodu, 'CUSTOM') as ders_kodu,
                       dp.ders_tipi,
                       (SELECT dhi2.havuz_kodu FROM Ders_Havuz_Iliskisi dhi2
                        JOIN Bolumler b2 ON dhi2.bolum_id = b2.bolum_id
                        WHERE dhi2.ders_adi = dp.ders_adi AND b2.fakulte_num = ? LIMIT 1) as havuz_kodu,
                       1 as is_pool
                FROM Ders_Programi dp
                LEFT JOIN Dersler d ON dp.ders_adi = d.ders_adi AND dp.ders_instance = d.ders_instance
                LEFT JOIN Ogretmenler o ON dp.ogretmen_id = o.ogretmen_num
                WHERE EXISTS (
                    SELECT 1 FROM Ders_Havuz_Iliskisi dhi
                    JOIN Bolumler b ON dhi.bolum_id = b.bolum_id
                    WHERE dhi.ders_adi = dp.ders_adi
                    AND b.fakulte_num = ?
                    AND (dhi.sinif_duzeyi = ? OR dhi.sinif_duzeyi = 0)
                )
                GROUP BY dp.gun, dp.baslangic, dp.bitis, dp.ders_adi, o.ad, o.soyad, dp.derslik_id, dp.ders_tipi
            """
            self.c.execute(query, (faculty_id, year, faculty_id, faculty_id, year))
            rows = self.c.fetchall()
            
            result = []
            for r in rows:
                gun, start, end, ders, hoca, oda, codes, ders_tipi, havuz_kodu, is_pool = r
                if not oda:
                    oda = "Belirsiz"
                result.append((gun, start, end, ders, hoca, oda, codes, ders_tipi, havuz_kodu, is_pool))
            return result
        except Exception as e:
            print(f"Error fetching common schedule: {e}")
            return []
    
    # Advanced database operations using DbManager
    def add_faculty(self, faculty_name: str) -> Optional[int]:
        """
        Add a new faculty using DbManager
        
        Args:
            faculty_name: Name of the faculty
        
        Returns:
            Optional[int]: Faculty ID if successful, None otherwise
        """
        try:
            faculty_id = self.fakulte_ekle(faculty_name)
            return faculty_id
        except Exception as e:
            self.error_occurred.emit(f"Fakülte eklenirken hata oluştu: {str(e)}")
            return None
    
    def add_department(self, faculty_id: int, department_name: str) -> Optional[int]:
        """
        Add a new department using DbManager
        
        Args:
            faculty_id: Faculty ID
            department_name: Name of the department
        
        Returns:
            Optional[int]: Department ID if successful, None otherwise
        """
        try:
            department_id = self.bolum_ekle(faculty_id, department_name)
            return department_id
        except Exception as e:
            self.error_occurred.emit(f"Bölüm eklenirken hata oluştu: {str(e)}")
            return None
    
    def get_faculties(self) -> List[Tuple[int, str]]:
        """
        Get all faculties
        
        Returns:
            List[Tuple[int, str]]: List of (faculty_id, faculty_name) tuples
        """
        try:
            self.c.execute("SELECT fakulte_num, fakulte_adi FROM Fakulteler ORDER BY fakulte_adi")
            return self.c.fetchall()
        except Exception as e:
            self.error_occurred.emit(f"Fakülteler yüklenirken hata oluştu: {str(e)}")
            return []
    
    def close_connections(self):
        """Close database connections"""
        try:
            self.conn.close()
        except Exception as e:
            print(f"Veritabanı bağlantısı kapatılırken hata: {str(e)}")
    


    # ════════════════════════════════════════════════════════════════
    # STUDENT & STUDENT-NUMBER HELPERS
    # ════════════════════════════════════════════════════════════════

    def fakulte_numarasini_al(self, ogrenci_num2: int) -> int:
        numara_str = str(ogrenci_num2).zfill(10)  # 10 haneye tamamla, güvenlik için
        return int(numara_str[2:4])
    
    def bolum_numarasini_al(self, bolum_adi: str, fakulte_num: int) -> int:
        self.c.execute('''
            SELECT bolum_num 
            FROM Bolumler 
            WHERE bolum_adi = ? AND fakulte_num = ?
        ''', (bolum_adi, fakulte_num))
        
        sonuc = self.c.fetchone()
        
        if sonuc:
            return sonuc[0]
        else:
            return 0
            
    def get_department_name(self, dept_id: int) -> Optional[str]:
        """Get department name from ID"""
        try:
            self.c.execute("SELECT bolum_adi FROM Bolumler WHERE bolum_id = ?", (dept_id,))
            row = self.c.fetchone()
            return row[0] if row else None
        except Exception as e:
            print(f"Error fetching dept name: {e}")
            return None

    def _format_ogrenci_num(self, girme_senesi, fakulte_num, bolum_num, program_tipi, sira):
        """Öğrenci numarası formatını oluştur: YY0FBBPSSS"""
        year_part = str(girme_senesi)[-2:]  # YY
        faculty_part = f"{fakulte_num:02d}"  # FF
        dept_part = f"{bolum_num:02d}"       # BB
        program_part = str(program_tipi)     # P
        sequence_part = f"{sira:03d}"        # SSS
        return int(f"{year_part}0{faculty_part}{dept_part}{program_part}{sequence_part}")

    def _parse_ogrenci_num(self, ogrenci_num):
        """Öğrenci numarasını parse et"""
        num_str = str(ogrenci_num).zfill(10)
        return {
            'year': int(num_str[0:2]),
            'faculty': int(num_str[2:4]),
            'dept': int(num_str[4:6]),
            'program': int(num_str[6:7]),
            'sequence': int(num_str[7:10])
        }

    # Fakülte ekle
    def fakulte_ekle(self, fakulte_adi):
        with self.conn:
            self.c.execute("INSERT INTO Fakulteler (fakulte_adi) VALUES (?)", (fakulte_adi,))
            return self.c.lastrowid

    def get_course_faculty_map(self) -> Dict[Tuple[str, int], List[str]]:
        """
        Get mapping of (course_name, instance) -> List[Faculty Names]
        Used for restricting Labs to Science/Engineering faculties.
        """
        try:
            query = '''
                SELECT DISTINCT d.ders_adi, d.ders_instance, f.fakulte_adi
                FROM Dersler d
                JOIN Ders_Sinif_Iliskisi dsi ON d.ders_adi = dsi.ders_adi AND d.ders_instance = dsi.ders_instance
                JOIN Ogrenci_Donemleri od ON dsi.donem_sinif_num = od.donem_sinif_num
                JOIN Bolumler b ON od.bolum_num = b.bolum_id
                JOIN Fakulteler f ON b.fakulte_num = f.fakulte_num
            '''
            self.c.execute(query)
            rows = self.c.fetchall()
            
            mapping = {}
            for ders, instance, fakulte in rows:
                key = (ders, instance)
                if key not in mapping:
                    mapping[key] = []
                mapping[key].append(fakulte)
            
            # Deduplicate faculty lists
            for key in mapping:
                mapping[key] = list(set(mapping[key]))
            
            return mapping
        except Exception as e:
            print(f"Error fetching course faculty map: {e}")
            return {}
    
    # Bölüm ekle (otomatik 4-digit global bolum_id ataması)
    def bolum_ekle(self, fakulte_identifier: int | str, bolum_adi: str, by_name: bool = False) -> int:
        """
        Bolum ekler.
        :param fakulte_identifier: Fakulte numarası (int) veya fakulte adı (str)
        :param bolum_adi: Eklenecek bölümün adı (str)
        :param by_name: True ise fakulte_identifier fakulte adı olarak değerlendirilir.
                        False ise fakulte numarası olarak değerlendirilir.
        :return: Yeni 4-digit global bolum_id (int)
        """
        with self.conn:
            if by_name:
                # Fakülte adından numarasını bul
                self.c.execute('SELECT fakulte_num FROM Fakulteler WHERE fakulte_adi = ?', (fakulte_identifier,))
                res = self.c.fetchone()
                if res is None:
                    raise ValueError(f"Fakulte adi '{fakulte_identifier}' bulunamadi.")
                fakulte_num = res[0]
            else:
                fakulte_num = fakulte_identifier

            # Fakülte içi bölüm numarasını hesapla
            self.c.execute('SELECT COALESCE(MAX(bolum_num), 0) + 1 FROM Bolumler WHERE fakulte_num = ?', (fakulte_num,))
            yeni_bolum_num = self.c.fetchone()[0]

            # 4-digit global bolum_id oluştur: FFBB (Fakülte 2-digit + Bölüm 2-digit)
            global_bolum_id = int(f"{fakulte_num:02d}{yeni_bolum_num:02d}")

            # Bölüm ekle
            self.c.execute('''
                INSERT INTO Bolumler (bolum_id, bolum_num, bolum_adi, fakulte_num)
                VALUES (?, ?, ?, ?)
            ''', (global_bolum_id, yeni_bolum_num, bolum_adi, fakulte_num))
            return global_bolum_id
    
    # Öğrenci Sinifı ekle (otomatik donem_sinif_num hesaplaması)
    def ogrenci_sinifi_ekle(self, bolum_id: int, sinif_duzeyi: int, ogrenci_sayisi: int = 0) -> int:
        with self.conn:
            self.c.execute('SELECT fakulte_num, bolum_num FROM Bolumler WHERE bolum_id = ?', (bolum_id,))
            result = self.c.fetchone()
            if not result:
                raise ValueError("Bölüm bulunamadı.")
            fakulte_num, bolum_num = result

            donem_sinif_num = int(f"{fakulte_num}{bolum_num}0{sinif_duzeyi}")

            self.c.execute('''
                INSERT INTO Ogrenci_Donemleri (donem_sinif_num, sinif_duzeyi, bolum_num, ogrenci_sayisi) 
                VALUES (?, ?, ?, ?)
            ''', (donem_sinif_num, sinif_duzeyi, bolum_id, ogrenci_sayisi))
            return donem_sinif_num

    def sinif_ogrenci_sayisini_guncelle(self, donem_sinif_num: str, ogrenci_sayisi: int):
        with self.conn:
            self.c.execute('''
                UPDATE Ogrenci_Donemleri 
                SET ogrenci_sayisi = ? 
                WHERE donem_sinif_num = ?
            ''', (ogrenci_sayisi, donem_sinif_num))
    
    # Ders ekle (ders_instance otomatik atanır)
    def ders_ekle(self, ders_adi, ders_kodu=None, teori_odasi=None, lab_odasi=None, teori_saati=0, uygulama_saati=0, lab_saati=0):
        with self.conn:
            self.c.execute('SELECT ders_instance FROM Dersler WHERE ders_adi = ?', (ders_adi,))
            kullanilanlar = {row[0] for row in self.c.fetchall()}

            instance = 1
            while instance in kullanilanlar:
                instance += 1
            # Kullanılmayan en küçük pozitif sayıyı bulana kadar devam eder.

            self.c.execute('''
                INSERT INTO Dersler (ders_kodu, ders_adi, ders_instance, teori_odasi, lab_odasi, teori_saati, uygulama_saati, lab_saati)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (ders_kodu, ders_adi, instance, teori_odasi, lab_odasi, teori_saati, uygulama_saati, lab_saati))
            return instance
    
    def ogrenci_ekle(self, ad, soyad, bolum_num, fakulte_num, 
                 girme_senesi=None, kacinci_donem=None):
        program_tipi = 0  # Normal öğrenci

        if girme_senesi is None:
            from datetime import datetime
            girme_senesi = datetime.now().year - 1

        with self.conn:
            self.c.execute('''
                SELECT COUNT(*) FROM Ogrenciler
                WHERE girme_senesi = ? AND bolum_num = ? AND fakulte_num = ? AND ikinci_bolum_turu IS NULL
            ''', (girme_senesi, bolum_num, fakulte_num))
            sira = self.c.fetchone()[0] + 1

            ogrenci_num = self._format_ogrenci_num(girme_senesi, fakulte_num, bolum_num, program_tipi, sira)

            self.c.execute('''
                INSERT INTO Ogrenciler (
                    ogrenci_num, ad, soyad, girme_senesi, kacinci_donem,
                    bolum_num, fakulte_num
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                ogrenci_num, ad, soyad, girme_senesi, kacinci_donem,
                bolum_num, fakulte_num
            ))

            return ogrenci_num

    def ogrenci_ekle2(self, ogrenci_num, ikinci_bolumu, ikinci_bolum_turu,
                     girme_senesi2=None, kacinci_donem2=None,):

        # Program tipi belirleme (8: yandal, 9: ikinci anadal)
        if ikinci_bolum_turu.lower() == 'yandal':
            program_tipi = 8
        elif ikinci_bolum_turu.lower() == 'anadal':
            program_tipi = 9
        else:
            raise ValueError("Geçersiz ikinci bölüm türü: 'Yandal' veya 'Anadal' olmalı.")
        
        if girme_senesi2 is None:
            from datetime import datetime
            girme_senesi2 = datetime.now().year - 1

        with self.conn:
            # İkinci bölüm farklı fakülteden olabilir, fakulte_num'u ikinci bölümden al
            self.c.execute('SELECT fakulte_num FROM Bolumler WHERE bolum_adi = ?', (ikinci_bolumu,))
            fakulte_result = self.c.fetchone()
            if not fakulte_result:
                raise ValueError(f"İkinci bölüm '{ikinci_bolumu}' bulunamadı.")
            fakulte_num2 = fakulte_result[0]
            
            bolum_num2 = self.bolum_numarasini_al(ikinci_bolumu, fakulte_num2)

            # Aynı yıl, fakülte, bölüm ve program tipinde kaç kişi kayıtlı?
            self.c.execute('''
                SELECT COUNT(*) FROM Ogrenciler
                WHERE girme_senesi2 = ?
                  AND ikinci_bolum_num = ?
                  AND ikinci_bolum_turu = ?
            ''', (girme_senesi2, bolum_num2, ikinci_bolum_turu))
            sira = self.c.fetchone()[0] + 1

            # Öğrenci numarası: YY0FBBPSSS (ikinci fakülte numarası kullanılır)
            ogrenci_num2 = self._format_ogrenci_num(girme_senesi2, fakulte_num2, bolum_num2, program_tipi, sira)

            self.c.execute('''
                UPDATE Ogrenciler
                SET ikinci_bolum_num = ?, ikinci_bolum_turu = ?, ogrenci_num2 = ?, girme_senesi2 = ?, kacinci_donem2 = ?
                WHERE ogrenci_num = ?
            ''', (bolum_num2, ikinci_bolum_turu, ogrenci_num2, girme_senesi2, kacinci_donem2, ogrenci_num))

            return ogrenci_num2
    
    def verilen_ders_ekle(self, ogrenci_num, yeni_dersler):
        # Mevcut ders_listesini al
        self.c.execute('SELECT ders_listesi FROM Verilen_Dersler WHERE ogrenci_num = ?', (ogrenci_num,))
        sonuc = self.c.fetchone()

        if sonuc is None:
            # Kayıt yoksa direkt ekle
            ders_listesi_str = '|'.join(yeni_dersler)
            self.c.execute('INSERT INTO Verilen_Dersler (ogrenci_num, ders_listesi) VALUES (?, ?)', (ogrenci_num, ders_listesi_str))
        else:
            mevcut_dersler = sonuc[0].split('|') if sonuc[0] else []
            # Yeni dersleri mevcut listeye ekle, tekrarı önle
            toplam_dersler = list(set(mevcut_dersler + yeni_dersler))
            ders_listesi_str = '|'.join(sorted(toplam_dersler))  # İstersen sıralayabilirsin
            # Güncelle
            self.c.execute('UPDATE Verilen_Dersler SET ders_listesi = ? WHERE ogrenci_num = ?', (ders_listesi_str, ogrenci_num))
        
        self.conn.commit()

    def verilen_dersleri_getir(self, ogrenci_num):
        self.c.execute('SELECT ders_listesi FROM Verilen_Dersler WHERE ogrenci_num = ?', (ogrenci_num,))
        row = self.c.fetchone()
        return row[0].split('|') if row and row[0] else []

    def alinan_ders_ekle(self, ders_adi, ders_instance, donem_sinif_num):
        self.c.execute('''
            INSERT OR IGNORE INTO Alinan_Dersler (ders_adi, ders_instance, donem_sinif_num)
            VALUES (?, ?, ?)
        ''', (ders_adi, ders_instance, donem_sinif_num))
        self.conn.commit()

    def alinan_dersleri_getir(self, donem_sinif_num):
        self.c.execute('SELECT ders_adi, ders_instance FROM Alinan_Dersler WHERE donem_sinif_num = ?', (donem_sinif_num,))
        return self.c.fetchall()
    
    # ════════════════════════════════════════════════════════════════
    # CLASSROOM CRUD
    # ════════════════════════════════════════════════════════════════

    def derslik_ekle(self, derslik_adi, tip, kapasite, floor=0, ozellikler=None, notlar=None):
        """Derslik ekle"""
        # Ensure tipping matches schema (derslik_tipi)
        self.c.execute('''
            INSERT INTO Derslikler (derslik_adi, derslik_tipi, kapasite, floor, ozellikler, notlar)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (derslik_adi, tip, kapasite, floor, ozellikler, notlar))
        self.conn.commit()
        return self.c.lastrowid

    def derslik_guncelle(self, derslik_num, data):
        """Derslik bilgilerini güncelle"""
        # data keys: derslik_adi, derslik_tipi, kapasite, floor, notlar
        query = 'UPDATE Derslikler SET '
        params = []
        updates = []
        
        for key, value in data.items():
            updates.append(f"{key} = ?")
            params.append(value)
            
        query += ", ".join(updates)
        query += " WHERE derslik_num = ?"
        params.append(derslik_num)
        
        self.c.execute(query, tuple(params))
        self.conn.commit()
        return True

    def get_derslik_by_id(self, derslik_num):
        """Derslik detaylarını getir"""
        self.c.execute('SELECT derslik_num, derslik_adi, derslik_tipi, kapasite, floor, notlar FROM Derslikler WHERE derslik_num = ?', (derslik_num,))
        return self.c.fetchone()

    def derslik_sil(self, derslik_num):
        """Derslik soft delete - gerçekten silmez, sadece işaretler"""
        from datetime import datetime
        self.c.execute('''
            UPDATE Derslikler 
            SET silindi = 1, silinme_tarihi = ?
            WHERE derslik_num = ?
        ''', (datetime.now(), derslik_num))
        self.conn.commit()

    def aktif_derslikleri_getir(self):
        """Sadece aktif (silinmemiş) derslikleri getir"""
        # Ensure column 'floor' and 'notlar' exist or handle it gracefully? 
        # Assuming migration ran.
        try:
            self.c.execute('SELECT derslik_num, derslik_adi, derslik_tipi, kapasite, floor, notlar FROM Derslikler WHERE silindi = 0')
            return self.c.fetchall()
        except sqlite3.OperationalError:
            # Fallback for old schema if migration failed silently (shouldn't happen)
            print("WARNING: 'floor' or 'notlar' column missing in Derslikler. Returning default.")
            self.c.execute('SELECT derslik_num, derslik_adi, derslik_tipi, kapasite FROM Derslikler WHERE silindi = 0')
            rows = self.c.fetchall()
            # Append default floor 0 and empty notlar
            return [r + (0, "") for r in rows]

    def tum_derslikleri_getir(self):
        """Tüm derslikleri getir (silinmiş olanlar dahil)"""
        self.c.execute('SELECT derslik_num, derslik_adi, derslik_tipi, kapasite, silindi, silinme_tarihi FROM Derslikler')
        return self.c.fetchall()

    # ════════════════════════════════════════════════════════════════
    # TEACHER AVAILABILITY & UNAVAILABILITY
    # ════════════════════════════════════════════════════════════════

    def add_teacher_unavailability(self, teacher_id: int, day: str, start_time: str, end_time: str, yil: str = "Hepsi", donem: str = "Hepsi", description: str = "") -> bool:
        """
        Add a time slot where the teacher is NOT available.
        """
        try:
            # Check for existing overlap for this teacher within the same year/semester scope
            self.c.execute('''
                SELECT id FROM Ogretmen_Musaitlik 
                WHERE ogretmen_id = ? AND gun = ? AND yil = ? AND donem = ?
                AND (
                    (baslangic <= ? AND bitis >= ?) OR
                    (baslangic <= ? AND bitis >= ?) OR
                    (baslangic >= ? AND bitis <= ?)
                )
            ''', (teacher_id, day, yil, donem, start_time, start_time, end_time, end_time, start_time, end_time))
            
            if self.c.fetchone():
                return False # Already marked as unavailable
            
            self.c.execute('''
                INSERT INTO Ogretmen_Musaitlik (ogretmen_id, gun, baslangic, bitis, yil, donem, description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (teacher_id, day, start_time, end_time, yil, donem, description))
            self.conn.commit()
            return True
        except Exception as e:
            self.error_occurred.emit(f"Müsaitlik eklenirken hata: {str(e)}")
            return False

    def get_teacher_unavailability(self, teacher_id: int, yil: str = None, donem: str = None) -> List[tuple]:
        """Get all unavailable slots for a teacher"""
        try:
            # Controller expects: (day, start, end, id, description, ...)
            query = '''
                SELECT om.gun, om.baslangic, om.bitis, om.id, om.description, o.preferred_day_span, om.yil, om.donem
                FROM Ogretmen_Musaitlik om
                JOIN Ogretmenler o ON om.ogretmen_id = o.ogretmen_num
                WHERE om.ogretmen_id = ? 
            '''
            params = [teacher_id]
            
            if yil:
                query += " AND (om.yil = 'Hepsi' OR om.yil = ?)"
                params.append(yil)
                
            if donem:
                query += " AND (om.donem = 'Hepsi' OR om.donem = ?)"
                params.append(donem)
                
            query += '''
                ORDER BY 
                    CASE om.gun 
                        WHEN 'Pazartesi' THEN 1 
                        WHEN 'Salı' THEN 2 
                        WHEN 'Çarşamba' THEN 3 
                        WHEN 'Perşembe' THEN 4 
                        WHEN 'Cuma' THEN 5 
                        WHEN 'Cumartesi' THEN 6 
                        WHEN 'Pazar' THEN 7 
                    END, om.baslangic
            '''
            self.c.execute(query, tuple(params))
            return self.c.fetchall()
        except Exception as e:
            print(f"Error fetching unavailability: {e}")
            return []

    def get_combined_availability(self, teacher_id: int = None) -> List[dict]:
        """
        Get both Day Spans and Unavailability Slots combined.
        Returns list of dicts:
        {
            'type': 'span' | 'slot',
            'teacher_id': int,
            'teacher_name': str,
            # For Span:
            'span_value': int,
            # For Slot:
            'id': int,
            'day': str,
            'start': str,
            'end': str,
            'yil': str,
            'donem': str,
            'description': str
        }
        """
        results = []
        try:
            # 1. Fetch Teachers (Filtered or All)
            if teacher_id:
                self.c.execute("SELECT ogretmen_num, ad, soyad, preferred_day_span, room_request FROM Ogretmenler WHERE ogretmen_num = ?", (teacher_id,))
            else:
                self.c.execute("SELECT ogretmen_num, ad, soyad, preferred_day_span, room_request FROM Ogretmenler ORDER BY ad, soyad")
            
            teachers = self.c.fetchall()
            
            for t in teachers:
                t_num, t_ad, t_soyad, t_span, t_room = t
                t_name = f"{t_ad} {t_soyad}"
                
                # Add Span Entry if exists or if we need to pass room_pref to UI
                if (t_span and t_span > 0) or t_room:
                    results.append({
                        'type': 'span',
                        'teacher_id': t_num,
                        'teacher_name': t_name,
                        'span_value': t_span or 0,
                        'room_pref': t_room or ""
                    })
                
                # 2. Fetch Slots for this teacher
                self.c.execute('''
                    SELECT id, gun, baslangic, bitis, yil, donem, description 
                    FROM Ogretmen_Musaitlik 
                    WHERE ogretmen_id = ?
                    ORDER BY 
                    CASE gun 
                        WHEN 'Pazartesi' THEN 1 
                        WHEN 'Salı' THEN 2 
                        WHEN 'Çarşamba' THEN 3 
                        WHEN 'Perşembe' THEN 4 
                        WHEN 'Cuma' THEN 5 
                        WHEN 'Cumartesi' THEN 6 
                        WHEN 'Pazar' THEN 7 
                    END, baslangic
                ''', (t_num,))
                slots = self.c.fetchall()
                
                for s in slots:
                    results.append({
                        'type': 'slot',
                        'teacher_id': t_num,
                        'teacher_name': t_name,
                        'id': s[0],
                        'day': s[1],
                        'start': s[2],
                        'end': s[3],
                        'yil': s[4],
                        'donem': s[5],
                        'description': s[6]
                    })
                    
            return results
            
        except Exception as e:
            print(f"Error fetching combined availability: {e}")
            return []

    def remove_teacher_unavailability(self, unavailability_id: int) -> bool:
        """Remove an unavailability slot"""
        try:
            self.c.execute("DELETE FROM Ogretmen_Musaitlik WHERE id = ?", (unavailability_id,))
            self.conn.commit()
            return True
        except Exception as e:
            self.error_occurred.emit(f"Müsaitlik silinirken hata: {str(e)}")
            return False

    def update_teacher_unavailability(self, u_id: int, teacher_id: int, day: str, start: str, end: str, yil: str = "Hepsi", donem: str = "Hepsi", description: str = "") -> bool:
        """Update unavailability slot"""
        try:
            # Check for existing overlap (excluding self)
            self.c.execute('''
                SELECT id FROM Ogretmen_Musaitlik 
                WHERE ogretmen_id = ? AND gun = ? AND yil = ? AND donem = ? AND id != ?
                AND (
                    (baslangic <= ? AND bitis >= ?) OR
                    (baslangic <= ? AND bitis >= ?) OR
                    (baslangic >= ? AND bitis <= ?)
                )
            ''', (teacher_id, day, yil, donem, u_id, start, start, end, end, start, end))
            
            if self.c.fetchone():
                return False # Overlap
            
            self.c.execute('''
                UPDATE Ogretmen_Musaitlik 
                SET gun = ?, baslangic = ?, bitis = ?, yil = ?, donem = ?, description = ?
                WHERE id = ?
            ''', (day, start, end, yil, donem, description, u_id))
            self.conn.commit()
            return True
        except Exception as e:
            self.error_occurred.emit(f"Müsaitlik güncellenirken hata: {str(e)}")
            return False



    # ════════════════════════════════════════════════════════════════
    # STUDENT QUERIES & GRADES
    # ════════════════════════════════════════════════════════════════

    def get_student_grades(self, student_id: int, show_history: bool = False) -> List[tuple]:
        """
        Get student grades.
        If show_history is False, returns only the latest attempt for each course.
        """
        try:
            if show_history:
                query = '''
                    SELECT t1.*, (SELECT akts FROM Dersler WHERE ders_kodu = t1.ders_kodu LIMIT 1) as akts 
                    FROM Ogrenci_Notlari t1 
                    WHERE t1.ogrenci_num = ? 
                    ORDER BY t1.donem DESC
                '''
                self.c.execute(query, (student_id,))
            else:
                # Filter out grades that are referenced as 'previous' by another grade
                query = '''
                    SELECT t1.*, (SELECT akts FROM Dersler WHERE ders_kodu = t1.ders_kodu LIMIT 1) as akts
                    FROM Ogrenci_Notlari t1
                    LEFT JOIN Ogrenci_Notlari t2 ON t1.id = t2.onceki_not_id
                    WHERE t1.ogrenci_num = ? AND t2.id IS NULL
                    ORDER BY t1.donem DESC
                '''
                self.c.execute(query, (student_id,))
            return self.c.fetchall()
        except Exception as e:
            print(f"Error fetching grades: {e}")
            return []

    def get_students(self, filters: Dict[str, any] = None) -> List[tuple]:
        """
        Get students based on filters.
        filters: {
            'fakulte_id': int, 
            'bolum_id': int, 
            'sinif': int, 
            'search': str,
            'show_regular': bool,
            'show_irregular': bool,
            'show_cap_yandal': bool
        }
        Returns: List of (ogrenci_num, ad, soyad, bolum_adi, sinif)
        """
        try:
            query = '''
                SELECT o.ogrenci_num, o.ad, o.soyad, b.bolum_adi, o.kacinci_donem
                FROM Ogrenciler o
                JOIN Bolumler b ON o.bolum_num = b.bolum_id
                WHERE 1=1
            '''
            params = []

            if filters:
                if filters.get('fakulte_id'):
                    query += " AND o.fakulte_num = ?"
                    params.append(filters['fakulte_id'])
                
                if filters.get('bolum_id'):
                    query += " AND o.bolum_num = ?"
                    params.append(filters['bolum_id'])
                
                if filters.get('sinif'):
                    # kacinci_donem is semester count (1-8). Year = (kacinci_donem + 1) // 2
                    target_year = filters['sinif']
                    min_sem = (target_year * 2) - 1
                    max_sem = target_year * 2
                    query += " AND o.kacinci_donem BETWEEN ? AND ?"
                    params.extend([min_sem, max_sem])
                
                if filters.get('search'):
                    search_term = f"%{filters['search']}%"
                    query += " AND (o.ad LIKE ? OR o.soyad LIKE ? OR CAST(o.ogrenci_num AS TEXT) LIKE ?)"
                    params.extend([search_term, search_term, search_term])

                # Student Type Filters
                # Default to showing all if keys are missing (backward compatibility)
                show_regular = filters.get('show_regular', True)
                show_irregular = filters.get('show_irregular', True)
                show_cap_yandal = filters.get('show_cap_yandal', True)

                # If all are true, no need to filter (optimization)
                if not (show_regular and show_irregular and show_cap_yandal):
                    type_conditions = []
                    
                    # Regular: No second major AND expected semester
                    # Expected semester = (Current Year - Entry Year) * 2 + 1 (For Fall)
                    # NOTE: Database seems to be in Fall 2024 state, but system year is 2025.
                    # Adjusting by -1 to match database state.
                    effective_year = datetime.now().year - 1
                    
                    if show_regular:
                        type_conditions.append(f"(o.ikinci_bolum_turu IS NULL AND o.kacinci_donem = ({effective_year} - o.girme_senesi) * 2 + 1)")
                    
                    # Irregular: No second major AND NOT expected semester
                    if show_irregular:
                        type_conditions.append(f"(o.ikinci_bolum_turu IS NULL AND o.kacinci_donem != ({effective_year} - o.girme_senesi) * 2 + 1)")
                    
                    # ÇAP/Yandal: Has second major
                    if show_cap_yandal:
                        type_conditions.append("(o.ikinci_bolum_turu IS NOT NULL)")
                    
                    if type_conditions:
                        query += " AND (" + " OR ".join(type_conditions) + ")"
                    else:
                        # If all are false, show nothing
                        query += " AND 0"

            query += " ORDER BY o.ad, o.soyad"
            
            self.c.execute(query, params)
            return self.c.fetchall()
        except Exception as e:
            print(f"Error fetching students: {e}")
            return []

    # get_all_faculties removed — use get_faculties() which is equivalent and ordered.

    def get_all_departments(self) -> List[tuple]:
        """Get all departments (id, name)"""
        try:
            self.c.execute("SELECT bolum_id, bolum_adi FROM Bolumler")
            return self.c.fetchall()
        except Exception as e:
            print(f"Error fetching departments: {e}")
            return []

    def get_teacher_span(self, teacher_id: int) -> int:
        """Get preferred day span for a teacher"""
        try:
            self.c.execute("SELECT preferred_day_span FROM Ogretmenler WHERE ogretmen_num = ?", (teacher_id,))
            row = self.c.fetchone()
            # Return 0 if NULL or not set
            return row[0] if row and row[0] is not None else 0
        except Exception as e:
            print(f"Error getting teacher span: {e}")
            return 0

    def get_all_teacher_day_spans(self) -> List[tuple]:
        """Get (teacher_id, preferred_day_span) for all teachers with a span set."""
        try:
            self.c.execute(
                "SELECT ogretmen_num, preferred_day_span FROM Ogretmenler "
                "WHERE preferred_day_span IS NOT NULL AND preferred_day_span > 0"
            )
            return self.c.fetchall()
        except Exception as e:
            print(f"Error fetching teacher day spans: {e}")
            return []

    def get_pool_codes_by_department(self, dept_id: int) -> List[str]:
        """Get unique pool codes used by a department"""
        try:
            self.c.execute("""
                SELECT DISTINCT dhi.havuz_kodu 
                FROM Ders_Havuz_Iliskisi dhi
                WHERE dhi.bolum_id = ? 
                ORDER BY dhi.havuz_kodu
            """, (dept_id,))
            return [row[0] for row in self.c.fetchall() if row[0]]
        except Exception as e:
            print(f"Error fetching pool codes: {e}")
            return []

    def update_teacher_span(self, teacher_id: int, span: int) -> bool:
        """Update preferred day span for a teacher"""
        try:
            # Clean span value: 0 for "No Constraint"
            val = span if span > 0 else None
            self.c.execute("UPDATE Ogretmenler SET preferred_day_span = ? WHERE ogretmen_num = ?", (val, teacher_id))
            self.conn.commit()
            return True
        except Exception as e:
            self.error_occurred.emit(f"Çalışma bloğu güncellenirken hata: {str(e)}")
            return False

    def get_teacher_room_request(self, teacher_id: int) -> str:
        """Get room request note for a teacher"""
        try:
            self.c.execute("SELECT room_request FROM Ogretmenler WHERE ogretmen_num = ?", (teacher_id,))
            row = self.c.fetchone()
            return row[0] if row and row[0] else ""
        except Exception as e:
            print(f"Error getting room request: {e}")
            return ""

    def update_teacher_room_request(self, teacher_id: int, request: str) -> bool:
        """Update room request note for a teacher"""
        try:
            val = request if request.strip() else None
            self.c.execute("UPDATE Ogretmenler SET room_request = ? WHERE ogretmen_num = ?", (val, teacher_id))
            self.conn.commit()
            return True
        except Exception as e:
            self.error_occurred.emit(f"Oda tercihi güncellenirken hata: {str(e)}")
            return False

    # ════════════════════════════════════════════════════════════════
    # MASTER VIEW & SNAPSHOTS
    # ════════════════════════════════════════════════════════════════

    def get_master_schedule_data(self) -> List[Dict]:
        """
        Fetch ALL schedule data for Master View (Teachers & Classrooms).
        Includes IDs and Names for both resources.
        """
        try:
            query = '''
                SELECT dp.program_id, 
                       dp.ders_adi, 
                       dp.gun, dp.baslangic, dp.bitis,
                       dp.ogretmen_id, (o.ad || ' ' || o.soyad) as ogretmen_adi,
                       dp.derslik_id, dlk.derslik_adi, dlk.derslik_tipi,
                       d.ders_kodu,
                       GROUP_CONCAT(DISTINCT b.bolum_adi || ' ' || od.sinif_duzeyi || '. Sınıf') as siniflar
                FROM Ders_Programi dp
                LEFT JOIN Ogretmenler o ON dp.ogretmen_id = o.ogretmen_num
                LEFT JOIN Derslikler dlk ON dp.derslik_id = dlk.derslik_num
                LEFT JOIN Dersler d ON dp.ders_adi = d.ders_adi AND dp.ders_instance = d.ders_instance
                LEFT JOIN Ders_Sinif_Iliskisi dsi ON d.ders_adi = dsi.ders_adi AND d.ders_instance = dsi.ders_instance
                LEFT JOIN Ogrenci_Donemleri od ON dsi.donem_sinif_num = od.donem_sinif_num
                LEFT JOIN Bolumler b ON od.bolum_num = b.bolum_id
                GROUP BY dp.program_id, dp.ders_adi, dp.gun, dp.baslangic, dp.bitis, 
                         dp.ogretmen_id, o.ad, o.soyad, dp.derslik_id, dlk.derslik_adi, dlk.derslik_tipi
            '''
            self.c.execute(query)
            rows = self.c.fetchall()
            
            data = []
            for r in rows:
                data.append({
                    'id': r[0],
                    'course_name': r[1],
                    'day': r[2],
                    'start': r[3],
                    'end': r[4],
                    'teacher_id': r[5],
                    'teacher_name': r[6],
                    'classroom_id': r[7],
                    'classroom_name': r[8],
                    'classroom_type': r[9],
                    'code': r[10],
                    'groups': r[11]
                })
            return data
        except Exception as e:
            print(f"Error fetching master schedule: {e}")
            self.error_occurred.emit(f"Genel takvim verisi çekilirken hata: {e}")
            return []

    # --- Schedule History / Snapshots ---

    def save_snapshot(self, name: str, semester: str) -> bool:
        """Save current schedule as a snapshot"""
        import json
        try:
            # 1. Fetch current schedule data using Master Data (Hydrated with Teacher Names)
            # This ensures Master View can read it later without manual joins
            data = self.get_master_schedule_data()
            
            # Note: get_master_schedule_data returns keys like 'teacher_name' which MasterView expects.
            # Original raw dump lacked these.
            
            json_data = json.dumps(data)
            
            # 2. Insert into snapshots
            self.c.execute(
                "INSERT INTO schedule_snapshots (name, semester, data) VALUES (?, ?, ?)",
                (name, semester, json_data)
            )
            self.conn.commit()
            return True
        except Exception as e:
            self.error_occurred.emit(f"Program kaydedilirken hata: {str(e)}")
            return False

    def get_snapshots(self) -> List[Dict]:
        """Get list of saved snapshots"""
        try:
            self.c.execute("SELECT id, name, created_at, semester FROM schedule_snapshots ORDER BY created_at DESC")
            rows = self.c.fetchall()
            return [
                {'id': r[0], 'name': r[1], 'created_at': r[2], 'semester': r[3]}
                for r in rows
            ]
        except Exception as e:
            self.error_occurred.emit(f"Geçmiş programlar alınırken hata: {str(e)}")
            return []
            
    def get_snapshot_data(self, snapshot_id: int) -> List[Dict]:
        """Get data for a specific snapshot"""
        import json
        try:
            self.c.execute("SELECT data FROM schedule_snapshots WHERE id = ?", (snapshot_id,))
            row = self.c.fetchone()
            if row:
                return json.loads(row[0])
            return []
        except Exception as e:
            self.error_occurred.emit(f"Program verisi alınırken hata: {str(e)}")
            return []

    # ════════════════════════════════════════════════════════════════
    # COMMON COURSE GROUPS (ORTAK DERSLER)
    # ════════════════════════════════════════════════════════════════

    def get_similar_course_groups(self) -> List[str]:
        """
        Returns a list of (course_name, count) tuples where count > 1, indicating
        multiple Dersler instances exist for that exact course name.
        These are candidates to be configured as a common/shared scheduling block.
        """
        try:
            # We don't use DISTINCT so we can count multiple instances of the exact same name
            self.c.execute("SELECT ders_adi FROM Dersler")
            names = [row[0] for row in self.c.fetchall() if row[0]]
            
            from collections import defaultdict
            base_counts = defaultdict(int)
            
            def get_base(n):
                return n.strip()
                
            for n in names:
                base_counts[get_base(n)] += 1
                
            # Dönüş tipi: [(base_name, count), ...]
            return sorted(list(base_counts.items()))
        except Exception as e:
            print(f"Error fetching similar course groups: {e}")
            return []

    def get_courses_by_base_name(self, base_name: str) -> List[dict]:
        """
        Returns specific course instances that match the base name.
        """
        try:
            query = '''
                SELECT DISTINCT d.ders_adi, d.ders_instance, d.teori_saati, d.uygulama_saati, d.lab_saati,
                       GROUP_CONCAT(DISTINCT COALESCE(b.bolum_adi, b2.bolum_adi)) as bolumler,
                       og.grup_id
                FROM Dersler d
                LEFT JOIN Ders_Sinif_Iliskisi dsi ON d.ders_adi = dsi.ders_adi AND d.ders_instance = dsi.ders_instance
                LEFT JOIN Ogrenci_Donemleri od ON dsi.donem_sinif_num = od.donem_sinif_num
                LEFT JOIN Bolumler b ON od.bolum_num = b.bolum_id
                
                LEFT JOIN Ders_Havuz_Iliskisi dhi ON d.ders_adi = dhi.ders_adi AND d.ders_instance = dhi.ders_instance
                LEFT JOIN Bolumler b2 ON dhi.bolum_id = b2.bolum_id
                
                LEFT JOIN Ortak_Ders_Gruplari og ON d.ders_adi = og.ders_adi AND d.ders_instance = og.ders_instance
                
                WHERE d.ders_adi = ?
                GROUP BY d.ders_adi, d.ders_instance, d.teori_saati, d.uygulama_saati, d.lab_saati, og.grup_id
            '''
            self.c.execute(query, (base_name,))
            rows = self.c.fetchall()
            
            results = []
            for r in rows:
                results.append({
                    'ders_adi': r[0],
                    'ders_instance': r[1],
                    't': r[2], 'u': r[3], 'l': r[4],
                    'bolumler': r[5] if r[5] else 'Bölüm Ataması Yok',
                    'grup_id': r[6]
                })
            return results
        except Exception as e:
            print(f"Error fetching courses for base name '{base_name}': {e}")
            return []

    def save_common_course_group(self, courses: List[Tuple[str, int]]) -> bool:
        """
        Saves a cluster of courses together under a new group ID.
        courses = [(ders_adi1, ders_instance1), (ders_adi2, ders_instance2), ...]
        """
        if not courses or len(courses) < 2:
            return False
            
        try:
            self.c.execute("SELECT MAX(grup_id) FROM Ortak_Ders_Gruplari")
            row = self.c.fetchone()
            new_grup_id = 1 if (not row or row[0] is None) else row[0] + 1
            
            with self.conn:
                for ders_adi, ders_instance in courses:
                    self.c.execute(
                        "DELETE FROM Ortak_Ders_Gruplari WHERE ders_adi = ? AND ders_instance = ?",
                        (ders_adi, ders_instance)
                    )
                    
                    self.c.execute(
                        "INSERT INTO Ortak_Ders_Gruplari (grup_id, ders_adi, ders_instance) VALUES (?, ?, ?)",
                        (new_grup_id, ders_adi, ders_instance)
                    )
            return True
        except Exception as e:
            print(f"Error saving common course group: {e}")
            self.error_occurred.emit(f"Ortak ders grubu kaydedilirken hata: {str(e)}")
            return False

    def auto_group_all_common_courses(self) -> dict:
        """
        Automatically groups all identical-named courses into their own groups,
        provided they share the exact same T, U, and L hours.
        """
        try:
            with self.conn:
                # Bul: Birden fazla instance'ı olan ders isimleri
                self.c.execute('''
                    SELECT d.ders_adi
                    FROM Dersler d
                    GROUP BY d.ders_adi
                    HAVING COUNT(d.ders_instance) > 1
                ''')
                duplicate_names = [row[0] for row in self.c.fetchall()]
                
                if not duplicate_names:
                    return {"success": True, "message": "Gruplanacak ders bulunamadı."}
                
                self.c.execute('SELECT MAX(grup_id) FROM Ortak_Ders_Gruplari')
                row = self.c.fetchone()
                current_grup_id = row[0] if row[0] is not None else 0
                
                grouped_count = 0
                
                for ders_adi in duplicate_names:
                    # Get all instances and their T/U/L
                    self.c.execute('''
                        SELECT ders_instance, teori_saati, uygulama_saati, lab_saati 
                        FROM Dersler WHERE ders_adi = ?
                    ''', (ders_adi,))
                    instances = self.c.fetchall()
                    
                    if not instances: continue
                    
                    # Ensure they all have identical T, U, L
                    first_t = instances[0][1]
                    first_u = instances[0][2]
                    first_l = instances[0][3]
                    
                    is_identical = all(r[1] == first_t and r[2] == first_u and r[3] == first_l for r in instances)
                    if not is_identical:
                        # Skip this course as it has mismatched hours
                        continue
                        
                    # Find if already grouped
                    self.c.execute('SELECT ders_instance, grup_id FROM Ortak_Ders_Gruplari WHERE ders_adi = ?', (ders_adi,))
                    existing = self.c.fetchall()
                    existing_instances = {r[0] for r in existing}
                    
                    # Instances to add
                    to_add = [r[0] for r in instances if r[0] not in existing_instances]
                    
                    if len(to_add) > 1 or (len(to_add) == 1 and existing_instances):
                        # Find existing grup_id or mint new one
                        if existing:
                            grup_id = existing[0][1]
                        else:
                            current_grup_id += 1
                            grup_id = current_grup_id
                            
                        # Insert
                        for inst in to_add:
                            self.c.execute('''
                                INSERT INTO Ortak_Ders_Gruplari (grup_id, ders_adi, ders_instance)
                                VALUES (?, ?, ?)
                            ''', (grup_id, ders_adi, inst))
                        
                        grouped_count += 1
                        
            return {"success": True, "message": f"Tüm aynı isimli dersler tarandı. Toplam {grouped_count} yeni ders grubu oluşturuldu veya güncellendi."}
        except Exception as e:
            print(f"Error in auto grouping: {e}")
            return {"success": False, "message": str(e)}

    def get_common_course_groups(self) -> List[dict]:
        """
        Returns all configured common course groups.
        """
        try:
            query = '''
                SELECT o.grup_id, o.ders_adi, o.ders_instance,
                       GROUP_CONCAT(DISTINCT b.bolum_adi) as bolumler
                FROM Ortak_Ders_Gruplari o
                LEFT JOIN Ders_Sinif_Iliskisi dsi ON o.ders_adi = dsi.ders_adi AND o.ders_instance = dsi.ders_instance
                LEFT JOIN Ogrenci_Donemleri od ON dsi.donem_sinif_num = od.donem_sinif_num
                LEFT JOIN Bolumler b ON od.bolum_num = b.bolum_id
                GROUP BY o.grup_id, o.ders_adi, o.ders_instance
                ORDER BY o.grup_id, o.ders_adi
            '''
            self.c.execute(query)
            rows = self.c.fetchall()
            
            groups = {}
            for r in rows:
                g_id, d_adi, d_inst, bolumler = r
                if g_id not in groups:
                    groups[g_id] = []
                groups[g_id].append({
                    'ders_adi': d_adi,
                    'ders_instance': d_inst,
                    'bolumler': bolumler if bolumler else 'Bölüm Ataması Yok'
                })
            
            results = []
            for g_id, c_list in groups.items():
                results.append({
                    'grup_id': g_id,
                    'courses': c_list
                })
            return results
        except Exception as e:
            print(f"Error fetching common course groups: {e}")
            return []

    def delete_common_course_group(self, grup_id: int) -> bool:
        """
        Deletes a specific common course group.
        """
        try:
            with self.conn:
                self.c.execute("DELETE FROM Ortak_Ders_Gruplari WHERE grup_id = ?", (grup_id,))
            return True
        except Exception as e:
            print(f"Error deleting common course group {grup_id}: {e}")
            self.error_occurred.emit(f"Ortak ders grubu silinirken hata: {str(e)}")
            return False
