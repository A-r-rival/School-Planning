# -*- coding: utf-8 -*-
"""
Scheduler Services Module
Decoupled components for fetching, resolving, and building schedulable courses.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Set, FrozenSet, Tuple, Dict, Any
from enum import Enum, auto
import collections
import re
import sys
import os
# curriculum_data is in database/
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database"))
import curriculum_data

# ==========================================
# Enums & Dataclasses
# ==========================================

class CourseRole(Enum):
    CORE = "CORE"
    ELECTIVE = "ELECTIVE"

@dataclass
class RawCourseRow:
    """Represents a flat, unmerged row from the database join."""
    name: str
    instance: int
    t: int
    u: int
    l: int
    akts: int
    code: str
    department: str
    class_year: int
    faculty: str
    group_id: int
    t_room: Optional[int]
    l_room: Optional[int]
    teacher_ids: List[int]
    is_from_pool: bool = False
    pool_code: Optional[str] = None
    common_group_id: Optional[int] = None
    student_count: int = 0
    semester_season: str = ""
    host_department: str = ""

@dataclass(frozen=True)
class ProgramCourseContext:
    """
    Defines the role of a course within a specific program (Dept + Year).
    Example: (CompEng, Year 4, ELECTIVE, pool='SDIII')
    """
    department: str
    year: int
    role: CourseRole
    pool_code: Optional[str] = None

@dataclass
class PhysicalCourse:
    """
    Represents a physical course instance (merged from multiple DB rows).
    This is the unit that actually gets scheduled (variables created).
    """
    name: str
    teacher_ids: FrozenSet[int]
    t: int
    u: int
    l: int
    akts: int
    code: str
    fixed_t_room: Optional[int]
    fixed_l_room: Optional[int]
    faculties: Set[str] = field(default_factory=set)
    group_ids: Set[int] = field(default_factory=set) # Raw group IDs
    contexts: Set[ProgramCourseContext] = field(default_factory=set) # Semantic Contexts
    instance: int = 1 # Default to 1 if not specified
    student_count: int = 0
    semester_season: str = ""


    @property
    def key(self):
        """Unique key for merging logic."""
        return (self.name, self.teacher_ids, self.t, self.u, self.l)


# ==========================================
# Services
# ==========================================

class SchedulerCourseRepository:
    """
    Responsible for fetching raw course data from the database.
    Does NOT apply high-level filtering (like 'Engineering only') unless strictly necessary for the query.
    """
    def __init__(self, db_model):
        self.db_model = db_model
        self._pool_year_map = self._build_pool_year_map()

    def _build_pool_year_map(self) -> dict:
        """
        Builds a runtime mapping of (department, havuz_kodu) -> set(sinif_duzeyi)
        from curriculum_data.py. This avoids DB dependency and auto-updates
        when the curriculum file changes.
        """
        pool_map = collections.defaultdict(set)  # (dept_name, pool_code) -> set(sinif_duzeyi)
        for dept_name, dept_data in curriculum_data.DEPARTMENTS_DATA.items():
            pool_codes_def = dept_data.get('pool_codes', {})
            pools = dept_data.get('pools', {})
            curriculum = dept_data.get('curriculum', {})
            
            for semester_key, semester_courses in curriculum.items():
                # Extract year from "5. Dönem / 3. Yıl Güz Dönemi"
                year_match = re.search(r'(\d+)\.\s*Y[ıi]l', semester_key)
                if not year_match:
                    continue
                sinif_duzeyi = int(year_match.group(1))
                
                if isinstance(semester_courses, list):
                    for course_entry in semester_courses:
                        if isinstance(course_entry, list) and len(course_entry) >= 2:
                            course_code = course_entry[0]
                            if course_code in pool_codes_def or course_code in pools:
                                pool_map[(dept_name, course_code)].add(sinif_duzeyi)
        return dict(pool_map)

    def fetch_course_rows(self) -> List[RawCourseRow]:
        """
        Fetches all course instances joined with student groups and teachers.
        """
        # 1. Build Teacher Map ((Course Name, Instance) -> {Teacher IDs})
        teacher_map = collections.defaultdict(set)
        # Fetch instance as well
        self.db_model.c.execute("""
            SELECT ogretmen_id, ders_adi, ders_instance
            FROM Ders_Ogretmen_Iliskisi
        """)
        for t_id, d_name, d_inst in self.db_model.c.fetchall():
            if d_name:
                # Key is now (Name, Instance)
                # If d_inst is None (legacy), we might need fallback? 
                # But schema enforces PK, so it shouldn't be None.
                key = (d_name.strip(), d_inst)
                teacher_map[key].add(t_id)

        # 2. Fetch Raw Course Rows (Core + Pool)
        query = '''
            SELECT d.ders_adi, d.ders_instance, d.teori_saati, d.uygulama_saati, d.lab_saati, d.akts,
                   d.teori_odasi, d.lab_odasi,
                   dsi.donem_sinif_num,
                   f.fakulte_adi,
                   d.ders_kodu,
                   b.bolum_adi,
                   od.sinif_duzeyi,
                   0 AS is_from_pool,
                   od.ogrenci_sayisi,
                   od.donem_sinif_num,
                   NULL AS pool_dhi_year
            FROM Dersler d
            JOIN Ders_Sinif_Iliskisi dsi ON d.ders_instance = dsi.ders_instance AND d.ders_adi = dsi.ders_adi
            JOIN Ogrenci_Donemleri od ON dsi.donem_sinif_num = od.donem_sinif_num
            JOIN Bolumler b ON od.bolum_num = b.bolum_id
            JOIN Fakulteler f ON b.fakulte_num = f.fakulte_num

            UNION ALL

            SELECT d.ders_adi, d.ders_instance, d.teori_saati, d.uygulama_saati, d.lab_saati, d.akts,
                   d.teori_odasi, d.lab_odasi,
                   od.donem_sinif_num,
                   f.fakulte_adi,
                   d.ders_kodu,
                   b.bolum_adi,
                   od.sinif_duzeyi,
                   1 AS is_from_pool,
                   od.ogrenci_sayisi,
                   od.donem_sinif_num,
                   dhi.sinif_duzeyi AS pool_dhi_year
            FROM Dersler d
            JOIN Ders_Havuz_Iliskisi dhi ON d.ders_instance = dhi.ders_instance AND d.ders_adi = dhi.ders_adi
            JOIN Bolumler b ON dhi.bolum_id = b.bolum_id
            JOIN Fakulteler f ON b.fakulte_num = f.fakulte_num
            JOIN Ogrenci_Donemleri od ON od.bolum_num = b.bolum_id AND (od.sinif_duzeyi = dhi.sinif_duzeyi OR dhi.sinif_duzeyi = 0)
        '''
        # Also fetch havuz_kodu for pool rows to enable Python-side filtering
        # We need a separate query for pool rows to get havuz_kodu
        self.db_model.c.execute(query)
        raw_rows = self.db_model.c.fetchall()
        
        # Build a lookup: (ders_adi, ders_instance, bolum_id) -> havuz_kodu
        self.db_model.c.execute('SELECT ders_adi, ders_instance, bolum_id, havuz_kodu FROM Ders_Havuz_Iliskisi')
        pool_code_lookup = {}
        for prow in self.db_model.c.fetchall():
            key = (prow[0].strip() if prow[0] else '', prow[1], prow[2])
            pool_code_lookup[key] = prow[3]
        
        # Build bolum_adi -> bolum_id lookup for CurriculumResolver mapping
        self.db_model.c.execute('SELECT bolum_id, bolum_adi FROM Bolumler')
        bolum_id_lookup = {r[1].strip(): r[0] for r in self.db_model.c.fetchall()}
        
        # We now rely on the SQL join (od.sinif_duzeyi = dhi.sinif_duzeyi) for filtering.
        rows = raw_rows
        pool_filtered_count = 0

        # 3. Fetch Common Course Groups Mapping
        self.db_model.c.execute("SELECT grup_id, ders_adi, ders_instance FROM Ortak_Ders_Gruplari")
        common_groups_map = {}
        for row in self.db_model.c.fetchall():
            if row[1]:
                common_groups_map[(row[1].strip(), row[2])] = row[0]

        # 4. Fetch Host Department Mapping
        self.db_model.c.execute('''
            SELECT dsi.ders_adi, dsi.ders_instance, b.bolum_adi
            FROM Ders_Sinif_Iliskisi dsi
            JOIN Ogrenci_Donemleri od ON dsi.donem_sinif_num = od.donem_sinif_num
            JOIN Bolumler b ON od.bolum_num = b.bolum_id
        ''')
        host_map = {}
        for h_row in self.db_model.c.fetchall():
            h_name = h_row[0].strip() if h_row[0] else ''
            h_inst = h_row[1]
            h_dept = h_row[2].strip() if h_row[2] else ''
            if (h_name, h_inst) not in host_map:
                host_map[(h_name, h_inst)] = h_dept

        result_rows = []
        for r in rows:
            # First element has 16 columns for non-pool, 17 for pool. Handle flexibly:
            name, instance, t, u, l, akts, t_room, l_room, group_id, fac_name, code, dept_name, class_year, is_from_pool, student_count, semester_season = r[:16]
            pool_dhi_year = r[16] if len(r) > 16 else None
            
            # Normalize
            name = name.strip() if name else ""
            dept_name = dept_name.strip() if dept_name else ""
            fac_name = fac_name.strip() if fac_name else ""
            code = code.strip() if code else ""
            
            # Resolve teachers using specific instance
            # If no specific assignment found, we could potentially fall back to "global" assignment for that course name?
            # But "Strict" is better for the user's requirement.
            t_ids = teacher_map.get((name, instance), set())
            
            c_group_id = common_groups_map.get((name, instance))
            
            p_code = None
            if is_from_pool:
                d_id = bolum_id_lookup.get(dept_name)
                if d_id is not None:
                    p_code = pool_code_lookup.get((name, instance, d_id))
                    
                # Python-level pool year validation to prevent over-constraining (genel havuz -> all years)
                if pool_dhi_year == 0 and p_code:
                    allowed_years = self._pool_year_map.get((dept_name, p_code))
                    if allowed_years and class_year not in allowed_years:
                        pool_filtered_count += 1
                        continue # Skip this row (e.g. Makine 1st year for ZSD if ZSD is only 3rd/4th year)
            
            host_dept = host_map.get((name, instance), dept_name)

            result_rows.append(RawCourseRow(
                name=name,
                instance=instance,
                t=t if t is not None else 0,
                u=u if u is not None else 0,
                l=l if l is not None else 0,
                akts=akts if akts is not None else 0,
                code=code,
                department=dept_name,
                class_year=class_year,
                faculty=fac_name,
                group_id=group_id,
                t_room=t_room,
                l_room=l_room,
                teacher_ids=list(t_ids),
                is_from_pool=bool(is_from_pool),
                pool_code=p_code,
                common_group_id=c_group_id,
                student_count=student_count if student_count else 0,
                semester_season=semester_season if semester_season else "",
                host_department=host_dept
            ))
            
        if pool_filtered_count > 0:
            print(f"DEBUG: Pool year filter removed {pool_filtered_count} unnecessary rows.")
            
        print(f"DEBUG: Repository fetched {len(result_rows)} raw rows.")
        return result_rows


class CurriculumResolver:
    """
    Determines the context (Core vs Elective) of a course for a specific program.
    """
    def __init__(self):
        # We access the global structure directly, 
        # or we could pass it in. For now, direct import.
        self.dept_data = curriculum_data.DEPARTMENTS_DATA

    def resolve_context(self, row: RawCourseRow) -> Optional[ProgramCourseContext]:
        """
        Determines the role of the course for the row's Department + Year.
        Strict logic:
        - If from Ders_Havuz_Iliskisi (is_from_pool == True) -> ELECTIVE
        - Else (from Ders_Sinif_Iliskisi) -> CORE
        """
        if row.is_from_pool:
            role = CourseRole.ELECTIVE
            pool_code = row.pool_code
        else:
            role = CourseRole.CORE
            pool_code = None
        
        return ProgramCourseContext(
            department=row.department,
            year=row.class_year,
            role=role,
            pool_code=pool_code
        )


class CourseMerger:
    """
    Merges duplicate rows (same course, different student groups) into PhysicalCourses.
    Aggregates contexts and validates consistency.
    """
    def merge(self, rows: List[RawCourseRow], resolver: CurriculumResolver) -> List[PhysicalCourse]:
        merged_map = {} # Key -> PhysicalCourse

        for row in rows:
            # 1. Resolve Context
            context = resolver.resolve_context(row)
            if not context:
                continue # Skip ignored pool rows

            # Calculate effective student count
            row_student_count = row.student_count
            if context.role == CourseRole.ELECTIVE:
                row_student_count = int(row_student_count * 0.25)

            # 2. Merge Key
            # If manually grouped, force them into the same key
            if row.common_group_id is not None:
                key = ("COMMON_GROUP", row.common_group_id)
            elif row.is_from_pool:
                # Pool courses MUST merge with their host core course
                key = (row.name, frozenset(row.teacher_ids), row.t, row.u, row.l, row.instance, row.host_department)
            else:
                # Core courses use their own department in the key to prevent accidental merging 
                # (which preserves the user's manual "Ortak Ders Grupları" override feature)
                key = (row.name, frozenset(row.teacher_ids), row.t, row.u, row.l, row.instance, row.department)
            
            if key not in merged_map:
                merged_map[key] = PhysicalCourse(
                    name=row.name,
                    teacher_ids=frozenset(row.teacher_ids),
                    t=row.t, u=row.u, l=row.l,
                    akts=row.akts,
                    code=row.code,
                    fixed_t_room=row.t_room,
                    fixed_l_room=row.l_room,
                    faculties={row.faculty} if row.faculty else set(),
                    group_ids={row.group_id},
                    contexts={context},
                    instance=row.instance,
                    student_count=row_student_count,
                    semester_season=row.semester_season
                )
            else:
                existing = merged_map[key]
                existing.student_count += row_student_count
                existing.group_ids.add(row.group_id)
                existing.contexts.add(context)
                if row.faculty:
                    existing.faculties.add(row.faculty)
                    
                # If this is a common group merge, combine their names for clarity (e.g. Analiz 1 | Analiz 2)
                if row.common_group_id is not None and row.name not in existing.name:
                    existing.name = f"{existing.name} | {row.name}"
                    
                # Union teachers (in case different teachers are assigned to parts of the same common group)
                if row.common_group_id is not None:
                    # PhysicalCourse.teacher_ids is a frozenset, need to recreate it
                    combined_teachers = set(existing.teacher_ids).union(row.teacher_ids)
                    existing.teacher_ids = frozenset(combined_teachers)
                    
                # Optimistic room assignment (if one has it, use it)
                if row.t_room and not existing.fixed_t_room:
                    existing.fixed_t_room = row.t_room
                if row.l_room and not existing.fixed_l_room:
                    existing.fixed_l_room = row.l_room



        # 3. Validate Contexts
        final_courses = []
        for course in merged_map.values():
            self._validate_contexts(course)
            final_courses.append(course)
            
        return final_courses

    def _validate_contexts(self, course: PhysicalCourse):
        """
        Ensures a single (Dept, Year) pair does not have conflicting roles.
        If a course is scheduled as both CORE and ELECTIVE for the same group, 
        CORE takes precedence and the ELECTIVE context is removed.
        """
        seen = {} # (Dept, Year) -> ctx
        to_remove = set()
        
        for ctx in course.contexts:
            key = (ctx.department, ctx.year)
            if key in seen:
                existing_ctx = seen[key]
                if existing_ctx.role != ctx.role:
                    # Conflict! Let Core win.
                    if existing_ctx.role == CourseRole.CORE:
                        to_remove.add(ctx)
                    else:
                        to_remove.add(existing_ctx)
                        seen[key] = ctx
            else:
                seen[key] = ctx
                
        for ctx in to_remove:
            course.contexts.remove(ctx)


class SchedulableCourseBuilder:
    """
    Converts PhysicalCourses into the dictionary format expected by ORToolsScheduler.
    """
    def build_blocks(self, physical_courses: List[PhysicalCourse]) -> List[dict]:
        blocks = []
        for pc in physical_courses:
            
            # Base dictionary
            # Legacy fields: 'is_elective' is REMOVED.
            # New fields: 'program_contexts'
            
            common_props = {
                'name': pc.name,
                'teacher_ids': list(pc.teacher_ids),
                'group_ids': list(pc.group_ids),
                'code': pc.code,
                'departments': list(set(ctx.department for ctx in pc.contexts)),
                'program_contexts': list(pc.contexts), # THE NEW TRUTH
                'faculties': list(pc.faculties),

                'parent_key': (pc.name, pc.instance), # Standardized for DB Update usage
                'instance': pc.instance,
                'student_count': pc.student_count,
                'semester_season': pc.semester_season
            }
            
            # Generate Sub-blocks (Theory, Practice, Lab)
            if pc.t > 0:
                blocks.append({
                    **common_props,
                    'type': 'Teori',
                    'duration': pc.t * 2,
                    'fixed_room': pc.fixed_t_room
                })
            
            if pc.u > 0:
                blocks.append({
                    **common_props,
                    'type': 'Uygulama',
                    # U usually shares theory room or has none
                    'duration': pc.u * 2,
                    'fixed_room': pc.fixed_t_room 
                })
                
            if pc.l > 0:
                blocks.append({
                    **common_props,
                    'type': 'Lab',
                    'duration': pc.l * 2,
                    'fixed_room': pc.fixed_l_room
                })
                
        return blocks
