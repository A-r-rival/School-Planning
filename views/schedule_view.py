# -*- coding: utf-8 -*-
"""
Schedule View - MVC Pattern
Handles all UI components and user interactions
"""
from PyQt5.QtWidgets import (
    QWidget, QLineEdit, QPushButton, QTimeEdit, QVBoxLayout, 
    QListWidget, QComboBox, QLabel, QHBoxLayout, QCompleter, 
    QMessageBox, QInputDialog
)
from PyQt5.QtCore import QTime, pyqtSignal
from typing import List, Tuple, Optional


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
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ders Programı Oluşturucu - MVC")
        self.setGeometry(100, 100, 450, 700)  # Slightly larger for better UI
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout()
        
        # Course input section
        self._create_course_inputs(layout)
        
        # Time input section
        self._create_time_inputs(layout)
        
        # Action buttons
        self._create_action_buttons(layout)
        
        # Course list
        self._create_course_list(layout)
        
        # Advanced features buttons
        self._create_advanced_buttons(layout)
        
        self.setLayout(layout)
    
    def _create_course_inputs(self, layout: QVBoxLayout):
        """Create course input fields"""
        # Course name input
        self.ders_input = QLineEdit()
        self.ders_input.setPlaceholderText("Ders Adı")
        layout.addWidget(self.ders_input)
        
        # Teacher input
        self.hoca_input = QLineEdit()
        self.hoca_input.setPlaceholderText("Hoca Adı")
        layout.addWidget(self.hoca_input)
        
        # Day selection
        self.gun_input = QComboBox()
        self.gun_input.addItems(["Pazartesi", "Salı", "Çarşamba", "Perşembe", 
                                "Cuma", "Cumartesi", "Pazar"])
        layout.addWidget(self.gun_input)
    
    def _create_time_inputs(self, layout: QVBoxLayout):
        """Create time input fields"""
        # Time input layout
        saat_layout = QHBoxLayout()
        
        # Start time
        self.saat_baslangic = QTimeEdit()
        self.saat_baslangic.setDisplayFormat("HH:mm")
        self.saat_baslangic.setTime(QTime(9, 0))  # Default to 09:00
        
        # End time
        self.saat_bitis = QTimeEdit()
        self.saat_bitis.setDisplayFormat("HH:mm")
        self.saat_bitis.setTime(QTime(10, 0))  # Default to 10:00
        
        # Add labels and widgets
        saat_layout.addWidget(QLabel("Başlangıç:"))
        saat_layout.addWidget(self.saat_baslangic)
        saat_layout.addWidget(QLabel("Bitiş:"))
        saat_layout.addWidget(self.saat_bitis)
        
        layout.addLayout(saat_layout)
        
        # Connect auto-fill end time
        self.saat_baslangic.timeChanged.connect(self._auto_fill_end_time)
    
    def _create_action_buttons(self, layout: QVBoxLayout):
        """Create action buttons"""
        # Add course button
        self.ekle_button = QPushButton("Dersi Ekle")
        self.ekle_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        layout.addWidget(self.ekle_button)
        
        # Remove course button
        self.sil_button = QPushButton("Seçili Dersi Sil")
        self.sil_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:pressed {
                background-color: #b71c1c;
            }
        """)
        layout.addWidget(self.sil_button)
    
    def _create_course_list(self, layout: QVBoxLayout):
        """Create course list widget"""
        # Course list label
        list_label = QLabel("Ders Listesi:")
        list_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 10px;")
        layout.addWidget(list_label)
        
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
    
    def _create_advanced_buttons(self, layout: QVBoxLayout):
        """Create advanced feature buttons"""
        # Advanced features label
        advanced_label = QLabel("Gelişmiş Özellikler:")
        advanced_label.setStyleSheet("font-weight: bold; font-size: 12px; margin-top: 10px;")
        layout.addWidget(advanced_label)
        
        # Add faculty button
        self.fakulte_ekle_button = QPushButton("Fakülte Ekle")
        self.fakulte_ekle_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px;
                font-size: 12px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        layout.addWidget(self.fakulte_ekle_button)
        
        # Add department button
        self.bolum_ekle_button = QPushButton("Bölüm Ekle")
        self.bolum_ekle_button.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                padding: 8px;
                font-size: 12px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        layout.addWidget(self.bolum_ekle_button)
    
    def _connect_signals(self):
        """Connect internal signals"""
        self.ekle_button.clicked.connect(self._on_add_course_clicked)
        self.sil_button.clicked.connect(self._on_remove_course_clicked)
        self.fakulte_ekle_button.clicked.connect(self._on_add_faculty_clicked)
        self.bolum_ekle_button.clicked.connect(self._on_add_department_clicked)
    
    def _auto_fill_end_time(self):
        """Automatically set end time to 50 minutes after start time"""
        start_time = self.saat_baslangic.time()
        end_time = start_time.addSecs(50 * 60)  # Add 50 minutes
        self.saat_bitis.setTime(end_time)
    
    def _on_add_course_clicked(self):
        """Handle add course button click"""
        course_data = {
            'ders': self.ders_input.text().strip(),
            'hoca': self.hoca_input.text().strip(),
            'gun': self.gun_input.currentText(),
            'baslangic': self.saat_baslangic.time().toString("HH:mm"),
            'bitis': self.saat_bitis.time().toString("HH:mm")
        }
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
        items = self.ders_listesi.findItems(course_info, 0)
        for item in items:
            row = self.ders_listesi.row(item)
            self.ders_listesi.takeItem(row)
    
    def clear_inputs(self):
        """Clear all input fields"""
        self.ders_input.clear()
        self.hoca_input.clear()
        self.saat_baslangic.setTime(QTime(9, 0))
        self.saat_bitis.setTime(QTime(10, 0))
        self.gun_input.setCurrentIndex(0)
    
    def update_teacher_completer(self, teachers: List[str]):
        """Update teacher autocomplete"""
        completer = QCompleter(teachers)
        completer.setCaseSensitivity(0)  # Case insensitive
        self.hoca_input.setCompleter(completer)
    
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
