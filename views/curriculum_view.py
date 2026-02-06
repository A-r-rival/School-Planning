# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, 
    QTableWidgetItem, QHeaderView, QComboBox, QLabel, 
    QPushButton, QLineEdit
)
from PyQt5.QtCore import Qt

class CurriculumViewDialog(QDialog):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.setWindowTitle("Müfredat Görüntüleme")
        self.setGeometry(200, 200, 900, 600)
        
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout()
        
        # --- Filters ---
        filter_layout = QHBoxLayout()
        
        # Faculty
        self.combo_faculty = QComboBox()
        self.combo_faculty.addItem("Tüm Fakülteler", None)
        self.combo_faculty.currentIndexChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(QLabel("Fakülte:"))
        filter_layout.addWidget(self.combo_faculty)
        
        # Department
        self.combo_dept = QComboBox()
        self.combo_dept.addItem("Tüm Bölümler", None)
        self.combo_dept.currentIndexChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(QLabel("Bölüm:"))
        filter_layout.addWidget(self.combo_dept)
        
        # Year/Pool Filter
        self.combo_year = QComboBox()
        self.combo_year.addItem("Tüm Sınıflar", None)
        self.combo_year.addItems([str(i) for i in range(1, 5)])
        self.combo_year.addItem("Havuz Dersleri", 99) # Special value for Pool
        self.combo_year.currentIndexChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(QLabel("Sınıf / Havuz:"))
        filter_layout.addWidget(self.combo_year)
        
        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Ders Adı Ara...")
        self.search_input.textChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.search_input)
        
        layout.addLayout(filter_layout)
        
        # --- Table ---
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Ders Kodu", "Ders Adı", "T", "U", "L", "AKTS", "Tip", "Bölüm/Havuz"
        ])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents) # Code
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents) # T
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents) # U
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents) # L
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents) # AKTS
        
        layout.addWidget(self.table)
        
        # Close Button
        btn_close = QPushButton("Kapat")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)
        
        self.setLayout(layout)
        
    def _load_data(self):
        # Load Faculties
        if hasattr(self.controller.model, 'get_faculties'):
             faculties = self.controller.model.get_faculties()
             for f_id, f_name in faculties:
                 self.combo_faculty.addItem(f_name, f_id)
                 
        # Initial Load
        self._refresh_table()

    def _on_filter_changed(self):
        # Handle Faculty -> Dept cascading
        sender = self.sender()
        if sender == self.combo_faculty:
            fac_id = self.combo_faculty.currentData()
            self.combo_dept.clear()
            self.combo_dept.addItem("Tüm Bölümler", None)
            if fac_id:
                depts = self.controller.model.get_departments_by_faculty(fac_id)
                for d_id, d_name in depts:
                    self.combo_dept.addItem(d_name, d_id)
                    
        self._refresh_table()

    def _refresh_table(self):
        # Gather filters
        dept_id = self.combo_dept.currentData()
        year_data = self.combo_year.currentData()
        
        # Determine year filter
        # If year_data is string '1'..'4' (actually added as strings above but distinct from 99)
        # Wait, I added 1..4 as strings in addItems, but 99 as data.
        # Need to handle standard items.
        # `combo_year` items: (Text, Data)
        # 0: "Tüm", None
        # 1..4: "1".."4", None (default) -> text is data
        # 5: "Havuz", 99
        
        year_filter = None
        if year_data == 99:
             year_filter = 99
        else:
             txt = self.combo_year.currentText()
             if txt.isdigit():
                 year_filter = int(txt)

        search = self.search_input.text().lower()
        
        # Fetch Data
        if hasattr(self.controller.model, 'get_all_curriculum_details'):
            # Model handles merging logic based on year_filter
            courses = self.controller.model.get_all_curriculum_details(dept_id, year_filter)
            
            # Filter locally for name
            filtered = []
            for c in courses:
                # c structure: (Code, Name, T, U, L, AKTS, Type, Detail, SortYear, IsPool)
                if search and search not in c[1].lower():
                    continue
                filtered.append(c)
                
            self._populate_table(filtered)

    def _populate_table(self, data):
        self.table.setRowCount(0)
        current_header = None
        
        # We assume data is sorted by SortYear (Year ASC, then Pool=99)
        for row_data in data:
            sort_year = row_data[8]
            is_pool = row_data[9]
            
            # Determine Header Title
            header_title = ""
            if is_pool == 1 or sort_year == 99:
                header_title = "Havuz Dersleri"
            else:
                header_title = f"{sort_year}. Sınıf"
                
            # Insert Header if changed
            if header_title != current_header:
                current_header = header_title
                self._add_header_row(header_title)
                
            # Insert Data Row
            row_idx = self.table.rowCount()
            self.table.insertRow(row_idx)
            
            # Values (Skip indices 8, 9)
            display_vals = row_data[:8]
            
            for col_idx, val in enumerate(display_vals):
                item = QTableWidgetItem(str(val))
                item.setFlags(item.flags() ^ Qt.ItemIsEditable) 
                self.table.setItem(row_idx, col_idx, item)

    def _add_header_row(self, title):
        row_idx = self.table.rowCount()
        self.table.insertRow(row_idx)
        
        # Merge all columns
        self.table.setSpan(row_idx, 0, 1, 8)
        
        header_item = QTableWidgetItem(title)
        header_item.setFlags(Qt.ItemIsEnabled) # Read only, not selectable
        header_item.setTextAlignment(Qt.AlignCenter)
        header_item.setBackground(Qt.gray) 
        # Make it look distinct
        font = header_item.font()
        font.setBold(True)
        header_item.setFont(font)
        
        self.table.setItem(row_idx, 0, header_item)
