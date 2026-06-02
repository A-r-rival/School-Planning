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
    QLineEdit, QCheckBox, QTabWidget, QWidget, QCompleter, QSpinBox, QFrame, # Added QCompleter, QFrame
    QListWidget, QListWidgetItem, QGroupBox, QFileDialog
)
from PyQt5.QtCore import Qt, QTime
from PyQt5.QtGui import QColor

from views.add_unavailability_dialog import AddUnavailabilityDialog
from services.excel_exporter import ExcelExporter



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
        for t in self.teachers:
            if len(t) >= 2:
                 self.teacher_combo.addItem(t[1], t[0])
        # Semester Filter
        term_filter_layout = QHBoxLayout()
        term_filter_layout.addWidget(QLabel("Tabloda Görüntülenen Dönem:"))
        self.term_filter_combo = QComboBox()
        self.term_filter_combo.addItems(["Tümü", "Güz", "Bahar", "Yaz"])
        self.term_filter_combo.currentIndexChanged.connect(self._on_teacher_changed)
        term_filter_layout.addWidget(self.term_filter_combo)
        
        self.teacher_combo.currentIndexChanged.connect(self._on_teacher_changed)
        teacher_layout.addWidget(self.teacher_combo)
        
        filter_group.addLayout(teacher_layout)
        filter_group.addLayout(term_filter_layout)
        
        # --- GLOBAL PREFERENCES GROUP ---
        # Moved up here from the bottom of the tab so it is not confused with Adding a block
        self.pref_group_box = QGroupBox("Öğretmen Genel Tercihleri (Otomatik Kaydedilir)")
        self.pref_group_box.setVisible(False) # Hidden until a teacher is selected
        pref_layout = QHBoxLayout(self.pref_group_box)

        pref_layout.addWidget(QLabel("Haftalık Max Gün:"))
        self.span_combo = QComboBox()
        self.span_combo.addItem("Serbest", 0)
        self.span_combo.addItem("2 Gün", 2)
        self.span_combo.addItem("3 Gün", 3)
        self.span_combo.addItem("4 Gün", 4)
        self.span_combo.currentIndexChanged.connect(lambda idx: self._on_span_changed(self.span_combo.currentData()))
        pref_layout.addWidget(self.span_combo)
        
        pref_layout.addSpacing(20)

        pref_layout.addWidget(QLabel("Oda/Kat Tercihi:"))
        self.room_pref_input = QLineEdit()
        self.room_pref_input.setPlaceholderText("Örn: Zemin, Lab, A101")
        self.room_pref_input.textChanged.connect(self._on_room_pref_changed)
        pref_layout.addWidget(self.room_pref_input)
        
        filter_group.addWidget(self.pref_group_box)
        layout.addLayout(filter_group)
        
        # --- TABS ---
        self.tabs = QTabWidget()
        
        # TAB 1: Unavailability (Existing functionality)
        self.tab_availability = QWidget()
        av_layout = QVBoxLayout()
        
        # List of Unavailability
        self.table = QTableWidget()
        self.table.setColumnCount(6) 
        self.table.setHorizontalHeaderLabels(["Öğretmen", "Tip", "Dönem/Yıl", "Kısıt", "Açıklama", "İşlem"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        self.table.setColumnWidth(1, 110)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        self.table.setColumnWidth(2, 110)
        header.setSectionResizeMode(3, QHeaderView.Fixed) # Kısıt fixed
        self.table.setColumnWidth(3, 160) # Set to 160px
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.setAlternatingRowColors(True) # Enable zebra striping
        av_layout.addWidget(self.table)
        
        # Add Button
        self.add_button = QPushButton("Yeni Saat Kısıtı Ekle")
        self.add_button.setStyleSheet("font-weight: bold; font-size: 14px; padding: 10px;")
        self.add_button.clicked.connect(self._on_add_clicked)
        av_layout.addWidget(self.add_button)
        
        self.tab_availability.setLayout(av_layout)
        self.tabs.addTab(self.tab_availability, "Zaman ve Gün Kısıtları")
        
        # TAB 2: Course Assignments (New functionality from plan)
        self.tab_assignments = QWidget()
        as_layout = QVBoxLayout()
        
        # Add Assignment Form
        # action_layout will now be the top layout
        action_layout = QHBoxLayout()
        
        # Assign Button
        self.btn_assign = QPushButton("Dersi Öğretmene Ata")
        self.btn_assign.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;") # Blue
        self.btn_assign.clicked.connect(self._on_assign_clicked)
        action_layout.addWidget(self.btn_assign)

        # Unassign Button
        self.btn_unassign = QPushButton("Atamayı Kaldır")
        self.btn_unassign.setStyleSheet("background-color: #E0E0E0; color: black; font-weight: bold;") # Gray
        self.btn_unassign.clicked.connect(self._on_unassign_clicked)
        action_layout.addWidget(self.btn_unassign)
        
        as_layout.addLayout(action_layout)
        
        # Assignment List
        # Filters specific to this tab
        filter_layout = QHBoxLayout()
        
        self.search_assignments = QLineEdit()
        self.search_assignments.setPlaceholderText("Ders Ara...")
        self.search_assignments.setMinimumWidth(150)
        self.search_assignments.textChanged.connect(lambda: self._load_assignments(self.teacher_combo.currentData()))
        filter_layout.addWidget(self.search_assignments)

        self.chk_show_assigned = QCheckBox("Atanan Dersler")
        self.chk_show_assigned.setChecked(True)
        self.chk_show_assigned.stateChanged.connect(lambda: self._load_assignments(self.teacher_combo.currentData()))
        filter_layout.addWidget(self.chk_show_assigned)

        self.chk_show_unassigned = QCheckBox("Atanmamış Dersler")
        self.chk_show_unassigned.setChecked(True)
        self.chk_show_unassigned.stateChanged.connect(lambda: self._load_assignments(self.teacher_combo.currentData()))
        filter_layout.addWidget(self.chk_show_unassigned)
        
        filter_layout.addStretch()
        
        # Export Button
        self.btn_export = QPushButton("Dışa Aktar (Excel/CSV)")
        self.btn_export.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.btn_export.clicked.connect(self._on_export_clicked)
        filter_layout.addWidget(self.btn_export)
        
        # Move Curriculum Button here and align right
        self.btn_quick_template = QPushButton("Müfredatı Düzenle")
        self.btn_quick_template.setToolTip("Müfredat listesini görüntüle ve düzenle")
        self.btn_quick_template.clicked.connect(self._open_curriculum_view)
        filter_layout.addWidget(self.btn_quick_template)

        as_layout.addLayout(filter_layout)

        self.assign_table = QTableWidget()
        self.assign_table.setColumnCount(4)
        self.assign_table.setHorizontalHeaderLabels(["Ders Adı", "Şube / Not", "Dönem", "Öğretmen"])
        header = self.assign_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Fixed) # Dönem
        self.assign_table.setColumnWidth(2, 90)
        self.assign_table.setAlternatingRowColors(True) # Enable zebra striping
        self.assign_table.setSelectionBehavior(QTableWidget.SelectRows) # Select full rows
        self.assign_table.setSelectionMode(QTableWidget.SingleSelection)
        as_layout.addWidget(self.assign_table)
        
        self.tab_assignments.setLayout(as_layout)
        self.tabs.addTab(self.tab_assignments, "Ders Atamaları")
        
        # TAB 3: Common Courses (Ortak Ders Grupları)
        self.tab_common_courses = QWidget()
        cc_layout = QHBoxLayout()
        
        # Left Panel: Groups list
        left_panel = QVBoxLayout()
        left_panel.addWidget(QLabel("Benzer İsimli Ders Grupları:"))
        
        self.search_common_groups = QLineEdit()
        self.search_common_groups.setPlaceholderText("Ders Ara...")
        self.search_common_groups.setMinimumWidth(220)
        self.search_common_groups.textChanged.connect(self._filter_common_groups)
        left_panel.addWidget(self.search_common_groups)
        
        filter_layout = QHBoxLayout()
        self.chk_hide_single_common = QCheckBox("Tekil Dersleri Gizle")
        self.chk_hide_single_common.setChecked(True)
        self.chk_hide_single_common.stateChanged.connect(lambda: self._filter_common_groups(self.search_common_groups.text()))
        filter_layout.addWidget(self.chk_hide_single_common)
        
        self.btn_manage_templates = QPushButton("Şablonları Yönet")
        self.btn_manage_templates.setStyleSheet("background-color: #2196F3; color: white;")
        self.btn_manage_templates.clicked.connect(self._open_template_manager)
        filter_layout.addWidget(self.btn_manage_templates)
        
        left_panel.addLayout(filter_layout)
        
        # QListWidget is now globally imported
        self.list_common_groups = QListWidget()
        self.list_common_groups.setMinimumWidth(220)
        self.list_common_groups.itemClicked.connect(self._on_common_group_clicked)
        left_panel.addWidget(self.list_common_groups)
        # QPushButton and QMessageBox are now globally imported
        
        auto_group_layout = QHBoxLayout()
        
        self.btn_auto_group_all = QPushButton("Tüm Aynı İsimlileri Grupla")
        self.btn_auto_group_all.clicked.connect(self._auto_group_all_common_courses)
        auto_group_layout.addWidget(self.btn_auto_group_all)
        
        self.btn_auto_group_three = QPushButton("3'lü Grupla")
        self.btn_auto_group_three.clicked.connect(self._auto_group_three_common_courses)
        auto_group_layout.addWidget(self.btn_auto_group_three)
        
        self.btn_clear_all_groups = QPushButton("Tüm Grupları Temizle (Tekilleştir)")
        self.btn_clear_all_groups.setStyleSheet("color: red;")
        self.btn_clear_all_groups.clicked.connect(self._clear_all_common_groups)
        auto_group_layout.addWidget(self.btn_clear_all_groups)
        
        left_panel.addLayout(auto_group_layout)
        
        cc_layout.addLayout(left_panel)
        
        # Right Panel: Selection & Validation
        right_panel = QVBoxLayout()
        right_panel.addWidget(QLabel("Gruptaki Dersler (Birleştirilecekleri Seçin):"))
        
        self.list_common_instances = QListWidget()
        right_panel.addWidget(self.list_common_instances)
        
        # Action layout
        cc_action_layout = QHBoxLayout()
        
        self.chk_filter_by_selected = QCheckBox("Sadece Seçili dersin gruplarını göster")
        self.chk_filter_by_selected.setChecked(False)
        self.chk_filter_by_selected.stateChanged.connect(self._apply_configured_groups_filter)
        cc_action_layout.addWidget(self.chk_filter_by_selected)
        
        cc_action_layout.addStretch()
        
        self.btn_save_common_group = QPushButton("Seçilileri Ortak Ders Olarak Kaydet")
        self.btn_save_common_group.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.btn_save_common_group.clicked.connect(self._on_save_common_group_clicked)
        cc_action_layout.addWidget(self.btn_save_common_group)
        
        right_panel.addLayout(cc_action_layout)
        
        # Bottom Panel: Existing configured groups
        right_panel.addWidget(QLabel("Mevcut Ortak Ders Grupları:"))
        self.table_common_groups = QTableWidget()
        self.table_common_groups.setColumnCount(3)
        self.table_common_groups.setHorizontalHeaderLabels(["Grup No", "Birleşik Dersler (Şubeler)", "İşlem"])
        header_cc = self.table_common_groups.horizontalHeader()
        header_cc.setSectionResizeMode(1, QHeaderView.Stretch)
        header_cc.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header_cc.setSectionResizeMode(2, QHeaderView.Fixed)
        self.table_common_groups.setColumnWidth(2, 60)
        self.table_common_groups.verticalHeader().setVisible(False)
        self.table_common_groups.itemClicked.connect(self._on_configured_group_clicked)
        self.table_common_groups.setSelectionBehavior(QTableWidget.SelectRows)
        right_panel.addWidget(self.table_common_groups)
        
        cc_layout.addLayout(right_panel)
        
        self.tab_common_courses.setLayout(cc_layout)
        self.tabs.addTab(self.tab_common_courses, "Ortak Ders Grupları")
        
        layout.addWidget(self.tabs)
        self.setLayout(layout)
        # Note: Do NOT call _on_teacher_changed(0) here because controller is not set yet.
        
    def _open_template_manager(self):
        from views.template_manager_dialog import TemplateManagerDialog
        if not hasattr(self, 'controller') or not self.controller:
            QMessageBox.warning(self, "Hata", "Sistem yükleniyor, lütfen bekleyin.")
            return
            
        dialog = TemplateManagerDialog(self.controller.model, self)
        if dialog.exec_() == QDialog.Accepted:
            self._load_common_course_groups()
            
    def set_controller(self, controller):
        self.controller = controller
        # Trigger initial load now that we have the controller
        if self.teachers:
             self._on_teacher_changed(0)
             
        # Load curriculum courses
        if hasattr(self.controller.model, 'get_curriculum_courses'):
            # self.controller.model.get_curriculum_courses() # No longer used for combo
            pass
            
        # Load Common Course Groups Data
        if hasattr(self, '_load_common_course_groups'):
            self._load_common_course_groups()
        
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


    def _load_assignments(self, teacher_id):
        """Load courses assigned for this teacher (or ALL)"""
        try:
            self.assign_table.setRowCount(0)
            
            assigned = []
            
            is_all = (teacher_id == -1)
            
            if is_all:
                assigned = self.controller.model.get_all_courses_assigned_to_teachers() # (ders, instance, hoca, teacher_id)
                current_teacher_name = None 
            else:
                assigned = self.controller.model.get_courses_assigned_to_teacher(teacher_id) # (ders, instance)
                current_teacher_name = self.teacher_combo.currentText()
            
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
                self.assign_table.setSpan(row, 0, 1, 4)
                
            # Helper to add row
            def add_row(display_name, db_course_name, detail, semester_text, item_type, teacher_name="", row_teacher_id=None, group_tooltip=""):
                row = self.assign_table.rowCount()
                self.assign_table.insertRow(row)
                
                final_teacher_name = teacher_name
                if item_type == "ASSIGNMENT" and not is_all:
                     final_teacher_name = self.teacher_combo.currentText()
                     row_teacher_id = teacher_id
                
                self.assign_table.setItem(row, 0, QTableWidgetItem(display_name))
                
                item_detail = QTableWidgetItem(detail)
                if group_tooltip:
                    item_detail.setToolTip(group_tooltip)
                self.assign_table.setItem(row, 1, item_detail)
                
                self.assign_table.setItem(row, 2, QTableWidgetItem(semester_text))
                self.assign_table.setItem(row, 3, QTableWidgetItem(final_teacher_name))
                
                self.assign_table.item(row, 0).setData(Qt.UserRole, (item_type, db_course_name, detail, row_teacher_id))

            # --- Section 1: Assigned ---
            target_term = self.term_filter_combo.currentText()
            search_text = self.search_assignments.text().lower() if hasattr(self, 'search_assignments') else ""
            lookup = getattr(self.controller.model, 'semester_lookup', {})
            
            if self.chk_show_assigned.isChecked() and assigned:
                if is_all:
                     add_banner("Tüm Atamalar", "#B3E5FC")
                
                for item in assigned:
                    # Resolve semester strings
                    course_name = item[0]
                    if search_text and search_text not in course_name.lower():
                        continue
                        
                    if is_all:
                        course_code = item[4] if len(item) >= 5 else ""
                    else:
                        course_code = item[2] if len(item) >= 3 else ""
                        
                    display_name = f"{course_name} ({course_code})" if course_code else course_name
                        
                    sem_set = set()
                    if course_code:
                        sem_set = lookup.get(course_code, set())
                    if not sem_set:
                        sem_set = lookup.get(course_name, set())
                    if not sem_set:
                        # try base name split
                        base_name = course_name.split(' (')[0]
                        sem_set = lookup.get(base_name, set())
                        
                    sem_str = ", ".join(sorted(list(sem_set))) if sem_set else "?"
                    
                    if target_term != "Tümü" and target_term not in sem_set:
                        # Skip if it doesn't match the selected filter
                        if target_term == "Bahar" and "Bahar" not in sem_set and "Güz" in sem_set:
                            continue
                        if target_term == "Güz" and "Güz" not in sem_set and "Bahar" in sem_set:
                            continue
                
                    if is_all:
                        # item: (ders, instance, hoca, teacher_id, ders_kodu)
                        try:
                            # Safe unpacking with debug
                            if len(item) >= 4:
                                instance = item[1]
                                hoca = item[2]
                                t_id = item[3]
                            elif len(item) >= 3:
                                # Legacy/Fallback: Missing teacher ID
                                instance = item[1]
                                hoca = item[2]
                                t_id = None # No delete button for these
                            else:
                                print(f"ERROR: Invalid item shape in assigned list: {item}")
                                continue
                                
                            tooltip = self.controller.model.get_departments_for_course_instance(course_name, instance)
                            add_row(display_name, course_name, f"Şube {instance}", sem_str, "ASSIGNMENT", teacher_name=hoca, row_teacher_id=t_id, group_tooltip=tooltip)
                        except IndexError as e:
                            print(f"IndexError unpacking item: {item}. Error: {e}")
                            continue
                    else:
                        instance = item[1]
                        tooltip = self.controller.model.get_departments_for_course_instance(course_name, instance)
                        add_row(display_name, course_name, f"Şube {instance}", sem_str, "ASSIGNMENT", group_tooltip=tooltip)

            # --- Section 2: Unassigned ---
            unassigned = self.controller.model.get_unassigned_courses()
            if unassigned and self.chk_show_unassigned.isChecked():
                add_banner("Atanmamış Dersler", "#FFCDD2") # Light Red
                for item in unassigned:
                     course_name = item[0]
                     instance = item[1]
                     course_code = item[2] if len(item) >= 3 else ""
                     display_name = f"{course_name} ({course_code})" if course_code else course_name

                     if search_text and search_text not in course_name.lower():
                         continue
                         
                     # Resolve semester
                     sem_set = set()
                     if course_code:
                         sem_set = lookup.get(course_code, set())
                     if not sem_set:
                         sem_set = lookup.get(course_name, set())
                     if not sem_set:
                         base_name = course_name.split(' (')[0]
                         sem_set = lookup.get(base_name, set())
                     
                     sem_str = ", ".join(sorted(list(sem_set))) if sem_set else "?"

                     # Apply semester filter
                     if target_term != "Tümü" and target_term not in sem_set:
                         if target_term == "Bahar" and "Bahar" not in sem_set and "Güz" in sem_set:
                             continue
                         if target_term == "Güz" and "Güz" not in sem_set and "Bahar" in sem_set:
                             continue

                     tooltip = self.controller.model.get_departments_for_course_instance(course_name, instance)
                     add_row(display_name, course_name, f"Şube {instance}", sem_str, "UNASSIGNED", teacher_name="-", row_teacher_id=None, group_tooltip=tooltip)
            
        except Exception as e:
            print(f"Error loading assignments: {e}")
            import traceback
            traceback.print_exc()


    def _get_selected_assignment_data(self):
        """Get metadata from the currently selected row in assign_table"""
        row = self.assign_table.currentRow()
        if row < 0: return None
        item = self.assign_table.item(row, 0)
        if not item: return None
        return item.data(Qt.UserRole)

    def _on_assign_clicked(self):
        """Assign selected course from table to the teacher currently in filter"""
        data = self._get_selected_assignment_data()
        if not data:
             QMessageBox.warning(self, "Uyarı", "Lütfen listeden (Atanmamış Dersler kısmından) bir ders seçiniz.")
             return
             
        item_type, course_name, detail, current_tid = data
        target_teacher_id = self.teacher_combo.currentData()
        target_teacher_name = self.teacher_combo.currentText()
        
        if target_teacher_id is None or target_teacher_id == -1:
             QMessageBox.warning(self, "Hata", "Lütfen dersi atamak istediğiniz öğretmeni üstten seçiniz.")
             return

        # detail is "Şube {instance}"
        instance = int(detail.replace("Şube ", "")) if "Şube" in detail else 1

        # Confirmation
        msg = f"'{course_name}' (Şube {instance}) dersini {target_teacher_name} öğretmenine atamak istediğinize emin misiniz?"
        if QMessageBox.question(self, "Atama Onayı", msg, QMessageBox.Yes | QMessageBox.No) == QMessageBox.No:
             return

        try:
            success = self.controller.model.assign_teacher_to_course(target_teacher_id, course_name, instance)
            if success:
                self._load_assignments(target_teacher_id)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Atama başarısız: {e}")

    def _on_unassign_clicked(self):
        """Remove assignment for selected course in table"""
        data = self._get_selected_assignment_data()
        if not data:
             QMessageBox.warning(self, "Uyarı", "Lütfen listeden atamasını kaldırmak istediğiniz dersi seçiniz.")
             return
             
        item_type, course_name, detail, teacher_id = data
        
        if item_type != "ASSIGNMENT" or teacher_id is None:
             QMessageBox.warning(self, "Uyarı", "Bu ders zaten atanmamış veya silinebilir bir ataması yok.")
             return

        # detail is "Şube {instance}"
        instance = int(detail.replace("Şube ", "")) if "Şube" in detail else 1

        # Confirm
        msg = f"'{course_name}' (Şube {instance}) dersinin atamasını kaldırmak istediğinize emin misiniz?"
        if QMessageBox.question(self, "Kaldırma Onayı", msg, QMessageBox.Yes | QMessageBox.No) == QMessageBox.No:
             return

        try:
            with self.controller.model.conn:
                 self.controller.model.conn.execute(
                     "DELETE FROM Ders_Ogretmen_Iliskisi WHERE ogretmen_id=? AND ders_adi=? AND ders_instance=?",
                     (teacher_id, course_name, instance)
                 )
            self._load_assignments(self.teacher_combo.currentData())
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kaldırma işlemi başarısız: {e}")


            
    # Removed _on_want_clicked and _on_block_clicked
        
    def _on_export_clicked(self):
        """Export the assignment table data to Excel or CSV"""
        try:
            if not hasattr(self.controller.model, 'get_all_courses_assigned_to_teachers'):
                QMessageBox.warning(self, "Hata", "Dışa aktarma fonksiyonu modelde bulunamadı.")
                return
                
            # Generate default filename
            parent_view = self.parent()
            faculty_prefix = "Genel"
            semester = "Bahar"
            year = "2025-2026"
            if parent_view:
                if hasattr(parent_view, 'filter_combo_faculty') and parent_view.filter_combo_faculty.currentText() != "Tümü":
                    fac_name = parent_view.filter_combo_faculty.currentText()
                    faculty_prefix = "".join([w[0].upper() for w in fac_name.split() if w.lower() not in ["ve", "ile"]])
                
                if hasattr(parent_view, 'radio_guz') and parent_view.radio_guz.isChecked(): semester = "Güz"
                elif hasattr(parent_view, 'radio_bahar') and parent_view.radio_bahar.isChecked(): semester = "Bahar"
                elif hasattr(parent_view, 'radio_yaz') and parent_view.radio_yaz.isChecked(): semester = "Yaz"
                
                if hasattr(parent_view, 'filter_combo_year') and parent_view.filter_combo_year.currentText() != "Tümü":
                    year = parent_view.filter_combo_year.currentText()

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
                # Fetch all data regardless of filter
                assigned = self.controller.model.get_all_courses_assigned_to_teachers()
                unassigned = self.controller.model.get_unassigned_courses()
                
                if file_path.endswith('.xlsx'):
                    # Fetch schedule data for the master grid
                    schedule_data = self.controller.model.get_master_schedule_data()
                    dept_data = self.controller.model.get_department_course_categories()
                    
                    # Pass them to the new unified exporter
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
            
    def _open_curriculum_view(self):
        """Open Curriculum View"""
        from views.curriculum_view import CurriculumViewDialog # Lazy import
        dialog = CurriculumViewDialog(self.controller, self)
        # We don't necessarily wait for exec result to refresh unless we want to
        dialog.exec_()
        # Refresh course list in case changes happened
        # if hasattr(self.controller.model, 'get_curriculum_courses'):
        #      courses = self.controller.model.get_curriculum_courses()
        #      self._update_course_combo(courses)

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
                    elif data['action_type'] == 'room':
                        # Update Room/Floor Preference
                        self.controller.handle_teacher_room_pref_change(data['teacher_id'], data['room'])
                        QMessageBox.information(self, "Bilgi", "Oda/Kat kısıtı güncellendi.")
                    else:
                        # Add Unavailability Slot Only
                        self.controller.add_teacher_unavailability(
                            data['teacher_id'], 
                            data['day'], 
                            data['start'], 
                            data['end'],
                            data['yil'],
                            data['donem'],
                            data['desc']
                        )
        except Exception as e:
            print(f"CRASH in _on_add_clicked: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Hata", f"Ekleme penceresi açılırken hata: {str(e)}")


    def _on_room_pref_changed(self, text):
        """Handle room preference change"""
        try:
            teacher_id = self.teacher_combo.currentData()
            if teacher_id is not None and teacher_id != -1 and hasattr(self, 'controller'):
                 self.controller.handle_teacher_room_pref_change(teacher_id, text)
        except Exception as e:
            print(f"Error in _on_room_pref_changed: {e}")

    def update_table(self, data):
        """Update table with availability data (Slots + Spans)"""
        self.table.setRowCount(0)
        
        # Get selected filter
        target_term = self.term_filter_combo.currentText() # "Tümü", "Güz", "Bahar", "Yaz"
        
        filtered_data = []
        for item in data:
            if item.get('type') == 'span':
                # Populate global pref fields
                span_val = item.get('span_value', 0)
                room_txt = item.get('room_pref', '')
                
                # Update but block signals temporarily to avoid triggering save loops
                self.span_combo.blockSignals(True)
                idx = self.span_combo.findData(span_val)
                if idx >= 0:
                    self.span_combo.setCurrentIndex(idx)
                self.span_combo.blockSignals(False)
                
                self.room_pref_input.blockSignals(True)
                self.room_pref_input.setText(room_txt)
                self.room_pref_input.blockSignals(False)
                
            elif item.get('type') == 'slot':
                donem = item.get('donem', 'Hepsi')
                if target_term != "Tümü" and donem != "Hepsi" and donem != target_term:
                    continue # Skip this slot if it doesn't match the table filter
                    
            filtered_data.append(item)
            
        for item in filtered_data:
            # item is a dict now
            teacher_name = item.get('teacher_name', '-')
            item_type = item.get('type')
            
            type_text = "-"
            detail_text = "-"
            desc_text = "-"
            del_type = ""
            del_id = -1
            
            if item_type == 'span':
                val = item.get('span_value', 0)
                if val == 0:
                    continue # Do not show "0 Günlük Blok" in the Unavailability table
                type_text = "Blok Kısıtı"
                detail_text = f"{val} Günlük Blok"
                desc_text = "-"
                term_text = "Hepsi"
                del_type = 'span'
                del_id = item.get('teacher_id')
                
            elif item_type == 'slot':
                type_text = "Saat Kısıtı"
                day = item.get('day')
                start = item.get('start')
                end = item.get('end')
                detail_text = f"{day} {start}-{end}"
                desc_text = item.get('description', '')
                yil = item.get('yil', 'Hepsi')
                donem = item.get('donem', 'Hepsi')
                if yil == 'Hepsi' and donem == 'Hepsi':
                    term_text = 'Hepsi'
                elif yil == 'Hepsi':
                    term_text = donem
                elif donem == 'Hepsi':
                    term_text = yil
                else:
                    term_text = f"{yil} {donem}"
                del_type = 'slot'
                del_id = item.get('id')

            current_row = self.table.rowCount()
            self.table.insertRow(current_row)
            
            self.table.setItem(current_row, 0, QTableWidgetItem(teacher_name))
            self.table.setItem(current_row, 1, QTableWidgetItem(type_text))
            self.table.setItem(current_row, 2, QTableWidgetItem(term_text))
            self.table.setItem(current_row, 3, QTableWidgetItem(detail_text))
            self.table.setItem(current_row, 4, QTableWidgetItem(desc_text))
            
            delete_btn = QPushButton("Sil")
            delete_btn.clicked.connect(partial(self._on_delete_clicked, del_type, del_id))
            self.table.setCellWidget(current_row, 5, delete_btn)

    def _on_delete_clicked(self, item_type, item_id):
        """Confirm before deleting"""
        try:
            msg = "Bu saat kısıtı kaydını silmek istediğinize emin misiniz?"
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

    # ════════════════════════════════════════════════════════════════
    # COMMON COURSE GROUPS TAB LOGIC
    # ════════════════════════════════════════════════════════════════

    def _load_common_course_groups(self):
        """Load common course groups into list and table"""
        if not hasattr(self, 'controller') or not hasattr(self.controller, 'model'):
            return
            
        # 1. Load left panel (similar name groups)
        self.list_common_groups.clear()
        if hasattr(self.controller.model, 'get_similar_course_groups'):
            similar_groups = self.controller.model.get_similar_course_groups()
            # QListWidgetItem is globally imported
            for base_name, count in similar_groups:
                item = QListWidgetItem(f"{base_name} ({count} Seçenek)")
                item.setData(Qt.UserRole, count)
                item.setData(Qt.UserRole + 1, base_name)
                self.list_common_groups.addItem(item)
                
        # 2. Load bottom panel (configured groups)
        self.table_common_groups.setRowCount(0)
        self.list_common_instances.clear() # Clear selection panel just in case
        
        if hasattr(self.controller.model, 'get_common_course_groups'):
            configured_groups = self.controller.model.get_common_course_groups()
            
            for row_idx, grp_data in enumerate(configured_groups):
                self.table_common_groups.insertRow(row_idx)
                
                g_id = grp_data['grup_id']
                courses = grp_data['courses']
                
                # Format courses display
                course_strs = []
                all_bolumler = set()
                for c in courses:
                    course_strs.append(f"{c['ders_adi']} (Şube {c['ders_instance']}, Bölüm: {c['bolumler']})")
                    all_bolumler.add(c['bolumler'])
                
                self.table_common_groups.setItem(row_idx, 0, QTableWidgetItem(str(g_id)))
                
                joined_item = QTableWidgetItem(" | ".join(course_strs))
                joined_item.setToolTip("\\n".join(course_strs))
                self.table_common_groups.setItem(row_idx, 1, joined_item)

                # Display departments for the group
                bolum_text = ", ".join(sorted(list(all_bolumler)))
                self.table_common_groups.setItem(row_idx, 2, QTableWidgetItem(bolum_text))
                
                # Delete Group Button
                btn_delete = QPushButton("Grup Sil")
                btn_delete.setStyleSheet("color: red;")
                btn_delete.clicked.connect(lambda checked, gid=g_id: self._on_delete_common_group_clicked(gid))
                self.table_common_groups.setCellWidget(row_idx, 3, btn_delete)
                
        # 3. Apply filter using current search text to hide single-variation courses correctly on load
        self._filter_common_groups(self.search_common_groups.text())
        
        # 4. Apply selection filter
        self._apply_configured_groups_filter()

    def _apply_configured_groups_filter(self):
        """Filter right side table based on left side selection if checkbox is checked"""
        is_checked = self.chk_filter_by_selected.isChecked()
        selected_base_name = None
        
        if is_checked:
            current_item = self.list_common_groups.currentItem()
            if current_item:
                selected_base_name = current_item.data(Qt.UserRole + 1)
                
        for row in range(self.table_common_groups.rowCount()):
            if not is_checked or not selected_base_name:
                self.table_common_groups.setRowHidden(row, False)
                continue
                
            item = self.table_common_groups.item(row, 1)
            if item and selected_base_name in item.text():
                self.table_common_groups.setRowHidden(row, False)
            else:
                self.table_common_groups.setRowHidden(row, True)

    def _on_configured_group_clicked(self, item):
        """When a group is clicked, select its base name on the left and check its items in the middle"""
        row = item.row()
        grup_id_str = self.table_common_groups.item(row, 0).text()
        if not grup_id_str.isdigit(): return
        target_grup_id = int(grup_id_str)
        
        course_text = self.table_common_groups.item(row, 1).text()
        base_name = course_text.split(' (Şube')[0].strip()
        
        # Select base name in the left list
        for i in range(self.list_common_groups.count()):
            list_item = self.list_common_groups.item(i)
            if list_item.data(Qt.UserRole + 1) == base_name:
                self.list_common_groups.setCurrentItem(list_item)
                self._on_common_group_clicked(list_item)
                break
                
        # Check the items in the middle list
        for i in range(self.list_common_instances.count()):
            mid_item = self.list_common_instances.item(i)
            if f"[Grup: {target_grup_id}]" in mid_item.text():
                mid_item.setCheckState(Qt.Checked)
            else:
                mid_item.setCheckState(Qt.Unchecked)

    def _auto_group_all_common_courses(self):
        # QMessageBox is globally imported
        reply = QMessageBox.question(self, 'Otomatik Gruplama', 
            "Mevcut sistemde birden fazla şubesi olan (aynı isim ve krediye sahip) TÜM DERSLER kendi adıyla oluşturulacak ortak gruplara otomatik olarak EKLENECEKTİR.\n\nBu işlemi onaylıyor musunuz?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            
        if reply == QMessageBox.Yes:
            result = self.controller.model.auto_group_all_common_courses()
            if result.get("success"):
                QMessageBox.information(self, "Başarılı", result.get("message", "İşlem başarılı."))
                self._load_common_course_groups()
                # Clear lists to prevent stale selection
                self.list_common_instances.clear()
            else:
                QMessageBox.warning(self, "Hata", result.get("message", "Bir hata oluştu."))

    def _auto_group_three_common_courses(self):
        reply = QMessageBox.question(self, "3'lü Gruplama", 
            "Mevcut sistemde birden fazla şubesi olan TÜM DERSLER en fazla 3 şube içerecek şekilde alt gruplara (Örn: Ders 1. Grup, Ders 2. Grup) ayrılacaktır.\n\nÖzellikle çok bölümlü büyük kapasiteli derslerin çakışmasını önlemek için idealdir. Onaylıyor musunuz?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            
        if reply == QMessageBox.Yes:
            result = self.controller.model.auto_group_all_common_courses(chunk_size=3)
            if result.get("success"):
                QMessageBox.information(self, "Başarılı", result.get("message", "İşlem başarılı."))
                self._load_common_course_groups()
                self.list_common_instances.clear()
            else:
                QMessageBox.warning(self, "Hata", result.get("message", "Bilinmeyen hata."))

    def _clear_all_common_groups(self):
        reply = QMessageBox.question(self, "Tüm Grupları Temizle", 
            "Oluşturulmuş TÜM Ortak Ders Grupları silinecek ve dersler tamamen tekilleştirilecektir.\n\nBu işlem geri alınamaz. Onaylıyor musunuz?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            
        if reply == QMessageBox.Yes:
            result = self.controller.model.clear_all_common_groups()
            if result.get("success"):
                QMessageBox.information(self, "Başarılı", result.get("message", "Tüm gruplar temizlendi."))
                self._load_common_course_groups()
                self.list_common_instances.clear()
            else:
                QMessageBox.warning(self, "Hata", result.get("message", "Bilinmeyen hata."))

    def _filter_common_groups(self, text):
        """Filter the left panel list of common groups"""
        search_text = text.lower()
        hide_single = self.chk_hide_single_common.isChecked()
        for i in range(self.list_common_groups.count()):
            item = self.list_common_groups.item(i)
            count = item.data(Qt.UserRole)
            base_name = item.data(Qt.UserRole + 1).lower()
            
            should_hide = False
            if hide_single and count <= 1:
                should_hide = True
            elif search_text not in base_name:
                should_hide = True
                
            item.setHidden(should_hide)

    def _on_common_group_clicked(self, item):
        """Populate the middle panel with instances of the selected base name"""
        base_name = item.data(Qt.UserRole + 1)
        self.list_common_instances.clear()
        
        if hasattr(self, 'controller') and hasattr(self.controller.model, 'get_courses_by_base_name'):
            instances = self.controller.model.get_courses_by_base_name(base_name)
            
            # QListWidgetItem is globally imported
            for inst in instances:
                # Add checkbox item
                grup_info = f" [Grup: {inst['grup_id']}]" if inst.get('grup_id') else ""
                list_item = QListWidgetItem(f"{inst['ders_adi']} (Şube {inst['ders_instance']} - {inst['bolumler']}){grup_info}")
                list_item.setFlags(list_item.flags() | Qt.ItemIsUserCheckable)
                list_item.setCheckState(Qt.Unchecked)
                
                # Store tuple data
                list_item.setData(Qt.UserRole, (inst['ders_adi'], inst['ders_instance'], inst['t'], inst['u'], inst['l']))
                self.list_common_instances.addItem(list_item)
                
        self._apply_configured_groups_filter()


    def _on_save_common_group_clicked(self):
        """Save checked items as a new common group"""
        selected_courses = []
        ref_t, ref_u, ref_l = None, None, None
        
        for i in range(self.list_common_instances.count()):
            item = self.list_common_instances.item(i)
            if item.checkState() == Qt.Checked:
                data = item.data(Qt.UserRole) # (ders_adi, ders_instance, t, u, l)
                ders_adi, ders_instance, t, u, l = data
                selected_courses.append((ders_adi, ders_instance))
                
                # Validation logic: Ensure T/U/L structure matches
                if ref_t is None:
                    ref_t, ref_u, ref_l = t, u, l
                else:
                    if ref_t != t or ref_u != u or ref_l != l:
                        QMessageBox.warning(self, "Yapı Uyuşmazlığı", "Gruplanmak istenen derslerin Kredi/Saat yapıları (T/U/L) birbirinden farklı olamaz!")
                        return
        
        if len(selected_courses) < 2:
            QMessageBox.warning(self, "Eksik Seçim", "Ortak ders grubu oluşturmak için en az 2 ders seçmelisiniz.")
            return
            
        msg = "Seçili dersler ortak ders grubu olarak birleştirilecek. Bu dersler scheduler'da tek blok gibi değerlendirilecektir.\nOnaylıyor musunuz?"
        if QMessageBox.question(self, "Grup Onayı", msg, QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            if hasattr(self.controller, 'save_common_course_group'):
                success = self.controller.save_common_course_group(selected_courses)
                if success:
                    QMessageBox.information(self, "Başarılı", "Ortak ders grubu başarıyla kaydedildi.")
                    self._load_common_course_groups()
            else:
                 QMessageBox.warning(self, "Hata", "Controller metodu bulunamadı.")


    def _on_delete_common_group_clicked(self, grup_id):
        """Delete an existing group"""
        msg = f"Grup (ID: {grup_id}) silinecektir. Emin misiniz?"
        if QMessageBox.question(self, "Silme Onayı", msg, QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            if hasattr(self.controller, 'delete_common_course_group'):
                success = self.controller.delete_common_course_group(grup_id)
                if success:
                    QMessageBox.information(self, "Başarılı", "Grup silindi.")
                    self._load_common_course_groups()
            else:
                QMessageBox.warning(self, "Hata", "Controller metodu bulunamadı.")
