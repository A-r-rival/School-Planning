# -*- coding: utf-8 -*-
"""
Schedule Controller - MVC Pattern
Handles communication between Model and View
"""
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from models.schedule_model import ScheduleModel
    from views.schedule_view import ScheduleView
from views.calendar_view import CalendarView
from views.student_view import StudentView
from views.teacher_availability_view import TeacherAvailabilityView
from controllers.scheduler import ORToolsScheduler
from scripts.parse_curriculum import Regexes  # Import central Regex logic
from scripts import curriculum_data # Import data source
from PyQt5.QtWidgets import QMessageBox
from utils.schedule_merger import merge_course_strings, merge_consecutive_blocks


class ScheduleController:
    """
    Controller class for schedule management
    Handles communication between Model and View
    """
    
    def __init__(self, model: 'ScheduleModel', view: 'ScheduleView'):
        """
        Initialize controller with model and view
        
        Args:
            model: ScheduleModel instance
            view: ScheduleView instance
        """
        self.model = model
        self.view = view
        
        # Connect signals
        self._connect_model_signals()
        self._connect_view_signals()
        
        # Initialize view with existing data
        self._initialize_view()
        
        # Calendar View (Lazy initialization)
        self.calendar_view = None
    
    def _connect_model_signals(self):
        """Connect model signals to view methods"""
        # Connect model signals to view updates
        self.model.course_added.connect(self.view.add_course_to_list)
        self.model.course_removed.connect(self.view.remove_course_from_list)
        self.model.error_occurred.connect(self.view.show_error_message)
    
    def _connect_view_signals(self):
        """Connect view signals to controller methods"""
        # Connect view signals to controller methods
        self.view.course_add_requested.connect(self.handle_add_course)
        self.view.course_remove_requested.connect(self.handle_remove_course)
        self.view.faculty_add_requested.connect(self.handle_add_faculty)
        self.view.department_add_requested.connect(self.handle_add_department)
        self.view.open_calendar_requested.connect(self.open_calendar_view)
        self.view.open_student_view_requested.connect(self.open_student_view)
        self.view.open_teacher_availability_requested.connect(self.open_teacher_availability_view)
        self.view.generate_schedule_requested.connect(self.generate_automatic_schedule)
        self.view.filter_changed.connect(self.handle_schedule_view_filter)
    
    def _initialize_view(self):
        """Initialize view with existing data from model"""
        # Load existing courses
        courses = self.model.get_all_courses()
        self.view.display_courses(courses)
        
        # Load teachers for autocomplete
        teachers = self.model.get_teachers()
        self.view.update_teacher_completer(teachers)

        # Initialize Filters
        facs = self.model.get_faculties()
        self.view.update_filter_combo("faculty", facs)
    
    def handle_add_course(self, course_data: dict):
        """
        Handle add course request from view
        
        Args:
            course_data: Dictionary containing course information
        """
        # Convert dict to CourseInput entity
        from models.entities import CourseInput
        
        try:
            course_input = CourseInput(
                ders=course_data['ders'],
                hoca=course_data['hoca'],
                gun=course_data['gun'],
                baslangic=course_data['baslangic'],
                bitis=course_data['bitis']
            )
        except (KeyError, ValueError) as e:
            # Validation error - show to user
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self.view, "Hata", f"Geçersiz ders bilgisi: {e}")
            return
        
        # Model will handle validation and database operations
        success = self.model.add_course(course_input)
        
        if success:
            # Clear inputs on successful addition
            self.view.clear_inputs()
            
            # Update teacher completer with new teacher if needed
            teachers = self.model.get_teachers()
            self.view.update_teacher_completer(teachers)
    
    def handle_remove_course(self, course_info: str):
        """
        Handle remove course request from view
        
        Args:
            course_info: Course information string
        """
        # Model will handle database operations
        success = self.model.remove_course(course_info)
        
        if success:
            # Update teacher completer after removal
            teachers = self.model.get_teachers()
            self.view.update_teacher_completer(teachers)
    
    def handle_add_faculty(self, faculty_name: str):
        """
        Handle add faculty request from view
        
        Args:
            faculty_name: Name of the faculty to add
        """
        faculty_id = self.model.add_faculty(faculty_name)
        
        if faculty_id:
            self.view.show_success_message(f"Fakülte başarıyla eklendi! ID: {faculty_id}")
        # Error message will be shown by model signal if failed
    
    def handle_add_department(self, faculty_id: int, department_name: str):
        """
        Handle add department request from view
        
        Args:
            faculty_id: Faculty ID (ignored, will get from dialog)
            department_name: Department name (ignored, will get from dialog)
        """
        # First, show faculty selection dialog
        faculties = self.model.get_faculties()
        ok, selected_faculty_id = self.view.show_faculty_selection_dialog(faculties)
        
        if not ok:
            return  # User cancelled
        
        # Then, show department name input dialog
        ok, department_name = self.view.show_department_input_dialog()
        
        if not ok or not department_name:
            return  # User cancelled or empty name
        
        # Add department using model
        department_id = self.model.add_department(selected_faculty_id, department_name)
        
        if department_id:
            self.view.show_success_message(f"Bölüm başarıyla eklendi! ID: {department_id}")
        # Error message will be shown by model signal if failed
    
    def refresh_data(self):
        """Refresh all data from model to view"""
        # Reload courses
        courses = self.model.get_all_courses()
        courses = merge_course_strings(courses) # Merge blocks
        self.view.display_courses(courses)
        
        # Reload teachers
        teachers = self.model.get_teachers()
        self.view.update_teacher_completer(teachers)
    
    def close_application(self):
        """Handle application close event"""
        # Close database connections through model
        self.model.close_connections()
    
    # Additional controller methods for future extensions
    
    def export_schedule(self, format_type: str = "text"):
        """
        Export schedule in specified format
        
        Args:
            format_type: Export format ('text', 'csv', 'json')
        """
        # This can be implemented later for export functionality
        courses = self.model.get_all_courses()
        # Implementation would depend on format_type
        pass
    
    def import_schedule(self, file_path: str):
        """
        Import schedule from file
        
        Args:
            file_path: Path to import file
        """
        # This can be implemented later for import functionality
        pass
    
    def validate_schedule(self) -> list:
        """
        Validate entire schedule for conflicts and issues
        
        Returns:
            List of validation issues
        """
        # This can be implemented later for comprehensive validation
        issues = []
        # Implementation would check for various conflicts and issues
        return issues
    
    def get_statistics(self) -> dict:
        """
        Get schedule statistics
        
        Returns:
            Dictionary with statistics
        """
        courses = self.model.get_all_courses()
        teachers = self.model.get_teachers()
        
        stats = {
            'total_courses': len(courses),
            'total_teachers': len(teachers),
            'days_with_classes': len(set(course.split(' - ')[2].split(' ')[0] for course in courses)),
            'courses_per_day': {}
        }
        
        # Calculate courses per day
        for course in courses:
            parts = course.split(' - ')
            if len(parts) >= 3:
                day = parts[2].split(' ')[0]
                stats['courses_per_day'][day] = stats['courses_per_day'].get(day, 0) + 1
        
        return stats
        return stats

    def open_calendar_view(self):
        """Open the weekly calendar view"""
        if not self.calendar_view:
            self.calendar_view = CalendarView()
            self.calendar_view.filter_changed.connect(self.handle_calendar_filter)
            
        # Populate initial filters based on current view type
        current_view = self.calendar_view.view_type_combo.currentText()
        self.handle_calendar_filter("type_changed", {"type": current_view})
        
        self.calendar_view.show()
        
    # Merging utilities moved to utils/schedule_merger.py
        
    def handle_schedule_view_filter(self, filters):
        """Handle filter changes from ScheduleView"""
        faculty_id = filters.get("faculty_id")
        dept_id = filters.get("dept_id")
        year = filters.get("year")
        day = filters.get("day")
        
        # 1. Update Departments if Faculty changed (and Dept is None)
        if faculty_id and not dept_id:
             # Fetch depts
             items = self.model.get_departments_by_faculty(faculty_id)
             # Add "Ortak Dersler" option
             items.append((-1, "Ortak Dersler"))
             self.view.update_filter_combo("dept", items)
             # Do NOT return, proceed to filter list with faculty_id

        # 2. Filter List
        courses = []
        if faculty_id:
             if dept_id:
                 if dept_id == -1:
                     # "Ortak Dersler": Fetch all for now (simulated)
                     courses = self.model.get_courses_by_faculty(faculty_id, year, day)
                 else:
                     # Specific Dept
                     courses = self.model.get_courses_by_department(dept_id, year, day)
             else:
                 # Faculty Selected, Dept = "Tüm Bölümler"
                 courses = self.model.get_courses_by_faculty(faculty_id, year, day)
        else:
             # No Faculty Selected -> Show All Courses (Ders_Programi)
             all_courses = self.model.get_all_courses()
             
             # Apply Day Filter (Client-side for 'All Courses' view)
             if day:
                 print(f"DEBUG: Filtering for day: {day}")
                 courses = [c for c in all_courses if f"({day}" in c]
             else:
                 courses = all_courses
             
        # 3. Apply Text Filters (Client-side)
        search_text = filters.get("search_text", "").lower()
        teacher_text = filters.get("teacher_text", "").lower()
        
        if search_text or teacher_text:
            filtered_courses = []
            for course_str in courses:
                if search_text and search_text not in course_str.lower():
                    continue
                    
                if teacher_text and teacher_text not in course_str.lower():
                     continue
                
                filtered_courses.append(course_str)
            courses = filtered_courses
        
        # 4. Apply Elective/Core Filters
        only_elective = filters.get("only_elective", False)
        only_core = filters.get("only_core", False)
        
        # If both checked or neither checked, show all
        if only_elective and not only_core:
            # Show only electives - check for "Seçmeli" in course string
            courses = [c for c in courses if "seçmeli" in c.lower()]
        elif only_core and not only_elective:
            # Show only cores (not seçmeli)
            courses = [c for c in courses if "seçmeli" not in c.lower()]
        # else: show all (both checked or neither checked)

        # Merge consecutive blocks
        courses = merge_course_strings(courses)
        
        self.view.display_courses(courses)

    def handle_calendar_filter(self, event_type, data):
        """Handle filter changes from calendar view"""
        if event_type == "type_changed":
            view_type = data["type"]
            if view_type == "Öğretmen":
                items = self.model.get_all_teachers_with_ids()
                self.calendar_view.update_filter_options(1, items)
            elif view_type == "Derslik":
                items = self.model.get_all_classrooms_with_ids()
                self.calendar_view.update_filter_options(1, items)
            elif view_type == "Öğrenci Grubu":
                print("DEBUG: Loading Student Group view filters")
                items = self.model.get_faculties()
                print(f"DEBUG: Loaded {len(items)} faculties")
                self.calendar_view.update_filter_options(1, items)
                
        elif event_type == "filter_selected":
            # Handle specific selections
            schedule_data = []
            
            if "teacher_id" in data and data["teacher_id"]:
                raw_schedule = self.model.get_schedule_by_teacher(data["teacher_id"])
                # Model: (day, start, end, course, room, code, type)
                for item in raw_schedule:
                    if len(item) == 7:
                        day, start, end, course, room, code, ders_tipi = item
                        tip_label = ders_tipi if ders_tipi else "?"
                        display_course = f"[{code}] {course} ({tip_label})"
                        room_label = room if room else "Belirsiz"
                        extra = f"Oda: {room_label}"
                        # Pad with is_elective=False, real_course_name
                        schedule_data.append((day, start, end, display_course, extra, False, course))
                    elif len(item) == 6:  # Fallback for old data without type
                        day, start, end, course, room, code = item
                        display_course = f"[{code}] {course}"
                        room_label = room if room else "Belirsiz"
                        extra = f"Oda: {room_label}"
                        schedule_data.append((day, start, end, display_course, extra, False, course))
                    else:
                        schedule_data.append(item)
                
            elif "classroom_id" in data and data["classroom_id"]:
                raw_schedule = self.model.get_schedule_by_classroom(data["classroom_id"])
                # Model: (day, start, end, course, teacher, code, type)
                for item in raw_schedule:
                    if len(item) == 7:
                        day, start, end, course, teacher, code, ders_tipi = item
                        tip_label = ders_tipi if ders_tipi else "?"
                        display_course = f"[{code}] {course} ({tip_label})"
                        teacher_label = teacher if teacher else "Belirsiz"
                        extra = f"Öğretmen: {teacher_label}"
                        # Pad with is_elective=False, real_course_name
                        schedule_data.append((day, start, end, display_course, extra, False, course))
                    elif len(item) == 6:  # Fallback
                        day, start, end, course, teacher, code = item
                        display_course = f"[{code}] {course}"
                        teacher_label = teacher if teacher else "Belirsiz"
                        extra = f"Öğretmen: {teacher_label}"
                        schedule_data.append((day, start, end, display_course, extra, False, course))
                    else:
                        schedule_data.append(item)
                
            elif "faculty_id" in data:
                # If only faculty selected, update departments
                if "dept_id" not in data or not data["dept_id"]:
                    print(f"DEBUG: Fetching departments for faculty {data['faculty_id']}")
                    items = self.model.get_departments_by_faculty(data["faculty_id"])
                    
                    # --- ADD ORTAK DERSLER ---
                    items.append((-1, "Ortak Dersler"))
                    # -------------------------
                    
                    print(f"DEBUG: Found {len(items)} departments (inc. Ortak)")
                    self.calendar_view.update_filter_options(2, items)
                    
                # If dept selected and year selected, fetch schedule
                elif "year" in data and data["year"]: # Year might be string "1", "2"...
                     # Validation: Ensure year is digits (not 'Seçiniz...')
                     if not str(data["year"]).isdigit():
                         # print(f"DEBUG: Invalid year selected: {data['year']}")
                         return

                     print(f"DEBUG: Fetching schedule for dept {data['dept_id']} year {data['year']}")
                     
                     # Ortak Dersler Handling
                     department_id = int(data['dept_id']) 
                     
                     
                     if department_id == -1:
                         # Fetch Common Courses Schedule
                         raw_schedule = self.model.get_schedule_for_faculty_common(data["faculty_id"], int(data["year"]))
                     else:
                         raw_schedule = self.model.get_schedule_by_student_group(department_id, int(data["year"]))
                     
                     print(f"DEBUG: Raw schedule fetched. Count: {len(raw_schedule)}")
                     if raw_schedule:
                         print(f"DEBUG: First item sample: {raw_schedule[0]}")
                     
                     # Model: (day, start, end, course, teacher, room, code)
                     schedule_data = []
                     for idx, item in enumerate(raw_schedule):
                          try:
                              if len(item) == 8: # New format with ders_tipi
                                  day, start, end, course, teacher, room, code, ders_tipi = item
                                  tip_label = ders_tipi if ders_tipi else "?"
                                  display_course = f"[{code}] {course} ({tip_label})"
                                  room_label = room if room else "Belirsiz"
                                  teacher_label = teacher if teacher else "Belirsiz"
                                  extra_info = f"Öğretmen: {teacher_label}\nOda: {room_label}"
                                  
                                  
                                  # Check elective and get pool codes
                                  # Strategy: Look up in curriculum_data first (Truth), then fallback to Regex/Name
                                  
                                  # 1. Determine Dept Name from ID if available
                                  dept_name_for_lookup = None
                                  if "dept_id" in data and data["dept_id"] and int(data["dept_id"]) != -1:
                                       dept_name_for_lookup = self.model.get_department_name(int(data["dept_id"]))
                                  # If not available (e.g. Teacher View), we might try to infer or skip specific pool lookup
                                  
                                  pool_codes = []
                                  is_elective = False
                                  
                                  # 2. Look up in curriculum_data
                                  if dept_name_for_lookup:
                                       dept_data = curriculum_data.DEPARTMENTS_DATA.get(dept_name_for_lookup)
                                       # The key in curriculum_data.py is 'pool_codes', not 'pools'
                                       if dept_data and 'pool_codes' in dept_data:
                                           
                                           # Clean name from " (Seçmeli)" suffix for lookup tests
                                           # Also remove square brackets if internal code puts them? No, usually not.
                                           clean_name = course.split(" (S")[0].strip()
                                           
                                           for p_code_key, p_course_names in dept_data['pool_codes'].items():
                                                # p_course_names is a list of STRINGS (course names)
                                                for db_name in p_course_names:
                                                     # db_name is already the course name string
                                                     # Robust check: case-insensitive, strip whitespace
                                                     # Also check if one contains the other (e.g. "Makine Öğrenmesi" vs "Makine Öğrenmesi (Seçmeli)")
                                                     if db_name.lower().strip() == clean_name.lower().strip() or \
                                                        db_name.lower().strip() in clean_name.lower().strip() or \
                                                        clean_name.lower().strip() in db_name.lower().strip():
                                                          pool_codes.append(p_code_key)
                                                          is_elective = True
                                                          break
                                  
                                  # 3. Fallback: If not found in curriculum_data (or no dept context), use Regex/Name
                                  if not is_elective:
                                      # Use Regex for robust detection of pool codes from the COURSE CODE string
                                      pool_code_match = Regexes.pool_code.search(code)
                                      if pool_code_match:
                                          is_elective = True
                                          # Extract known types
                                          upper_code = code.upper()
                                          if upper_code.startswith("ZSD"): pool_codes.append("ZSD")
                                          elif upper_code.startswith("ÜSD") or upper_code.startswith("USD"): pool_codes.append("ÜSD")
                                          elif upper_code.startswith("GSD"): pool_codes.append("GSD")
                                          elif "SD" in upper_code: pool_codes.append("SD")
                                      elif "seçmeli" in course.lower() or "sdi" in code.lower() or "gsd" in code.lower():
                                          is_elective = True
                                          # No default pool assigned
                                  
                                  # Deduplicate validation
                                  pool_codes = sorted(list(set(pool_codes)))
                                  
                                  if "CSE301" in code:
                                      print(f"DEBUG: Processing CSE301. Dept: {dept_name_for_lookup}")
                                      print(f"DEBUG: Clean Name: '{clean_name}'")
                                      print(f"DEBUG: Found Pools: {pool_codes}")
                                      print(f"DEBUG: is_elective: {is_elective}")
                                  
                                  schedule_data.append((day, start, end, display_course, extra_info, is_elective, course, code, pool_codes))
         
                              elif len(item) == 7:
                                  day, start, end, course, teacher, room, code = item
                                  display_course = f"[{code}] {course}"
                                  room_label = room if room else "Belirsiz"
                                  teacher_label = teacher if teacher else "Belirsiz"
                                  extra_info = f"Öğretmen: {teacher_label}\nOda: {room_label}"
                                  
                                  is_elective = "seçmeli" in course.lower() or "sdi" in code.lower() or "gsd" in code.lower()
                                  schedule_data.append((day, start, end, display_course, extra_info, is_elective, course))
                              elif len(item) == 6: # Legacy/Fallback
                                  day, start, end, course, teacher, room = item
                                  room_label = room if room else "Belirsiz"
                                  teacher_label = teacher if teacher else "Belirsiz"
                                  extra_info = f"Öğretmen: {teacher_label}\nOda: {room_label}"
                                  
                                  is_elective = "seçmeli" in course.lower()
                                  schedule_data.append((day, start, end, course, extra_info, is_elective, course))
                              else:
                                  schedule_data.append(item)
                          except Exception as e:
                              print(f"ERROR processing item {idx}: {item} - Error: {e}")
                              import traceback
                              traceback.print_exc()
                              continue
                              
                          if False: # Placeholder to maintain indentation flow if needed
                              pass
            
            if schedule_data:
                # Merge consecutive blocks
                schedule_data = merge_consecutive_blocks(schedule_data)
                # Post-process for Student Group View mainly
                if "dept_id" in data and data["dept_id"]:
                    final_data = []
                    # Group by (day, start, end)
                    import collections
                    grouped = collections.defaultdict(list)
                    
                    show_electives = data.get("show_electives", False)
                    
                    for item in schedule_data:
                        # item is header + (is_elective, raw_name)
                        if len(item) >= 7:
                            key = (item[0], item[1], item[2]) # day, start, end
                            grouped[key].append(item)
                        else:
                             final_data.append(item)
                             
                    for key, items in grouped.items():
                        electives = [x for x in items if len(x) >= 6 and x[5]]
                        cores = [x for x in items if not (len(x) >= 6 and x[5])]
                        
                        # Add all cores
                        for c in cores:
                            final_data.append(c[:5]) # Strip flags
                            
                        # Handle Electives
                        if electives:
                            # PASS ALL ELECTIVE DATA TO CALENDAR VIEW
                            # The View will handle filtering based on checkboxes!
                            for e in electives:
                                # Ensure we pass the full extended data tuple (9 items)
                                # (day, start, end, display, extra, is_e, real_name, code, pools)
                                # item may have more than 9, but we need at least up to pools
                                if len(e) >= 9:
                                    final_data.append(e[:9])
                                else:
                                    # Fallback if somehow shorter? Should not happen with new loop
                                    final_data.append(e) 
                                
                    self.calendar_view.display_schedule(final_data)
                else:
                    # Regular view (Teacher/Room) - just strip flags
                    clean_data = [x[:5] for x in schedule_data]
                    self.calendar_view.display_schedule(clean_data)
                    
                self.calendar_view.show()
            else:
                self.calendar_view.display_schedule([])

    def open_student_view(self):
        """Open the student management view"""
        if not hasattr(self, 'student_view') or self.student_view is None:
            self.student_view = StudentView()
            self.student_view.filter_changed.connect(self.handle_student_filter)
            self.student_view.student_selected.connect(self.handle_student_selection)
            
            faculties = self.model.get_all_faculties()
            departments = self.model.get_all_departments()
            self.student_view.set_filter_options(faculties, departments)
            
            # Initial load (all students)
            self.handle_student_filter({})
            
        self.student_view.showMaximized()
        self.student_view.raise_()

    def handle_student_filter(self, filters):
        """Handle filter changes from StudentView"""
        students = self.model.get_students(filters)
        self.student_view.update_student_list(students)

    def handle_student_selection(self, student_id):
        """Handle student selection to show transcript"""
        grades = self.model.get_student_grades(student_id, show_history=True)
        self.student_view.update_transcript(grades)

    # Teacher Availability Methods
    def open_teacher_availability_view(self):
        """Open teacher availability dialog"""
        # Ensure only one instance exists
        if hasattr(self, 'availability_view') and self.availability_view is not None:
            try:
                self.availability_view.close()
                self.availability_view.deleteLater()
            except:
                pass
        
        teachers = self.model.get_all_teachers_with_ids()
        self.availability_view = TeacherAvailabilityView(self.view, teachers)
        self.availability_view.set_controller(self)
        self.availability_view.show()
        
    def load_teacher_availability(self, teacher_id: int):
        """Load availability for specific teacher"""
        # Updated to use combined availability (Fixes previous partial update)
        data = self.model.get_combined_availability(teacher_id)
        self.availability_view.update_table(data)
        
        # Span is now handled in the Add Dialog, not set on the main view
        # span = self.model.get_teacher_span(teacher_id)
        # self.availability_view.set_span(span)

    def handle_teacher_span_change(self, teacher_id: int, span: int):
        """Handle teacher span preference change"""
        self.model.update_teacher_span(teacher_id, span)

    def load_all_teacher_availability(self):
        """Load availability for ALL teachers"""
        # New model method returns list of dicts
        data = self.model.get_combined_availability() 
        self.availability_view.update_table(data)

        
    def add_teacher_unavailability(self, teacher_id: int, day: str, start: str, end: str, description: str = ""):
        """Add unavailability slot"""
        success = self.model.add_teacher_unavailability(teacher_id, day, start, end, description)
        if success:
            if self.availability_view.teacher_combo.currentData() == -1:
                 self.load_all_teacher_availability()
            else:
                 self.load_teacher_availability(teacher_id)
            QMessageBox.information(self.availability_view, "Başarılı", "Müsaitlik eklendi.")

    def update_teacher_unavailability(self, u_id: int, teacher_id: int, day: str, start: str, end: str, description: str = ""):
        """Update unavailability slot"""
        success = self.model.update_teacher_unavailability(u_id, teacher_id, day, start, end, description)
        if success:
            if self.availability_view.teacher_combo.currentData() == -1:
                 self.load_all_teacher_availability()
            else:
                 self.load_teacher_availability(teacher_id)
            QMessageBox.information(self.availability_view, "Başarılı", "Güncelleme yapıldı.")
        else:
            QMessageBox.warning(self.availability_view, "Hata", "Bu saat aralığı zaten ekli veya çakışıyor!")
            
    def handle_delete_request(self, item_type: str, item_id: int):
        """Handle deletion of either a slot or a span"""
        success = False
        if item_type == 'slot':
            success = self.model.remove_teacher_unavailability(item_id)
        elif item_type == 'span':
            # item_id here is actually teacher_id for span
            success = self.model.update_teacher_span(item_id, 0)
            
        if success:
             # Refresh view logic
            teacher_id = self.availability_view.teacher_combo.currentData()
            if teacher_id == -1:
                self.load_all_teacher_availability()
            else:
                self.load_teacher_availability(teacher_id)
                
    # Keep wrapper for compatibility or direct slot deletion if needed
    def remove_teacher_unavailability(self, unavailability_id: int):
         self.handle_delete_request('slot', unavailability_id)
            
    # Automatic Scheduler
    def generate_automatic_schedule(self):
        """Run the automatic scheduler"""
        reply = QMessageBox.question(
            self.view, 
            "Otomatik Program", 
            "Mevcut ders programı silinecek ve otomatik olarak yeniden oluşturulacak.\nDevam etmek istiyor musunuz?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                scheduler = ORToolsScheduler(self.model)
                success = scheduler.solve()
                
                if success:
                    QMessageBox.information(self.view, "Başarılı", "Ders programı başarıyla oluşturuldu!")
                    self.refresh_data()
                else:
                    QMessageBox.warning(self.view, "Başarısız", "Uygun bir program bulunamadı!\nKısıtlamaları kontrol edin.")
            except Exception as e:
                QMessageBox.critical(self.view, "Hata", f"Program oluşturulurken hata: {str(e)}")

    # Merging utilities moved to utils/schedule_merger.py
