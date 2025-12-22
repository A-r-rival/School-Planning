# -*- coding: utf-8 -*-
"""
Teacher Availability View
Dialog for managing teacher unavailability slots
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QComboBox, 
    QTableWidget, QTableWidgetItem, QPushButton, 
    QLabel, QTimeEdit, QMessageBox, QHeaderView
)
from PyQt5.QtCore import Qt, QTime

class TeacherAvailabilityView(QDialog):
    def __init__(self, parent=None, teachers=None):
        super().__init__(parent)
        self.setWindowTitle("Öğretmen Müsaitlik Durumu")
        self.setGeometry(200, 200, 600, 500)
        self.teachers = teachers or []
        
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout()
        
        # Teacher Selection
        teacher_layout = QHBoxLayout()
        teacher_layout.addWidget(QLabel("Öğretmen Seç:"))
        self.teacher_combo = QComboBox()
        self.teacher_combo.addItem("Tüm Öğretmenler", -1)  # Add All Teachers option
        for t_id, t_name in self.teachers:
            self.teacher_combo.addItem(t_name, t_id)
        self.teacher_combo.currentIndexChanged.connect(self._on_teacher_changed)
        teacher_layout.addWidget(self.teacher_combo)
        layout.addLayout(teacher_layout)
        
        # Add Unavailability Section
        add_layout = QHBoxLayout()
        
        self.day_combo = QComboBox()
        self.day_combo.addItems(["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma"])
        add_layout.addWidget(QLabel("Gün:"))
        add_layout.addWidget(self.day_combo)
        
        self.start_time = QTimeEdit()
        self.start_time.setDisplayFormat("HH:mm")
        self.start_time.setTime(QTime(9, 0))
        add_layout.addWidget(QLabel("Başlangıç:"))
        add_layout.addWidget(self.start_time)
        
        self.end_time = QTimeEdit()
        self.end_time.setDisplayFormat("HH:mm")
        self.end_time.setTime(QTime(12, 0))
        add_layout.addWidget(QLabel("Bitiş:"))
        add_layout.addWidget(self.end_time)
        
        self.add_button = QPushButton("Müsait Değil Ekle")
        self.add_button.clicked.connect(self._on_add_clicked)
        add_layout.addWidget(self.add_button)
        
        layout.addLayout(add_layout)
        
        # List of Unavailability
        self.table = QTableWidget()
        self.table.setColumnCount(5)  # Increased column count for Teacher Name
        self.table.setHorizontalHeaderLabels(["Öğretmen", "Gün", "Başlangıç", "Bitiş", "İşlem"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)
        
        self.setLayout(layout)
        
        # Initial load
        if self.teachers:
            self._on_teacher_changed(0)
            
    def set_controller(self, controller):
        self.controller = controller
        
    def _on_teacher_changed(self, index):
        if hasattr(self, 'controller'):
            teacher_id = self.teacher_combo.currentData()
            
            if teacher_id == -1:
                self.controller.load_all_teacher_availability()
                self.add_button.setEnabled(False) # Cannot add to "All Teachers"
            else:
                self.controller.load_teacher_availability(teacher_id)
                self.add_button.setEnabled(True)
            
    def _on_add_clicked(self):
        if hasattr(self, 'controller'):
            teacher_id = self.teacher_combo.currentData()
            day = self.day_combo.currentText()
            start = self.start_time.time().toString("HH:mm")
            end = self.end_time.time().toString("HH:mm")
            
            if start >= end:
                QMessageBox.warning(self, "Hata", "Başlangıç saati bitişten önce olmalı!")
                return
                
            self.controller.add_teacher_unavailability(teacher_id, day, start, end)
            
    def update_table(self, data):
        """Update table with unavailability data"""
        self.table.setRowCount(0)
        # Data format: (day, start, end, u_id, teacher_name)
        for row_idx, item in enumerate(data):
            if len(item) == 5:
                day, start, end, u_id, teacher_name = item
            else:
                # Fallback
                day, start, end, u_id = item
                teacher_name = None
            
            self.table.insertRow(row_idx)
            
            t_name_item = QTableWidgetItem(teacher_name if teacher_name else "-")
            self.table.setItem(row_idx, 0, t_name_item)
            self.table.setItem(row_idx, 1, QTableWidgetItem(day))
            self.table.setItem(row_idx, 2, QTableWidgetItem(start))
            self.table.setItem(row_idx, 3, QTableWidgetItem(end))
            
            delete_btn = QPushButton("Sil")
            delete_btn.clicked.connect(lambda checked, uid=u_id: self.controller.remove_teacher_unavailability(uid))
            self.table.setCellWidget(row_idx, 4, delete_btn)
