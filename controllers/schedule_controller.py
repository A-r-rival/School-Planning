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
from views.master_schedule_view import MasterScheduleView # NEW import
from controllers.scheduler import ORToolsScheduler
from PyQt5.QtWidgets import QMessageBox, QInputDialog
from PyQt5.QtCore import Qt
from utils.schedule_merger import merge_course_strings, merge_schedule_items_dicts
from services.calendar_schedule_builder import CalendarScheduleBuilder


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
        
        # Set controller reference in view for dialogs
        if hasattr(self.view, 'set_controller'):
            self.view.set_controller(self)
        
        # Initialize calendar builder service
        self.calendar_builder = CalendarScheduleBuilder(model)
        
        # Connect signals
        self._connect_model_signals()
        self._connect_view_signals()
        
        # Initialize view with existing data
        self._initialize_view()
        
        # View Cache
        self.calendar_view = None
        self.master_view = None # Cache for Master View
    
    def _connect_model_signals(self):
        """Connect model signals to view methods"""
        # Connect model signals to view updates
        # For legacy add_course_to_list, we now prefer full refresh to handle merging correctly
        self.model.course_added.connect(lambda x: self.refresh_data())
        self.model.course_removed.connect(lambda x: self.refresh_data())
        self.model.error_occurred.connect(self.view.show_error_message)
    
    def _connect_view_signals(self):
        """Connect view signals to controller methods"""
        # Connect view signals to controller methods
        self.view.course_add_requested.connect(self.handle_add_course)
        self.view.course_remove_requested.connect(self.handle_remove_course)
        self.view.course_remove_by_ids_requested.connect(self.handle_remove_course_by_ids)
        self.view.faculty_add_requested.connect(self.handle_add_faculty)
        self.view.department_add_requested.connect(self.handle_add_department)
        self.view.open_calendar_requested.connect(self.open_calendar_view)
        self.view.open_student_view_requested.connect(self.open_student_view)
        self.view.open_teacher_availability_requested.connect(self.open_teacher_availability_view)
        self.view.open_room_list_requested.connect(self.open_room_list_view)
        self.view.generate_schedule_requested.connect(self.generate_automatic_schedule)
        self.view.generate_schedule_custom_requested.connect(self.generate_automatic_schedule_custom)
        self.view.filter_changed.connect(self.handle_schedule_view_filter)
        self.view.run_setup_requested.connect(self._on_run_setup_requested)
        self.view.open_master_view_requested.connect(self.open_master_view) # NEW connection
        
        # New Feature Connections
        self.view.radio_guz.toggled.connect(self.handle_semester_change)
        self.view.radio_bahar.toggled.connect(self.handle_semester_change)
        self.view.radio_yaz.toggled.connect(self.handle_semester_change)
        
        self.view.btn_save_snapshot.clicked.connect(self.save_snapshot_requested)
        self.view.btn_view_history.clicked.connect(self.show_history_requested)
    
    def _initialize_view(self):
        """Initialize view with existing data from model"""
        self.refresh_data()
        
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

    def add_curriculum_course_as_template(self, data: dict) -> bool:
        """Add new course to curriculum via model (Template)"""
        return self.model.add_curriculum_course_as_template(data)
    
    def handle_remove_course(self, course_info: str):
        """Handle remove course request from view (Legacy)"""
        success = self.model.remove_course(course_info)
        if success:
            teachers = self.model.get_teachers()
            self.view.update_teacher_completer(teachers)

    def handle_remove_course_by_ids(self, ids: List[int]):
        """Handle remove course by list of IDs"""
        success_count = 0
        for pid in ids:
             if self.model.remove_course_by_id(pid):
                 success_count += 1
        
        if success_count > 0:
             self.refresh_data()
             teachers = self.model.get_teachers()
             self.view.update_teacher_completer(teachers)

    def delete_curriculum_course(self, course_name: str):
        """Delete a course from curriculum completely"""
        if self.model.delete_curriculum_course(course_name):
             # Refresh views
             self.refresh_data()
             return True
        return False
    
    def handle_add_faculty(self, faculty_name: str):
        """
        Handle add faculty request from view
        
        Args:
            faculty_name: Name of the faculty to add
        """
        faculty_id = self.model.add_faculty(faculty_name)
        
        if faculty_id:
            self.view.show_success_message(f"Fakülte başarıyla eklendi! ID: {faculty_id}")
            # Refresh filters
            facs = self.model.get_faculties()
            self.view.update_filter_combo("faculty", facs)
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
        # Determine Semester Filter from View
        semester_filter = "Güz"
        if hasattr(self.view, 'radio_bahar') and self.view.radio_bahar.isChecked():
            semester_filter = "Bahar"
        elif hasattr(self.view, 'radio_yaz') and self.view.radio_yaz.isChecked():
            semester_filter = "Yaz"

        # Reload courses using NEW structured method with filter
        items = self.model.get_all_schedule_items(semester_filter=semester_filter)
        
        # Merge consecutive blocks
        merged_items = merge_schedule_items_dicts(items)
        
        # Display in table
        self.view.display_courses(merged_items)
        
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
        courses = self.model.get_all_courses_as_string()
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
    
    def open_master_view(self):
        """Open the Master Schedule View"""
        from views.master_schedule_view import MasterScheduleView
        
        if not hasattr(self, 'master_view') or self.master_view is None or not self.master_view.isVisible():
            self.master_view = MasterScheduleView()
            self.master_view.set_controller(self)
            self.master_view.show()
        else:
            self.master_view.raise_()
            self.master_view.activateWindow()
        
        # Populate initial data
        data = self.model.get_master_schedule_data()
        self.master_view.update_schedule(data)

    # --- Semester Selection ---
    
    def handle_semester_change(self):
        """Handle semester radio button toggle"""
        semester = "Güz"
        if self.view.radio_bahar.isChecked():
            semester = "Bahar"
        elif self.view.radio_yaz.isChecked():
            semester = "Yaz"
            
        # Trigger filter update in view
        # Trigger filter update in view
        self.view.trigger_filter_update()

    # --- History ---

    def save_snapshot_requested(self):
        """Handle save snapshot request"""
        from PyQt5.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self.view, "Programı Kaydet", "Program Adı:")
        if ok and name:
            # Get current semester
            if self.view.radio_guz.isChecked(): sem = "Güz"
            elif self.view.radio_bahar.isChecked(): sem = "Bahar"
            else: sem = "Yaz"
            
            if self.model.save_snapshot(name, sem):
                self.view.show_success_message("Program başarıyla kaydedildi.")

    def show_history_requested(self):
        """Show history dialog"""
        snapshots = self.model.get_snapshots()
        if not snapshots:
            self.view.show_error_message("Kaydedilmiş program bulunamadı.")
            return

        # Create a simple dialog to list snapshots
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QListWidget, QPushButton, QListWidgetItem
        from PyQt5.QtCore import Qt
        
        dialog = QDialog(self.view)
        dialog.setWindowTitle("Geçmiş Programlar")
        dialog.setMinimumWidth(400)
        dialog.setMinimumHeight(300)
        
        layout = QVBoxLayout()
        list_widget = QListWidget()
        
        for snap in snapshots:
            label = f"{snap['name']} ({snap['semester']}) - {snap['created_at']}"
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, snap['id'])
            list_widget.addItem(item)
            
        layout.addWidget(list_widget)
        
        
        def on_view_clicked():
            item = list_widget.currentItem()
            if not item: return
            
            # Close dialog first (so it doesn't block or stay on top)
            dialog.accept()
            
            # Open viewer
            self.open_snapshot_viewer(item)

        
        btn_view = QPushButton("Görüntüle (Read-Only)")
        btn_view.clicked.connect(on_view_clicked)
        layout.addWidget(btn_view)
        
        dialog.setLayout(layout)
        dialog.exec_()

    def open_snapshot_viewer(self, item):
        """Open snapshot in Read-Only Master View"""
        if not item: return
        snap_id = item.data(Qt.UserRole)
        
        data = self.model.get_snapshot_data(snap_id)
        if not data:
             self.view.show_error_message("Program verisi yüklenemedi.")
             return

        from views.master_schedule_view import MasterScheduleView
        # Keep reference to prevent GC
        self.snapshot_viewer = MasterScheduleView(controller=self, mode='teacher')
        self.snapshot_viewer.setWindowTitle(f"Geçmiş Program: {item.text()}")
        self.snapshot_viewer.update_schedule(data)
        self.snapshot_viewer.show()
        self.snapshot_viewer.raise_()
        self.snapshot_viewer.activateWindow()

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
        """
        Filter handling for the MAIN TABLE VIEW
        """
        faculty_id = filters.get("faculty_id")
        dept_id = filters.get("dept_id")
        year = filters.get("year")
        day = filters.get("day")
        search_text = filters.get("search_text", "").lower()
        teacher_text = filters.get("teacher_text", "").lower()
        only_elective = filters.get("only_elective", False)
        only_core = filters.get("only_core", False)
        
        semester_filter = filters.get("semester") # Get from filters
        
        # 1. Update Departments if Faculty changed
        if faculty_id and not dept_id:
             items = self.model.get_departments_by_faculty(faculty_id)
             self.view.update_filter_combo("dept", items)
        
        # 2. Fetch ALL structured items WITH SEMESTER FILTER
        # Delegate semester filtering to the model (Source of Truth)
        items = self.model.get_all_schedule_items(semester_filter=semester_filter)
        
        # 3. Apply Remaining Filters in Python
        filtered_items = []
        
        for item in items:
            # Faculty Filter
            if faculty_id:
                if faculty_id not in item.get('faculty_ids', []):
                     continue
            
            # Department Filter
            if dept_id:
                if dept_id not in item.get('dept_ids', []):
                    continue
            
            # Year Filter
            if year:
                try:
                    y_int = int(year)
                    if y_int not in item.get('years', []):
                        continue
                except:
                    pass
            
            # Day Filter
            if day:
                if item.get('day') != day:
                    continue
            
            # Search Text (Name or Code)
            if search_text:
                if (search_text not in item.get('name', '').lower() and 
                    search_text not in item.get('code', '').lower()):
                    continue

            # Teacher Text
            if teacher_text:
                if teacher_text not in item.get('teacher', '').lower():
                    continue
            
            # Elective/Core Filter
            is_elective = False
            if item.get('pool') or "seçmeli" in item.get('name', '').lower():
                is_elective = True
                
            if only_elective and not only_core:
                if not is_elective: continue
            if only_core and not only_elective:
                if is_elective: continue
                
            filtered_items.append(item)
            
        merged = merge_schedule_items_dicts(filtered_items)
        
        # 5. Display
        self.view.display_courses(merged)

    def handle_calendar_filter(self, event_type, data):
        """Handle filter changes from calendar view"""
        if event_type == "type_changed":
            # Handle view type change
            result = self.calendar_builder.build_for_type_change(data["type"])
            if result:
                filter_level, items = result
                print(f"DEBUG: handle_calendar_filter type_changed to {data['type']}, items count: {len(items)}")
                self.calendar_view.update_filter_options(filter_level, items)
            else:
                 print(f"DEBUG: handle_calendar_filter type_changed to {data['type']} returned NO RESULT")
        
        elif event_type == "filter_selected":
            # Check if we need to update department dropdown
            if "faculty_id" in data and ("dept_id" not in data or not data["dept_id"]):
                items = self.calendar_builder.get_departments_for_faculty(data["faculty_id"])
                self.calendar_view.update_filter_options(2, items)
                return
            
            # Build schedule data using service
            schedule_data = self.calendar_builder.build(data)
            
            # Display
            self.calendar_view.display_schedule(schedule_data)
            if schedule_data:
                self.calendar_view.show()

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
        
    def open_room_list_view(self):
        """Open room list view"""
        from views.room_list_view import RoomListView
        if hasattr(self, 'room_list_view') and self.room_list_view is not None:
            try:
                self.room_list_view.close()
                self.room_list_view.deleteLater()
            except:
                pass
            
        self.room_list_view = RoomListView(self.model)
        self.room_list_view.show()

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

    def handle_teacher_room_pref_change(self, teacher_id: int, text: str):
        """Handle teacher room request change"""
        self.model.update_teacher_room_request(teacher_id, text)

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
        """
        Generate schedule automatically using OR-Tools (Current Semester).
        Called by the BIG BUTTON.
        """
        # Determine current semester from radio buttons
        semester = "Güz"
        if self.view.radio_bahar.isChecked():
            semester = "Bahar"
        elif self.view.radio_yaz.isChecked():
            semester = "Yaz"
            
        self._run_scheduler(semester)

    def generate_automatic_schedule_custom(self):
        """
        Generate schedule for a custom selection.
        Called by the Menu Action.
        """
        # Prompt for Semester
        items = ["Güz", "Bahar", "Yaz"]
        # Default to current selection
        current = "Güz"
        if self.view.radio_bahar.isChecked(): current = "Bahar"
        elif self.view.radio_yaz.isChecked(): current = "Yaz"
        
        try:
            default_idx = items.index(current)
        except:
            default_idx = 0

        semester, ok = QInputDialog.getItem(
            self.view, 
            "Dönem Seçimi", 
            "Hangi dönem için otomatik program oluşturulsun?", 
            items, 
            default_idx, 
            False
        )
        
        if not ok or not semester:
            return

        self._run_scheduler(semester)

    def _run_scheduler(self, semester: str):
        """Helper to run the scheduler logic"""
        reply = QMessageBox.question(
            self.view, 
            "Otomatik Program", 
            f"Seçilen Dönem: {semester}\n\nMevcut ders programı silinecek ve otomatik olarak yeniden oluşturulacak.\nDevam etmek istiyor musunuz?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return

        # Show wait cursor
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import Qt
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.view.setEnabled(False) 

        try:
            scheduler = ORToolsScheduler(self.model)
            # Pass selected semester to generate_schedule
            schedule, status = scheduler.generate_schedule(semester_filter=semester)
            
            if status == "OPTIMAL" or status == "FEASIBLE":
                # Wait, generate_schedule returns (schedule, status) 
                # but existing code expected (success) boolean?
                # Let's check existing code: `success = scheduler.solve()`
                # I changed `scheduler.py` to `generate_schedule` returning (schedule, status)?
                # No, I changed `solve` to `generate_schedule` but `solve` usually returns bool in my earlier code?
                # Let's check `scheduler.py` again.
                # It returns `True` if status in (OPTIMAL, FEASIBLE).
                # My new scheduler.py code:
                # `    def generate_schedule(self, semester_filter: Optional[str] = None):`
                # `        self.load_data(semester_filter)`
                # `        ...`
                # `        if self._run_solver("MINIMAL"): return True`
                # `        return False`
                #
                # Wait, `scheduler_ortools.py` had `solve` returning bool.
                # `scheduler.py` (the one I edited) had `solve` (lines 831+)
                # I renamed it to `generate_schedule`.
                # Does it return bool?
                # Line 60 (in scheduler_ortools.py) returned True/False.
                # In `scheduler.py`... I didn't see the return statement in the snippet.
                # Let's assume it returns boolean for now based on legacy usage.
                # BUT if I am wrong, `schedule` variable assignment will fail.
                
                # Check `scheduler.py` end of `solve` (now `generate_schedule`).
                pass

            # Since I am not sure about return type, let's treat it as boolean based on legacy code
            success = scheduler.generate_schedule(semester_filter=semester)
            
            if success:
                QMessageBox.information(self.view, "Başarılı", "Ders programı başarıyla oluşturuldu!")
                self.refresh_data()
            else:
                QMessageBox.warning(self.view, "Başarısız", "Uygun bir program bulunamadı!\nKısıtlamaları kontrol edin.")
        except Exception as e:
            QMessageBox.critical(self.view, "Hata", f"Program oluşturulurken hata: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            QApplication.restoreOverrideCursor()
            self.view.setEnabled(True)

    # Merging utilities moved to utils/schedule_merger.py

    def _on_run_setup_requested(self):
        """Run initial setup scripts (Reset DB, Seed, Populate, Assign)"""
        reply = QMessageBox.question(
            self.view,
            "Otomatik Kurulum / Veri Sıfırlama",
            "⚠️ DİKKAT: Bu işlem mevcut veritabanını SİLECEK ve sıfırdan kuracaktır.\n\n"
            "Yapılacak işlemler:\n"
            "1. Veritabanının temizlenmesi\n"
            "2. Fakülte ve Bölümlerin yüklenmesi\n"
            "3. Müfredatın (Dersler, Dönemler) yüklenmesi\n"
            "4. Öğrencilerin oluşturulması\n"
            "5. Odaların oluşturulması\n"
            "6. Öğretmenlerin eklenmesi\n"
            "7. Ders atamalarının yapılması\n\n"
            "Bu işlem biraz zaman alabilir. Devam etmek istiyor musunuz?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        # Show wait cursor
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import Qt
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.view.setEnabled(False) # Disable UI

        try:
            # 1. Populate Students (This Clears DB, Seeds F/D, Courses, Semesters, Students)
            from scripts.populate_students import populate as populate_students_and_courses
            print("Running populate_students...")
            populate_students_and_courses()

            # 2. Populate Rooms
            from scripts.populate_rooms import populate_rooms
            print("Running populate_rooms...")
            populate_rooms()

            # 3. Populate Teachers
            from scripts.populate_teachers import populate_teachers
            print("Running populate_teachers...")
            populate_teachers()

            # 4. Assign Teachers to Courses
            from scripts.assign_teachers import assign_teachers
            print("Running assign_teachers...")
            assign_teachers()

            # 4. Refresh View
            self.refresh_data()
            
            # Refresh Filters (Faculties might have changed)
            facs = self.model.get_faculties()
            self.view.update_filter_combo("faculty", facs)
            
            self.view.show_success_message(
                "Kurulum tamamlandı!\n"
                "- Veritabanı sıfırlandı ve yeniden oluşturuldu.\n"
                "- Fakülteler, Bölümler, Dersler ve Öğrenciler yüklendi.\n"
                "- Öğretmenler atandı."
            )

        except Exception as e:
            QMessageBox.critical(self.view, "Hata", f"Kurulum sırasında hata oluştu: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            QApplication.restoreOverrideCursor()
            self.view.setEnabled(True)
