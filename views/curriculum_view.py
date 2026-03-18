# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, 
    QTableWidgetItem, QHeaderView, QComboBox, QLabel, 
    QPushButton, QLineEdit, QRadioButton, QButtonGroup,
    QCheckBox, QWidget, QScrollArea, QFrame, QMessageBox,
    QSizePolicy
)
from PyQt5.QtCore import Qt

class CurriculumViewDialog(QDialog):
    def __init__(self, controller, parent=None, enable_delete_mode=False):
        super().__init__(parent)
        self.controller = controller
        self.enable_delete_mode = enable_delete_mode # Store initial state
        self.setWindowTitle("Müfredat Görüntüleme")
        self.setGeometry(200, 200, 1250, 750) # Increased Size (+150px)
        
        # Fix for dropdowns appearing as separate windows
        self.setStyleSheet("""
            QComboBox { combobox-popup: 0; }
        """)
        
        self.pool_checkboxes = {} # Map pool_code -> QCheckBox
        
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout()
        
        # --- Filter Row 1: Structural ---
        row1_layout = QHBoxLayout()
        
        # Faculty
        self.combo_faculty = QComboBox()
        self.combo_faculty.addItem("Tüm Fakülteler", None)
        self.combo_faculty.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed) # Responsive
        self.combo_faculty.currentIndexChanged.connect(self._on_filter_changed)
        row1_layout.addWidget(QLabel("Fakülte:"))
        row1_layout.addWidget(self.combo_faculty, 1) # Stretch factor 1
        
        # Department
        self.combo_dept = QComboBox()
        self.combo_dept.addItem("Tüm Bölümler", None)
        self.combo_dept.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed) # Responsive
        self.combo_dept.currentIndexChanged.connect(self._on_dept_changed) # Special handler
        row1_layout.addWidget(QLabel("Bölüm:"))
        row1_layout.addWidget(self.combo_dept, 1) # Stretch factor 1
        
        # Year/Pool Filter
        self.combo_year = QComboBox()
        self.combo_year.addItem("Tümü", None) # Changed from "Tüm Sınıflar"
        for i in range(1, 5):
            self.combo_year.addItem(f"{i}. Sınıf", i)
        self.combo_year.addItem("Havuz Dersleri", 99) 
        self.combo_year.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed) # Responsive
        self.combo_year.currentIndexChanged.connect(self._on_filter_changed)
        row1_layout.addWidget(QLabel("Sınıf / Havuz:"))
        row1_layout.addWidget(self.combo_year, 1) # Stretch factor 1
        
        # Script runner button
        self.btn_run_script = QPushButton("Müfredat İsimlerini Temizle")
        self.btn_run_script.setStyleSheet("background-color: #ff9800; color: white; font-weight: bold;")
        self.btn_run_script.clicked.connect(self._run_sanitize_script)
        row1_layout.addWidget(self.btn_run_script)
        
        # row1_layout.addStretch() # REMOVED: Filters now fill the row
        layout.addLayout(row1_layout)
        
        # --- Filter Row 2: Type & Search ---
        row2_layout = QHBoxLayout()

        # Semester Filter (NEW)
        row2_layout.addWidget(QLabel("Dönem:"))
        self.sem_group = QButtonGroup(self)
        self.rb_sem_all = QRadioButton("Hepsi")
        self.rb_sem_guz = QRadioButton("Güz")
        self.rb_sem_bahar = QRadioButton("Bahar")
        self.rb_sem_yaz = QRadioButton("Yaz")
        
        self.rb_sem_all.setChecked(True) # Default
        
        self.sem_group.addButton(self.rb_sem_all)
        self.sem_group.addButton(self.rb_sem_guz)
        self.sem_group.addButton(self.rb_sem_bahar)
        self.sem_group.addButton(self.rb_sem_yaz)
        
        self.rb_sem_all.toggled.connect(self._on_filter_changed)
        self.rb_sem_guz.toggled.connect(self._on_filter_changed)
        self.rb_sem_bahar.toggled.connect(self._on_filter_changed)
        self.rb_sem_yaz.toggled.connect(self._on_filter_changed)
        
        row2_layout.addWidget(self.rb_sem_all)
        row2_layout.addWidget(self.rb_sem_guz)
        row2_layout.addWidget(self.rb_sem_bahar)
        row2_layout.addWidget(self.rb_sem_yaz)
        
        row2_layout.addSpacing(20)
        
        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Ders Adı/Kodu...") # Updated text
        self.search_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed) # Responsive
        self.search_input.textChanged.connect(self._display_only_refresh)
        row2_layout.addWidget(QLabel("Ara:"))
        row2_layout.addWidget(self.search_input, 1) # Stretch factor 1 (Takes available space)
        
        # Spacer
        row2_layout.addSpacing(10) # Reduced from 20
        
        # Course Type Filter (Radio Group)
        self.type_group = QButtonGroup(self)
        
        self.rb_all = QRadioButton("Hepsi")
        self.rb_all.setChecked(True)
        self.rb_core = QRadioButton("Sadece Zorunlu")
        self.rb_elective = QRadioButton("Sadece Havuz")
        
        self.type_group.addButton(self.rb_all)
        self.type_group.addButton(self.rb_core)
        self.type_group.addButton(self.rb_elective)

        
        self.rb_all.toggled.connect(self._on_filter_changed)
        self.rb_core.toggled.connect(self._on_filter_changed)
        self.rb_elective.toggled.connect(self._on_filter_changed)
        
        row2_layout.addWidget(QLabel("Ders Tipi:"))
        row2_layout.addWidget(self.rb_all)
        row2_layout.addWidget(self.rb_core)
        row2_layout.addWidget(self.rb_elective)
        
        # Delete Mode Checkbox
        row2_layout.addSpacing(20)
        self.chk_delete_mode = QCheckBox("Ders Silme Modu")
        self.chk_delete_mode.setStyleSheet("color: red; font-weight: bold;")
        self.chk_delete_mode.setChecked(self.enable_delete_mode) # Set initial state
        self.chk_delete_mode.stateChanged.connect(self._toggle_delete_mode) 
        row2_layout.addWidget(self.chk_delete_mode)
        
        # Group Courses Checkbox (NEW)
        row2_layout.addSpacing(20)
        self.chk_group_courses = QCheckBox("Benzer İsimleri Grupla")
        self.chk_group_courses.setStyleSheet("color: #2196F3; font-weight: bold;")
        self.chk_group_courses.setChecked(False) # Default OFF
        self.chk_group_courses.stateChanged.connect(self._on_group_toggle_changed) # NEW handler
        row2_layout.addWidget(self.chk_group_courses)

        # row2_layout.addStretch() # REMOVED: Search input expands instead
        layout.addLayout(row2_layout)
        
        # --- Filter Row 3: Group Specific (NEW) ---
        self.group_filter_container = QFrame()
        self.group_filter_container.setFrameShape(QFrame.NoFrame)
        self.group_filter_container.setVisible(False) # Hidden by default
        
        row3_layout = QHBoxLayout(self.group_filter_container)
        row3_layout.setContentsMargins(5, 5, 5, 5)
        
        self.chk_hide_single = QCheckBox("Tek Girdili Grupları Gösterme")
        self.chk_hide_single.setStyleSheet("color: #673AB7; font-weight: bold;")
        self.chk_hide_single.setChecked(True) # Enabled by default
        self.chk_hide_single.stateChanged.connect(self._on_filter_changed)
        row3_layout.addWidget(self.chk_hide_single)
        
        row3_layout.addSpacing(20)
        self.btn_edit_common_courses = QPushButton("Ortak Dersleri Düzenle")
        self.btn_edit_common_courses.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; padding: 5px 15px;")
        self.btn_edit_common_courses.clicked.connect(self._on_edit_common_courses_clicked)
        row3_layout.addWidget(self.btn_edit_common_courses)

        row3_layout.addStretch()
        
        layout.addWidget(self.group_filter_container)
        
        # --- Dynamic Pool Filter Row (Row 3 - Hidden by default) ---
        self.pool_filter_container = QFrame()
        self.pool_filter_container.setFrameShape(QFrame.StyledPanel)
        self.pool_filter_container.setVisible(False) # Hidden initially
        self.pool_filter_container.setFixedHeight(45) # Explicitly constrain height
        
        pool_layout = QHBoxLayout(self.pool_filter_container)
        pool_layout.setContentsMargins(5, 5, 5, 5)
        
        pool_layout.addWidget(QLabel("Havuzları Filtrele:"))
        
        # Scroll Area for checkboxes if many
        self.pool_scroll = QScrollArea()
        self.pool_scroll.setWidgetResizable(True)
        self.pool_scroll.setFixedHeight(40) # Ensure content fits
        self.pool_scroll.setFrameShape(QFrame.NoFrame)
        self.pool_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff) # Horizontal only
        
        self.pool_checkbox_widget = QWidget()
        self.pool_checkbox_layout = QHBoxLayout(self.pool_checkbox_widget)
        self.pool_checkbox_layout.setContentsMargins(0, 0, 0, 0)
        self.pool_checkbox_layout.addStretch() # Left align
        
        self.pool_scroll.setWidget(self.pool_checkbox_widget)
        pool_layout.addWidget(self.pool_scroll)
        
        layout.addWidget(self.pool_filter_container)

        # --- Table ---
        self.table = QTableWidget()
        self.table.setColumnCount(10) # Increased to 10 (Added Semester)
        self.table.setHorizontalHeaderLabels([
            "Ders Kodu", "Ders Adı", "T", "U", "L", "AKTS", "Dönem", "Tip", "Bölüm/Havuz", "İşlem"
        ])
        self.table.cellClicked.connect(self._on_cell_clicked)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents) 
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents) 
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents) 
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents) 
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents) 
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents) # Dönem
        
        # Halve width of Type (Index 7)
        header.setSectionResizeMode(7, QHeaderView.Fixed) 
        self.table.setColumnWidth(7, 100) 

        header.setSectionResizeMode(9, QHeaderView.Fixed) 
        self.table.setColumnWidth(9, 80) 
        
        layout.addWidget(self.table)
        
        
        self.setLayout(layout)
        
    def _load_data(self):
        if hasattr(self.controller.model, 'get_faculties'):
             faculties = self.controller.model.get_faculties()
             for f_id, f_name in faculties:
                 self.combo_faculty.addItem(f_name, f_id)
        self._refresh_table()

    def _run_sanitize_script(self):
        msg = "Curriculum isimlerini yabancı dilden arındırıp, roma rakamlarını düzeltmek ister misiniz?\n\nBu işlem veri tabanını (curriculum_data.py) doğrudan güncelleyecektir."
        reply = QMessageBox.question(self, "İsimleri Temizle", msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            import subprocess
            import os
            script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts", "sanitize_course_names.py")
            try:
                result = subprocess.run(["python", script_path], capture_output=True, text=True)
                if result.returncode == 0:
                    QMessageBox.information(self, "Başarılı", "Müfredat isimleri başarıyla temizlendi!\n\nDeğişikliklerin ekrana yansıması için programı yeniden başlatmanız gerekebilir.")
                else:
                    QMessageBox.warning(self, "Hata", f"Betik çalışırken bir hata oluştu:\n{result.stderr}")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Betik çalıştırılamadı:\n{str(e)}")

    def _on_dept_changed(self):
        # Trigger general refresh, which handles visibility
        self._on_filter_changed()

    def _on_filter_changed(self):
        # Handle Faculty -> Dept cascading
        sender = self.sender()
        if sender == self.combo_faculty:
            fac_id = self.combo_faculty.currentData()
            self.combo_dept.blockSignals(True)
            self.combo_dept.clear()
            self.combo_dept.addItem("Tüm Bölümler", None)
            if fac_id:
                depts = self.controller.model.get_departments_by_faculty(fac_id)
                for d_id, d_name in depts:
                    self.combo_dept.addItem(d_name, d_id)
            self.combo_dept.blockSignals(False)
            
            # Hide pool filter if faculty changed (dept reset to none)
            self.pool_filter_container.setVisible(False)
                    
        self._refresh_table()

    def _on_group_toggle_changed(self, state):
        """Handle 'Benzer İsimleri Grupla' toggle"""
        is_active = (state == Qt.Checked)
        self.group_filter_container.setVisible(is_active)
        self._on_filter_changed()

    def _on_edit_common_courses_clicked(self):
        if hasattr(self.controller, 'open_common_courses_tab'):
            self.controller.open_common_courses_tab()
        else:
            QMessageBox.warning(self, "Bilgi", "Controller 'open_common_courses_tab' metodu henüz uygulanmadı.")

    def _refresh_table(self):
        # Gather filters
        dept_id = self.combo_dept.currentData()
        year_filter = self.combo_year.currentData() # Now directly int or None
        faculty_id = self.combo_faculty.currentData()

        # Update Pool Filter Visibility Logic
        # Show ONLY IF: Dept is selected AND (Year is None/All OR Year is Havuz/99) AND NOT Grouped
        should_show_pools = False
        is_grouped = self.chk_group_courses.isChecked()
        if dept_id and not is_grouped:
            if year_filter is None or year_filter == 99:
                 should_show_pools = True
        
        self.pool_filter_container.setVisible(should_show_pools)

        search = self.search_input.text().lower()
        
        # Determine Semester Filter
        semester_filter = None
        if self.rb_sem_guz.isChecked(): semester_filter = "Güz"
        elif self.rb_sem_bahar.isChecked(): semester_filter = "Bahar"
        elif self.rb_sem_yaz.isChecked(): semester_filter = "Yaz"
        
        # Fetch Data
        if hasattr(self.controller.model, 'get_all_curriculum_details'):
            # Note: Model currently ignores semester_filter due to DB limitation
            courses = self.controller.model.get_all_curriculum_details(
                dept_id, year_filter, faculty_id, semester_filter=semester_filter
            )
            
            # --- 1. Update Dynamic Pool Checkboxes (Only if Dept Selected) ---
            if dept_id:
                # Find all unique pool codes in this filtered data
                # Row Structure: (..., 10:IsPool, 11:PoolCode)
                current_pool_codes = set()
                for c in courses:
                    if c[10] == 1 and c[11]: # IsPool and HasCode
                        current_pool_codes.add(c[11])
                
                # Update UI Checkboxes
                # Remove obsolete
                for code in list(self.pool_checkboxes.keys()):
                    if code not in current_pool_codes:
                        chk = self.pool_checkboxes.pop(code)
                        self.pool_checkbox_layout.removeWidget(chk)
                        chk.deleteLater()
                
                # Add new
                sorted_codes = sorted(list(current_pool_codes))
                for code in sorted_codes:
                    if code not in self.pool_checkboxes:
                        chk = QCheckBox(code)
                        chk.setChecked(True) # Default visible
                        chk.stateChanged.connect(self._display_only_refresh) # Optimize: don't re-query
                        self.pool_checkboxes[code] = chk
                        # Insert before stretch (which is the last item)
                        count = self.pool_checkbox_layout.count()
                        self.pool_checkbox_layout.insertWidget(count-1, chk)
            else:
                 # Clear all if no dept
                 for chk in self.pool_checkboxes.values():
                     self.pool_checkbox_layout.removeWidget(chk)
                     chk.deleteLater()
                 self.pool_checkboxes.clear()

            # --- 2. Filter Client-Side (Search & Pools & Type & Grouping Mode) ---
            visible_pools = []
            if dept_id and self.pool_filter_container.isVisible():
                 for code, cb in self.pool_checkboxes.items():
                     if cb.isChecked():
                         visible_pools.append(code)

            is_grouped = self.chk_group_courses.isChecked()

            filtered = []
            for c in courses:
                # c structure: ... 8:Detail, 9:SortYear, 10:IsPool, 11:PoolCode
                
                # Filter by Search
                code, name = str(c[0]).lower(), str(c[1]).lower()
                if search and (search not in code and search not in name):
                    continue
                
                is_pool = c[10] # Correct Index
                pool_code = c[11] # Correct Index
                
                # Filter by Type
                if self.rb_core.isChecked() and is_pool == 1: continue
                if self.rb_elective.isChecked() and is_pool == 0: continue
                
                # Filter out ALL pools if we are currently Grouping
                if is_grouped and is_pool == 1: continue
                
                # Dynamic Pool Filter
                if self.pool_filter_container.isVisible():
                     if is_pool == 1 and pool_code:
                         if pool_code not in visible_pools:
                             continue

                filtered.append(c)
            
            # --- 3. Apply Grouping if enabled ---
            is_grouped = self.chk_group_courses.isChecked()
            
            if is_grouped:
                import re
                
                def get_base_name(course_tuple):
                    # Index 10 is is_pool, 11 is pool_code
                    is_pool = course_tuple[10]
                    pool_code = course_tuple[11]
                    
                    if is_pool == 1:
                        # Keep pools grouped together by their pool code
                        pc = str(pool_code).strip().upper() if pool_code else "GENEL"
                        return f"~HAVUZ_{pc}" # Prefix ~ forces it to the bottom of the sort list conceptually, or keeps them clustered
                    
                    # Index 1 is the course name (ders_adi)
                    name = str(course_tuple[1])
                    
                    # Split logic: ignore after ':' or '(Benzer delimiter)' or "-"
                    # Priority: Colon, then Dash. 
                    if ':' in name:
                        base = name.split(':')[0]
                    elif '-' in name:
                        base = name.split('-')[0]
                    else:
                        base = name
                        
                    # Clean up trailing spaces and convert to a comparable format
                    base = base.strip().upper()
                    
                    # Normalizing numbers (Analiz 1 vs Analiz 2) to ensure they are NOT grouped together.
                    # This happens automatically because "Analiz 1" and "Analiz 2" don't have colons, so base names differ.
                    return base

                # Sort by Base Name, then by original Name to keep related ones together
                filtered.sort(key=lambda x: (get_base_name(x), str(x[1])))
                
                # Filter out single-entry groups if requested
                if self.chk_hide_single.isChecked():
                    from collections import defaultdict
                    group_counts = defaultdict(int)
                    # First pass: count entries in each group
                    for c in filtered:
                        group_counts[get_base_name(c)] += 1
                    
                    # Second pass: filter (but always keep pools)
                    final_filtered = []
                    for c in filtered:
                        gn = get_base_name(c)
                        if gn.startswith("~HAVUZ_") or group_counts[gn] > 1:
                            final_filtered.append(c)
                    filtered = final_filtered
                    
            self._populate_table(filtered, is_grouped=is_grouped)

    def _display_only_refresh(self): # Helper for search box
         self._refresh_table()

    def _toggle_delete_mode(self, state):
        """
        Optimized: Only toggle column visibility, do NOT repopulate table.
        This prevents freezing when toggling the checkbox.
        """
        is_delete_mode = (state == Qt.Checked)
        # Column 9 is the Action column
        self.table.setColumnHidden(9, not is_delete_mode)
        
        # We also need to loop through rows to instantiate buttons IF they don't exist yet?
        # Actually, _populate_table creates them but hides column. 
        # Wait, previous logic in _populate_table was:
        # if is_delete_mode: create button
        # This means if we toggled ON, we need buttons. 
        # If we didn't create them initially, we need to create them now.
        # BUT, to be truly fast, we should probably create them ALWAYS but hide the column.
        # OR, we lazily create them here.
        
        if is_delete_mode:
            # Check if first row has button. If not, we might need to populate.
            # But repopulating causes freeze. 
            # Better approach: update _populate_table to ALWAYS create buttons, 
            # and just hide the column.
            pass

    def _display_only_refresh(self): # Helper for search box
         self._refresh_table()

    def _unused_placeholder(self):
        pass

    # ... (Rest of methods) ...

    def _populate_table(self, data, is_grouped=False):
        self.table.setUpdatesEnabled(False) # Optimize performance
        from PyQt5.QtGui import QColor
        self.table.setRowCount(0)
        # Ensure column visibility matches checkbox
        self.table.setColumnHidden(9, not self.chk_delete_mode.isChecked())
        
        current_header = None
        
        # Predefined colors
        CORE_COLOR = "#cfe2f3" # Light Blue
        GROUP_COLOR = "#fffbd7" # Light Yellow for Name Groups
        
        # Pool colors generator (simple consistent hash)
        def get_pool_color(code):
            # List of distinct pastel colors
            colors = ["#e6b8af", "#f4cccc", "#fce5cd", "#fff2cc", "#d9ead3", "#d0e0e3", "#c9daf8", "#d9d2e9"]
            if not code: return "#eeeeee"
            idx = sum(ord(c) for c in code) % len(colors)
            return colors[idx]

        for row_data in data:
            # Indices: 8:Detail, 9:SortYear, 10:IsPool, 11:PoolCode
            detail_text = row_data[8]
            sort_year = row_data[9]
            is_pool = row_data[10]
            _raw_pool_code = row_data[11] 
            course_name = str(row_data[1])
            
            # Normalize Pool Code
            pool_code = str(_raw_pool_code).strip().upper() if _raw_pool_code else ""
            
            # Determine Header Title based on Grouping Mode
            header_title = ""
            banner_color = Qt.gray # Default
            
            if is_grouped:
                if is_pool == 1:
                    # Keep Pool Header behavior even in grouped mode
                    header_title = f"{pool_code} Havuzu" if pool_code else "Genel Havuz"
                    banner_color = get_pool_color(pool_code)
                else:
                    if ':' in course_name:
                        base = course_name.split(':')[0]
                    elif '-' in course_name:
                        base = course_name.split('-')[0]
                    else:
                        base = course_name
                    base = base.strip()
                    header_title = f"Grup: {base}"
                    banner_color = GROUP_COLOR
            else:
                if is_pool == 1:
                    header_title = f"{pool_code} Havuzu" if pool_code else "Genel Havuz"
                    banner_color = get_pool_color(pool_code)
                else:
                    header_title = f"{sort_year}. Sınıf"
                    banner_color = CORE_COLOR
                
            # Insert Header if changed
            if header_title != current_header:
                current_header = header_title
                self._add_header_row(header_title, banner_color)
                
            # Insert Data Row
            row_idx = self.table.rowCount()
            self.table.insertRow(row_idx)
            
            # Values (Skip meta indices 8+)
            # 0..7 (Code...Type) matches Table Columns 0..7
            display_vals = row_data[:8]
            
            for col_idx, val in enumerate(display_vals):
                item = QTableWidgetItem(str(val))
                item.setFlags(item.flags() ^ Qt.ItemIsEditable) 
                self.table.setItem(row_idx, col_idx, item)
            
            # Column 8: Detail (Bölüm/Havuz)
            item_detail = QTableWidgetItem(str(detail_text))
            item_detail.setFlags(item_detail.flags() ^ Qt.ItemIsEditable)
            self.table.setItem(row_idx, 8, item_detail)
            
            # Column 9: Action (Lightweight text item)
            # Store course name in UserRole for easy access
            btn_item = QTableWidgetItem("Sil")
            btn_item.setTextAlignment(Qt.AlignCenter)
            btn_item.setForeground(Qt.red)
            btn_item.setBackground(QColor("#ffebee"))
            btn_item.setFont(self.table.font()) # Default font
            # Make it non-editable but selectable/enabled
            btn_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            btn_item.setData(Qt.UserRole, row_data[1]) # Store Name
            
            self.table.setItem(row_idx, 9, btn_item)
            
        self.table.setUpdatesEnabled(True) # Re-enable updates

    def _on_cell_clicked(self, row, col):
        """Handle cell clicks for custom actions"""
        if col == 9: # Delete Action Column
            item = self.table.item(row, col)
            if item:
                course_name = item.data(Qt.UserRole)
                if course_name:
                    self._on_delete_click(course_name)

    def _on_delete_click(self, course_name):
        """Handle delete action with confirmation"""
        msg = f"'{course_name}' dersini ve ilgili TÜM kayıtlarını (program, tercihler vs.) silmek istediğinize emin misiniz?\n\nBu işlem GERİ ALINAMAZ."
        reply = QMessageBox.question(self, "Ders Silme Onayı", msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            if hasattr(self.controller, 'delete_curriculum_course'):
                success = self.controller.delete_curriculum_course(course_name)
                if success:
                    QMessageBox.information(self, "Başarılı", f"'{course_name}' başarıyla silindi.")
                    self._load_data() # Refresh all
            else:
                QMessageBox.warning(self, "Hata", "Controller delete_curriculum_course metodunu desteklemiyor.")

    def _add_header_row(self, title, color_hex_or_obj=None):
        row_idx = self.table.rowCount()
        self.table.insertRow(row_idx)
        
        # Merge all columns
        self.table.setSpan(row_idx, 0, 1, 9)
        
        header_item = QTableWidgetItem(title)
        header_item.setFlags(Qt.ItemIsEnabled)
        header_item.setTextAlignment(Qt.AlignCenter)
        
        # Handle color input (string or Qt color?)
        from PyQt5.QtGui import QColor, QBrush
        
        brush = QBrush()
        brush.setStyle(Qt.SolidPattern)
        
        # If string, convert to QColor
        if isinstance(color_hex_or_obj, str):
            brush.setColor(QColor(color_hex_or_obj))
        elif color_hex_or_obj: 
             # Assume it works or fallback
             try:
                 brush.setColor(QColor(color_hex_or_obj))
             except:
                 brush.setColor(QColor("#cccccc"))
        else:
            brush.setColor(QColor("#cccccc"))

        header_item.setBackground(brush)
        
        font = header_item.font()
        font.setBold(True)
        header_item.setFont(font)
        
        self.table.setItem(row_idx, 0, header_item)
