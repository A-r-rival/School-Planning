# -*- coding: utf-8 -*-
"""
Schedule View - MVC Pattern
Handles all UI components and user interactions
"""
from PyQt5.QtWidgets import (
    QWidget, QLineEdit, QPushButton, QTimeEdit, QVBoxLayout, 
    QListWidget, QComboBox, QLabel, QHBoxLayout, QCompleter, 
    QMessageBox, QInputDialog, QDialog, QFormLayout, QDialogButtonBox
)
from PyQt5.QtCore import QTime, pyqtSignal, Qt
from typing import List, Tuple, Optional


class AddCourseDialog(QDialog):
    """Dialog for adding a new course"""
    def __init__(self, parent=None, teachers=None):
        super().__init__(parent)
        self.setWindowTitle("Yeni Ders Ekle")
        self.setMinimumWidth(400)
        self.course_data = None
        self.teachers = teachers or []
        self._setup_ui()

    def _setup_ui(self):
        layout = QFormLayout()
        
        # Inputs
        self.ders_input = QLineEdit()
        self.ders_input.setPlaceholderText("Örn: Matematik I")
        
        self.hoca_input = QLineEdit()
        self.hoca_input.setPlaceholderText("Örn: Prof. Dr. Ahmet Yılmaz")
        if self.teachers:
            completer = QCompleter(self.teachers)
            completer.setCaseSensitivity(0) # Case insensitive
            self.hoca_input.setCompleter(completer)
            
        self.gun_input = QComboBox()
        self.gun_input.addItems(["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma"])
        
        self.saat_baslangic = QTimeEdit()
        self.saat_baslangic.setDisplayFormat("HH:mm")
        self.saat_baslangic.setTime(QTime(9, 0))
        
        self.saat_bitis = QTimeEdit()
        self.saat_bitis.setDisplayFormat("HH:mm")
        self.saat_bitis.setTime(QTime(9, 50)) # Default 50 mins
        
        # Add to layout
        layout.addRow("Ders Adı:", self.ders_input)
        layout.addRow("Öğretmen:", self.hoca_input)
        layout.addRow("Gün:", self.gun_input)
        layout.addRow("Başlangıç:", self.saat_baslangic)
        layout.addRow("Bitiş:", self.saat_bitis)
        
        # Buttons
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self._validate_and_accept)
        self.buttons.rejected.connect(self.reject)
        
        layout.addWidget(self.buttons)
        self.setLayout(layout)
        
    def _validate_and_accept(self):
        if not self.ders_input.text().strip():
            QMessageBox.warning(self, "Hata", "Ders adı boş olamaz!")
            return
            
        self.course_data = {
            'ders': self.ders_input.text().strip(),
            'hoca': self.hoca_input.text().strip(),
            'gun': self.gun_input.currentText(),
            'baslangic': self.saat_baslangic.time().toString("HH:mm"),
            'bitis': self.saat_bitis.time().toString("HH:mm")
        }
        self.accept()
    
    def get_data(self):
        return self.course_data


class ScheduleView(QWidget):
    """
    View class for schedule management
    Handles UI components and user interface
    """
    
    # Signals for controller communication
    course_add_requested = pyqtSignal(dict)  # Emits course data when add button clicked
    course_remove_requested = pyqtSignal(str)  # Emits course info when remove button clicked
    faculty_add_requested = pyqtSignal(str)  # Emits faculty name when add faculty requested
    department_add_requested = pyqtSignal(int, str)  # Emits faculty_id, department_name when add department requested
    open_calendar_requested = pyqtSignal() # Emits when calendar button clicked
    open_student_view_requested = pyqtSignal() # Emits when student panel button clicked
    open_teacher_availability_requested = pyqtSignal() # Emits when availability button clicked
    generate_schedule_requested = pyqtSignal() # Emits when generate button clicked
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ders Programı Oluşturucu - MVC")
        self.setGeometry(100, 100, 1000, 800)  # Larger window for better UI
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout()
        
        # Action buttons (Top)
        self._create_action_buttons(layout)
        
        # Course list (Middle)
        self._create_course_list(layout)
        
        # Advanced features buttons (Bottom)
        self._create_advanced_buttons(layout)
        
        self.setLayout(layout)

    # Old input creation methods removed.

    def _create_action_buttons(self, layout: QVBoxLayout):
        """Create action buttons"""
        # Buttons layout
        buttons_layout = QHBoxLayout()
        
        # Add course button
        self.ekle_button = QPushButton("➕ Yeni Ders Ekle")
        self.ekle_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 12px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        buttons_layout.addWidget(self.ekle_button)
        
        # Remove course button
        self.sil_button = QPushButton("➖ Seçili Dersi Sil")
        self.sil_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 12px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        buttons_layout.addWidget(self.sil_button)
        
        layout.addLayout(buttons_layout)
    
    # _create_time_inputs removed.
    def _create_action_buttons(self, layout: QVBoxLayout):
        """Create action buttons"""
        # Buttons layout
        buttons_layout = QHBoxLayout()
        
        # Add course button
        self.ekle_button = QPushButton("➕ Yeni Ders Ekle")
        self.ekle_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 12px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        buttons_layout.addWidget(self.ekle_button)
        
        # Remove course button
        self.sil_button = QPushButton("➖ Seçili Dersi Sil")
        self.sil_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 12px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        buttons_layout.addWidget(self.sil_button)
        
        layout.addLayout(buttons_layout)

    def _create_course_list(self, layout: QVBoxLayout):
        """Create course list widget"""
        # Course list label
        list_label = QLabel("Ders Listesi:")
        list_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 10px;")
        layout.addWidget(list_label)
        
        # --- Filter Section ---
        filter_layout = QHBoxLayout()
        
        # Faculty Filter
        self.filter_faculty = QComboBox()
        self.filter_faculty.addItem("Tüm Fakülteler", None)
        self.filter_faculty.currentIndexChanged.connect(self._on_faculty_changed)
        
        # Department Filter
        self.filter_dept = QComboBox()
        self.filter_dept.addItem("Tüm Bölümler", None)
        self.filter_dept.currentIndexChanged.connect(self._on_filter_changed)
        self.filter_dept.setEnabled(False) # Disable until faculty selected
        
        # Year Filter
        self.filter_year = QComboBox()
        self.filter_year.addItem("Tüm Sınıflar", None)
        self.filter_year.addItems([str(i) for i in range(1, 5)])
        self.filter_year.currentIndexChanged.connect(self._on_filter_changed)

        # Day Filter
        self.filter_day = QComboBox()
        self.filter_day.addItem("Tüm Günler", None)
        self.filter_day.addItems(["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma"])
        self.filter_day.currentIndexChanged.connect(self._on_filter_changed)
        
        # Search Input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Ders Ara...")
        self.search_input.textChanged.connect(self._on_filter_changed)
        
        # Teacher Filter (Manual inputs for now, could be dropdown)
        self.search_teacher = QLineEdit()
        self.search_teacher.setPlaceholderText("👨‍🏫 Hoca Ara...")
        self.search_teacher.textChanged.connect(self._on_filter_changed)

        filter_layout.addWidget(self.filter_faculty)
        filter_layout.addWidget(self.filter_dept)
        filter_layout.addWidget(self.filter_year)
        filter_layout.addWidget(self.filter_day)
        filter_layout.addWidget(self.search_input)
        filter_layout.addWidget(self.search_teacher)
        
        layout.addLayout(filter_layout)
        
        # Course type filter - Radio buttons
        type_filter_layout = QHBoxLayout()
        
        from PyQt5.QtWidgets import QRadioButton, QButtonGroup
        
        # Create button group to make them mutually exclusive
        self.course_type_group = QButtonGroup()
        
        self.filter_all_courses = QRadioButton("Tüm Dersler")
        self.filter_all_courses.setChecked(True)  # Default
        self.filter_all_courses.toggled.connect(self._on_filter_changed)
        
        self.filter_only_core = QRadioButton("Sadece Doğrudan Zorunlu")
        self.filter_only_core.toggled.connect(self._on_filter_changed)
        
        self.filter_only_elective = QRadioButton("Sadece Seçmeli")
        self.filter_only_elective.toggled.connect(self._on_filter_changed)
        
        # Add to button group
        self.course_type_group.addButton(self.filter_all_courses)
        self.course_type_group.addButton(self.filter_only_core)
        self.course_type_group.addButton(self.filter_only_elective)
        
        type_filter_layout.addWidget(self.filter_all_courses)
        type_filter_layout.addWidget(self.filter_only_core)
        type_filter_layout.addWidget(self.filter_only_elective)
        type_filter_layout.addStretch()
        
        layout.addLayout(type_filter_layout)
        # ----------------------
        
        # Course list widget
        self.ders_listesi = QListWidget()
        self.ders_listesi.setStyleSheet("""
            QListWidget {
                border: 2px solid #ddd;
                border-radius: 5px;
                padding: 5px;
                background-color: #f9f9f9;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
        """)
        layout.addWidget(self.ders_listesi)

    # Signal for filters
    filter_changed = pyqtSignal(dict) 

    def _on_faculty_changed(self):
        """Handle faculty change: Reset dept and trigger update"""
        # Block signals to prevent double triggering during clear
        self.filter_dept.blockSignals(True)
        self.filter_dept.clear()
        self.filter_dept.addItem("Tüm Bölümler", None)
        self.filter_dept.setEnabled(False)
        self.filter_dept.blockSignals(False)
        
        # Now trigger the general update
        self._on_filter_changed()

    def _on_filter_changed(self):
        """Handle filter changes and emit signal"""
        # Determine course type filter from radio buttons
        only_elective = self.filter_only_elective.isChecked()
        only_core = self.filter_only_core.isChecked()
        
        filters = {
            "faculty_id": self.filter_faculty.currentData(),
            "dept_id": self.filter_dept.currentData(),
            # Only set year/day if valid index > 0 selected
            "year": self.filter_year.currentText() if self.filter_year.currentIndex() > 0 else None,
            "day": self.filter_day.currentText() if self.filter_day.currentIndex() > 0 else None,
            "search_text": self.search_input.text(),
            "teacher_text": self.search_teacher.text(),
            "only_elective": only_elective,
            "only_core": only_core
        }
        # If "Tüm Sınıflar" (None data) is not selected, pass the text value
        if self.filter_year.currentIndex() > 0:
             filters["year"] = self.filter_year.currentText()
             
        # If "Tüm Günler" is not selected
        if self.filter_day.currentIndex() > 0:
             filters["day"] = self.filter_day.currentText()

        self.filter_changed.emit(filters)

    def update_filter_combo(self, combo_name: str, items: List[Tuple]):
        """
        Update a filter combobox
        items: List of (id, name)
        """
        widget = None
        default_text = "Seçiniz..."
        
        if combo_name == "faculty":
            widget = self.filter_faculty
            default_text = "Tüm Fakülteler"
        elif combo_name == "dept":
            widget = self.filter_dept
            default_text = "Tüm Bölümler"
            
        if widget:
            widget.blockSignals(True)
            widget.clear()
            widget.addItem(default_text, None)
            for item_id, name in items:
                widget.addItem(str(name), item_id)
            
            # Enable if items > 1 (more than just default)
            widget.setEnabled(len(items) > 0)
            widget.blockSignals(False)
    
    def _create_advanced_buttons(self, layout: QVBoxLayout):
        """Create advanced feature buttons"""
        # Advanced features label
        advanced_label = QLabel("Gelişmiş Özellikler:")
        advanced_label.setStyleSheet("font-weight: bold; font-size: 16px; margin-top: 15px; margin-bottom: 5px;")
        layout.addWidget(advanced_label)
        
        # --- Faculty & Dept Buttons (Side-by-Side) ---
        fac_dept_layout = QHBoxLayout()
        
        # Add faculty button
        self.fakulte_ekle_button = QPushButton("Fakülte Ekle")
        self.fakulte_ekle_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px;
                font-size: 13px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        fac_dept_layout.addWidget(self.fakulte_ekle_button)
        
        # Add department button
        self.bolum_ekle_button = QPushButton("Bölüm Ekle")
        self.bolum_ekle_button.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                padding: 10px;
                font-size: 13px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        fac_dept_layout.addWidget(self.bolum_ekle_button)
        
        layout.addLayout(fac_dept_layout)

        # Open Calendar button
        self.calendar_button = QPushButton("Takvimi Göster")
        self.calendar_button.setStyleSheet("""
            QPushButton {
                background-color: #673AB7;
                color: white;
                border: none;
                padding: 8px;
                font-size: 12px;
                border-radius: 3px;
                margin-top: 5px;
            }
            QPushButton:hover {
                background-color: #5E35B1;
            }
        """)
        layout.addWidget(self.calendar_button)

        # Open Student Panel button
        self.student_button = QPushButton("Öğrenci Paneli")
        self.student_button.setStyleSheet("""
            QPushButton {
                background-color: #009688;
                color: white;
                border: none;
                padding: 8px;
                font-size: 12px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #00796B;
            }
        """)
        layout.addWidget(self.student_button)

        layout.addWidget(self.student_button)

        # Teacher Availability button
        self.teacher_availability_button = QPushButton("Öğretmen Müsaitlik")
        self.teacher_availability_button.setStyleSheet("""
            QPushButton {
                background-color: #FF5722;
                color: white;
                border: none;
                padding: 8px;
                font-size: 12px;
                border-radius: 3px;
                margin-top: 5px;
            }
            QPushButton:hover {
                background-color: #E64A19;
            }
        """)
        layout.addWidget(self.teacher_availability_button)

        # Generate Schedule button
        self.generate_schedule_button = QPushButton("Otomatik Program Oluştur")
        self.generate_schedule_button.setStyleSheet("""
            QPushButton {
                background-color: #3F51B5;
                color: white;
                border: none;
                padding: 12px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
                margin-top: 15px;
            }
            QPushButton:hover {
                background-color: #303F9F;
            }
        """)
        layout.addWidget(self.generate_schedule_button)

    def _connect_signals(self):
        """Connect internal signals"""
        self.ekle_button.clicked.connect(self._on_add_course_clicked)
        self.sil_button.clicked.connect(self._on_remove_course_clicked)
        self.fakulte_ekle_button.clicked.connect(self._on_add_faculty_clicked)
        self.bolum_ekle_button.clicked.connect(self._on_add_department_clicked)
        self.calendar_button.clicked.connect(self.open_calendar_requested.emit)
        self.student_button.clicked.connect(self.open_student_view_requested.emit)
        self.teacher_availability_button.clicked.connect(self.open_teacher_availability_requested.emit)
        self.generate_schedule_button.clicked.connect(self.generate_schedule_requested.emit)

    # _auto_fill_end_time removed as inputs are gone.
    
    # Temporary store for teacher list (set by controller)
    _cached_teachers = []

    def update_teacher_completer(self, teachers: List[str]):
        """Update teacher list for the dialog"""
        self._cached_teachers = teachers
        # Input widget is no longer here to update directly. 

    def _on_add_course_clicked(self):
        """Handle add course button click -> Open Dialog"""
        dialog = AddCourseDialog(self, self._cached_teachers)
        if dialog.exec_() == QDialog.Accepted:
            course_data = dialog.get_data()
            if course_data:
                 self.course_add_requested.emit(course_data)
    
    def _on_remove_course_clicked(self):
        """Handle remove course button click"""
        selected_item = self.ders_listesi.currentItem()
        if selected_item:
            self.course_remove_requested.emit(selected_item.text())
    
    def _on_add_faculty_clicked(self):
        """Handle add faculty button click"""
        faculty_name, ok = QInputDialog.getText(self, 'Fakülte Ekle', 'Fakülte Adı:')
        if ok and faculty_name.strip():
            self.faculty_add_requested.emit(faculty_name.strip())
    
    def _on_add_department_clicked(self):
        """Handle add department button click"""
        # This will be handled by controller with faculty selection
        self.department_add_requested.emit(0, "")  # Placeholder, controller will handle
    
    ###
    ########## Public methods for controller to call
    ###

    def display_courses(self, courses: List[str]):
        """Display courses in the list widget"""
        self.ders_listesi.clear()
        for course in courses:
            self.ders_listesi.addItem(course)
    
    def add_course_to_list(self, course_info: str):
        """Add a single course to the list"""
        self.ders_listesi.addItem(course_info)
    
    def remove_course_from_list(self, course_info: str):
        """Remove a course from the list"""
        items = self.ders_listesi.findItems(course_info, Qt.MatchExactly)
        for item in items:
            row = self.ders_listesi.row(item)
            self.ders_listesi.takeItem(row)
    
    def clear_inputs(self):
        """Clear all input fields - Not needed with Dialog"""
        pass
    
    def update_teacher_completer(self, teachers: List[str]):
        """Update teacher list for the dialog"""
        self._cached_teachers = teachers
        # Input widget is no longer here to update directly.
    
    def show_error_message(self, message: str):
        """Show error message to user"""
        QMessageBox.warning(self, "Hata", message)
    
    def show_success_message(self, message: str):
        """Show success message to user"""
        QMessageBox.information(self, "Başarılı", message)
    
    def show_faculty_selection_dialog(self, faculties: List[Tuple[int, str]]) -> Tuple[bool, int]:
        """
        Show faculty selection dialog
        
        Args:
            faculties: List of (faculty_id, faculty_name) tuples
        
        Returns:
            Tuple[bool, int]: (ok, faculty_id)
        """
        if not faculties:
            self.show_error_message("Önce bir fakülte eklemeniz gerekiyor!")
            return False, 0
        
        faculty_items = [f"{faculty[1]} (ID: {faculty[0]})" for faculty in faculties]
        faculty_choice, ok = QInputDialog.getItem(
            self, 'Fakülte Seç', 'Fakülte seçin:', faculty_items, 0, False
        )
        
        if ok and faculty_choice:
            # Extract faculty ID from selection
            faculty_id = int(faculty_choice.split('ID: ')[1].split(')')[0])
            return True, faculty_id
        
        return False, 0
    
    def show_department_input_dialog(self) -> Tuple[bool, str]:
        """
        Show department name input dialog
        
        Returns:
            Tuple[bool, str]: (ok, department_name)
        """
        department_name, ok = QInputDialog.getText(self, 'Bölüm Ekle', 'Bölüm Adı:')
        return ok, department_name.strip() if ok else ""
    
    def get_current_selected_course(self) -> Optional[str]:
        """Get currently selected course from list"""
        selected_item = self.ders_listesi.currentItem()
        return selected_item.text() if selected_item else None
