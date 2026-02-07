# -*- coding: utf-8 -*-
"""
Teacher Availability View
Dialog for managing teacher unavailability slots
"""
from functools import partial
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QComboBox, 
    QTableWidget, QTableWidgetItem, QPushButton, 
    QLabel, QTimeEdit, QMessageBox, QHeaderView,
    QLineEdit, QTabWidget, QWidget, QCompleter, QSpinBox # Added QCompleter
)
from PyQt5.QtCore import Qt, QTime

class AddUnavailabilityDialog(QDialog):
    def __init__(self, teachers, controller, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ekle / Güncelle")
        self.setGeometry(250, 250, 450, 350)
        self.teachers = teachers
        self.controller = controller
        self._setup_ui()
        
    def _setup_ui(self):
        main_layout = QVBoxLayout()
        
        # --- Common: Teacher Selection ---
        main_layout.addWidget(QLabel("Öğretmen:"))
        self.teacher_combo = QComboBox()
        self.teacher_combo.setEditable(True)
        self.teacher_combo.setInsertPolicy(QComboBox.NoInsert)
        self.teacher_combo.completer().setCompletionMode(QCompleter.PopupCompletion)
        self.teacher_combo.completer().setFilterMode(Qt.MatchContains)
        
        for t_id, t_name in self.teachers:
            self.teacher_combo.addItem(t_name, t_id)
        # Use activated to handle both mouse and keyboard selection reliably
        self.teacher_combo.activated[int].connect(self._on_teacher_changed)
        main_layout.addWidget(self.teacher_combo)
        
        # --- Tabs ---
        self.tabs = QTabWidget()
        
        # Tab 1: Day Span (Block Preference)
        self.tab_span = QWidget()
        span_layout = QVBoxLayout()
        span_layout.addWidget(QLabel("Bu öğretmen haftada en fazla kaç gün gelsin?"))
        span_layout.addWidget(QLabel("(0 = Kısıtlama Yok, tüm haftaya yayılabilir)"))
        
        self.span_combo = QComboBox()
        self.span_combo.addItem("Kısıtlama Yok (Serbest)", 0)
        self.span_combo.addItem("2 Güne Kısıtla", 2)
        self.span_combo.addItem("3 Güne Kısıtla", 3)
        self.span_combo.addItem("4 Güne Kısıtla", 4)
        span_layout.addWidget(self.span_combo)
        span_layout.addStretch()
        self.tab_span.setLayout(span_layout)
        
        # Tab 2: Specific Unavailability (Time/Day)
        self.tab_slot = QWidget()
        slot_layout = QVBoxLayout()
        slot_layout.addWidget(QLabel("Öğretmenin MÜSAİT OLMADIĞI zamanı ekle:"))
        
        # Day
        slot_layout.addWidget(QLabel("Gün:"))
        self.day_combo = QComboBox()
        self.day_combo.addItems(["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma"])
        slot_layout.addWidget(self.day_combo)
        
        # Time
        time_layout = QHBoxLayout()
        self.start_time = QTimeEdit()
        self.start_time.setDisplayFormat("HH:mm")
        self.start_time.setTime(QTime(9, 0))
        time_layout.addWidget(QLabel("Başlangıç:"))
        time_layout.addWidget(self.start_time)
        
        self.end_time = QTimeEdit()
        self.end_time.setDisplayFormat("HH:mm")
        self.end_time.setTime(QTime(12, 0))
        time_layout.addWidget(QLabel("Bitiş:"))
        time_layout.addWidget(self.end_time)
        slot_layout.addLayout(time_layout)
        
        # Description
        slot_layout.addWidget(QLabel("Açıklama (Opsiyonel):"))
        self.desc_input = QLineEdit()
        slot_layout.addWidget(self.desc_input)
        slot_layout.addStretch()
        self.tab_slot.setLayout(slot_layout)
        
        # Add tabs
        self.tabs.addTab(self.tab_span, "Çalışma Bloğu (Genel Kısıt)")
        self.tabs.addTab(self.tab_slot, "Saat/Gün Kısıtı (Özel)")
        
        main_layout.addWidget(self.tabs)
        
        # Buttons
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("Uygula / Ekle")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        main_layout.addLayout(btn_layout)
        
        self.setLayout(main_layout)
        
        # Initial load logic
        if self.teachers:
            self._on_teacher_changed(0)

    def _on_teacher_changed(self, index):
        if not hasattr(self, 'span_combo') or not hasattr(self, 'controller'):
            return

        t_id = self.teacher_combo.currentData()
        t_id = self.teacher_combo.currentData()
        
        # Ensure t_id is a valid integer
        if t_id is None:
            return
            
        if not isinstance(t_id, int):
            return

        if t_id != -1:
            try:
                # Load current span preference onto UI
                span = self.controller.model.get_teacher_span(t_id)
                idx = self.span_combo.findData(span)
                if idx >= 0:
                    self.span_combo.setCurrentIndex(idx)
                else:
                    self.span_combo.setCurrentIndex(0)
            except Exception as e:
                print(f"Error loading span for teacher {t_id}: {e}")

    def get_data(self):
        is_span_tab = (self.tabs.currentIndex() == 0)
        return {
            'teacher_id': self.teacher_combo.currentData(),
            'action_type': 'span' if is_span_tab else 'slot',
            'span': self.span_combo.currentData(),
            'day': self.day_combo.currentText(),
            'start': self.start_time.time().toString("HH:mm"),
            'end': self.end_time.time().toString("HH:mm"),
            'desc': self.desc_input.text()
        }

class TeacherAvailabilityView(QDialog):
    def __init__(self, parent=None, teachers=None):
        super().__init__(parent)
        self.setWindowTitle("Öğretmen Müsaitlik Durumu")
        self.setGeometry(100, 100, 1100, 700)
        self.teachers = teachers or []
        
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout()
        
        # Filter Section
        filter_group = QVBoxLayout()
        
        # Teacher Selection (Filter)
        teacher_layout = QHBoxLayout()
        teacher_layout.addWidget(QLabel("Filtrele (Öğretmen):"))
        self.teacher_combo = QComboBox()
        self.teacher_combo.setEditable(True)
        self.teacher_combo.setInsertPolicy(QComboBox.NoInsert)
        self.teacher_combo.completer().setCompletionMode(QCompleter.PopupCompletion)
        self.teacher_combo.completer().setFilterMode(Qt.MatchContains)
        
        self.teacher_combo.addItem("Tüm Öğretmenler", -1)
        for t_id, t_name in self.teachers:
            self.teacher_combo.addItem(t_name, t_id)
        self.teacher_combo.currentIndexChanged.connect(self._on_teacher_changed)
        teacher_layout.addWidget(self.teacher_combo)
        
        filter_group.addLayout(teacher_layout)
        layout.addLayout(filter_group)
        
        # --- TABS ---
        self.tabs = QTabWidget()
        
        # TAB 1: Unavailability (Existing functionality)
        self.tab_availability = QWidget()
        av_layout = QVBoxLayout()
        
        # List of Unavailability
        self.table = QTableWidget()
        self.table.setColumnCount(5) 
        self.table.setHorizontalHeaderLabels(["Öğretmen", "Tip", "Detay", "Açıklama", "İşlem"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        self.table.setColumnWidth(1, 130)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.setAlternatingRowColors(True) # Enable zebra striping
        av_layout.addWidget(self.table)
        
        # Add Button
        self.add_button = QPushButton("Yeni Namüsaitlik Ekle")
        self.add_button.setStyleSheet("font-weight: bold; font-size: 14px; padding: 10px;")
        self.add_button.clicked.connect(self._on_add_clicked)
        av_layout.addWidget(self.add_button)
        
        self.tab_availability.setLayout(av_layout)
        self.tabs.addTab(self.tab_availability, "Zamanlama ve Ders Blokları")
        
        # TAB 2: Course Assignments (New functionality from plan)
        self.tab_assignments = QWidget()
        as_layout = QVBoxLayout()
        
        # Add Assignment Form
        form_layout = QHBoxLayout()
        
        # 1. Course Dropdown (Curriculum Courses)
        self.course_combo = QComboBox()
        self.course_combo.setEditable(True)
        self.course_combo.addItem("Ders Seçiniz...", None)
        self.course_combo.setMinimumWidth(250)
        self.course_combo.completer().setCompletionMode(QCompleter.PopupCompletion)
        self.course_combo.completer().setFilterMode(Qt.MatchContains)
        form_layout.addWidget(QLabel("Ders:"))
        form_layout.addWidget(self.course_combo)
        
        # Quick Add Template Button
        self.btn_quick_template = QPushButton("Müfredatı Değiştir")
        self.btn_quick_template.setToolTip("Müfredata yeni ders ekle veya düzenle")
        self.btn_quick_template.clicked.connect(self._open_quick_template)
        form_layout.addWidget(self.btn_quick_template)
        
        # 2. Section (Instance) & Note
        # Instance is less relevant for preferences now, but still used for assignments? 
        # Assignment table uses (ders_adi, ders_instance). 
        # But User said "ders_instance olmasın text ders_secim_notu ile değiş". 
        # For ASSIGNMENT, instance is crucial for the schedule. 
        # For PREFERENCE, we use Note.
        
        # We will keep Instance Spin for "Assign" action.
        # And add Note Input for "Want/Block" action.
        
        self.instance_spin = QSpinBox() 
        self.instance_spin.setRange(1, 20)
        self.instance_spin.setPrefix("Şube ")
        self.instance_spin.setToolTip("Sadece 'Dersi Öğretmene Ata' işlemi için geçerlidir")
        form_layout.addWidget(QLabel("Şube (Atama):"))
        form_layout.addWidget(self.instance_spin)

        self.note_input = QLineEdit()
        self.note_input.setPlaceholderText("Not (Örn: İste/Engelle için)")
        self.note_input.setToolTip("Opsiyonel: İste/Engelle durumunda not düşebilirsiniz (Örn: Sadece İnşaat)")
        form_layout.addWidget(QLabel("Not:"))
        form_layout.addWidget(self.note_input)
        
        # 3. Action Buttons Layout
        action_layout = QHBoxLayout()
        
        # Want Button
        self.btn_want = QPushButton("İste")
        self.btn_want.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;") # Green
        self.btn_want.clicked.connect(self._on_want_clicked)
        action_layout.addWidget(self.btn_want)

        # Assign Button
        self.btn_assign = QPushButton("Dersi Öğretmene Ata")
        self.btn_assign.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;") # Blue
        self.btn_assign.clicked.connect(self._on_assign_clicked)
        action_layout.addWidget(self.btn_assign)

        # Block Button
        self.btn_block = QPushButton("Engelle")
        self.btn_block.setStyleSheet("background-color: #F44336; color: white; font-weight: bold;") # Red
        self.btn_block.clicked.connect(self._on_block_clicked)
        action_layout.addWidget(self.btn_block)
        
        as_layout.addLayout(form_layout) # Added missing form layout
        as_layout.addLayout(action_layout)
        
        # Assignment List
        self.assign_table = QTableWidget()
        self.assign_table.setColumnCount(5)
        self.assign_table.setHorizontalHeaderLabels(["Ders Adı", "Şube / Not", "Öğretmen", "Durum", "İşlem"])
        header = self.assign_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        # header.setSectionResizeMode(1, QHeaderView.ResizeToContents) # Changed to Stretch (default)
        header.setSectionResizeMode(3, QHeaderView.Fixed) # Status -> Fixed 70px
        self.assign_table.setColumnWidth(3, 70)
        header.setSectionResizeMode(4, QHeaderView.Fixed) # Action
        self.assign_table.setColumnWidth(4, 60)
        self.assign_table.setAlternatingRowColors(True) # Enable zebra striping
        as_layout.addWidget(self.assign_table)
        
        self.tab_assignments.setLayout(as_layout)
        self.tabs.addTab(self.tab_assignments, "Ders Atamaları")
        
        layout.addWidget(self.tabs)
        
        self.setLayout(layout)
        # Note: Do NOT call _on_teacher_changed(0) here because controller is not set yet.
            
    def set_controller(self, controller):
        self.controller = controller
        # Trigger initial load now that we have the controller
        if self.teachers:
             self._on_teacher_changed(0)
             
        # Load curriculum courses
        if hasattr(self.controller.model, 'get_curriculum_courses'):
            courses = self.controller.model.get_curriculum_courses()
            self._update_course_combo(courses)
        
    def _on_teacher_changed(self, index):
        """Handle filter change"""
        try:
            if hasattr(self, 'controller'):
                teacher_id = self.teacher_combo.currentData()
                
                # Check for validity
                if teacher_id is None: 
                    # Clear views if no valid teacher selected
                    self.table.setRowCount(0)
                    self.assign_table.setRowCount(0)
                    self.tab_assignments.setEnabled(False) 
                    return
                
                # Enable assignment tab
                self.tab_assignments.setEnabled(True)

                if teacher_id == -1:
                    self.controller.load_all_teacher_availability()
                    # Load ALL Assignments/Preferences
                    self._load_assignments(-1)
                else:
                    self.controller.load_teacher_availability(teacher_id)
                    # Load Assignments for specific teacher
                    self._load_assignments(teacher_id)
                    
        except Exception as e:
            print(f"Error in _on_teacher_changed: {e}")

    def _update_course_combo(self, courses):
        self.course_combo.clear()
        self.course_combo.addItem("Ders Seçiniz...", None)
        self.course_combo.addItems(courses)

    def _load_assignments(self, teacher_id):
        """Load courses assigned/preferred/blocked for this teacher (or ALL) with banners"""
        try:
            self.assign_table.setRowCount(0)
            
            assigned = []
            preferences = []
            
            is_all = (teacher_id == -1)
            
            # Need to get teacher ID for each row if in "All" mode
            # If not in "All" mode, we know the teacher_id from argument.
            
            if is_all:
                assigned = self.controller.model.get_all_courses_assigned_to_teachers() # (ders, instance, hoca, teacher_id_from_db??)
                # OOPS: get_all_courses_assigned_to_teachers currently returns (ders, instance, hoca_name). NO ID.
                # I need to fetch ID too.
                # Let's assume for now I can't easily get ID without updating model again.
                # BUT, I can map name to ID using self.teachers list! 
                # self.teachers is [(id, name), ...]
                # This is a bit fragile if names are not unique, but "ad || ' ' || soyad" is usually what we have.
                # Better: Update model? Or use lookup?
                # Let's use lookup from self.teachers for now.
                
                preferences = self.controller.model.get_all_teacher_course_preferences() # (ders, note, type, hoca)
            else:
                assigned = self.controller.model.get_courses_assigned_to_teacher(teacher_id) # (ders, instance)
                preferences = self.controller.model.get_teacher_course_preferences(teacher_id) # (ders, note, type)

            # Split preferences
            wanted = [p for p in preferences if p[2] == 'WANTED']
            blocked = [p for p in preferences if p[2] == 'BLOCKED']
            
            # Helper: Name to ID map
            name_to_id = {name: t_id for t_id, name in self.teachers}
            # Current teacher name for single view
            current_teacher_name = "-"
            if not is_all and teacher_id:
                 for tid, tname in self.teachers:
                      if tid == teacher_id:
                           current_teacher_name = tname
                           break
            
            # Helper to add banner
            def add_banner(text, color_hex):
                row = self.assign_table.rowCount()
                self.assign_table.insertRow(row)
                item = QTableWidgetItem(text)
                item.setBackground(QColor(color_hex)) 
                item.setForeground(Qt.black)
                item.setTextAlignment(Qt.AlignCenter)
                item.setFlags(Qt.ItemIsEnabled) # Not editable/selectable
                self.assign_table.setItem(row, 0, item)
                self.assign_table.setSpan(row, 0, 1, 5) # Span all 5 columns
                
            # Helper to add row
            def add_row(name, detail, status_text, item_type, teacher_name=None, row_teacher_id=None):
                row = self.assign_table.rowCount()
                self.assign_table.insertRow(row)
                
                final_teacher_name = teacher_name if teacher_name else current_teacher_name
                
                if is_all and teacher_name:
                    if row_teacher_id is None:
                         # Try lookup
                         row_teacher_id = name_to_id.get(teacher_name)
                
                # If not is_all, we use the main teacher_id
                if not is_all:
                    row_teacher_id = teacher_id
                    
                self.assign_table.setItem(row, 0, QTableWidgetItem(name))
                self.assign_table.setItem(row, 1, QTableWidgetItem(detail))
                self.assign_table.setItem(row, 2, QTableWidgetItem(final_teacher_name))
                self.assign_table.setItem(row, 3, QTableWidgetItem(status_text))
                
                # Delete Button
                if row_teacher_id is not None:
                     del_btn = QPushButton("Sil")
                     del_btn.setStyleSheet("background-color: #E0E0E0; color: black;") # Gray
                     # Allow multiple args in lambda? Use partial
                     del_btn.clicked.connect(partial(self._on_delete_assignment_click, item_type, name, detail, row_teacher_id))
                     self.assign_table.setCellWidget(row, 4, del_btn)
                else:
                     self.assign_table.setItem(row, 4, QTableWidgetItem("-"))

            from PyQt5.QtGui import QColor

            # --- Section 1: Assigned ---
            if assigned:
                add_banner("Atanan Dersler (Kesin)", "#B3E5FC") # Light Blue
                for item in assigned:
                    if is_all:
                        course_name, instance, hoca = item
                        add_row(course_name, f"Şube {instance}", "Atandı", "ASSIGNMENT", teacher_name=hoca)
                    else:
                        course_name, instance = item
                        add_row(course_name, f"Şube {instance}", "Atandı", "ASSIGNMENT")

            # --- Section 2: Wanted ---
            if wanted:
                add_banner("Talep Edilen Dersler (İstek)", "#A5D6A7") # Green
                for item in wanted:
                    if is_all:
                        course_name, note, _, hoca = item
                        note_display = note if note else "-"
                        add_row(course_name, note_display, "İsteniyor", "WANTED", teacher_name=hoca)
                    else:
                        course_name, note, _ = item
                        note_display = note if note else "-"
                        add_row(course_name, note_display, "İsteniyor", "WANTED")

            # --- Section 3: Blocked ---
            if blocked:
                add_banner("İstenmeyen Dersler (Bloke)", "#EF9A9A") # Red
                for item in blocked:
                    if is_all:
                        course_name, note, _, hoca = item
                        note_display = note if note else "-"
                        add_row(course_name, note_display, "Engellendi", "BLOCKED", teacher_name=hoca)
                    else:
                        course_name, note, _ = item
                        note_display = note if note else "-"
                        add_row(course_name, note_display, "Engellendi", "BLOCKED")
            
        except Exception as e:
            print(f"Error loading assignments: {e}")
            import traceback
            traceback.print_exc()

    def _on_delete_assignment_click(self, item_type, name, detail, teacher_id):
        """Confirm and delete assignment/preference"""
        try:
            msg = f"'{name}' ({detail}) kaydını listeden silmek istediğinize emin misiniz?"
            reply = QMessageBox.question(self, "Silme Onayı", msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                if item_type == "ASSIGNMENT":
                    # detail is "Şube {instance}"
                    instance = int(detail.replace("Şube ", "")) if "Şube" in detail else 1
                    with self.controller.model.conn:
                         self.controller.model.conn.execute(
                             "DELETE FROM Ders_Ogretmen_Iliskisi WHERE ogretmen_id=? AND ders_adi=? AND ders_instance=?",
                             (teacher_id, name, instance)
                         )
                else: # WANTED or BLOCKED
                    self.controller.model.remove_teacher_course_preference(teacher_id, name)
                
                # Reload current view
                current_filter = self.teacher_combo.currentData()
                self._load_assignments(current_filter)
                
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Silme işlemi başarısız: {e}")
            print(f"Delete error: {e}")

    def _on_assignment_table_dbl_click(self, row, col):
        """Handle deletion request"""
        try:
            item = self.assign_table.item(row, 0)
            if not item: return
            
            data = item.data(Qt.UserRole)
            if not data: return # Likely banner
            
            item_type, name, detail = data
            
            msg = f"'{name}' ({detail}) kaydını listeden kaldırmak istiyor musunuz?"
            if QMessageBox.question(self, "Silme Onayı", msg, QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
                teacher_id = self.teacher_combo.currentData()
                
                if item_type == "ASSIGNMENT":
                    # detail is "Şube X", need to parse or store raw instance
                    # Quick hack: detail is "Şube {instance}"
                    instance = int(detail.replace("Şube ", ""))
                    # Delete logic for assignment (Directly calling model/repo, assuming direct access is OK for now as per legacy code)
                    # Ideally should be in controller
                    with self.controller.model.conn:
                         self.controller.model.conn.execute(
                             "DELETE FROM Ders_Ogretmen_Iliskisi WHERE ogretmen_id=? AND ders_adi=? AND ders_instance=?",
                             (teacher_id, name, instance)
                         )
                else: # WANTED or BLOCKED
                    self.controller.model.remove_teacher_course_preference(teacher_id, name)
                    
                self._load_assignments(teacher_id)
                
        except Exception as e:
            print(f"Delete error: {e}")

    def _on_assign_clicked(self):
        """Assign selected course to selected teacher"""
        teacher_id = self.teacher_combo.currentData()
        course_name = self.course_combo.currentText()
        instance = self.instance_spin.value()
        
        self._validate_and_execute(teacher_id, course_name, lambda: 
            self.controller.model.assign_teacher_to_course(teacher_id, course_name, instance)
        )
            
    def _on_want_clicked(self):
        """Add Want preference"""
        teacher_id = self.teacher_combo.currentData()
        course_name = self.course_combo.currentText()
        note = self.note_input.text().strip()
        
        self._validate_and_execute(teacher_id, course_name, lambda:
            self.controller.model.add_teacher_course_preference(teacher_id, course_name, note, 'WANTED')
        )

    def _on_block_clicked(self):
        """Add Block preference"""
        teacher_id = self.teacher_combo.currentData()
        course_name = self.course_combo.currentText()
        note = self.note_input.text().strip()
        
        self._validate_and_execute(teacher_id, course_name, lambda:
            self.controller.model.add_teacher_course_preference(teacher_id, course_name, note, 'BLOCKED')
        )
        
    def _validate_and_execute(self, teacher_id, course_name, action_callback):
        if teacher_id is None or teacher_id == -1:
             QMessageBox.warning(self, "Hata", "Lütfen bir öğretmen seçiniz.")
             return
             
        if not course_name or self.course_combo.currentIndex() == 0:
             QMessageBox.warning(self, "Hata", "Lütfen bir ders seçiniz.")
             return
             
        # Execute
        try:
            success = action_callback()
            if success:
                self._load_assignments(teacher_id)
                # clear inputs?
                self.note_input.clear()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"İşlem başarısız: {e}")
            
    def _open_quick_template(self):
        """Open template dialog from here"""
        from views.add_curriculum_course_dialog import AddCurriculumCourseDialog # Lazy import
        dialog = AddCurriculumCourseDialog(self.controller, self)
        if dialog.exec_():
             # Refresh course list
             courses = self.controller.model.get_curriculum_courses()
             self._update_course_combo(courses)

    def _on_add_clicked(self):
        """Open Add Dialog"""
        try:
            if hasattr(self, 'controller'):
                dialog = AddUnavailabilityDialog(self.teachers, self.controller, self)
                if dialog.exec_():
                    data = dialog.get_data()
                    
                    if data['action_type'] == 'span':
                        # Update Span Preference Only
                        self.controller.handle_teacher_span_change(data['teacher_id'], data['span'])
                        QMessageBox.information(self, "Bilgi", "Çalışma bloğu tercihi güncellendi.")
                    else:
                        # Add Unavailability Slot Only
                        self.controller.add_teacher_unavailability(
                            data['teacher_id'], 
                            data['day'], 
                            data['start'], 
                            data['end'],
                            data['desc']
                        )
        except Exception as e:
            print(f"CRASH in _on_add_clicked: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Hata", f"Ekleme penceresi açılırken hata: {str(e)}")

    def update_table(self, data):
        """Update table with availability data (Slots + Spans)"""
        self.table.setRowCount(0)
        
        for row_idx, item in enumerate(data):
            # item is a dict now
            teacher_name = item.get('teacher_name', '-')
            item_type = item.get('type')
            
            type_text = "-"
            detail_text = "-"
            desc_text = "-"
            del_type = ""
            del_id = -1
            
            if item_type == 'span':
                type_text = "Haftalık Kısıt"
                val = item.get('span_value')
                detail_text = f"{val} Günlük Blok"
                desc_text = "-"
                del_type = 'span'
                del_id = item.get('teacher_id')
                
            elif item_type == 'slot':
                type_text = "Namüsaitlik"
                day = item.get('day')
                start = item.get('start')
                end = item.get('end')
                detail_text = f"{day} {start}-{end}"
                desc_text = item.get('description', '')
                del_type = 'slot'
                del_id = item.get('id')

            self.table.insertRow(row_idx)
            
            self.table.setItem(row_idx, 0, QTableWidgetItem(teacher_name))
            self.table.setItem(row_idx, 1, QTableWidgetItem(type_text))
            self.table.setItem(row_idx, 2, QTableWidgetItem(detail_text))
            self.table.setItem(row_idx, 3, QTableWidgetItem(desc_text))
            
            delete_btn = QPushButton("Sil")
            delete_btn.clicked.connect(partial(self._on_delete_clicked, del_type, del_id))
            self.table.setCellWidget(row_idx, 4, delete_btn)

    def _on_delete_clicked(self, item_type, item_id):
        """Confirm before deleting"""
        try:
            msg = "Bu namüsaitlik kaydını silmek istediğinize emin misiniz?"
            if item_type == 'span':
                msg = "Bu öğretmenin haftalık gün kısıtlamasını kaldırmak istediğinize emin misiniz?"
                
            reply = QMessageBox.question(self, 'Silme Onayı', 
                                         msg,
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                self.controller.handle_delete_request(item_type, item_id)
        except Exception as e:
            print(f"CRASH in _on_delete_clicked: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Hata", f"Silme işlemi sırasında hata: {e}")
