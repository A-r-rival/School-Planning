# -*- coding: utf-8 -*-
"""
Calendar Schedule Builder Service

Handles building schedule data for calendar views.
Extracted from ScheduleController to separate business logic.

INTERNAL CANONICAL FORMAT:
All schedule data within this service uses a single 9-tuple format:
    (day, start, end, display_course, extra_info,
     is_elective, real_course_name, course_code, pool_codes)

This prevents tuple-shape explosion and makes future dataclass migration trivial.
"""
from typing import Dict, List, Optional, Tuple, Any
from scripts.parse_curriculum import Regexes
from scripts import curriculum_data
from utils.schedule_merger import merge_consecutive_blocks
import collections


class CalendarScheduleBuilder:
    """
    Builds schedule data for calendar display.
    
    Responsibilities:
    - Fetch schedule data from model based on filters
    - Detect electives using curriculum data and regex
    - Format data for calendar display
    - Merge consecutive blocks
    - Group and post-process for student views
    
    TODO (post-model-refactor):
    - Extract ElectiveDetector as separate service
    - Extract StudentScheduleGrouper as separate service
    """
    
    def __init__(self, model):
        """
        Initialize builder with model dependency.
        
        Args:
            model: ScheduleModel instance for data access
        """
        self.model = model
    
    def build_for_type_change(self, view_type: str):
        """
        Handle view type change - returns filter options.
        
        Args:
            view_type: "Öğretmen", "Derslik", or "Öğrenci Grubu"
        
        Returns:
            Tuple of (filter_level, items) or None
        """
        if view_type == "Öğretmen":
            items = self.model.get_all_teachers_with_ids()
            return (1, items)
        elif view_type == "Derslik":
            items = self.model.get_all_classrooms_with_ids()
            return (1, items)
        elif view_type == "Öğrenci Grubu":
            items = self.model.get_faculties()
            return (1, items)
        return None
    
    def build(self, data: Dict[str, Any]) -> List[Tuple]:
        """
        Build schedule data based on filters.
        
        Args:
            data: Filter data dictionary with keys like:
                - teacher_id: int
                - classroom_id: int
                - faculty_id: int
                - dept_id: int
                - year: str/int
                - show_electives: bool
        
        Returns:
            List of schedule tuples for calendar display
        """
        schedule_data = []
        
        # Teacher view
        if data.get("teacher_id"):
            schedule_data = self._build_teacher_schedule(data["teacher_id"])
        
        # Classroom view
        elif data.get("classroom_id"):
            schedule_data = self._build_classroom_schedule(data["classroom_id"])
        
        # Student group view (faculty-based)
        elif data.get("faculty_id"):
            schedule_data = self._build_student_group_schedule(data)
        
        if schedule_data:
            # Merge consecutive blocks
            schedule_data = merge_consecutive_blocks(schedule_data)
            
            # Post-process for student group view
            if data.get("dept_id"):
                schedule_data = self._post_process_student_view(schedule_data, data)
            else:
                # Regular view (Teacher/Room) - strip to display format
                schedule_data = [self._strip_for_regular_view(x) for x in schedule_data]
        
        return schedule_data
    
    def get_departments_for_faculty(self, faculty_id: int) -> List[Tuple[int, str]]:
        """
        Get departments for a faculty, including "Ortak Dersler".
        
        Args:
            faculty_id: Faculty ID
        
        Returns:
            List of (dept_id, dept_name) tuples
        """
        items = self.model.get_departments_by_faculty(faculty_id)
        items.append((-1, "Ortak Dersler"))
        return items
    
    # ==================== Internal Tuple Format Helpers ====================
    
    def _strip_for_regular_view(self, item: Tuple) -> Tuple:
        """Strip to display format for teacher/classroom views (5-tuple)."""
        return item[:5]  # (day, start, end, display, extra)
    
    def _strip_for_core_student(self, item: Tuple) -> Tuple:
        """Strip to display format for core student courses (5-tuple)."""
        return item[:5]  # (day, start, end, display, extra)
    
    # ==================== Schedule Builders ====================
    
    def _build_teacher_schedule(self, teacher_id: int) -> List[Tuple]:
        """
        Build schedule for teacher view.
        Returns normalized 9-tuples.
        """
        raw_schedule = self.model.get_schedule_by_teacher(teacher_id)
        schedule_data = []
        
        for item in raw_schedule:
            if len(item) == 7:
                day, start, end, course, room, code, ders_tipi = item
                tip_label = ders_tipi if ders_tipi else "?"
                display_course = f"[{code}] {course} ({tip_label})"
                room_label = room if room else "Belirsiz"
                extra = f"Oda: {room_label}"
                
                # Normalize to 9-tuple (pad elective fields)
                schedule_data.append((
                    day, start, end, display_course, extra,
                    False,  # is_elective
                    course,  # real_course_name
                    code,    # course_code
                    []       # pool_codes
                ))
            elif len(item) == 6:  # Fallback
                day, start, end, course, room, code = item
                display_course = f"[{code}] {course}"
                room_label = room if room else "Belirsiz"
                extra = f"Oda: {room_label}"
                
                # Normalize to 9-tuple
                schedule_data.append((
                    day, start, end, display_course, extra,
                    False, course, code, []
                ))
            # Skip malformed items
        
        return schedule_data
    
    def _build_classroom_schedule(self, classroom_id: int) -> List[Tuple]:
        """
        Build schedule for classroom view.
        Returns normalized 9-tuples.
        """
        raw_schedule = self.model.get_schedule_by_classroom(classroom_id)
        schedule_data = []
        
        for item in raw_schedule:
            if len(item) == 7:
                day, start, end, course, teacher, code, ders_tipi = item
                tip_label = ders_tipi if ders_tipi else "?"
                display_course = f"[{code}] {course} ({tip_label})"
                teacher_label = teacher if teacher else "Belirsiz"
                extra = f"Öğretmen: {teacher_label}"
                
                # Normalize to 9-tuple
                schedule_data.append((
                    day, start, end, display_course, extra,
                    False, course, code, []
                ))
            elif len(item) == 6:  # Fallback
                day, start, end, course, teacher, code = item
                display_course = f"[{code}] {course}"
                teacher_label = teacher if teacher else "Belirsiz"
                extra = f"Öğretmen: {teacher_label}"
                
                # Normalize to 9-tuple
                schedule_data.append((
                    day, start, end, display_course, extra,
                    False, course, code, []
                ))
            # Skip malformed items
        
        return schedule_data
    
    def _build_student_group_schedule(self, data: Dict[str, Any]) -> List[Tuple]:
        """
        Build schedule for student group view.
        Returns normalized 9-tuples with full elective detection.
        """
        # Check if we have dept and year
        if not (data.get("dept_id") and data.get("year")):
            return []
        
        # Validation: Ensure year is digits
        if not str(data["year"]).isdigit():
            return []
        
        department_id = int(data["dept_id"])
        
        # Fetch schedule (common courses or department-specific)
        if department_id == -1:
            raw_schedule = self.model.get_schedule_for_faculty_common(
                data["faculty_id"], int(data["year"])
            )
        else:
            raw_schedule = self.model.get_schedule_by_student_group(
                department_id, int(data["year"])
            )
        
        return self._process_student_schedule(raw_schedule, data)
    
    def _process_student_schedule(
        self, raw_schedule: List[Tuple], data: Dict[str, Any]
    ) -> List[Tuple]:
        """
        Process raw student schedule with elective detection.
        Returns normalized 9-tuples.
        """
        schedule_data = []
        dept_name_for_lookup = None
        
        # Get department name for curriculum lookup
        if data.get("dept_id") and int(data["dept_id"]) != -1:
            dept_name_for_lookup = self.model.get_department_name(int(data["dept_id"]))
        
        for idx, item in enumerate(raw_schedule):
            try:
                if len(item) == 8:  # New format with ders_tipi
                    day, start, end, course, teacher, room, code, ders_tipi = item
                    tip_label = ders_tipi if ders_tipi else "?"
                    display_course = f"[{code}] {course} ({tip_label})"
                    room_label = room if room else "Belirsiz"
                    teacher_label = teacher if teacher else "Belirsiz"
                    extra_info = f"Öğretmen: {teacher_label}\nOda: {room_label}"
                    
                    # Detect electives
                    is_elective, pool_codes = self._detect_elective(
                        course, code, dept_name_for_lookup
                    )
                    
                    # Normalized 9-tuple
                    schedule_data.append((
                        day, start, end, display_course, extra_info,
                        is_elective, course, code, pool_codes
                    ))
                
                elif len(item) == 7:
                    day, start, end, course, teacher, room, code = item
                    display_course = f"[{code}] {course}"
                    room_label = room if room else "Belirsiz"
                    teacher_label = teacher if teacher else "Belirsiz"
                    extra_info = f"Öğretmen: {teacher_label}\nOda: {room_label}"
                    
                    # Simple elective detection (fallback)
                    is_elective = "seçmeli" in course.lower() or "sdi" in code.lower() or "gsd" in code.lower()
                    
                    # Normalized 9-tuple
                    schedule_data.append((
                        day, start, end, display_course, extra_info,
                        is_elective, course, code, []
                    ))
                
                elif len(item) == 6:  # Legacy
                    day, start, end, course, teacher, room = item
                    room_label = room if room else "Belirsiz"
                    teacher_label = teacher if teacher else "Belirsiz"
                    extra_info = f"Öğretmen: {teacher_label}\nOda: {room_label}"
                    
                    is_elective = "seçmeli" in course.lower()
                    
                    # Normalized 9-tuple
                    schedule_data.append((
                        day, start, end, course, extra_info,
                        is_elective, course, "", []
                    ))
                # Skip malformed items
            
            except Exception as e:
                print(f"ERROR processing item {idx}: {item} - Error: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        return schedule_data
    
    def _detect_elective(
        self, course_name: str, course_code: str, dept_name: Optional[str] = None
    ) -> Tuple[bool, List[str]]:
        """
        Detect if course is elective and determine pool codes.
        
        Args:
            course_name: Course name
            course_code: Course code
            dept_name: Department name for curriculum lookup
        
        Returns:
            (is_elective, pool_codes) tuple
        """
        pool_codes = []
        is_elective = False
        
        # 1. Look up in curriculum_data (truth source)
        if dept_name:
            dept_data = curriculum_data.DEPARTMENTS_DATA.get(dept_name)
            if dept_data and 'pool_codes' in dept_data:
                clean_name = course_name.split(" (S")[0].strip()
                
                for p_code_key, p_course_names in dept_data['pool_codes'].items():
                    for db_name in p_course_names:
                        # Robust case-insensitive match
                        if (db_name.lower().strip() == clean_name.lower().strip() or
                            db_name.lower().strip() in clean_name.lower().strip() or
                            clean_name.lower().strip() in db_name.lower().strip()):
                            pool_codes.append(p_code_key)
                            is_elective = True
                            break
        
        # 2. Fallback: Regex/Name detection
        if not is_elective:
            pool_code_match = Regexes.pool_code.search(course_code)
            if pool_code_match:
                is_elective = True
                upper_code = course_code.upper()
                if upper_code.startswith("ZSD"):
                    pool_codes.append("ZSD")
                elif upper_code.startswith("ÜSD") or upper_code.startswith("USD"):
                    pool_codes.append("ÜSD")
                elif upper_code.startswith("GSD"):
                    pool_codes.append("GSD")
                elif "SD" in upper_code:
                    pool_codes.append("SD")
            elif "seçmeli" in course_name.lower() or "sdi" in course_code.lower() or "gsd" in course_code.lower():
                is_elective = True
        
        # Deduplicate
        pool_codes = sorted(list(set(pool_codes)))
        
        return is_elective, pool_codes
    
    def _post_process_student_view(
        self, schedule_data: List[Tuple], data: Dict[str, Any]
    ) -> List[Tuple]:
        """
        Post-process student view data - group and separate electives/cores.
        Input: 9-tuples
        Output: Mixed 5-tuples (cores) and 9-tuples (electives)
        """
        final_data = []
        grouped = collections.defaultdict(list)
        
        # Group by time slot
        for item in schedule_data:
            # All items are now 9-tuples
            key = (item[0], item[1], item[2])  # day, start, end
            grouped[key].append(item)
        
        for key, items in grouped.items():
            # Separate electives (is_elective=True at index 5)
            electives = [x for x in items if x[5]]
            cores = [x for x in items if not x[5]]
            
            # Add cores (strip to 5-tuple)
            for c in cores:
                final_data.append(self._strip_for_core_student(c))
            
            # Add electives (keep full 9-tuple for view filtering)
            for e in electives:
                final_data.append(e)  # Full 9-tuple
        
        return final_data
