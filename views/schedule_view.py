from PyQt5.QtWidgets import (
    QWidget, QLineEdit, QPushButton, QTimeEdit, QVBoxLayout, 
    QListWidget, QComboBox, QLabel, QHBoxLayout, QCompleter, 
    QMessageBox, QInputDialog, QDialog, QFormLayout, QDialogButtonBox,
    QGroupBox, QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView
)
from PyQt5.QtCore import QTime, pyqtSignal, Qt
from typing import List, Tuple, Optional, Dict, Union
from views.add_curriculum_course_dialog import AddCurriculumCourseDialog


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
    course_remove_requested = pyqtSignal(str)  # Emits course info when remove button clicked (Legacy for single ID string)
    course_remove_by_ids_requested = pyqtSignal(list) # NEW: Emits list of IDs to remove
    faculty_add_requested = pyqtSignal(str)  # Emits faculty name when add faculty requested
    department_add_requested = pyqtSignal(int, str)  # Emits faculty_id, department_name when add department requested
    open_calendar_requested = pyqtSignal() # Emits when calendar button clicked
    open_student_view_requested = pyqtSignal() # Emits when student panel button clicked
    open_teacher_availability_requested = pyqtSignal() # Emits when availability button clicked
    generate_schedule_requested = pyqtSignal() # Emits when generate button clicked
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ders Programı Oluşturucu - MVC")
        self.setGeometry(100, 100, 1340, 870)  # Larger window for table
        
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
        """Create action buttons (Grouped)"""
        
        # --- Group 1: Curriculum Operations ---
        curr_group = QGroupBox("Müfredat İşlemleri")
        curr_group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid gray; border-radius: 5px; margin-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px 0 3px; }")
        curr_layout = QHBoxLayout()
        
        # Button: Add Standard Template
        self.btn_template = QPushButton("📝 Müfredata Ekle/Çıkar")
        self.btn_template.setToolTip("Müfredata yeni ders ekle veya mevcut dersleri düzenle (Havuz/Sınıf)")
        self.btn_template.setStyleSheet("""
            QPushButton {
                background-color: #2196F3; 
                color: white; 
                padding: 10px; 
                font-weight: bold; 
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #1976D2; }
        """)
        self.btn_template.clicked.connect(self._open_template_dialog)
        curr_layout.addWidget(self.btn_template)
        
        # Button: View Curriculum (NEW)
        self.btn_view_curr = QPushButton("👀 Müfredatı Görüntüle")
        self.btn_view_curr.setToolTip("Tüm müfredat derslerini liste halinde görüntüle")
        self.btn_view_curr.setStyleSheet("""
            QPushButton {
                background-color: #009688; 
                color: white; 
                padding: 10px; 
                font-weight: bold; 
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #00796B; }
        """)
        self.btn_view_curr.clicked.connect(self._open_curriculum_view)
        curr_layout.addWidget(self.btn_view_curr)
        
        curr_group.setLayout(curr_layout)
        layout.addWidget(curr_group)
        
        # --- Group 2: Schedule (Ad Hoc) Operations ---
        adhoc_group = QGroupBox("Program (Ad Hoc) İşlemleri")
        adhoc_group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid gray; border-radius: 5px; margin-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px 0 3px; }")
        adhoc_layout = QHBoxLayout()
        
        # Button: Add Ad Hoc
        self.ekle_button = QPushButton("➕ Sadece Bu Dönemki Programa Ekle")
        self.ekle_button.setToolTip("Mevcut programa manuel ders ekle (Müfredat dışı veya ekstra)")
        self.ekle_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; 
                color: white; 
                padding: 10px; 
                font-weight: bold; 
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #388E3C; }
        """)
        # clicked signal connected in controller usually? No, likely in main or controller init.
        # Check original code structure for connections. usually controller connects 'ekle_button.clicked'
        adhoc_layout.addWidget(self.ekle_button)
        
        # Button: Remove Selected (RENAMED)
        self.sil_button = QPushButton("➖ Seçili Dersi Bu Dönemlik Sil")
        self.sil_button.setToolTip("Takvimden seçili dersi bu dönem için siler (Müfredattan silmez)")
        self.sil_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336; 
                color: white; 
                padding: 10px; 
                font-weight: bold; 
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #D32F2F; }
        """)
        # Connection handling is external usually
        adhoc_layout.addWidget(self.sil_button)
        
        adhoc_group.setLayout(adhoc_layout)
        layout.addWidget(adhoc_group)
    
    # _create_time_inputs removed.


    def _create_course_list(self, layout: QVBoxLayout):
        """Create course list widget (Table)"""
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
        
        from PyQt5.QtWidgets import QRadioButton, QButtonGroup, QCheckBox
        
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
        
        # Checkbox for Pool Code
        self.show_pool_code_cb = QCheckBox("Havuz Kodu Göster")
        self.show_pool_code_cb.setChecked(True) # Default to shown as per previous behavior
        self.show_pool_code_cb.toggled.connect(self.toggle_pool_column)
        
        type_filter_layout.addWidget(self.filter_all_courses)
        type_filter_layout.addWidget(self.filter_only_core)
        type_filter_layout.addWidget(self.filter_only_elective)
        type_filter_layout.addSpacing(20)
        type_filter_layout.addWidget(self.show_pool_code_cb)
        type_filter_layout.addStretch()
        
        layout.addLayout(type_filter_layout)
        # ----------------------
        
        # Course TABLE widget
        self.ders_listesi = QTableWidget()
        self.ders_listesi.setColumnCount(6)
        self.ders_listesi.setHorizontalHeaderLabels([
            "Havuz Kodu", "Ders Kodu", "Ders Adı", "Hocası", "Saatleri", "Zorunlu Olduğu Sınıflar"
        ])
        
        # Config Table
        self.ders_listesi.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.ders_listesi.setSelectionMode(QAbstractItemView.SingleSelection)
        self.ders_listesi.setAlternatingRowColors(True)
        self.ders_listesi.setEditTriggers(QAbstractItemView.NoEditTriggers) # Read only
        
        # Column Widths
        header = self.ders_listesi.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive) # Allow user resizing
        
        # 0: Havuz (Small)
        self.ders_listesi.setColumnWidth(0, 95)
        # 1: Code (Small)
        self.ders_listesi.setColumnWidth(1, 85)
        # 2: Name (Wider + 30px) -> Let's give it substantial space
        self.ders_listesi.setColumnWidth(2, 280) 
        # 3: Teacher (Medium)
        self.ders_listesi.setColumnWidth(3, 180)
        # 4: Time (Medium)
        self.ders_listesi.setColumnWidth(4, 160)
        # 5: Classes (Stretch remaining)
        header.setSectionResizeMode(5, QHeaderView.Stretch)
        

        
        # Styling
        self.ders_listesi.setStyleSheet("""
            QTableWidget {
                border: 2px solid #ddd;
                border-radius: 5px;
                background-color: #ffffff;
                alternate-background-color: #f5f5f5;
                gridline-color: #e0e0e0;
            }
            QHeaderView::section {
                background-color: #e0e0e0;
                padding: 4px;
                border: 1px solid #d0d0d0;
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: #000000;
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

    def toggle_pool_column(self, checked: bool):
        """Toggle visibility of Pool Code column"""
        # Pool Code is column 0
        self.ders_listesi.setColumnHidden(0, not checked)

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
    
    def _open_curriculum_view(self):
        """Open dialog to view all curriculum courses"""
        try:
            from views.curriculum_view import CurriculumViewDialog
            dialog = CurriculumViewDialog(self.controller, self)
            
            # Since this is a viewer, we just show it. 
            # If we wanted to return data, we'd handle Accepted.
            # But the user just wants to VIEW.
            dialog.exec_() 
            
        except ImportError:
            QMessageBox.warning(self, "Hata", "CurriculumViewDialog henüz oluşturulmadı/import edilemedi.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Müfredat görüntülenirken hata: {e}")

    # ... (other methods)

    def _create_advanced_buttons(self, layout: QVBoxLayout):
        """Create advanced feature buttons"""
        # Advanced features label - REMOVED per user request
        # advanced_label = QLabel("Gelişmiş Özellikler:")
        # advanced_label.setStyleSheet("font-weight: bold; font-size: 16px; margin-top: 15px; margin-bottom: 5px;")
        # layout.addWidget(advanced_label)
        
        # Row 1: Calendar & Teacher
        row1_layout = QHBoxLayout()
        
        # Open Calendar button
        self.calendar_button = QPushButton("Takvimi Göster")
        self.calendar_button.setStyleSheet("""
            QPushButton {
                background-color: #673AB7;
                color: white;
                border: none;
                padding: 12px;
                font-size: 13px;
                border-radius: 3px;
            }
            QPushButton:hover { background-color: #5E35B1; }
        """)
        row1_layout.addWidget(self.calendar_button)
        
        # Teacher Availability button
        self.teacher_availability_button = QPushButton("Öğretmen Müsaitlik ve Ders Atamaları")
        self.teacher_availability_button.setStyleSheet("""
            QPushButton {
                background-color: #FF5722;
                color: white;
                border: none;
                padding: 12px;
                font-size: 13px;
                border-radius: 3px;
            }
            QPushButton:hover { background-color: #E64A19; }
        """)
        row1_layout.addWidget(self.teacher_availability_button)
        
        layout.addLayout(row1_layout)

        # Row 2: Student Panel & Structural Operations
        row2_layout = QHBoxLayout()

        # Open Student Panel button
        self.student_button = QPushButton("Öğrenci Paneli")
        self.student_button.setStyleSheet("""
            QPushButton {
                background-color: #009688;
                color: white;
                border: none;
                padding: 12px;
                font-size: 13px;
                border-radius: 3px;
            }
            QPushButton:hover { background-color: #00796B; }
        """)
        row2_layout.addWidget(self.student_button)
        
        # Structural Operations Button (Fakülte, Bölüm vs.)
        self.struct_ops_button = QPushButton("Fakülte, Bölüm vs. İşlemleri")
        self.struct_ops_button.setStyleSheet("""
            QPushButton {
                background-color: #607D8B;  /* Blue Grey */
                color: white;
                border: none;
                padding: 12px;
                font-size: 13px;
                border-radius: 3px;
            }
            QPushButton:hover { background-color: #455A64; }
        """)
        
        # Create Menu for Structural Ops
        from PyQt5.QtWidgets import QMenu
        self.struct_menu = QMenu(self)
        
        action_add_faculty = self.struct_menu.addAction("Fakülte Ekle")
        # We need to connect these actions to the existing slots or signals, 
        # but previously they were button clicks connected in controller.
        # We can expose the actions or buttons. 
        # To minimize refactoring risk, we can keep the buttons but hide them/repurpose them?
        # Better: Allow controller to access these actions. 
        # OR: Connect these actions to emit signals that the controller listens to?
        # Currently controller likely does: view.fakulte_ekle_button.clicked.connect(...)
        # So I should PROBABLY keep self.fakulte_ekle_button as a property, but maybe not visible?
        # No, better to make valid QObjects that the controller can find.
        
        # Let's assign the action triggers to the same place the old buttons went.
        # But wait, controller expects `view.fakulte_ekle_button`. 
        # I can mock that behavior or update controller. 
        # Safest: Update controller if possible. 
        # Let's create dummy hidden buttons that triggered by menu? 
        # Or just make `self.fakulte_ekle_button` match the Action? (QAction has triggered)
        # Controller likely uses `.clicked.connect`. QAction uses `.triggered.connect`.
        # I will keep `self.fakulte_ekle_button` as a QPushButton but NOT add it to layout, 
        # and connect menu action to button.click()! Hacky but safe for existing controller connections.
        
        # Re-create the buttons (hidden) so controller doesn't likely crash
        self.fakulte_ekle_button = QPushButton("Fakülte Ekle") 
        self.bolum_ekle_button = QPushButton("Bölüm Ekle")
        # Don't add to layout.
        
        action_add_faculty.triggered.connect(self.fakulte_ekle_button.click)
        
        action_add_dept = self.struct_menu.addAction("Bölüm Ekle")
        action_add_dept.triggered.connect(self.bolum_ekle_button.click)
        
        self.struct_ops_button.setMenu(self.struct_menu)
        row2_layout.addWidget(self.struct_ops_button)
        
        layout.addLayout(row2_layout)
        
        # Generate Schedule button
        self.generate_schedule_button = QPushButton("Otomatik Program Oluştur")
        self.generate_schedule_button.setStyleSheet("""
            QPushButton {
                background-color: #3F51B5;
                color: white;
                border: none;
                padding: 15px;
                font-size: 15px;
                font-weight: bold;
                border-radius: 5px;
                margin-top: 20px;
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

    def set_controller(self, controller):
        """Set controller reference for dialogs"""
        self.controller = controller

    # Temporary store for teacher list (set by controller)
    _cached_teachers = []

    def update_teacher_completer(self, teachers: List[str]):
        """Update teacher list for the dialog"""
        self._cached_teachers = teachers
        # Input widget is no longer here to update directly. 

    def _open_template_dialog(self):
        """Open dialog to add course to curriculum"""
        try:
             # Lazy import to avoid circular dependency if any?
             # No, imported at top.
             dialog = AddCurriculumCourseDialog(self.controller, self)
             if dialog.exec_() == QDialog.Accepted:
                 # Logic handled in dialog (controller calls)
                 pass
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Diyalog açılırken hata: {e}")
    
    def _on_add_course_clicked(self):
        """Handle add course button click -> Open Dialog"""
        dialog = AddCourseDialog(self, self._cached_teachers)
        if dialog.exec_() == QDialog.Accepted:
            course_data = dialog.get_data()
            if course_data:
                 self.course_add_requested.emit(course_data)
    
    def _on_remove_course_clicked(self):
        """Handle remove course button click"""
        # With table, we can have multi selection, but we restricted to SingleSelection
        selected_row = self.ders_listesi.currentRow()
        
        if selected_row >= 0:
            # We stored ID/IDs in the first item's UserRole
            item = self.ders_listesi.item(selected_row, 0)
            if item:
                course_name = self.ders_listesi.item(selected_row, 2).text() # Name column
                ids = item.data(Qt.UserRole) # Should be list of IDs
                
                reply = QMessageBox.question(self, 'Silme Onayı', 
                                             f"'{course_name}' dersini (ve birleştirilmiş bloklarını) bu dönemlik programdan silmek istediğinize emin misiniz?",
                                             QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                
                if reply == QMessageBox.Yes:
                    if isinstance(ids, list):
                         self.course_remove_by_ids_requested.emit(ids)
                    else:
                         # Fallback if just ID
                         self.course_remove_by_ids_requested.emit([ids])
        else:
            QMessageBox.warning(self, "Uyarı", "Silinecek bir ders seçmediniz.")
    
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

    def display_courses(self, courses: Union[List[str], List[Dict]]):
        """
        Display courses in the table widget.
        Supports both legacy formatted strings (list of str) and new structured data (list of dictionaries).
        """
        self.ders_listesi.setRowCount(0)
        
        if not courses:
            return

        # Check if structured
        is_structured = isinstance(courses[0], dict) if len(courses) > 0 else False
        
        if is_structured:
            self.ders_listesi.setRowCount(len(courses))
            for i, data in enumerate(courses):
                # Columns: ["Havuz Kodu", "Ders Kodu", "Ders Adı", "Hocası", "Saatleri", "Alan Sınıflar"]
                
                # Pool
                self.ders_listesi.setItem(i, 0, QTableWidgetItem(data.get('pool', '')))
                
                # Code
                self.ders_listesi.setItem(i, 1, QTableWidgetItem(data.get('code', '')))
                
                # Name
                self.ders_listesi.setItem(i, 2, QTableWidgetItem(data.get('name', '')))
                
                # Teacher
                self.ders_listesi.setItem(i, 3, QTableWidgetItem(data.get('teacher', '')))
                
                # Time: Day xx:xx-xx:xx
                time_str = f"{data.get('day', '')} {data.get('start', '')}-{data.get('end', '')}"
                self.ders_listesi.setItem(i, 4, QTableWidgetItem(time_str))
                
                # Classes
                self.ders_listesi.setItem(i, 5, QTableWidgetItem(data.get('classes', '')))
                
                # Store IDs in the first column item for deletion
                # 'ids' should be in the data dict if merged, or 'id' if not
                ids = data.get('ids', [data.get('id')])
                self.ders_listesi.item(i, 0).setData(Qt.UserRole, ids)
                
        else:
            # Fallback for strings (if ever needed, or transitional)
            # We can parse them or just put in Name col
            # But the plan is to switch controller.
            # Assuming controller will send dicts
            pass
    
    def clear_inputs(self):
        """Clear all input fields - Not needed with Dialog"""
        pass
    
    def show_error_message(self, message: str):
        """Show error message to user"""
        QMessageBox.warning(self, "Hata", message)
    
    def show_success_message(self, message: str):
        """Show success message to user"""
        QMessageBox.information(self, "Başarılı", message)
    
    def show_faculty_selection_dialog(self, faculties: List[Tuple[int, str]]) -> Tuple[bool, int]:
        """Show faculty selection dialog"""
        if not faculties:
            self.show_error_message("Önce bir fakülte eklemeniz gerekiyor!")
            return False, 0
        
        faculty_items = [f"{faculty[1]} (ID: {faculty[0]})" for faculty in faculties]
        faculty_choice, ok = QInputDialog.getItem(
            self, 'Fakülte Seç', 'Fakülte seçin:', faculty_items, 0, False
        )
        
        if ok and faculty_choice:
            faculty_id = int(faculty_choice.split('ID: ')[1].split(')')[0])
            return True, faculty_id
        
        return False, 0
    
    def show_department_input_dialog(self) -> Tuple[bool, str]:
        """Show department name input dialog"""
        department_name, ok = QInputDialog.getText(self, 'Bölüm Ekle', 'Bölüm Adı:')
        return ok, department_name.strip() if ok else ""
