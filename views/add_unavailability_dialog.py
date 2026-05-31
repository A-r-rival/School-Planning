# -*- coding: utf-8 -*-
"""
Add Unavailability Dialog
Dialog for managing teacher unavailability slots
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QComboBox, 
    QPushButton, QLabel, QTimeEdit, QLineEdit, QWidget, QCompleter, QTabWidget
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
        
        for t in self.teachers:
            if len(t) >= 2:
                 self.teacher_combo.addItem(t[1], t[0])
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
        slot_layout.addWidget(QLabel("Öğretmenin saat kısıtını (müsait olmadığı zamanı) ekle:"))
        
        # Year and Semester filter
        term_layout = QHBoxLayout()
        term_layout.addWidget(QLabel("Yıl:"))
        self.yil_combo = QComboBox()
        self.yil_combo.addItems(["Hepsi", "2023-2024", "2024-2025", "2025-2026", "2026-2027"])
        term_layout.addWidget(self.yil_combo)
        
        term_layout.addWidget(QLabel("Dönem:"))
        self.donem_combo = QComboBox()
        self.donem_combo.addItems(["Hepsi", "Güz", "Bahar", "Yaz"])
        term_layout.addWidget(self.donem_combo)
        slot_layout.addLayout(term_layout)
        
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
        
        # Tab 3: Room Preference
        self.tab_room = QWidget()
        room_layout = QVBoxLayout()
        room_layout.addWidget(QLabel("Bu öğretmenin hangi oda veya katta ders vermesini istiyorsunuz?"))
        room_layout.addWidget(QLabel("(Örn: Zemin, A101, Lab)"))
        self.room_input = QLineEdit()
        self.room_input.setPlaceholderText("Örn: Zemin, Lab, A101")
        room_layout.addWidget(self.room_input)
        room_layout.addStretch()
        self.tab_room.setLayout(room_layout)
        
        # Add tabs
        self.tabs.addTab(self.tab_span, "Gün Kısıtı (Haftalık Max Gün)")
        self.tabs.addTab(self.tab_slot, "Saat Kısıtı")
        self.tabs.addTab(self.tab_room, "Oda/Kat Kısıtı")
        
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

    def _on_span_changed(self, value: int):
        """Handle span preference change"""
        teacher_id = self.teacher_combo.currentData()
        if teacher_id != -1 and self.controller:
            self.controller.handle_teacher_span_change(teacher_id, value)

    def _on_teacher_changed(self, index):
        """Handle teacher selection change"""
        teacher_id = self.teacher_combo.itemData(index)
        if teacher_id != -1 and self.controller:
            # Load preferences
            span = self.controller.model.get_teacher_span(teacher_id)
            self.span_combo.blockSignals(True)
            idx = self.span_combo.findData(span)
            if idx >= 0:
                self.span_combo.setCurrentIndex(idx)
            else:
                self.span_combo.setCurrentIndex(0)
            self.span_combo.blockSignals(False)
            
            # Enable inputs
            self.span_combo.setEnabled(True)
        else:
            self.span_combo.setEnabled(False)

    def get_data(self):
        idx = self.tabs.currentIndex()
        if idx == 0:
            action_type = 'span'
        elif idx == 1:
            action_type = 'slot'
        else:
            action_type = 'room'
            
        return {
            'teacher_id': self.teacher_combo.currentData(),
            'action_type': action_type,
            'span': self.span_combo.currentData(),
            'day': self.day_combo.currentText(),
            'start': self.start_time.time().toString("HH:mm"),
            'end': self.end_time.time().toString("HH:mm"),
            'yil': getattr(self, 'yil_combo', None).currentText() if hasattr(self, 'yil_combo') else "Hepsi",
            'donem': getattr(self, 'donem_combo', None).currentText() if hasattr(self, 'donem_combo') else "Hepsi",
            'desc': self.desc_input.text(),
            'room': getattr(self, 'room_input', None).text() if hasattr(self, 'room_input') else ""
        }
