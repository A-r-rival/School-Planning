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
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.setWindowTitle("Müfredat Görüntüleme")
        self.setGeometry(200, 200, 1150, 750) # Increased Size (+150px)
        
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
        
        # row1_layout.addStretch() # REMOVED: Filters now fill the row
        layout.addLayout(row1_layout)
        
        # --- Filter Row 2: Type & Search ---
        row2_layout = QHBoxLayout()
        
        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Ders Adı/Kodu...") # Updated text
        self.search_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed) # Responsive
        self.search_input.textChanged.connect(self._on_filter_changed)
        row2_layout.addWidget(QLabel("Ara:"))
        row2_layout.addWidget(self.search_input, 1) # Stretch factor 1 (Takes available space)
        
        # Spacer
        row2_layout.addSpacing(10) # Reduced from 20
        
        # Course Type Filter (Radio Group)
        self.type_group = QButtonGroup(self)
        
        self.rb_all = QRadioButton("Hepsi")
        self.rb_all.setChecked(True)
        self.rb_core = QRadioButton("Sadece Zorunlu")
        self.rb_elective = QRadioButton("Sadece Seçmeli (Havuz)")
        
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
        
        # row2_layout.addStretch() # REMOVED: Search input expands instead
        layout.addLayout(row2_layout)
        
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
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Ders Kodu", "Ders Adı", "T", "U", "L", "AKTS", "Tip", "Bölüm/Havuz"
        ])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents) 
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents) 
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents) 
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents) 
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents) 
        
        layout.addWidget(self.table)
        
        
        self.setLayout(layout)
        
    def _load_data(self):
        if hasattr(self.controller.model, 'get_faculties'):
             faculties = self.controller.model.get_faculties()
             for f_id, f_name in faculties:
                 self.combo_faculty.addItem(f_name, f_id)
        self._refresh_table()

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

    def _refresh_table(self):
        # Gather filters
        dept_id = self.combo_dept.currentData()
        year_filter = self.combo_year.currentData() # Now directly int or None
        faculty_id = self.combo_faculty.currentData()

        # Update Pool Filter Visibility Logic
        # Show ONLY IF: Dept is selected AND (Year is None/All OR Year is Havuz/99)
        should_show_pools = False
        if dept_id:
            if year_filter is None or year_filter == 99:
                 should_show_pools = True
        
        self.pool_filter_container.setVisible(should_show_pools)

        search = self.search_input.text().lower()
        
        # Fetch Data
        if hasattr(self.controller.model, 'get_all_curriculum_details'):
            courses = self.controller.model.get_all_curriculum_details(dept_id, year_filter, faculty_id)
            
            # --- 1. Update Dynamic Pool Checkboxes (Only if Dept Selected) ---
            if dept_id:
                # Find all unique pool codes in this filtered data
                # Row Structure: (..., IsPool=9, PoolCode=10)
                current_pool_codes = set()
                for c in courses:
                    if c[9] == 1 and c[10]: # IsPool and HasCode
                        current_pool_codes.add(c[10])
                
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
                        chk.stateChanged.connect(self._refresh_table_display_only) # Optimize: don't re-query
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

            self.cached_courses = courses # Cache for filtering
            self._filter_and_populate()

    def _refresh_table_display_only(self):
        # Triggered by checkbox toggle, no need to query DB
        if hasattr(self, 'cached_courses'):
            self._filter_and_populate()

    def _filter_and_populate(self):
        filtered = []
        search = self.search_input.text().lower()
        
        # Determines Type Filter
        show_core = self.rb_all.isChecked() or self.rb_core.isChecked()
        show_elective = self.rb_all.isChecked() or self.rb_elective.isChecked()
        
        # Determine Pool Visibility (Set of allowed codes)
        visible_pools = set()
        for code, chk in self.pool_checkboxes.items():
            if chk.isChecked():
                visible_pools.add(code)
        
        for c in self.cached_courses:
            # c: (Code, Name, T, U, L, AKTS, Type, Detail, SortYear, IsPool, PoolCode)
            code_text = str(c[0]) if c[0] else ""
            name = c[1]
            is_pool = c[9]
            pool_code = c[10]
            
            # 1. Search Text (Name OR Code)
            if search:
                # Basic case-insensitive check
                if search not in name.lower() and search not in code_text.lower():
                    continue
                
            # 2. Type Filter
            if is_pool == 0 and not show_core:
                continue
            if is_pool == 1 and not show_elective:
                continue
                
            # 3. Dynamic Pool Toggle (Only if Dept Selected AKA visible_pools has entries potential)
            # If Dept is selected, user manages pool visibility.
            # If Filter Area is Visible... checking visibility of container is proxy
            if self.pool_filter_container.isVisible():
                 if is_pool == 1 and pool_code:
                     if pool_code not in visible_pools:
                         continue

            filtered.append(c)
            
        self._populate_table(filtered)

    # ... (Rest of methods) ...

    def _populate_table(self, data):
        self.table.setRowCount(0)
        current_header = None
        
        # Predefined colors for Core
        CORE_COLOR = "#cfe2f3" # Light Blue
        
        # Pool colors generator (simple consistent hash)
        def get_pool_color(code):
            # List of distinct pastel colors
            colors = ["#e6b8af", "#f4cccc", "#fce5cd", "#fff2cc", "#d9ead3", "#d0e0e3", "#c9daf8", "#d9d2e9"]
            if not code: return "#eeeeee"
            idx = sum(ord(c) for c in code) % len(colors)
            return colors[idx]

        for row_data in data:
            sort_year = row_data[8]
            is_pool = row_data[9]
            _raw_pool_code = row_data[10] # Added Pool Code
            
            # Normalize Pool Code for Grouping
            pool_code = str(_raw_pool_code).strip().upper() if _raw_pool_code else ""
            
            # Determine Header Title
            header_title = ""
            banner_color = Qt.gray # Default
            
            if is_pool == 1:
                # Group by Pool Code
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
            display_vals = row_data[:8]
            
            for col_idx, val in enumerate(display_vals):
                item = QTableWidgetItem(str(val))
                item.setFlags(item.flags() ^ Qt.ItemIsEditable) 
                self.table.setItem(row_idx, col_idx, item)

    def _add_header_row(self, title, color_hex_or_obj=None):
        row_idx = self.table.rowCount()
        self.table.insertRow(row_idx)
        
        # Merge all columns
        self.table.setSpan(row_idx, 0, 1, 8)
        
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
