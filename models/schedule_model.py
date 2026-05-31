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
        from models.repositories import (
            TeacherRepository, ScheduleRepository, CourseRepository,
            RoomRepository, StudentRepository, FacultyDepartmentRepository
        )
        self.teacher_repo = TeacherRepository(self.c, self.conn)
        self.schedule_repo = ScheduleRepository(self.c, self.conn)
        self.course_repo = CourseRepository(self.c)  # Course repo doesn't need conn
        self.room_repo = RoomRepository(self.c, self.conn)
        self.student_repo = StudentRepository(self.c, self.conn)
        self.faculty_dept_repo = FacultyDepartmentRepository(self.c, self.conn)
        
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
    
    def get_all_schedule_items(self, semester_filter: Optional[str] = None, versiyon_id: int = None) -> List[Dict]:
        """
        Get all scheduled items with structured data for Table View.
        semester_filter: 'Güz' (Odd semesters), 'Bahar' (Even semesters), 'Yaz' (Empty)
        Returns:
            List[Dict]: List of course data objects with fields:
            id (list of ints for merged), pool, code, name, teacher, day, start, end, classes,
            metadata: faculty_ids, dept_ids, years (lists of ints)
        """
        if versiyon_id is None:
            versiyon_id = self.get_active_schedule_version()
            
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
                WHERE dp.versiyon_id = ?
                GROUP BY dp.program_id, dp.ders_adi, o.ad, o.soyad, dp.gun, dp.baslangic, dp.bitis, d.ders_kodu, d.ders_instance
            '''
            self.c.execute(query, (versiyon_id,))
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
                       COALESCE(d.ders_kodu, 'CUSTOM') as ders_kodu, dp.ders_tipi, dp.program_id
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
        Returns: List of (Course Name, Instance, Course Code).
        """
        try:
            self.c.execute("""
                SELECT i.ders_adi, i.ders_instance, d.ders_kodu
                FROM Ders_Ogretmen_Iliskisi i
                LEFT JOIN Dersler d ON i.ders_adi = d.ders_adi AND i.ders_instance = d.ders_instance
                WHERE i.ogretmen_id = ?
                ORDER BY i.ders_adi, i.ders_instance
            """, (teacher_id,))
            return self.c.fetchall()
        except Exception as e:
            print(f"Error fetching assigned courses: {e}")
            return []

    def get_all_courses_assigned_to_teachers(self) -> List[tuple]:
        """
        Get all courses assigned to any teacher
        Returns: List of (ders_adi, ders_instance, ogretmen_adi_soyadi, ogretmen_id, ders_kodu)
        """
        try:
            query = """
                SELECT i.ders_adi, i.ders_instance, (o.ad || ' ' || o.soyad) as hoca, o.ogretmen_num, d.ders_kodu
                FROM Ders_Ogretmen_Iliskisi i
                JOIN Ogretmenler o ON i.ogretmen_id = o.ogretmen_num
                LEFT JOIN Dersler d ON i.ders_adi = d.ders_adi AND i.ders_instance = d.ders_instance
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
        Returns: List of (ders_adi, ders_instance, ders_kodu)
        """
        try:
            query = """
                SELECT DISTINCT d.ders_adi, d.ders_instance, d.ders_kodu
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

    def get_departments_for_course_instance(self, ders_adi: str, ders_instance: int) -> str:
        """
        Returns a formatted string of departments and years this course instance belongs to.
        Used for UI tooltips.
        """
        try:
            query = """
                SELECT DISTINCT b.bolum_adi, od.sinif_duzeyi
                FROM Ders_Sinif_Iliskisi dsi
                JOIN Ogrenci_Donemleri od ON dsi.donem_sinif_num = od.donem_sinif_num
                JOIN Bolumler b ON od.bolum_num = b.bolum_id
                WHERE dsi.ders_adi = ? AND dsi.ders_instance = ?
                
                UNION ALL
                
                SELECT DISTINCT b.bolum_adi, dhi.sinif_duzeyi
                FROM Ders_Havuz_Iliskisi dhi
                JOIN Bolumler b ON dhi.bolum_id = b.bolum_id
                WHERE dhi.ders_adi = ? AND dhi.ders_instance = ?
            """
            self.c.execute(query, (ders_adi, ders_instance, ders_adi, ders_instance))
            rows = self.c.fetchall()
            
            if not rows:
                return "Bağlı bölüm bulunamadı."
                
            depts = {}
            for dept, year in rows:
                if dept not in depts:
                    depts[dept] = []
                if year == 0:
                    depts[dept].append("Genel")
                else:
                    depts[dept].append(f"{year}.Sınıf")
                    
            lines = []
            for dept, years in depts.items():
                lines.append(f"• {dept} ({', '.join(sorted(years))})")
                
            return "\n".join(lines)
        except Exception as e:
            print(f"Error fetching departments for course {ders_adi}: {e}")
            return ""

    # ════════════════════════════════════════════════════════════════
    # CURRICULUM MANAGEMENT
    # ════════════════════════════════════════════════════════════════

    def delete_curriculum_course(self, course_name: str) -> bool:
        return self.course_repo.delete_curriculum_course(course_name)



    def add_curriculum_course_as_template(self, data: dict) -> bool:
        return self.course_repo.add_curriculum_course_as_template(data)



    def get_schedule_by_classroom(self, classroom_id: int) -> List[tuple]:
        """Get schedule for a specific classroom"""
        try:
            query = '''
                SELECT dp.gun, dp.baslangic, dp.bitis, dp.ders_adi,
                       (SELECT ad || ' ' || soyad FROM Ogretmenler WHERE ogretmen_num = dp.ogretmen_id) as hoca,
                       GROUP_CONCAT(DISTINCT COALESCE(d.ders_kodu, 'CUSTOM')), dp.ders_tipi, dp.program_id
                FROM Ders_Programi dp
                LEFT JOIN Dersler d ON dp.ders_adi = d.ders_adi AND dp.ders_instance = d.ders_instance
                WHERE dp.derslik_id = ?
                GROUP BY dp.gun, dp.baslangic, dp.bitis, dp.ders_adi, dp.ogretmen_id, dp.ders_tipi, dp.program_id
            '''
#SQL kuralı: GROUP BY kullanırken, SELECT'teki aggregate olmayan (örn: SUM, COUNT, GROUP_CONCAT gibi fonksiyon kullanmayan) tüm sütunlar GROUP BY'da da olmalı
            self.c.execute(query, (classroom_id,))
            return self.c.fetchall()
        except Exception as e:
            print(f"Error fetching classroom schedule: {e}")
            return []

    def get_schedule_by_student_group(self, bolum_id: int, sinif_duzeyi: int, versiyon_id: int = None) -> List[tuple]:
        """Get schedule for a specific student group (Department + Year)"""
        if versiyon_id is None:
            versiyon_id = self.get_active_schedule_version()
            
        try:
            query = '''
                SELECT dp.gun, dp.baslangic, dp.bitis, dp.ders_adi,
                       (SELECT ad || ' ' || soyad FROM Ogretmenler WHERE ogretmen_num = dp.ogretmen_id) as hoca,
                       (SELECT derslik_adi FROM Derslikler WHERE derslik_num = dp.derslik_id) as oda,
                       COALESCE(d.ders_kodu, 'CUSTOM') as ders_kodu, dp.ders_tipi,
                       NULL as havuz_kodu,
                       0 as is_pool,
                       dp.ders_instance, dp.program_id
                FROM Ders_Programi dp
                LEFT JOIN Dersler d ON dp.ders_adi = d.ders_adi AND dp.ders_instance = d.ders_instance
                JOIN Ders_Sinif_Iliskisi dsi ON d.ders_adi = dsi.ders_adi AND d.ders_instance = dsi.ders_instance
                JOIN Ogrenci_Donemleri od ON dsi.donem_sinif_num = od.donem_sinif_num
                WHERE od.bolum_num = ? AND od.sinif_duzeyi = ? AND dp.versiyon_id = ?
                
                UNION ALL
                
                SELECT dp.gun, dp.baslangic, dp.bitis, dp.ders_adi,
                       (SELECT ad || ' ' || soyad FROM Ogretmenler WHERE ogretmen_num = dp.ogretmen_id) as hoca,
                       (SELECT derslik_adi FROM Derslikler WHERE derslik_num = dp.derslik_id) as oda,
                       COALESCE(d.ders_kodu, 'CUSTOM') as ders_kodu, dp.ders_tipi,
                       (SELECT GROUP_CONCAT(dhi2.havuz_kodu) FROM Ders_Havuz_Iliskisi dhi2 
                        WHERE dhi2.ders_adi = dp.ders_adi AND dhi2.bolum_id = ? 
                        AND (dhi2.sinif_duzeyi = ? OR dhi2.sinif_duzeyi = 0)) as havuz_kodu,
                       1 as is_pool,
                       dp.ders_instance, dp.program_id
                FROM Ders_Programi dp
                LEFT JOIN Dersler d ON dp.ders_adi = d.ders_adi AND dp.ders_instance = d.ders_instance
                WHERE dp.versiyon_id = ? AND EXISTS (
                    SELECT 1 FROM Ders_Havuz_Iliskisi dhi
                    WHERE dhi.ders_adi = dp.ders_adi
                    AND dhi.bolum_id = ?
                    AND (dhi.sinif_duzeyi = ? OR dhi.sinif_duzeyi = 0)
                )
            '''
            self.c.execute(query, (bolum_id, sinif_duzeyi, versiyon_id, bolum_id, sinif_duzeyi, versiyon_id, bolum_id, sinif_duzeyi))
            return self.c.fetchall()
        except Exception as e:
            print(f"Error fetching student schedule: {e}")
            return []

    def get_all_curriculum_details(self, dept_id: Optional[int] = None, year: Optional[int] = None, faculty_id: Optional[int] = None, semester_filter: Optional[str] = None) -> List[tuple]:
        return self.course_repo.get_all_curriculum_details(dept_id, year, faculty_id, semester_filter)


    def get_curriculum_courses(self) -> List[str]:
        return self.course_repo.get_curriculum_courses()


    def get_all_teachers_with_ids(self) -> List[Tuple[int, str, Optional[str]]]:
        return self.teacher_repo.get_all_teachers_with_ids()
    def get_all_classrooms_with_ids(self) -> List[Tuple[int, str, int]]:
        return self.room_repo.get_all_classrooms_with_ids()


    # ════════════════════════════════════════════════════════════════
    # FACULTY & DEPARTMENT
    # ════════════════════════════════════════════════════════════════

    def get_departments_by_faculty(self, faculty_id: int) -> List[Tuple[int, str]]:
        return self.faculty_dept_repo.get_departments_by_faculty(faculty_id)


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
        return self.course_repo.get_courses_by_department(dept_id, year, day)
    def get_schedule_for_faculty_common(self, faculty_id: int, year: int, versiyon_id: int = None) -> List[Tuple]:
        """Get schedule for Common Courses of a faculty, including pool courses."""
        if versiyon_id is None:
            versiyon_id = self.get_active_schedule_version()
            
        try:
            query = """
                SELECT dp.gun, dp.baslangic, dp.bitis, dp.ders_adi, 
                       (o.ad || ' ' || o.soyad) as hoca, 
                       (SELECT derslik_adi FROM Derslikler WHERE derslik_num = dp.derslik_id) as oda,
                       GROUP_CONCAT(DISTINCT d.ders_kodu) as ders_kodu,
                       dp.ders_tipi,
                       NULL as havuz_kodu,
                       0 as is_pool, dp.program_id
                FROM Ders_Programi dp
                JOIN Dersler d ON dp.ders_adi = d.ders_adi AND dp.ders_instance = d.ders_instance
                LEFT JOIN Ogretmenler o ON dp.ogretmen_id = o.ogretmen_num
                JOIN Ders_Sinif_Iliskisi dsi ON dsi.ders_instance = d.ders_instance AND dsi.ders_adi = d.ders_adi
                JOIN Ogrenci_Donemleri od ON dsi.donem_sinif_num = od.donem_sinif_num
                JOIN Bolumler b ON od.bolum_num = b.bolum_id
                WHERE b.fakulte_num = ? AND od.sinif_duzeyi = ? AND dp.versiyon_id = ?
                GROUP BY dp.gun, dp.baslangic, dp.bitis, dp.ders_adi, o.ad, o.soyad, dp.derslik_id, dp.ders_tipi, dp.program_id
                
                UNION ALL
                
                SELECT dp.gun, dp.baslangic, dp.bitis, dp.ders_adi, 
                       (o.ad || ' ' || o.soyad) as hoca, 
                       (SELECT derslik_adi FROM Derslikler WHERE derslik_num = dp.derslik_id) as oda,
                       COALESCE(d.ders_kodu, 'CUSTOM') as ders_kodu,
                       dp.ders_tipi,
                       (SELECT dhi2.havuz_kodu FROM Ders_Havuz_Iliskisi dhi2
                        JOIN Bolumler b2 ON dhi2.bolum_id = b2.bolum_id
                        WHERE dhi2.ders_adi = dp.ders_adi AND b2.fakulte_num = ? LIMIT 1) as havuz_kodu,
                       1 as is_pool, dp.program_id
                FROM Ders_Programi dp
                LEFT JOIN Dersler d ON dp.ders_adi = d.ders_adi AND dp.ders_instance = d.ders_instance
                LEFT JOIN Ogretmenler o ON dp.ogretmen_id = o.ogretmen_num
                WHERE dp.versiyon_id = ? AND EXISTS (
                    SELECT 1 FROM Ders_Havuz_Iliskisi dhi
                    JOIN Bolumler b ON dhi.bolum_id = b.bolum_id
                    WHERE dhi.ders_adi = dp.ders_adi
                    AND b.fakulte_num = ?
                    AND (dhi.sinif_duzeyi = ? OR dhi.sinif_duzeyi = 0)
                )
                GROUP BY dp.gun, dp.baslangic, dp.bitis, dp.ders_adi, o.ad, o.soyad, dp.derslik_id, dp.ders_tipi, dp.program_id
            """
            self.c.execute(query, (faculty_id, year, versiyon_id, faculty_id, versiyon_id, faculty_id, year))
            rows = self.c.fetchall()
            
            result = []
            for r in rows:
                gun, start, end, ders, hoca, oda, codes, ders_tipi, havuz_kodu, is_pool, program_id = r
                if not oda:
                    oda = "Belirsiz"
                result.append((gun, start, end, ders, hoca, oda, codes, ders_tipi, havuz_kodu, is_pool, program_id))
            return result
        except Exception as e:
            print(f"Error fetching common schedule: {e}")
            return []
    
    # Advanced database operations using DbManager
    def add_faculty(self, faculty_name: str) -> Optional[int]:
        return self.faculty_dept_repo.add_faculty(faculty_name)
    def add_department(self, faculty_id: int, department_name: str) -> Optional[int]:
        return self.faculty_dept_repo.add_department(faculty_id, department_name)
    def get_faculties(self) -> List[Tuple[int, str]]:
        return self.faculty_dept_repo.get_faculties()
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
        return self.faculty_dept_repo.fakulte_numarasini_al(ogrenci_num2)
    def bolum_numarasini_al(self, bolum_adi: str, fakulte_num: int) -> int:
        return self.faculty_dept_repo.bolum_numarasini_al(bolum_adi, fakulte_num)
    def get_department_name(self, dept_id: int) -> Optional[str]:
        return self.faculty_dept_repo.get_department_name(dept_id)


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
        return self.room_repo.derslik_ekle(derslik_adi, tip, kapasite, floor, ozellikler, notlar)


    def derslik_guncelle(self, derslik_num, data):
        return self.room_repo.derslik_guncelle(derslik_num, data)


    def get_derslik_by_id(self, derslik_num):
        return self.room_repo.get_derslik_by_id(derslik_num)


    def derslik_sil(self, derslik_num):
        return self.room_repo.derslik_sil(derslik_num)


    def aktif_derslikleri_getir(self):
        return self.room_repo.aktif_derslikleri_getir()


    def tum_derslikleri_getir(self):
        return self.room_repo.tum_derslikleri_getir()

    def get_lab_cleanup_settings(self) -> dict:
        """Returns {derslik_num: {'temizlik_tipi': type, 'sure_dk': mins, 'gun': day, 'baslangic': time}}"""
        try:
            self.c.execute("SELECT derslik_num, temizlik_tipi, sure_dk, gun, baslangic FROM Derslik_Temizlik_Ayarlari")
            return {r[0]: {'temizlik_tipi': r[1], 'sure_dk': r[2], 'gun': r[3], 'baslangic': r[4]} for r in self.c.fetchall()}
        except Exception as e:
            print(f"Error fetching lab cleanup settings: {e}")
            return {}

    def set_lab_cleanup_settings(self, derslik_num: int, temizlik_tipi: str, sure_dk: int, gun: str = None, baslangic: str = None):
        try:
            with self.conn:
                self.c.execute('''
                    INSERT OR REPLACE INTO Derslik_Temizlik_Ayarlari (derslik_num, temizlik_tipi, sure_dk, gun, baslangic)
                    VALUES (?, ?, ?, ?, ?)
                ''', (derslik_num, temizlik_tipi, sure_dk, gun, baslangic))
            return True
        except Exception as e:
            print(f"Error saving lab cleanup settings: {e}")
            self.error_occurred.emit(f"Temizlik ayarları kaydedilirken hata: {str(e)}")
            return False


    def add_teacher_unavailability(self, teacher_id: int, day: str, start_time: str, end_time: str, yil: str = "Hepsi", donem: str = "Hepsi", description: str = "") -> bool:
        return self.teacher_repo.add_teacher_unavailability(teacher_id, day, start_time, end_time, yil, donem, description)


    def get_teacher_unavailability(self, teacher_id: int, yil: str = None, donem: str = None) -> List[tuple]:
        return self.teacher_repo.get_teacher_unavailability(teacher_id, yil, donem)


    def get_combined_availability(self, teacher_id: int = None) -> List[dict]:
        return self.teacher_repo.get_combined_availability(teacher_id)


    def remove_teacher_unavailability(self, unavailability_id: int) -> bool:
        return self.teacher_repo.remove_teacher_unavailability(unavailability_id)


    def update_teacher_unavailability(self, u_id: int, teacher_id: int, day: str, start: str, end: str, yil: str = "Hepsi", donem: str = "Hepsi", description: str = "") -> bool:
        return self.teacher_repo.update_teacher_unavailability(u_id, teacher_id, day, start, end, yil, donem, description)


    def get_student_grades(self, student_id: int, show_history: bool = False) -> List[tuple]:
        return self.student_repo.get_student_grades(student_id, show_history)


    def get_students(self, filters: Dict[str, any] = None) -> List[tuple]:
        return self.student_repo.get_students(filters)


    def get_all_departments(self) -> List[tuple]:
        return self.faculty_dept_repo.get_all_departments()


    def get_teacher_span(self, teacher_id: int) -> int:
        return self.teacher_repo.get_teacher_span(teacher_id)


    def get_all_teacher_day_spans(self) -> List[tuple]:
        return self.teacher_repo.get_all_teacher_day_spans()


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
        return self.teacher_repo.update_teacher_span(teacher_id, span)


    def get_teacher_room_request(self, teacher_id: int) -> str:
        return self.teacher_repo.get_teacher_room_request(teacher_id)


    def update_teacher_room_request(self, teacher_id: int, request: str) -> bool:
        return self.teacher_repo.update_teacher_room_request(teacher_id, request)


    def get_master_schedule_data(self, versiyon_id: int = None) -> List[Dict]:
        """
        Fetch ALL schedule data for Master View (Teachers & Classrooms).
        Includes IDs and Names for both resources.
        """
        if versiyon_id is None:
            versiyon_id = self.get_active_schedule_version()
            
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
                WHERE dp.versiyon_id = ?
                GROUP BY dp.program_id, dp.ders_adi, dp.gun, dp.baslangic, dp.bitis, 
                         dp.ogretmen_id, o.ad, o.soyad, dp.derslik_id, dlk.derslik_adi, dlk.derslik_tipi
            '''
            self.c.execute(query, (versiyon_id,))
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

    def get_department_course_categories(self) -> dict:
        """
        Returns { department_name: { category_name: [(course_name, code), ...] } }
        where category_name is e.g. "1. Sınıf" or "ZSDII".
        """
        try:
            query_regular = """
                SELECT b.bolum_adi, od.sinif_duzeyi || '. Sınıf' as category, d.ders_adi, d.ders_kodu
                FROM Bolumler b
                JOIN Ogrenci_Donemleri od ON b.bolum_id = od.bolum_num
                JOIN Ders_Sinif_Iliskisi dsi ON od.donem_sinif_num = dsi.donem_sinif_num
                JOIN Dersler d ON dsi.ders_adi = d.ders_adi AND dsi.ders_instance = d.ders_instance
            """
            self.c.execute(query_regular)
            regular = self.c.fetchall()
            
            query_pool = """
                SELECT b.bolum_adi, dhi.havuz_kodu as category, d.ders_adi, d.ders_kodu
                FROM Bolumler b
                JOIN Ders_Havuz_Iliskisi dhi ON b.bolum_id = dhi.bolum_id
                JOIN Dersler d ON dhi.ders_adi = d.ders_adi AND dhi.ders_instance = d.ders_instance
            """
            self.c.execute(query_pool)
            pools = self.c.fetchall()
            
            results = {}
            for dept, cat, c_name, code in regular + pools:
                if dept not in results:
                    results[dept] = {}
                if cat not in results[dept]:
                    results[dept][cat] = set()
                results[dept][cat].add((c_name, code or ""))
                
            return {d: {c: sorted(list(v)) for c, v in cats.items()} for d, cats in results.items()}
        except Exception as e:
            print(f"Error fetching department categories: {e}")
            return {}

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

    def clear_all_common_groups(self) -> dict:
        """
        Deletes all common course groupings, reverting courses to single instances.
        """
        try:
            with self.conn:
                self.c.execute('DELETE FROM Ortak_Ders_Gruplari')
            return {"success": True, "message": "Tüm gruplamalar başarıyla temizlendi."}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def auto_group_all_common_courses(self, chunk_size=None) -> dict:
        """
        Automatically groups all identical-named courses into their own groups,
        provided they share the exact same T, U, and L hours.
        If chunk_size is provided, it splits the instances into multiple groups of max size chunk_size.
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
                        ORDER BY ders_instance
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
                        
                    if chunk_size:
                        # Clear existing for this course so we can re-chunk cleanly
                        self.c.execute('DELETE FROM Ortak_Ders_Gruplari WHERE ders_adi = ?', (ders_adi,))
                        inst_list = [r[0] for r in instances]
                        
                        # Chunk the instances
                        for i in range(0, len(inst_list), chunk_size):
                            chunk = inst_list[i:i+chunk_size]
                            if len(chunk) > 1:
                                current_grup_id += 1
                                for inst in chunk:
                                    self.c.execute('''
                                        INSERT INTO Ortak_Ders_Gruplari (grup_id, ders_adi, ders_instance)
                                        VALUES (?, ?, ?)
                                    ''', (current_grup_id, ders_adi, inst))
                                grouped_count += 1
                    else:
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

    # -------------------------------------------------------------------------
    # VERSIONING & TEMPLATING
    # -------------------------------------------------------------------------
    
    def create_schedule_version(self, ad: str, aciklama: str = "") -> int:
        try:
            with self.conn:
                self.c.execute("UPDATE Program_Versiyonlari SET is_active = 0")
                self.c.execute("INSERT INTO Program_Versiyonlari (ad, aciklama, is_active) VALUES (?, ?, 1)", (ad, aciklama))
                return self.c.lastrowid
        except Exception as e:
            print(f"Error creating schedule version: {e}")
            return -1

    def get_active_schedule_version(self) -> int:
        try:
            self.c.execute("SELECT versiyon_id FROM Program_Versiyonlari WHERE is_active = 1 LIMIT 1")
            row = self.c.fetchone()
            if row:
                return row[0]
            return self.create_schedule_version("Varsayılan Program", "Otomatik oluşturuldu")
        except Exception as e:
            print(f"Error getting active version: {e}")
            return 1
            
    def get_all_schedule_versions(self) -> list:
        try:
            self.c.execute("SELECT versiyon_id, ad, aciklama, tarih, is_active FROM Program_Versiyonlari ORDER BY tarih DESC")
            return [{"versiyon_id": r[0], "ad": r[1], "aciklama": r[2], "tarih": r[3], "is_active": r[4]} for r in self.c.fetchall()]
        except Exception as e:
            print(f"Error getting schedule versions: {e}")
            return []
            
    def set_active_schedule_version(self, versiyon_id: int) -> bool:
        try:
            with self.conn:
                self.c.execute("UPDATE Program_Versiyonlari SET is_active = 0")
                self.c.execute("UPDATE Program_Versiyonlari SET is_active = 1 WHERE versiyon_id = ?", (versiyon_id,))
            return True
        except Exception as e:
            print(f"Error setting active version: {e}")
            return False

    def save_group_template(self, ad: str, aciklama: str = "") -> bool:
        try:
            with self.conn:
                self.c.execute("INSERT INTO Ortak_Grup_Sablonlari (ad, aciklama) VALUES (?, ?)", (ad, aciklama))
                sablon_id = self.c.lastrowid
                
                self.c.execute("SELECT ders_adi, ders_instance, grup_id FROM Ortak_Ders_Gruplari")
                for row in self.c.fetchall():
                    self.c.execute("INSERT INTO Ortak_Grup_Sablon_Detay (sablon_id, ders_adi, ders_instance, grup_id) VALUES (?, ?, ?, ?)", (sablon_id, row[0], row[1], row[2]))
            return True
        except Exception as e:
            print(f"Error saving group template: {e}")
            self.error_occurred.emit(f"Şablon kaydedilirken hata: {str(e)}")
            return False

    def load_group_template(self, sablon_id: int) -> bool:
        try:
            with self.conn:
                self.c.execute("DELETE FROM Ortak_Ders_Gruplari")
                self.c.execute("SELECT ders_adi, ders_instance, grup_id FROM Ortak_Grup_Sablon_Detay WHERE sablon_id = ? ORDER BY grup_id", (sablon_id,))
                for row in self.c.fetchall():
                    self.c.execute("INSERT INTO Ortak_Ders_Gruplari (grup_id, ders_adi, ders_instance) VALUES (?, ?, ?)", (row[2], row[0], row[1]))
            return True
        except Exception as e:
            print(f"Error loading group template: {e}")
            self.error_occurred.emit(f"Şablon yüklenirken hata: {str(e)}")
            return False
            
    def get_group_templates(self) -> list:
        try:
            self.c.execute("SELECT sablon_id, ad, aciklama, tarih FROM Ortak_Grup_Sablonlari ORDER BY tarih DESC")
            return [{"sablon_id": r[0], "ad": r[1], "aciklama": r[2], "tarih": r[3]} for r in self.c.fetchall()]
        except Exception as e:
            print(f"Error getting group templates: {e}")
            return []
            
    def delete_group_template(self, sablon_id: int) -> bool:
        try:
            with self.conn:
                self.c.execute("DELETE FROM Ortak_Grup_Sablonlari WHERE sablon_id = ?", (sablon_id,))
            return True
        except Exception as e:
            print(f"Error deleting group template: {e}")
            self.error_occurred.emit(f"Şablon silinirken hata: {str(e)}")
            return False

