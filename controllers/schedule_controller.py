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
                # If dept selected and year selected, fetch schedule
                elif "year" in data and data["year"]:
                     schedule_data = self.model.get_schedule_by_student_group(data["dept_id"], int(data["year"]))
            
            if schedule_data:
                self.calendar_view.display_schedule(schedule_data)
            else:
                # Clear if no valid selection or no data
                self.calendar_view.display_schedule([])
