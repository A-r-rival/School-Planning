from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QLineEdit, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QSplitter, QFrame, QGroupBox, QCheckBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

class StudentView(QWidget):
    # Signal to request student data
    # args: filters dict
    filter_changed = pyqtSignal(dict)
    # Signal when a student is selected
    # args: student_id
    student_selected = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        
        # Splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        
        # --- Left Panel: Student List & Filters ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Filters Group
        filter_group = QGroupBox("Filtreler")
        filter_layout = QVBoxLayout()
        
        self.faculty_combo = QComboBox()
        self.faculty_combo.setPlaceholderText("Fakülte Seçiniz")
        self.faculty_combo.addItem("Tüm Fakülteler", None)
        
        self.dept_combo = QComboBox()
        self.dept_combo.setPlaceholderText("Bölüm Seçiniz")
        self.dept_combo.addItem("Tüm Bölümler", None)
        
        self.year_combo = QComboBox()
        self.year_combo.setPlaceholderText("Sınıf Seçiniz")
        self.year_combo.addItem("Tüm Sınıflar", None)
        for i in range(1, 5):
            self.year_combo.addItem(f"{i}. Sınıf", i)
            
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Öğrenci Ara (Ad, Soyad, No)...")

        # Student Type Checkboxes
        self.chk_regular = QCheckBox("Regular Göster")
        self.chk_regular.setChecked(True)
        self.chk_irregular = QCheckBox("Irregular Göster")
        self.chk_irregular.setChecked(True)
        self.chk_cap_yandal = QCheckBox("ÇAP/Yandal Göster")
        self.chk_cap_yandal.setChecked(True)
        
        filter_layout.addWidget(QLabel("Fakülte:"))
        filter_layout.addWidget(self.faculty_combo)
        filter_layout.addWidget(QLabel("Bölüm:"))
        filter_layout.addWidget(self.dept_combo)
        filter_layout.addWidget(QLabel("Sınıf:"))
        filter_layout.addWidget(self.year_combo)
        filter_layout.addWidget(QLabel("Öğrenci Tipi:"))
        filter_layout.addWidget(self.chk_regular)
        filter_layout.addWidget(self.chk_irregular)
        filter_layout.addWidget(self.chk_cap_yandal)
        filter_layout.addWidget(QLabel("Arama:"))
        filter_layout.addWidget(self.search_input)
        
        filter_group.setLayout(filter_layout)
        left_layout.addWidget(filter_group)
        
        # Student List Table
        self.student_table = QTableWidget()
        self.student_table.setColumnCount(3)
        self.student_table.setHorizontalHeaderLabels(["No", "Ad", "Soyad"])
        self.student_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.student_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.student_table.setSelectionMode(QTableWidget.SingleSelection)
        self.student_table.setEditTriggers(QTableWidget.NoEditTriggers)
        left_layout.addWidget(self.student_table)
        
        # --- Right Panel: Transcript & Details ---
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # Student Details Header
        self.student_info_group = QGroupBox("Öğrenci Bilgileri")
        info_layout = QVBoxLayout()
        self.lbl_name = QLabel("Öğrenci Seçilmedi")
        self.lbl_name.setFont(QFont("Arial", 12, QFont.Bold))
        self.lbl_name.setTextInteractionFlags(Qt.TextSelectableByMouse)
        
        self.lbl_dept = QLabel("-")
        self.lbl_dept.setTextInteractionFlags(Qt.TextSelectableByMouse)
        
        self.lbl_no = QLabel("-")
        self.lbl_no.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.lbl_semester = QLabel("-")
        self.lbl_semester.setTextInteractionFlags(Qt.TextSelectableByMouse)
        
        info_layout.addWidget(self.lbl_name)
        info_layout.addWidget(self.lbl_dept)
        info_layout.addWidget(self.lbl_no)
        info_layout.addWidget(self.lbl_semester)
        self.student_info_group.setLayout(info_layout)
        right_layout.addWidget(self.student_info_group)
        
        # Transcript Table
        self.transcript_table = QTableWidget()
        self.transcript_table.setColumnCount(6)
        self.transcript_table.setHorizontalHeaderLabels(["Dönem", "Ders Kodu", "Ders Adı", "AKTS", "Not", "Durum"])
        self.transcript_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.transcript_table.setEditTriggers(QTableWidget.NoEditTriggers)
        right_layout.addWidget(self.transcript_table)
        
        # Add widgets to splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([300, 600]) # Initial sizes
        
        main_layout.addWidget(splitter)
        
        # Connect signals
        self.faculty_combo.currentIndexChanged.connect(self.emit_filter_changed)
        self.dept_combo.currentIndexChanged.connect(self.emit_filter_changed)
        self.year_combo.currentIndexChanged.connect(self.emit_filter_changed)
        self.search_input.textChanged.connect(self.emit_filter_changed)
        self.chk_regular.stateChanged.connect(self.emit_filter_changed)
        self.chk_irregular.stateChanged.connect(self.emit_filter_changed)
        self.chk_cap_yandal.stateChanged.connect(self.emit_filter_changed)
        
        self.student_table.itemSelectionChanged.connect(self.on_student_selected)

    def emit_filter_changed(self):
        filters = {}
        
        # Faculty
        if self.faculty_combo.currentData():
            filters['fakulte_id'] = self.faculty_combo.currentData()
            
        # Dept
        if self.dept_combo.currentData():
            filters['bolum_id'] = self.dept_combo.currentData()
            
        # Year
        if self.year_combo.currentData():
            filters['sinif'] = self.year_combo.currentData()
            
        # Search
        if self.search_input.text():
            filters['search'] = self.search_input.text()

        # Student Types
        filters['show_regular'] = self.chk_regular.isChecked()
        filters['show_irregular'] = self.chk_irregular.isChecked()
        filters['show_cap_yandal'] = self.chk_cap_yandal.isChecked()
            
        self.filter_changed.emit(filters)

    def on_student_selected(self):
        selected_items = self.student_table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            student_id = int(self.student_table.item(row, 0).text())
            
            # Update Info Labels immediately from table data
            name = self.student_table.item(row, 1).text()
            surname = self.student_table.item(row, 2).text()
            
            # Retrieve stored data
            semester = self.student_table.item(row, 0).data(Qt.UserRole)
            
            self.lbl_name.setText(f"{name} {surname}")
            self.lbl_no.setText(f"No: {student_id}")
            self.lbl_semester.setText(f"Dönem: {semester}. Dönem")
            
            self.student_selected.emit(student_id)

    def update_student_list(self, students):
        """
        Update the student list table.
        students: List of tuples (ogrenci_num, ad, soyad, bolum_adi, kacinci_donem)
        """
        self.student_table.setRowCount(0)
        for row_idx, student in enumerate(students):
            self.student_table.insertRow(row_idx)
            # No, Ad, Soyad
            item_no = QTableWidgetItem(str(student[0]))
            item_no.setData(Qt.UserRole, student[4]) # Store semester
            
            self.student_table.setItem(row_idx, 0, item_no)
            self.student_table.setItem(row_idx, 1, QTableWidgetItem(student[1]))
            self.student_table.setItem(row_idx, 2, QTableWidgetItem(student[2]))
            
    def update_transcript(self, grades):
        """
        Update the transcript table.
        grades: List of tuples from Ogrenci_Notlari table + AKTS
        (id, ogrenci_num, ders_kodu, ders_adi, harf_notu, durum, donem, onceki_not_id, akts)
        """
        self.transcript_table.setRowCount(0)
        # Sort by Semester (Donem)
        sorted_grades = sorted(grades, key=lambda x: x[6], reverse=True)
        
        current_semester = None
        
        for grade in sorted_grades:
            grade_semester = grade[6]
            
            # Insert Separator Row if semester changes
            if grade_semester != current_semester:
                row_idx = self.transcript_table.rowCount()
                self.transcript_table.insertRow(row_idx)
                
                # Create separator item
                sep_item = QTableWidgetItem(f"--- {grade_semester} ---")
                sep_item.setTextAlignment(Qt.AlignCenter)
                font = QFont()
                font.setBold(True)
                sep_item.setFont(font)
                sep_item.setBackground(Qt.lightGray)
                
                self.transcript_table.setItem(row_idx, 0, sep_item)
                self.transcript_table.setSpan(row_idx, 0, 1, 6) # Span all 6 columns
                
                current_semester = grade_semester
            
            # Insert Grade Row
            row_idx = self.transcript_table.rowCount()
            self.transcript_table.insertRow(row_idx)
            
            # Donem, Kod, Ad, AKTS, Not, Durum
            self.transcript_table.setItem(row_idx, 0, QTableWidgetItem(grade[6])) # Donem
            self.transcript_table.setItem(row_idx, 1, QTableWidgetItem(grade[2])) # Kod
            self.transcript_table.setItem(row_idx, 2, QTableWidgetItem(grade[3])) # Ad
            
            # AKTS (Index 8)
            akts_val = str(grade[8]) if len(grade) > 8 and grade[8] is not None else "-"
            self.transcript_table.setItem(row_idx, 3, QTableWidgetItem(akts_val))
            
            self.transcript_table.setItem(row_idx, 4, QTableWidgetItem(grade[4])) # Not
            
            status_item = QTableWidgetItem(grade[5]) # Durum
            if grade[5] == "Geçti":
                status_item.setForeground(Qt.green)
            elif grade[5] == "Kaldı":
                status_item.setForeground(Qt.red)
                
            self.transcript_table.setItem(row_idx, 5, status_item)

    def set_filter_options(self, faculties, departments):
        """
        Populate filter combo boxes.
        faculties: List of (id, name)
        departments: List of (id, name)
        """
        # Save current selection
        current_fac = self.faculty_combo.currentData()
        current_dept = self.dept_combo.currentData()
        
        self.faculty_combo.blockSignals(True)
        self.dept_combo.blockSignals(True)
        
        self.faculty_combo.clear()
        self.faculty_combo.addItem("Tüm Fakülteler", None)
        for f_id, f_name in faculties:
            self.faculty_combo.addItem(f_name, f_id)
            
        self.dept_combo.clear()
        self.dept_combo.addItem("Tüm Bölümler", None)
        for d_id, d_name in departments:
            self.dept_combo.addItem(d_name, d_id)
            
        # Restore selection if possible
        if current_fac:
            idx = self.faculty_combo.findData(current_fac)
            if idx >= 0: self.faculty_combo.setCurrentIndex(idx)
            
        if current_dept:
            idx = self.dept_combo.findData(current_dept)
            if idx >= 0: self.dept_combo.setCurrentIndex(idx)
            
        self.faculty_combo.blockSignals(False)
        self.dept_combo.blockSignals(False)
