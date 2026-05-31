
from PyQt5.QtWidgets import (
    QWidget, QLineEdit, QPushButton, QTimeEdit, QVBoxLayout, 
    QListWidget, QComboBox, QLabel, QHBoxLayout, QCompleter, 
    QMessageBox, QInputDialog, QDialog, QFormLayout, QDialogButtonBox,
    QGroupBox, QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView,
    QRadioButton, QFileDialog
)
from PyQt5.QtCore import QTime, pyqtSignal, Qt
from typing import List, Tuple, Optional, Dict, Union
from views.add_curriculum_course_dialog import AddCurriculumCourseDialog
from services.excel_exporter import ExcelExporter
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
    course_remove_by_ids_requested = pyqtSignal(list) # Emits list of IDs to remove
    faculty_add_requested = pyqtSignal(str)  # Emits faculty name when add faculty requested
    department_add_requested = pyqtSignal(int, str)  # Emits faculty_id, department_name when add department requested
    open_calendar_requested = pyqtSignal() # Emits when calendar button clicked
    open_student_view_requested = pyqtSignal() # Emits when student panel button clicked
    open_teacher_availability_requested = pyqtSignal() # Emits when availability button clicked
    generate_schedule_requested = pyqtSignal() # Emits when generate button clicked
    run_setup_requested = pyqtSignal() # Emits when setup/load data requested
    open_master_view_requested = pyqtSignal(str) # NEW: Emits mode ('teacher' or 'classroom')
    open_room_list_requested = pyqtSignal() # NEW: Emits when room list button clicked
    
    # Custom signal for menu action
    generate_schedule_custom_requested = pyqtSignal()
    
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

    def _toggle_theme(self, checked):
        from PyQt5.QtWidgets import QApplication
        app = QApplication.instance()
        if checked:
            self.btn_theme_toggle.setText("☀️ Aydınlık Mod")
            from main import set_dark_theme
            set_dark_theme(app)
        else:
            self.btn_theme_toggle.setText("🌙 Karanlık Mod")
            from main import set_light_theme
            set_light_theme(app)

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
        
        # Wrap curr_group and theme toggle in a horizontal layout
        top_row = QHBoxLayout()
        top_row.addWidget(curr_group, 1)
        
        self.btn_theme_toggle = QPushButton("🌙 Karanlık Mod")
        self.btn_theme_toggle.setCheckable(True)
        self.btn_theme_toggle.setStyleSheet("""
            QPushButton {
                background-color: #333; color: white; padding: 15px 25px; border-radius: 5px; font-weight: bold; font-size: 13px; margin-top: 10px;
            }
            QPushButton:checked {
                background-color: #f1c40f; color: black;
            }
        """)
        self.btn_theme_toggle.toggled.connect(self._toggle_theme)
        top_row.addWidget(self.btn_theme_toggle)
        
        layout.addLayout(top_row)
        
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
        
        # --- NEW Group: History Operations ---
        hist_group = QGroupBox("Geçmiş Programlar")
        hist_group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid gray; border-radius: 5px; margin-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px 0 3px; }")
        hist_layout = QHBoxLayout()
        
        self.btn_save_snapshot = QPushButton("💾 Güncel Programı Kaydet")
        self.btn_save_snapshot.setToolTip("Mevcut programın bir kopyasını kaydet")
        self.btn_save_snapshot.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0; 
                color: white; 
                padding: 10px; 
                font-weight: bold; 
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #7B1FA2; }
        """)
        
        self.btn_view_history = QPushButton("📜 Geçmiş Programlar")
        self.btn_view_history.setToolTip("Kaydedilmiş eski programları görüntüle")
        self.btn_view_history.setStyleSheet("""
            QPushButton {
                background-color: #673AB7; 
                color: white; 
                padding: 10px; 
                font-weight: bold; 
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #512DA8; }
        """)
        
        self.btn_compare_versions = QPushButton("🔄 Karşılaştır ve Düzenle")
        self.btn_compare_versions.setToolTip("İki versiyonu karşılaştırın veya programı manuel düzenleyin")
        self.btn_compare_versions.setStyleSheet("""
            QPushButton {
                background-color: #FF9800; 
                color: white; 
                padding: 10px; 
                font-weight: bold; 
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #F57C00; }
        """)
        
        hist_layout.addWidget(self.btn_save_snapshot)
        hist_layout.addWidget(self.btn_view_history)
        hist_layout.addWidget(self.btn_compare_versions)
        hist_group.setLayout(hist_layout)
        layout.addWidget(hist_group)
    
    # _create_time_inputs removed.


    def _create_course_list(self, layout: QVBoxLayout):
        """Create course list widget (Table)"""
        # Course list header layout
        header_layout = QHBoxLayout()
        
        list_label = QLabel("Ders Listesi:")
        list_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 10px;")
        header_layout.addWidget(list_label)
        
        header_layout.addStretch()
        
        from datetime import datetime
        now = datetime.now()
        current_date_str = now.strftime("%d.%m.%Y")
        
        # Calculate Academic Term
        month = now.month
        year = now.year
        
        # Academic year starts in September
        if month >= 9:
            academic_year = f"{year}-{year+1}"
            if month >= 9 and month <= 1: # 1 is Jan next year (Wait, Jan is < 9. Let's simplify)
                pass # Handled below
        else:
            academic_year = f"{year-1}-{year}"
            
        if month in [9, 10, 11, 12, 1]:
            current_term = "Güz"
        elif month in [2, 3, 4, 5, 6]:
            current_term = "Bahar"
        else:
            current_term = "Yaz"
            
        info_label = QLabel(f"Güncel Tarih: {current_date_str}   Güncel Dönem: {academic_year} {current_term}")
        info_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #555; margin-top: 10px; padding-right: 15px;")
        header_layout.addWidget(info_label)
        
        layout.addLayout(header_layout)
        
        # --- Filter Section ---
        filter_layout = QHBoxLayout()
        
        # Faculty Filter
        self.filter_faculty = QComboBox()
        self.filter_faculty.addItem("Tüm Fakülteler", None)
        self.filter_faculty.currentIndexChanged.connect(self._on_faculty_changed)
        
        # Department Filter
        self.filter_dept = QComboBox()
        self.filter_dept.addItem("Tüm Bölümler", None)
        self.filter_dept.currentIndexChanged.connect(self.trigger_filter_update)
        self.filter_dept.setEnabled(False) # Disable until faculty selected
        
        # Year Filter
        self.filter_year = QComboBox()
        self.filter_year.addItem("Tüm Sınıflar", None)
        self.filter_year.addItems([str(i) for i in range(1, 5)])
        self.filter_year.currentIndexChanged.connect(self.trigger_filter_update)

        # Day Filter
        self.filter_day = QComboBox()
        self.filter_day.addItem("Tüm Günler", None)
        self.filter_day.addItems(["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma"])
        self.filter_day.currentIndexChanged.connect(self.trigger_filter_update)
        
        # Search Input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Ders Ara...")
        self.search_input.textChanged.connect(self.trigger_filter_update)
        
        # Teacher Filter
        self.search_teacher = QLineEdit()
        self.search_teacher.setPlaceholderText("👨‍🏫 Hoca Ara...")
        self.search_teacher.textChanged.connect(self.trigger_filter_update)

        filter_layout.addWidget(self.filter_faculty)
        filter_layout.addWidget(self.filter_dept)
        filter_layout.addWidget(self.filter_year)
        filter_layout.addWidget(self.filter_day)
        filter_layout.addWidget(self.search_input)
        filter_layout.addWidget(self.search_teacher)
        
        layout.addLayout(filter_layout)
        
        # Course type filter - Radio buttons
        type_filter_layout = QHBoxLayout()
        
        from PyQt5.QtWidgets import QRadioButton, QButtonGroup, QCheckBox, QFrame

        # --- NEW: Semester Selection Logic moved here ---
        semester_layout = QHBoxLayout()
        semester_label = QLabel("Görüntülenen Dönemi Değiştir:")
        semester_label.setStyleSheet("font-weight: bold;")
        
        self.radio_guz = QRadioButton("Güz")
        self.radio_bahar = QRadioButton("Bahar")
        self.radio_yaz = QRadioButton("Yaz")
        
        # Default
        # Default: Set based on current month
        from datetime import datetime
        current_month = datetime.now().month
        
        # Güz: 9, 10, 11, 12, 1
        # Bahar: 2, 3, 4, 5, 6
        # Yaz: 7, 8
        if current_month in [9, 10, 11, 12, 1]:
            self.radio_guz.setChecked(True)
            default_sem = "Güz"
        elif current_month in [2, 3, 4, 5, 6]:
            self.radio_bahar.setChecked(True)
            default_sem = "Bahar"
        elif current_month in [7, 8]:
            self.radio_yaz.setChecked(True)
            default_sem = "Yaz"
        else:
             self.radio_guz.setChecked(True) # Fallback
             default_sem = "Güz"
        
        # Connect signals
        self.radio_guz.toggled.connect(self.trigger_filter_update)
        self.radio_bahar.toggled.connect(self.trigger_filter_update)
        self.radio_yaz.toggled.connect(self.trigger_filter_update)
        
        semester_layout.addWidget(semester_label)
        semester_layout.addWidget(self.radio_guz)
        semester_layout.addWidget(self.radio_bahar)
        semester_layout.addWidget(self.radio_yaz)
        
        self.current_semester_display = QLabel(f"Şu an Görüntülenen Dönem: {default_sem}")
        self.current_semester_display.setStyleSheet("font-weight: bold; color: #E64A19; padding-left: 20px;")
        semester_layout.addWidget(self.current_semester_display)
        
        semester_layout.addSpacing(20)
        
        # Add separator line
        line = QFrame()
        line.setFrameShape(QFrame.VLine)
        line.setFrameShadow(QFrame.Sunken)
        semester_layout.addWidget(line)
        semester_layout.addSpacing(20)

        # Add to main type filter layout at the start
        type_filter_layout.addLayout(semester_layout)
        # ------------------------------------------------
        
        # Create button group to make them mutually exclusive
        self.course_type_group = QButtonGroup()
        
        self.filter_all_courses = QRadioButton("Tüm Dersler")
        self.filter_all_courses.setChecked(True)  # Default
        self.filter_all_courses.toggled.connect(self.trigger_filter_update)
        
        self.filter_only_core = QRadioButton("Sadece Doğrudan Zorunlu")
        self.filter_only_core.toggled.connect(self.trigger_filter_update)
        
        self.filter_only_elective = QRadioButton("Sadece Seçmeli")
        self.filter_only_elective.toggled.connect(self.trigger_filter_update)
        
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
            }
            QTableWidget::item {
                padding: 5px;
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
        self.trigger_filter_update()

    def trigger_filter_update(self):
        """Handle filter changes and emit signal"""
        
        # Determine and update semester display
        selected_sem = "Güz" if self.radio_guz.isChecked() else ("Bahar" if self.radio_bahar.isChecked() else "Yaz")
        if hasattr(self, 'current_semester_display'):
            self.current_semester_display.setText(f"Şu an Görüntülenen Dönem: {selected_sem}")

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
            "only_core": only_core,
            # Semester Selection
            "semester": "Güz" if self.radio_guz.isChecked() else ("Bahar" if self.radio_bahar.isChecked() else "Yaz")
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
            # Check if already open
            if hasattr(self, 'curriculum_dialog') and self.curriculum_dialog is not None:
                if self.curriculum_dialog.isVisible():
                    self.curriculum_dialog.activateWindow()
                    self.curriculum_dialog.raise_()
                    return
                else:
                    # If closed but object exists, close properly and recreate (or just reuse?)
                    # Safer to recreate to ensure fresh state/event loop connection
                    try:
                        self.curriculum_dialog.close()
                    except:
                        pass
                    self.curriculum_dialog = None

            from views.curriculum_view import CurriculumViewDialog
            self.curriculum_dialog = CurriculumViewDialog(self.controller, self)
            
            # Use show() instead of exec_() for modeless window
            self.curriculum_dialog.show() 
            
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
        self.calendar_button = QPushButton("Takvimleri Göster")
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
        
        # MASTER VIEW BUTTON (NEW)
        self.btn_master_view = QPushButton("Genel Toplu Takvimleri Göster")
        self.btn_master_view.setStyleSheet("""
            QPushButton {
                background-color: #3F51B5;
                color: white;
                border: none;
                padding: 12px;
                font-size: 13px;
                border-radius: 3px;
            }
            QPushButton:hover { background-color: #303F9F; }
        """)
        # Menu for Master View
        from PyQt5.QtWidgets import QMenu
        self.master_menu = QMenu(self)
        action_master_teacher = self.master_menu.addAction("Öğretmenler Genel Takvimi")
        action_master_room = self.master_menu.addAction("Derslikler Genel Takvimi")
        
        action_master_teacher.triggered.connect(lambda: self.open_master_view_requested.emit('teacher'))
        action_master_room.triggered.connect(lambda: self.open_master_view_requested.emit('classroom'))
        
        self.btn_master_view.setMenu(self.master_menu)
        row1_layout.addWidget(self.btn_master_view)

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

        # Room List Button (NEW)
        self.btn_view_rooms = QPushButton("Odaları Listele")
        self.btn_view_rooms.setStyleSheet("""
            QPushButton {
                background-color: #795548;
                color: white;
                border: none;
                padding: 12px;
                font-size: 13px;
                border-radius: 3px;
            }
            QPushButton:hover { background-color: #5D4037; }
        """)
        row1_layout.addWidget(self.btn_view_rooms)
        
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
        
        # Re-create the buttons (hidden) so controller doesn't likely crash
        self.fakulte_ekle_button = QPushButton("Fakülte Ekle") 
        self.bolum_ekle_button = QPushButton("Bölüm Ekle")
        # Don't add to layout.
        
        action_add_faculty.triggered.connect(self.fakulte_ekle_button.click)
        
        action_add_dept = self.struct_menu.addAction("Bölüm Ekle")
        action_add_dept.triggered.connect(self.bolum_ekle_button.click)
        
        self.struct_menu.addSeparator()
        
        action_lab_cleanup = self.struct_menu.addAction("🧪 Lab Temizlik Ayarları")
        action_lab_cleanup.triggered.connect(self._open_lab_cleanup_dialog)
        
        self.struct_menu.addSeparator()
        
        # New Setup Action
        action_run_setup = self.struct_menu.addAction("⚙️ Otomatik Kurulum / Veri Yükle")
        action_run_setup.triggered.connect(self.run_setup_requested.emit)
        
        self.struct_menu.addSeparator()
        
        # New Export Action
        action_export = self.struct_menu.addAction("📥 Dışa Aktar (Excel/CSV)")
        action_export.triggered.connect(self._on_export_clicked)
        
        self.struct_menu.addSeparator()
        action_gen_custom = self.struct_menu.addAction("📅 Farklı Bir Dönem İçin Program Oluştur...")
        action_gen_custom.triggered.connect(self.generate_schedule_custom_requested.emit)
        
        self.struct_ops_button.setMenu(self.struct_menu)
        row2_layout.addWidget(self.struct_ops_button)
        
        # About / Licenses Button
        self.btn_about = QPushButton("ℹ️ Hakkında: Lisanslar")
        self.btn_about.setStyleSheet("""
            QPushButton {
                background-color: #333;
                color: white;
                border: none;
                padding: 12px;
                font-size: 13px;
                border-radius: 3px;
                font-family: 'Segoe UI Emoji', 'Segoe UI', Arial;
            }
            QPushButton:hover {
                background-color: #555;
            }
        """)
        self.btn_about.clicked.connect(self._show_about_dialog)
        row2_layout.addWidget(self.btn_about)
        
        layout.addLayout(row2_layout)
        
        # Generate Schedule button (Renamed)
        self.generate_schedule_button = QPushButton("Filtrede Seçili Dönem İçin Otomatik Ders Programı Oluştur")
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
        self.btn_view_rooms.clicked.connect(self.open_room_list_requested.emit)
        self.generate_schedule_button.clicked.connect(self.generate_schedule_requested.emit)

    def _show_about_dialog(self):
        """Displays the THIRD_PARTY_LICENSES.md file in a dialog"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton
        import os
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Hakkında & Üçüncü Parti Lisanslar")
        dialog.setGeometry(200, 200, 750, 550)
        
        layout = QVBoxLayout()
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        
        try:
            # Assuming we are in views/ so we go one up
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            license_path = os.path.join(base_dir, "THIRD_PARTY_LICENSES.md")
            if os.path.exists(license_path):
                with open(license_path, "r", encoding="utf-8") as f:
                    text_edit.setMarkdown(f.read())
            else:
                text_edit.setPlainText("Lisans dosyası bulunamadı. Lütfen proje dizinindeki THIRD_PARTY_LICENSES.md dosyasını kontrol edin.")
        except Exception as e:
            text_edit.setPlainText(f"Lisans dosyası okunamadı: {e}")
            
        layout.addWidget(text_edit)
        
        close_btn = QPushButton("Kapat")
        close_btn.setStyleSheet("padding: 10px; font-weight: bold;")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.setLayout(layout)
        dialog.exec_()
        
    def _open_lab_cleanup_dialog(self):
        """Opens the Lab Cleanup settings dialog"""
        try:
            from views.lab_cleanup_dialog import LabCleanupDialog
            dialog = LabCleanupDialog(self.controller, self)
            dialog.exec_()
        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Hata", f"Lab temizlik ekranı açılamadı: {e}")

    def _on_export_clicked(self):
        """Export the schedule and assignments to Excel or CSV directly from the main view"""
        try:
            if not hasattr(self, 'controller') or not hasattr(self.controller, 'model'):
                QMessageBox.warning(self, "Hata", "Sistem henüz yüklenmedi.")
                return
                
            if not hasattr(self.controller.model, 'get_all_courses_assigned_to_teachers'):
                QMessageBox.warning(self, "Hata", "Dışa aktarma fonksiyonu modelde bulunamadı.")
                return
                
            faculty_prefix = "Genel"
            semester = "Bahar"
            year = "2025-2026"
            
            if hasattr(self, 'filter_combo_faculty') and self.filter_combo_faculty.currentText() != "Tümü":
                fac_name = self.filter_combo_faculty.currentText()
                faculty_prefix = "".join([w[0].upper() for w in fac_name.split() if w.lower() not in ["ve", "ile"]])
            
            if hasattr(self, 'radio_guz') and self.radio_guz.isChecked(): semester = "Güz"
            elif hasattr(self, 'radio_bahar') and self.radio_bahar.isChecked(): semester = "Bahar"
            elif hasattr(self, 'radio_yaz') and self.radio_yaz.isChecked(): semester = "Yaz"
            
            if hasattr(self, 'filter_combo_year') and self.filter_combo_year.currentText() != "Tümü":
                year = self.filter_combo_year.currentText()

            import os
            if not os.path.exists("exports"):
                os.makedirs("exports")
            default_filename = os.path.join("exports", f"{faculty_prefix} {year} {semester} Ders Programı.xlsx")
                
            options = QFileDialog.Options()
            file_path, selected_filter = QFileDialog.getSaveFileName(
                self, "Ders Programını Kaydet", default_filename, 
                "Excel Dosyası (*.xlsx);;CSV Dosyası (*.csv)", options=options
            )
            if file_path:
                assigned = self.controller.model.get_all_courses_assigned_to_teachers()
                unassigned = self.controller.model.get_unassigned_courses()
                
                if file_path.endswith('.xlsx') or 'Excel' in selected_filter:
                    if not file_path.endswith('.xlsx'):
                        file_path += '.xlsx'
                    
                    schedule_data = self.controller.model.get_master_schedule_data()
                    dept_data = self.controller.model.get_department_course_categories()
                    ExcelExporter.export_schedule_to_excel(file_path, schedule_data, assigned, unassigned, dept_data)
                    QMessageBox.information(self, "Başarılı", "Ders programı başarıyla Excel'e aktarıldı!")
                else:
                    if not file_path.endswith('.csv'):
                        file_path += '.csv'
                    ExcelExporter.export_assignments_to_csv(file_path, assigned, unassigned)
                    QMessageBox.information(self, "Başarılı", "CSV dosyası başarıyla dışa aktarıldı!")
                    
        except Exception as e:
            QMessageBox.critical(self, "Dışa Aktarma Hatası", f"Dosya kaydedilirken bir hata oluştu:\n{str(e)}")
            import traceback
            traceback.print_exc()

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
