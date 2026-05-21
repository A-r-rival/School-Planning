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
import sys
import os

# curriculum_data is in database/
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database"))
import curriculum_data
from utils.schedule_merger import merge_consecutive_blocks


class CalendarScheduleBuilder:
    """
    Builds schedule data for calendar display.
    
    Responsibilities:
    - Fetch schedule data from model based on filters
    - Detect electives using curriculum data and regex
    - Format data for calendar display
    - Merge consecutive blocks
    - Group and post-process for student views
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
    
    def build(self, data: Dict[str, Any]) -> Dict[str, Any]:
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
            Dictionary with:
                - 'schedule': List of schedule tuples for calendar display
                - 'metadata': dict with extra info (e.g. day_span)
        """
        schedule_data = []
        metadata = {}
        
        # Teacher view
        if data.get("teacher_id"):
            schedule_data = self._build_teacher_schedule(data["teacher_id"])
            metadata['day_span'] = self.model.get_teacher_span(data["teacher_id"])
        
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
                # Keep 9-tuple for Teacher view if it contains UNAVAILABLE tag
                schedule_data = [
                    self._strip_for_regular_view(x) if not (len(x) > 6 and x[6] == "UNAVAILABLE") else x 
                    for x in schedule_data
                ]
        
        return {
            'schedule': schedule_data,
            'metadata': metadata
        }
    
    def get_departments_for_faculty(self, faculty_id: int) -> List[Tuple[int, str]]:
        """
        Get departments for a faculty, including "Ortak Dersler".
        """
        items = self.model.get_departments_by_faculty(faculty_id)
        # Ensure Ortak Dersler is added only if not present
        if not any(it[0] == -1 for it in items):
            items.append((-1, "Ortak Dersler"))
        return items
    
    # ==================== Internal Tuple Format Helpers ====================
    
    def _strip_for_regular_view(self, item: Tuple) -> Tuple:
        """Strip to display format for teacher/classroom views (5-tuple)."""
        return item[:5]  # (day, start, end, display, extra)
    

    
    # ==================== Schedule Builders ====================
    
    def _build_teacher_schedule(self, teacher_id: int) -> List[Tuple]:
        """
        Build schedule for teacher view.
        Returns normalized 9-tuples.
        """
        raw_schedule = self.model.get_schedule_by_teacher(teacher_id)
        schedule_data = []
        
        # 1. Add booked courses
        for item in raw_schedule:
            if len(item) == 7:
                day, start, end, course, room, code, ders_tipi = item
                tip_label = ders_tipi if ders_tipi else "?"
                display_course = f"[{code}] {course} ({tip_label})"
                room_label = room if room else "Belirsiz"
                extra = f"Oda: {room_label}"
                
                # Normalize to 9-tuple
                schedule_data.append((
                    day, start, end, display_course, extra,
                    False, course, code, []
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
        
        # 2. Add unavailability (restricted hours)
        unavailability = self.model.get_teacher_unavailability(teacher_id)
        # unavailability schema: (gun, baslangic, bitis, id, description, span, yil, donem)
        for gun, baslangic, bitis, u_id, desc, *rest in unavailability:
            schedule_data.append((
                gun, baslangic, bitis, "KISITLI / MÜSAİT DEĞİL", desc,
                False, "UNAVAILABLE", "", []
            ))
        
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
        department_id = data.get("dept_id")
        year = data.get("year")
        faculty_id = data.get("faculty_id")
        
        # Validation: Ensure we have at least dept and year
        if department_id is None or year is None:
            return []
            
        # Ensure year is digits
        if not str(year).isdigit():
            return []
            
        department_id = int(department_id)
        
        # Fetch schedule (common courses or department-specific)
        if department_id == -1:
            if faculty_id is None:
                return []
            raw_schedule = self.model.get_schedule_for_faculty_common(
                faculty_id, int(year)
            )
        else:
            raw_schedule = self.model.get_schedule_by_student_group(
                department_id, int(year)
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
                # DB student group format (new 11-column format)
                if len(item) == 11:
                    day, start, end, course_name, teacher, room, code, ders_tipi, pool_data, is_pool, instance = item
                    
                    tip_label = ders_tipi if ders_tipi else "?"
                    display_course = f"[{code}] {course_name} ({tip_label})"
                    
                    room_label = room if room else "Belirsiz"
                    teacher_label = teacher if teacher else "Belirsiz"
                    
                    extra_lines = []
                    if instance:
                        extra_lines.append(f"Şube {instance}")
                    extra_lines.append(f"Öğretmen: {teacher_label}")
                    extra_lines.append(f"Oda: {room_label}")
                    
                    extra_info = "\n".join(extra_lines)
                    
                    is_elective = bool(is_pool)
                    
                    # Robust pool_data handling: ensure it's a list
                    if isinstance(pool_data, list):
                        p_list = pool_data
                    elif pool_data:
                        p_list = [x.strip() for x in str(pool_data).split(',') if x.strip()]
                    else:
                        p_list = []
                        
                    if not is_elective:
                        # Fallback heuristic
                        is_elective, p_list_detected = self._detect_elective(course_name, code, dept_name_for_lookup)
                        if is_elective and not p_list:
                            p_list = p_list_detected
                            
                    schedule_data.append((day, start, end, display_course, extra_info, is_elective, course_name, code, p_list))
                
                # Pre-normalized 9-tuple format
                elif len(item) == 9:
                    day, start, end, course_disp, extra, is_elec, course_name, code, pool_data = item
                    
                    # Robust pool_data handling
                    if isinstance(pool_data, list):
                        p_list = pool_data
                    elif pool_data:
                        p_list = [x.strip() for x in str(pool_data).split(',') if x.strip()]
                    else:
                        p_list = []
                        
                    schedule_data.append((day, start, end, course_disp, extra, bool(is_elec), course_name, code, p_list))
                elif len(item) == 8:  # Old format with ders_tipi
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
                    is_elective, pool_codes = self._detect_elective(course, code, dept_name_for_lookup)
                    
                    # Normalized 9-tuple
                    schedule_data.append((
                        day, start, end, display_course, extra_info,
                        is_elective, course, code, pool_codes
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
        Detect if course is elective and determine pool codes based on prefix and name.
        """
        pool_codes = []
        is_elective = False
        
        upper_code = str(course_code).upper().strip()
        upper_name = str(course_name).upper().strip()
        
        # 1. Check for USD/ÜSD (University Elective)
        if upper_code.startswith("USD") or upper_code.startswith("ÜSD") or "ÜNİVERSİTE SEÇMELİ" in upper_name:
            pool_codes.append("USD") # Normalize to USD
            return True, pool_codes

        # 2. Check for ZSD (Mandatory Elective)
        if upper_code.startswith("ZSD") or "BÖLÜM SEÇMELİ" in upper_name or "ZORUNLU SEÇMELİ" in upper_name:
            # Normalize ZSDI, ZSDII -> ZSD
            pool_codes.append("ZSD")
            return True, pool_codes
            
        # 3. Check for GSD (General Elective)
        if upper_code.startswith("GSD") or "GENEL SEÇMELİ" in upper_name:
            pool_codes.append("GSD")
            return True, pool_codes

        # 4. Check for general SD prefix (Normal Elective)
        if upper_code.startswith("SD"):
            # Normalize SDI, SDII -> SD
            pool_codes.append("SD")
            return True, pool_codes
        elif "SEÇMELİ" in upper_name:
            pool_codes.append("SD")
            return True, pool_codes
            
        return False, []
    
    def _post_process_student_view(
        self, schedule_data: List[Tuple], data: Dict[str, Any]
    ) -> List[Tuple]:
        """
        Post-process student view data - group and separate electives/cores.
        Input: 9-tuples
        Output: Mixed 5-tuples (cores) and 9-tuples (electives)
        """
        final_data = []
        
        for item in schedule_data:
            if len(item) < 6: continue
            
            is_elective = item[5]
            if is_elective:
                # Electives MUST be preserved as 9-tuples for the UI checkboxes to work
                # UI truth relies on indices 5 (is_elec) and 8 (pool_codes)
                final_data.append(item)
            else:
                # Cores are stripped to 5-tuple for simpler rendering logic
                # (day, start, end, display, extra)
                final_data.append(self._strip_for_regular_view(item))
        
        return final_data
