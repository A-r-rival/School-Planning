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
from scripts import curriculum_data

# ==========================================
# Enums & Dataclasses
# ==========================================

class CourseRole(Enum):
    CORE = "CORE"
    ELECTIVE = "ELECTIVE"

@dataclass
class RawCourseRow:
    """Represents a single row from the database join (Course + StudentGroup)."""
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
    teacher_ids: Set[int] = field(default_factory=set)

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


    @property
    def key(self):
        """Unique key for merging logic."""
        return (self.name, self.teacher_ids, self.t, self.u, self.l)


# ==========================================
# Services
# ==========================================

class CourseRepository:
    """
    Responsible for fetching raw course data from the database.
    Does NOT apply high-level filtering (like 'Engineering only') unless strictly necessary for the query.
    """
    def __init__(self, db_model):
        self.db_model = db_model

    def fetch_course_rows(self) -> List[RawCourseRow]:
        """
        Fetches all course instances joined with student groups and teachers.
        """
        # 1. Build Teacher Map (Course Name -> {Teacher IDs})
        # Note: We rely on course name matching for teachers as per original logic.
        teacher_map = collections.defaultdict(set)
        self.db_model.c.execute("""
            SELECT ogretmen_id, ders_adi 
            FROM Ders_Ogretmen_Iliskisi
        """)
        for t_id, d_name in self.db_model.c.fetchall():
            if d_name:
                teacher_map[d_name.strip()].add(t_id)

        # 2. Fetch Raw Course Rows
        query = '''
            SELECT d.ders_adi, d.ders_instance, d.teori_saati, d.uygulama_saati, d.lab_saati, d.akts,
                   d.teori_odasi, d.lab_odasi,
                   dsi.donem_sinif_num,
                   f.fakulte_adi,
                   d.ders_kodu,
                   b.bolum_adi,
                   od.sinif_duzeyi
            FROM Dersler d
            JOIN Ders_Sinif_Iliskisi dsi ON d.ders_instance = dsi.ders_instance AND d.ders_adi = dsi.ders_adi
            JOIN Ogrenci_Donemleri od ON dsi.donem_sinif_num = od.donem_sinif_num
            JOIN Bolumler b ON od.bolum_num = b.bolum_id
            JOIN Fakulteler f ON b.fakulte_num = f.fakulte_num
        '''
        self.db_model.c.execute(query)
        rows = self.db_model.c.fetchall()

        result_rows = []
        for r in rows:
            name, instance, t, u, l, akts, t_room, l_room, group_id, fac_name, code, dept_name, class_year = r
            
            # Normalize
            name = name.strip() if name else ""
            dept_name = dept_name.strip() if dept_name else ""
            fac_name = fac_name.strip() if fac_name else ""
            code = code.strip() if code else ""
            
            # Resolve teachers
            t_ids = teacher_map.get(name, set())
            
            result_rows.append(RawCourseRow(
                name=name,
                instance=instance,
                t=t, u=u, l=l,
                akts=akts,
                code=code,
                department=dept_name,
                class_year=class_year,
                faculty=fac_name,
                group_id=group_id,
                t_room=t_room,
                l_room=l_room,
                teacher_ids=t_ids
            ))
            
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

    def resolve_context(self, row: RawCourseRow) -> ProgramCourseContext:
        """
        Determines the role of the course for the row's Department + Year.
        Strict logic:
        - If explicitly in a pool for this Dept -> ELECTIVE
        - Else -> CORE
        """
        dept_info = self.dept_data.get(row.department)
        role = CourseRole.CORE
        pool_code = None

        if dept_info and 'pool_codes' in dept_info:
             # Wait, structure is dept_info['pool_codes']? No, verify structure.
             # scripts/curriculum_data.py: 
             # DEPARTMENTS_DATA = { 
             #    "Bilgisayar Müh": { 
             #        "curriculum": {...}, 
             #        "pool_codes": { "SDIII": ["Name1", ...] } 
             #    } 
             # }
             
             # Reverse lookup: Check if row.name is in any pool list
             target_name = row.name.lower()
             
             # Check strict string match (case-insensitive)
             # Note: In real data, names might tricky.
             # We assume strict match or substring? 
             # Data file uses full names.
             # NOTE:
             # This resolver intentionally uses STRICT name matching.
             # If a course is not found in pool definitions, it is treated as CORE.
             # This avoids accidental elective classification.
             for p_code, p_courses in dept_info.get('pool_codes', {}).items():
                 if any(c_name.strip().lower() == target_name for c_name in p_courses):
                     role = CourseRole.ELECTIVE
                     pool_code = p_code
                     break
        
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
            
            # 2. Merge Key
            # (Name, Teachers, T, U, L, Instance)
            # Fix: Include instance in unique key to prevent merging distinct instances of same course
            key = (row.name, frozenset(row.teacher_ids), row.t, row.u, row.l, row.instance)
            
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
                    instance=row.instance
                )
            else:
                existing = merged_map[key]
                existing.group_ids.add(row.group_id)
                existing.contexts.add(context)
                if row.faculty:
                    existing.faculties.add(row.faculty)
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
        """
        seen = {} # (Dept, Year) -> Role
        for ctx in course.contexts:
            key = (ctx.department, ctx.year)
            if key in seen and seen[key] != ctx.role:
                # Conflict!
                # STRICT VALIDATION: Raise error to prevent ambiguous scheduling.
                error_msg = f"CRITICAL DATA ERROR: Conflicting roles for course '{course.name}' in context {key}. Found: {seen[key]} vs {ctx.role}. A student group cannot have the same course as both Core and Elective."
                print(error_msg)
                raise ValueError(error_msg)
            seen[key] = ctx.role


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
                'instance': pc.instance
            }
            
            # Generate Sub-blocks (Theory, Practice, Lab)
            if pc.t > 0:
                blocks.append({
                    **common_props,
                    'type': 'Teori',
                    'duration': pc.t,
                    'fixed_room': pc.fixed_t_room
                })
            
            if pc.u > 0:
                blocks.append({
                    **common_props,
                    'type': 'Uygulama',
                    # U usually shares theory room or has none
                    'duration': pc.u,
                    'fixed_room': pc.fixed_t_room 
                })
                
            if pc.l > 0:
                blocks.append({
                    **common_props,
                    'type': 'Lab',
                    'duration': pc.l,
                    'fixed_room': pc.fixed_l_room
                })
                
        return blocks
