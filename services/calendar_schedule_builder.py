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
            try:
                self.model.c.execute("SELECT ad || ' ' || soyad FROM Ogretmenler WHERE ogretmen_num = ?", (data["teacher_id"],))
                row = self.model.c.fetchone()
                metadata['title'] = f"Öğretmen: {row[0]}" if row else "Öğretmen"
            except: pass
        
        # Classroom view
        elif data.get("classroom_id"):
            schedule_data = self._build_classroom_schedule(data["classroom_id"])
            try:
                self.model.c.execute("SELECT derslik_adi FROM Derslikler WHERE derslik_num = ?", (data["classroom_id"],))
                row = self.model.c.fetchone()
                metadata['title'] = f"Oda: {row[0]}" if row else "Oda"
            except: pass
        
        # Student group view (faculty-based or department-based)
        elif data.get("faculty_id") or data.get("dept_id"):
            schedule_data = self._build_student_group_schedule(data)
            try:
                if int(data.get("dept_id", 0)) == -1:
                    metadata['title'] = f"Ortak Dersler ({data.get('year')}. Sınıf)"
                else:
                    self.model.c.execute("SELECT bolum_adi FROM Bolumler WHERE bolum_id = ?", (data["dept_id"],))
                    row = self.model.c.fetchone()
                    metadata['title'] = f"Bölüm: {row[0]} {data.get('year')}. Sınıf" if row else "Öğrenci Grubu"
            except: pass
            
        # Inject the explicit semester from data if provided
        if "semester" in data:
            metadata["semester"] = data["semester"]
        
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
        """Strip to display format for teacher/classroom views, keeping program_id at the end."""
        # Create a new tuple with the first 5 elements, pad with None, and append program_id if exists
        program_id = item[10] if len(item) > 10 else None
        return item[:5] + (False, "", "", [], None, program_id)
    

    
    # ==================== Schedule Builders ====================
    
    def _build_teacher_schedule(self, teacher_id: int, versiyon_id=None) -> List[Tuple]:
        """
        Build schedule for teacher view.
        Returns normalized 9-tuples.
        """
        raw_schedule = self.model.get_teacher_schedule(teacher_id, versiyon_id=versiyon_id) if hasattr(self.model, 'get_teacher_schedule') else self.model.get_schedule_by_teacher(teacher_id)
        schedule_data = []
        
        # Fetch classes for tooltips
        program_ids = [item[-1] for item in raw_schedule if item[-1]]
        classes_map = self.model.get_classes_for_programs(program_ids) if hasattr(self.model, 'get_classes_for_programs') else {}
        
        # 1. Add booked courses
        for item in raw_schedule:
            if len(item) == 8:
                day, start, end, course, room, code, ders_tipi, program_id = item
                tip_label = ders_tipi if ders_tipi else "?"
                display_course = f"[{code}] {course} ({tip_label})"
                room_label = room if room else "Belirsiz"
                
                extra_lines = [f"Oda: {room_label}"]
                if program_id and classes_map.get(program_id):
                    extra_lines.append(f"Sınıflar: {classes_map[program_id]}")
                extra = "\n".join(extra_lines)
                
                # Normalize to 11-tuple (index 10 is program_id)
                schedule_data.append((
                    day, start, end, display_course, extra,
                    False, course, code, [], None, program_id
                ))
            elif len(item) == 7:  # Fallback
                day, start, end, course, room, code, program_id = item
                display_course = f"[{code}] {course}"
                room_label = room if room else "Belirsiz"
                
                extra_lines = [f"Oda: {room_label}"]
                if program_id and classes_map.get(program_id):
                    extra_lines.append(f"Sınıflar: {classes_map[program_id]}")
                extra = "\n".join(extra_lines)
                
                schedule_data.append((
                    day, start, end, display_course, extra,
                    False, course, code, [], None, program_id
                ))
        
        # 2. Add unavailability (restricted hours)
        unavailability = self.model.get_teacher_unavailability(teacher_id)
        # unavailability schema: (gun, baslangic, bitis, id, description, span, yil, donem)
        for gun, baslangic, bitis, u_id, desc, *rest in unavailability:
            schedule_data.append((
                gun, baslangic, bitis, "KISITLI / MÜSAİT DEĞİL", desc,
                False, "UNAVAILABLE", "", [], None, None
            ))
        
        return schedule_data
    
    def _build_classroom_schedule(self, classroom_id: int, versiyon_id=None) -> List[Tuple]:
        """
        Build schedule for classroom view.
        Returns normalized 9-tuples.
        """
        raw_schedule = self.model.get_room_schedule(classroom_id, versiyon_id=versiyon_id) if hasattr(self.model, 'get_room_schedule') else self.model.get_schedule_by_classroom(classroom_id)
        schedule_data = []
        
        # Fetch classes for tooltips
        program_ids = [item[-1] for item in raw_schedule if item[-1]]
        classes_map = self.model.get_classes_for_programs(program_ids) if hasattr(self.model, 'get_classes_for_programs') else {}
        
        for item in raw_schedule:
            if len(item) == 8:
                day, start, end, course, teacher, code, ders_tipi, program_id = item
                tip_label = ders_tipi if ders_tipi else "?"
                display_course = f"[{code}] {course} ({tip_label})"
                teacher_label = teacher if teacher else "Belirsiz"
                
                extra_lines = [f"Öğretmen: {teacher_label}"]
                if program_id and classes_map.get(program_id):
                    extra_lines.append(f"Sınıflar: {classes_map[program_id]}")
                extra = "\n".join(extra_lines)
                
                schedule_data.append((
                    day, start, end, display_course, extra,
                    False, course, code, [], None, program_id
                ))
            elif len(item) == 7:  # Fallback
                day, start, end, course, teacher, code, program_id = item
                display_course = f"[{code}] {course}"
                teacher_label = teacher if teacher else "Belirsiz"
                
                extra_lines = [f"Öğretmen: {teacher_label}"]
                if program_id and classes_map.get(program_id):
                    extra_lines.append(f"Sınıflar: {classes_map[program_id]}")
                extra = "\n".join(extra_lines)
                
                schedule_data.append((
                    day, start, end, display_course, extra,
                    False, course, code, [], None, program_id
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
        
        versiyon_id = data.get("versiyon_id")
        
        # Fetch schedule (common courses or department-specific)
        if department_id == -1:
            if faculty_id is None:
                return []
            raw_schedule = self.model.get_schedule_for_faculty_common(
                faculty_id, int(year), versiyon_id=versiyon_id
            )
        else:
            raw_schedule = self.model.get_schedule_by_student_group(
                department_id, int(year), versiyon_id=versiyon_id
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
            
        # Fetch classes for tooltips
        program_ids = [item[-1] for item in raw_schedule if item[-1]]
        classes_map = self.model.get_classes_for_programs(program_ids) if hasattr(self.model, 'get_classes_for_programs') else {}
        
        for idx, item in enumerate(raw_schedule):
            try:
                # DB student group format (new 12-column format)
                if len(item) == 12:
                    day, start, end, course_name, teacher, room, code, ders_tipi, pool_data, is_pool, instance, program_id = item
                    
                    tip_label = ders_tipi if ders_tipi else "?"
                    display_course = f"[{code}] {course_name} ({tip_label})"
                    
                    room_label = room if room else "Belirsiz"
                    teacher_label = teacher if teacher else "Belirsiz"
                    
                    extra_lines = []
                    extra_lines.append(f"Öğretmen: {teacher_label}")
                    extra_lines.append(f"Oda: {room_label}")
                    if instance:
                        extra_lines.append(f"Şube {instance}")
                    if program_id and classes_map.get(program_id):
                        extra_lines.append(f"Sınıflar: {classes_map[program_id]}")
                        
                    extra_info = "\n".join(extra_lines)
                    
                    is_elective = bool(is_pool)
                    
                    if isinstance(pool_data, list):
                        p_list = pool_data
                    elif pool_data:
                        p_list = [x.strip() for x in str(pool_data).split(',') if x.strip()]
                    else:
                        p_list = []
                        
                    if not is_elective:
                        is_elective, p_list_detected = self._detect_elective(course_name, code, dept_name_for_lookup)
                        if is_elective and not p_list:
                            p_list = p_list_detected
                            
                    schedule_data.append((day, start, end, display_course, extra_info, is_elective, course_name, code, p_list, None, program_id))
                
                # Faculty Common courses format
                elif len(item) == 11:
                    day, start, end, course_disp, extra, is_elec, course_name, code, pool_data, is_pool, program_id = item
                    
                    if isinstance(pool_data, list):
                        p_list = pool_data
                    elif pool_data:
                        p_list = [x.strip() for x in str(pool_data).split(',') if x.strip()]
                    else:
                        p_list = []
                        
                    schedule_data.append((day, start, end, course_disp, extra, bool(is_elec), course_name, code, p_list, None, program_id))                
                # Pre-normalized 10-tuple format
                elif len(item) == 10:
                    day, start, end, course_disp, extra, is_elec, course_name, code, pool_data, program_id = item
                    
                    if isinstance(pool_data, list):
                        p_list = pool_data
                    elif pool_data:
                        p_list = [x.strip() for x in str(pool_data).split(',') if x.strip()]
                    else:
                        p_list = []
                        
                    schedule_data.append((day, start, end, course_disp, extra, bool(is_elec), course_name, code, p_list, None, program_id))
                elif len(item) == 8:  # Old format with ders_tipi
                    day, start, end, course, teacher, room, code, ders_tipi = item
                    tip_label = ders_tipi if ders_tipi else "?"
                    display_course = f"[{code}] {course} ({tip_label})"
                    room_label = room if room else "Belirsiz"
                    teacher_label = teacher if teacher else "Belirsiz"
                    
                    extra_lines = [f"Öğretmen: {teacher_label}", f"Oda: {room_label}"]
                    # No program_id in this old 8-tuple format, unfortunately
                    extra_info = "\n".join(extra_lines)
                    
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
                    
                    extra_lines = [f"Öğretmen: {teacher_label}", f"Oda: {room_label}"]
                    extra_info = "\n".join(extra_lines)
                    
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
                    
                    extra_lines = [f"Öğretmen: {teacher_label}", f"Oda: {room_label}"]
                    extra_info = "\n".join(extra_lines)
                    
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
