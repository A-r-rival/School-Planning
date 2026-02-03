# -*- coding: utf-8 -*-
"""
Schedule Model - MVC Pattern
Handles all data operations and business logic

⚠️ FROZEN: Transitional ScheduleModel
This file is intentionally NOT clean.
Do not refactor further until:
- StudentModel
- FacultyModel
- ClassroomModel
- AvailabilityModel
are extracted.

Only bugfixes allowed.
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

simdiki_sene = datetime.now().year


class ScheduleModel(QObject):
    """
    Model class for schedule management
    Handles data operations and business logic
    """
    
    # Signals for view updates
    course_added = pyqtSignal(str)  # Emits course info when added
    course_removed = pyqtSignal(str)  # Emits course info when removed
    error_occurred = pyqtSignal(str)  # Emits error messages
    
    def __init__(self, db_path: str = None):
        super().__init__()
        
        # Initialize database path
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if db_path is None:
            db_path = os.path.join(script_dir, "database", "okul_veritabani.db")
        
        # Initialize database connection
        self.conn = sqlite3.connect(db_path)
        self.c = self.conn.cursor()
        # Initialize database and run migrations
        from models.repositories.migration import DatabaseMigration
        migration = DatabaseMigration(self.conn)
        migration.run_all()
        
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
    
    def remove_course(self, course_info: str) -> bool:
        """
        DEPRECATED: Remove a course from the schedule by parsing string.
        Use remove_course_by_id instead for better reliability.
        
        This method delegates to remove_course_by_id after minimal parsing.
        
        Args:
            course_info: Course information string (format: "[CODE] Name - Teacher (Day HH:MM-HH:MM)")
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Parse minimal info needed to find the course
            # Updated regex to handle optional {Havuzlar: ...} part
            import re
            # Pattern: [CODE] {optional pools} Name - Teacher (Day Time)
            match = re.search(r"\[(.*?)\](?:\s*\{Havuzlar:.*?\})?\s*(.*?)\s*-\s*(.*?)\s*\((.*?)\s*(\d{2}:\d{2})-(\d{2}:\d{2})\)", course_info)
            
            if not match:
                self.error_occurred.emit("Format hatası: Ders bilgisi okunamadı")
                return False
            
            code, ders_adi, hoca_adi, gun, baslangic, bitis = match.groups()
            
            # Find program_id in database
            query = '''
                SELECT dp.program_id
                FROM Ders_Programi dp
                JOIN Ogretmenler o ON dp.ogretmen_id = o.ogretmen_num
                WHERE dp.ders_adi = ? 
                AND (o.ad || ' ' || o.soyad) = ?
                AND dp.gun = ?
                AND dp.baslangic = ?
            '''
            self.c.execute(query, (ders_adi, hoca_adi, gun, baslangic))
            row = self.c.fetchone()
            
            if row:
                # Delegate to ID-based method
                success = self.remove_course_by_id(row[0])
                if success:
                    self.course_removed.emit(course_info)
                return success
            else:
                self.error_occurred.emit("Silinecek ders bulunamadı!")
                return False
                
        except Exception as e:
            self.error_occurred.emit(f"Ders silinirken hata: {str(e)}")
            return False
    
    def get_all_courses(self) -> List[str]:
        """
        Get all courses from database
        
        Returns:
            List[str]: List of course information strings
        """
        try:
            query = '''
                SELECT dp.ders_adi, o.ad || ' ' || o.soyad, dp.gun, dp.baslangic, dp.bitis, d.ders_kodu,
                       GROUP_CONCAT(DISTINCT b.bolum_adi || ' ' || od.sinif_duzeyi || '. Sınıf'),
                       GROUP_CONCAT(DISTINCT dhi.havuz_kodu)
                FROM Ders_Programi dp
                JOIN Ogretmenler o ON dp.ogretmen_id = o.ogretmen_num
                JOIN Dersler d ON dp.ders_adi = d.ders_adi AND dp.ders_instance = d.ders_instance
                LEFT JOIN Ders_Sinif_Iliskisi dsi ON d.ders_adi = dsi.ders_adi AND d.ders_instance = dsi.ders_instance
                LEFT JOIN Ogrenci_Donemleri od ON dsi.donem_sinif_num = od.donem_sinif_num
                LEFT JOIN Bolumler b ON od.bolum_num = b.bolum_id
                LEFT JOIN Ders_Havuz_Iliskisi dhi ON d.ders_adi = dhi.ders_adi AND d.ders_instance = dhi.ders_instance
                GROUP BY dp.program_id, dp.ders_adi, o.ad, o.soyad, dp.gun, dp.baslangic, dp.bitis, d.ders_kodu
            '''
            self.c.execute(query)
            rows = self.c.fetchall()
            
            courses = []
            for ders, hoca, gun, baslangic, bitis, kodu, siniflar, havuzlar in rows:
                saat = f"{baslangic}-{bitis}"
                # Format: [Code] {Pools: X,Y} Name - Teacher (Day Time) [Classes]
                display_code = kodu if kodu else "CODE"
                
                # Add pool information if available (for elective courses)
                pool_str = ""
                if havuzlar:
                    # Clean up and sort pool codes
                    pool_codes = sorted(set(p.strip() for p in havuzlar.split(',') if p.strip()))
                    if pool_codes:
                        pools_display = ', '.join(pool_codes)
                        pool_str = f" {{Havuzlar: {pools_display}}}"
                
                classes_str = f" [{siniflar}]" if siniflar else ""
                course_info = f"[{display_code}]{pool_str} {ders} - {hoca} ({gun} {saat}){classes_str}"
                courses.append(course_info)
            return courses
        except Exception as e:
            self.error_occurred.emit(f"Dersler yüklenirken hata: {str(e)}")
            return []
    
    def get_teachers(self) -> List[str]:
        """
        Get all unique teacher names
        
        Returns:
            List[str]: List of teacher names
        """
        try:
            teachers = self.teacher_repo.get_all()
            return [name for _, name in teachers]
        except Exception as e:
            self.error_occurred.emit(f"Öğretmenler yüklenirken hata oluştu: {str(e)}")
            return []
    
    def _validate_course_data(self, course_data: Dict[str, str]) -> bool:
        """
        Validate course data before adding
        
        Args:
            course_data: Course data dictionary
        
        Returns:
            bool: True if valid, False otherwise
        """
        required_fields = ['ders', 'hoca', 'gun', 'baslangic', 'bitis']
        
        # Check required fields
        for field in required_fields:
            if field not in course_data or not course_data[field].strip():
                self.error_occurred.emit(f"{field} alanı boş olamaz!")
                return False
        
        # Check time validity
        try:
            start_time = datetime.strptime(course_data['baslangic'], "%H:%M").time()
            end_time = datetime.strptime(course_data['bitis'], "%H:%M").time()
            
            if start_time >= end_time:
                self.error_occurred.emit("Başlangıç saati bitiş saatinden önce olmalıdır!")
                return False
                
        except ValueError:
            self.error_occurred.emit("Geçersiz saat formatı! (HH:MM formatında olmalı)")
            return False
        
        return True
    
    def _has_slot_conflict(self, slot: ScheduleSlot) -> bool:
        """
        DEPRECATED: Use schedule_repo.has_conflict instead.
        Kept for backward compatibility.
        """
        return self.schedule_repo.has_conflict(slot)
    
    def _check_time_conflict(self, gun: str, baslangic: str, bitis: str) -> bool:
        """
        DEPRECATED: Use schedule_repo.has_conflict instead.
        Kept for backward compatibility during refactoring.
        """
        slot = ScheduleSlot.from_strings(gun, baslangic, bitis)
        return self.schedule_repo.has_conflict(slot)

    def get_schedule_by_teacher(self, teacher_id: int) -> List[tuple]:
        """Get schedule for a specific teacher"""
        try:
            query = '''
                SELECT dp.gun, dp.baslangic, dp.bitis, dp.ders_adi, 
                       (SELECT derslik_adi FROM Derslikler WHERE derslik_num = dp.derslik_id) as oda,
                       d.ders_kodu, dp.ders_tipi
                FROM Ders_Programi dp
                JOIN Dersler d ON dp.ders_adi = d.ders_adi AND dp.ders_instance = d.ders_instance
                WHERE dp.ogretmen_id = ?
            '''
            self.c.execute(query, (teacher_id,))
            return self.c.fetchall()
        except Exception as e:
            print(f"Error fetching teacher schedule: {e}")
            return []

    def get_schedule_by_classroom(self, classroom_id: int) -> List[tuple]:
        """Get schedule for a specific classroom"""
        try:
            query = '''
                SELECT dp.gun, dp.baslangic, dp.bitis, dp.ders_adi,
                       (SELECT ad || ' ' || soyad FROM Ogretmenler WHERE ogretmen_num = dp.ogretmen_id) as hoca,
                       GROUP_CONCAT(DISTINCT d.ders_kodu), dp.ders_tipi
                FROM Ders_Programi dp
                JOIN Dersler d ON dp.ders_adi = d.ders_adi AND dp.ders_instance = d.ders_instance
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
                       d.ders_kodu, dp.ders_tipi
                FROM Ders_Programi dp
                JOIN Dersler d ON dp.ders_adi = d.ders_adi AND dp.ders_instance = d.ders_instance
                JOIN Ders_Sinif_Iliskisi dsi ON d.ders_adi = dsi.ders_adi AND d.ders_instance = dsi.ders_instance
                JOIN Ogrenci_Donemleri od ON dsi.donem_sinif_num = od.donem_sinif_num
                WHERE od.bolum_num = ? AND od.sinif_duzeyi = ?
            '''
            self.c.execute(query, (bolum_id, sinif_duzeyi))
            return self.c.fetchall()
        except Exception as e:
            print(f"Error fetching student schedule: {e}")
            return []

    def get_all_teachers_with_ids(self) -> List[Tuple[int, str]]:
        """Get all teachers with their IDs"""
        try:
            self.c.execute("SELECT ogretmen_num, ad || ' ' || soyad FROM Ogretmenler ORDER BY ad")
            return self.c.fetchall()
        except Exception as e:
            print(f"Error fetching teachers: {e}")
            return []
            
    def get_all_classrooms_with_ids(self) -> List[Tuple[int, str]]:
        """Get all classrooms with their IDs sorted naturally"""
        try:
            self.c.execute("SELECT derslik_num, derslik_adi FROM Derslikler WHERE silindi = 0")
            rows = self.c.fetchall()
            
            # Natural sort helper - sorts "Derslik 2" before "Derslik 10"
            def natural_keys(classroom_tuple):
                classroom_name = classroom_tuple[1]  # Get name from (id, name) tuple
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
        """Get schedule for Common Courses of a faculty."""
        try:
            # We group by the schedule slot (day, time, course, teacher) to avoid duplicates
            q2 = """
                SELECT dp.gun, dp.baslangic, dp.bitis, dp.ders_adi, 
                       (o.ad || ' ' || o.soyad), d.teori_odasi, GROUP_CONCAT(DISTINCT d.ders_kodu)
                FROM Ders_Programi dp
                JOIN Dersler d ON dp.ders_adi = d.ders_adi AND dp.ders_instance = d.ders_instance
                LEFT JOIN Ogretmenler o ON dp.ogretmen_id = o.ogretmen_num
                JOIN Ders_Sinif_Iliskisi dsi ON dsi.ders_instance = d.ders_instance AND dsi.ders_adi = d.ders_adi
                JOIN Ogrenci_Donemleri od ON dsi.donem_sinif_num = od.donem_sinif_num
                JOIN Bolumler b ON od.bolum_num = b.bolum_id
                WHERE b.fakulte_num = ? AND od.sinif_duzeyi = ?
                GROUP BY dp.gun, dp.baslangic, dp.bitis, dp.ders_adi, o.ad, o.soyad, d.teori_odasi
            """
            self.c.execute(q2, (faculty_id, year))
            rows = self.c.fetchall()
            result = []
            for r in rows:
                gun, start, end, ders, hoca, room_id, codes = r
                room_name = "Belirsiz"
                if room_id:
                    self.c.execute("SELECT derslik_adi FROM Derslikler WHERE derslik_num=?", (room_id,))
                    rr = self.c.fetchone()
                    if rr: room_name = rr[0]
                result.append((gun, start, end, ders, hoca, room_name, codes))
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
    
    # Database management methods from DbManager
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
        self.c.execute("INSERT INTO Fakulteler (fakulte_adi) VALUES (?)", (fakulte_adi,))
        self.conn.commit()
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
    def ogrenci_sinifi_ekle(self, bolum_id: int, sinif_duzeyi: int) -> int:
        with self.conn:
            self.c.execute('SELECT fakulte_num, bolum_num FROM Bolumler WHERE bolum_id = ?', (bolum_id,))
            result = self.c.fetchone()
            if not result:
                raise ValueError("Bölüm bulunamadı.")
            fakulte_num, bolum_num = result

            donem_sinif_num = int(f"{fakulte_num}{bolum_num}0{sinif_duzeyi}")

            self.c.execute('''
                INSERT INTO Ogrenci_Donemleri (donem_sinif_num, sinif_duzeyi, bolum_num) 
                VALUES (?, ?, ?)
            ''', (donem_sinif_num, sinif_duzeyi, bolum_id))
            return donem_sinif_num
    
    # Ders ekle (ders_instance otomatik atanır)
    def ders_ekle(self, ders_adi, ders_kodu=None, teori_odasi=None, lab_odasi=None, teori_saati=0, uygulama_saati=0, lab_saati=0):
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
        self.conn.commit()
        return instance
    
    def ogrenci_ekle(self, ad, soyad, bolum_num, fakulte_num, 
                 girme_senesi=None, kacinci_donem=None):
        program_tipi = 0  # Normal öğrenci

        if girme_senesi is None:
            girme_senesi = simdiki_sene

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

        self.conn.commit()
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
            girme_senesi2 = simdiki_sene

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

        self.conn.commit()
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
    
    def derslik_ekle(self, derslik_adi, tip, kapasite, ozellikler=None):
        """Derslik ekle"""
        self.c.execute('''
            INSERT INTO Derslikler (derslik_adi, tip, kapasite, ozellikler)
            VALUES (?, ?, ?, ?)
        ''', (derslik_adi, tip, kapasite, ozellikler))
        self.conn.commit()
        return self.c.lastrowid

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
        self.c.execute('SELECT derslik_num, derslik_adi, derslik_tipi, kapasite FROM Derslikler WHERE silindi = 0')
        return self.c.fetchall()

    def tum_derslikleri_getir(self):
        """Tüm derslikleri getir (silinmiş olanlar dahil)"""
        self.c.execute('SELECT derslik_num, derslik_adi, tip, kapasite, silindi, silinme_tarihi FROM Derslikler')
        return self.c.fetchall()

    def add_teacher_unavailability(self, teacher_id: int, day: str, start_time: str, end_time: str, description: str = "") -> bool:
        """
        Add a time slot where the teacher is NOT available.
        """
        try:
            # Check for existing overlap for this teacher
            self.c.execute('''
                SELECT id FROM Ogretmen_Musaitlik 
                WHERE ogretmen_id = ? AND gun = ? 
                AND (
                    (baslangic <= ? AND bitis >= ?) OR
                    (baslangic <= ? AND bitis >= ?) OR
                    (baslangic >= ? AND bitis <= ?)
                )
            ''', (teacher_id, day, start_time, start_time, end_time, end_time, start_time, end_time))
            
            if self.c.fetchone():
                return False # Already marked as unavailable

            self.c.execute('''
                INSERT INTO Ogretmen_Musaitlik (ogretmen_id, gun, baslangic, bitis, description)
                VALUES (?, ?, ?, ?, ?)
            ''', (teacher_id, day, start_time, end_time, description))
            self.conn.commit()
            return True
        except Exception as e:
            self.error_occurred.emit(f"Müsaitlik eklenirken hata: {str(e)}")
            return False

    def get_teacher_unavailability(self, teacher_id: int) -> List[tuple]:
        """Get all unavailable slots for a teacher"""
        try:
            # Controller expects: (day, start, end, id, description)
            self.c.execute('''
                SELECT om.gun, om.baslangic, om.bitis, om.id, om.description, o.preferred_day_span
                FROM Ogretmen_Musaitlik om
                JOIN Ogretmenler o ON om.ogretmen_id = o.ogretmen_num
                WHERE om.ogretmen_id = ? 
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
            ''', (teacher_id,))
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
            'description': str
        }
        """
        results = []
        try:
            # 1. Fetch Teachers (Filtered or All)
            if teacher_id:
                self.c.execute("SELECT ogretmen_num, ad, soyad, preferred_day_span FROM Ogretmenler WHERE ogretmen_num = ?", (teacher_id,))
            else:
                self.c.execute("SELECT ogretmen_num, ad, soyad, preferred_day_span FROM Ogretmenler ORDER BY ad, soyad")
            
            teachers = self.c.fetchall()
            
            for t in teachers:
                t_num, t_ad, t_soyad, t_span = t
                t_name = f"{t_ad} {t_soyad}"
                
                # Add Span Entry if exists
                if t_span and t_span > 0:
                    results.append({
                        'type': 'span',
                        'teacher_id': t_num,
                        'teacher_name': t_name,
                        'span_value': t_span
                    })
                
                # 2. Fetch Slots for this teacher
                self.c.execute('''
                    SELECT id, gun, baslangic, bitis, description 
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
                        'description': s[4]
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

    def update_teacher_unavailability(self, u_id: int, teacher_id: int, day: str, start: str, end: str, description: str = "") -> bool:
        """Update unavailability slot"""
        try:
            # Check for existing overlap (excluding self)
            self.c.execute('''
                SELECT id FROM Ogretmen_Musaitlik 
                WHERE ogretmen_id = ? AND gun = ? AND id != ?
                AND (
                    (baslangic <= ? AND bitis >= ?) OR
                    (baslangic <= ? AND bitis >= ?) OR
                    (baslangic >= ? AND bitis <= ?)
                )
            ''', (teacher_id, day, u_id, start, start, end, end, start, end))
            
            if self.c.fetchone():
                return False # Overlap
            
            self.c.execute('''
                UPDATE Ogretmen_Musaitlik 
                SET gun = ?, baslangic = ?, bitis = ?, description = ?
                WHERE id = ?
            ''', (day, start, end, description, u_id))
            self.conn.commit()
            return True
        except Exception as e:
            self.error_occurred.emit(f"Müsaitlik güncellenirken hata: {str(e)}")
            return False



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
                    # We use the global simdiki_sene variable. 
                    # NOTE: Database seems to be in Fall 2024 state, but system year is 2025.
                    # Adjusting by -1 to match database state.
                    effective_year = simdiki_sene - 1
                    
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

    def get_all_faculties(self) -> List[tuple]:
        """Get all faculties (id, name)"""
        try:
            self.c.execute("SELECT fakulte_num, fakulte_adi FROM Fakulteler")
            return self.c.fetchall()
        except Exception as e:
            print(f"Error fetching faculties: {e}")
            return []

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
