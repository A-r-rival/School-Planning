# -*- coding: utf-8 -*-
"""
Schedule Controller - MVC Pattern
Handles communication between Model and View
"""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.schedule_model import ScheduleModel
    from views.schedule_view import ScheduleView
from views.calendar_view import CalendarView
from views.student_view import StudentView
from views.teacher_availability_view import TeacherAvailabilityView
from controllers.scheduler import ORToolsScheduler
from PyQt5.QtWidgets import QMessageBox


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
    
    def _initialize_view(self):
        """Initialize view with existing data from model"""
        # Load existing courses
        courses = self.model.get_all_courses()
        self.view.display_courses(courses)
        
        # Load teachers for autocomplete
        teachers = self.model.get_teachers()
        self.view.update_teacher_completer(teachers)
    
    def handle_add_course(self, course_data: dict):
        """
        Handle add course request from view
        
        Args:
            course_data: Dictionary containing course information
        """
        # Model will handle validation and database operations
        success = self.model.add_course(course_data)
        
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
            
        # Populate initial filters (Teachers)
        self.handle_calendar_filter("type_changed", {"type": "Öğretmen"})
        
        self.calendar_view.show()
        
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
                items = self.model.get_faculties()
                self.calendar_view.update_filter_options(1, items)
                
        elif event_type == "filter_selected":
            # Handle specific selections
            schedule_data = []
            
            if "teacher_id" in data and data["teacher_id"]:
                schedule_data = self.model.get_schedule_by_teacher(data["teacher_id"])
                
            elif "classroom_id" in data and data["classroom_id"]:
                schedule_data = self.model.get_schedule_by_classroom(data["classroom_id"])
                
            elif "faculty_id" in data:
                # If only faculty selected, update departments
                if "dept_id" not in data or not data["dept_id"]:
                    items = self.model.get_departments_by_faculty(data["faculty_id"])
                    self.calendar_view.update_filter_options(2, items)
        teachers = self.model.get_teachers()
        self.view.update_teacher_completer(teachers)
    
    def handle_add_course(self, course_data: dict):
        """
        Handle add course request from view
        
        Args:
            course_data: Dictionary containing course information
        """
        # Model will handle validation and database operations
        success = self.model.add_course(course_data)
        
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
            
        # Populate initial filters (Teachers)
        self.handle_calendar_filter("type_changed", {"type": "Öğretmen"})
        
        self.calendar_view.show()
        
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
                schedule_data = self.model.get_schedule_by_teacher(data["teacher_id"])
                
            elif "classroom_id" in data and data["classroom_id"]:
                schedule_data = self.model.get_schedule_by_classroom(data["classroom_id"])
                
            elif "faculty_id" in data:
                # If only faculty selected, update departments
                if "dept_id" not in data or not data["dept_id"]:
                    print(f"DEBUG: Fetching departments for faculty {data['faculty_id']}")
                    items = self.model.get_departments_by_faculty(data["faculty_id"])
                    print(f"DEBUG: Found {len(items)} departments")
                    self.calendar_view.update_filter_options(2, items)
                # If dept selected and year selected, fetch schedule
                elif "year" in data and data["year"]:
                     print(f"DEBUG: Fetching schedule for dept {data['dept_id']} year {data['year']}")
                     raw_schedule = self.model.get_schedule_by_student_group(data["dept_id"], int(data["year"]))
                     # Transform 6-item tuple to 5-item tuple for view
                     # Model returns: (day, start, end, course, teacher, room)
                     # View expects: (day, start, end, course, extra_info)
                     schedule_data = []
                     for item in raw_schedule:
                         if len(item) == 6:
                             day, start, end, course, teacher, room = item
                             extra_info = f"{teacher}\n({room})"
                             schedule_data.append((day, start, end, course, extra_info))
                         else:
                             # Fallback if format is different
                             schedule_data.append(item)
            
            if schedule_data:
                # Update view
                self.calendar_view.display_schedule(schedule_data)
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
            
        self.student_view.show()
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
        teachers = self.model.get_all_teachers_with_ids()
        self.availability_view = TeacherAvailabilityView(self.view, teachers)
        self.availability_view.set_controller(self)
        self.availability_view.show()
        
    def load_teacher_availability(self, teacher_id: int):
        """Load availability for a teacher"""
        data = self.model.get_teacher_unavailability(teacher_id)
        self.availability_view.update_table(data)
        
    def add_teacher_unavailability(self, teacher_id: int, day: str, start: str, end: str):
        """Add unavailability slot"""
        success = self.model.add_teacher_unavailability(teacher_id, day, start, end)
        if success:
            self.load_teacher_availability(teacher_id)
        else:
            QMessageBox.warning(self.availability_view, "Hata", "Bu saat aralığı zaten ekli veya çakışıyor!")
            
    def remove_teacher_unavailability(self, unavailability_id: int):
        """Remove unavailability slot"""
        success = self.model.remove_teacher_unavailability(unavailability_id)
        if success:
            # We need to refresh the current teacher's list. 
            # But we don't have the teacher_id here directly.
            # We can get it from the view's current selection.
            teacher_id = self.availability_view.teacher_combo.currentData()
            self.load_teacher_availability(teacher_id)
            
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
