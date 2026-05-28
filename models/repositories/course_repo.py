# -*- coding: utf-8 -*-
"""
CourseRepository - Manages course data operations
Type-safe, minimal, transaction-agnostic
"""
import sqlite3
from typing import List, NamedTuple, Optional, Dict


# ---------- DTOs ----------

class CourseInstance(NamedTuple):
    """Represents a course instance (section)."""
    instance: int
    code: str


class CourseLookupResult(NamedTuple):
    """Result of get_or_create lookup."""
    instance: int
    code: str
    exists: bool  # False means caller must create via ders_ekle


# ---------- Repository ----------

class CourseRepository:
    """
    Repository for course data access.
    
    NOTE:
    This repository does NOT commit transactions.
    Transaction boundaries are managed by the calling service/model.
    """

    def __init__(self, cursor: sqlite3.Cursor):
        self._cursor = cursor

    # ---------- Queries ----------

    def get_or_create(self, name: str, default_code: str = "CODE") -> CourseLookupResult:
        """
        Get an existing course instance or signal that creation is required.

        Args:
            name: Course name
            default_code: Default code if not found
        
        Returns:
            CourseLookupResult with exists=False if caller must create

        Example:
            >>> result = repo.get_or_create("Matematik", "MAT101")
            >>> if not result.exists:
            ...     instance = model.ders_ekle(name, result.code, ...)
        """
        rows = self._fetch_instances(name)

        if rows:
            instance, code = rows[0]
            return CourseLookupResult(instance, code or default_code, True)

        return CourseLookupResult(1, default_code, False)

    def get_all(self) -> List[tuple[str, str]]:
        """Return all distinct courses (name, code)."""
        return self._execute(
            """
            SELECT DISTINCT ders_adi, ders_kodu
            FROM Dersler
            ORDER BY ders_adi
            """
        ).fetchall()

    def exists(self, name: str) -> bool:
        """Check if a course exists by name."""
        return self._execute(
            "SELECT 1 FROM Dersler WHERE ders_adi = ? LIMIT 1",
            (name,)
        ).fetchone() is not None

    def get_by_name(self, name: str) -> Optional[tuple[int, str, str]]:
        """Get single course by name: (ders_id, ders_adi, ders_kodu)."""
        return self._execute(
            """
            SELECT ders_id, ders_adi, ders_kodu
            FROM Dersler
            WHERE ders_adi = ?
            LIMIT 1
            """,
            (name,)
        ).fetchone()

    def get_instances(self, name: str) -> List[CourseInstance]:
        """Get all instances (sections) of a course."""
        rows = self._fetch_instances(name)
        return [CourseInstance(inst, code) for inst, code in rows]

    def get_id(self, name: str, instance: int) -> int:
        """
        Get course database ID by name and instance.
        
        Args:
            name: Course name
            instance: Course instance number
        
        Returns:
            ders_id from Dersler table
        
        Raises:
            CourseCreationError: Course instance not found
        """
        row = self._execute(
            """
            SELECT ders_id
            FROM Dersler
            WHERE ders_adi = ? AND ders_instance = ?
            """,
            (name, instance)
        ).fetchone()
        
        if not row:
            from models.services.exceptions import CourseCreationError
            raise CourseCreationError(
                f"Course instance not found: {name} (instance {instance})"
            )
        
        return row[0]
    
    def create_instance(self, name: str, code: str) -> int:
        """
        Create a new course instance with auto-calculated instance number.
        
        Args:
            name: Course name
            code: Course code
        
        Returns:
            int: New instance number
        
        Note: Properly calculates next instance to avoid conflicts.
        """
        # Calculate next instance number
        row = self._execute(
            """
            SELECT MAX(ders_instance)
            FROM Dersler
            WHERE ders_adi = ?
            """,
            (name,)
        ).fetchone()
        
        next_instance = (row[0] or 0) + 1
        
        # Create new instance
        self._execute(
            """
            INSERT INTO Dersler (ders_adi, ders_instance, ders_kodu)
            VALUES (?, ?, ?)
            """,
            (name, next_instance, code)
        )
        
        return next_instance

    # ---------- Internal helpers ----------

    def _execute(self, sql: str, params: tuple = ()):
        """
        Single point for SQL execution.
        Future: add logging, timing, debug here.
        """
        self._cursor.execute(sql, params)
        return self._cursor

    def _fetch_instances(self, name: str) -> List[tuple[int, str]]:
        """Helper to fetch course instances with consistent ordering."""
        return self._execute(
            """
            SELECT ders_instance, ders_kodu
            FROM Dersler
            WHERE ders_adi = ?
            ORDER BY ders_instance
            """,
            (name,)
        ).fetchall()

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
