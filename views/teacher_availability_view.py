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
    QLineEdit, QTabWidget, QWidget, QCompleter # Added QCompleter
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
        
        # List of Unavailability
        self.table = QTableWidget()
        self.table.setColumnCount(5) 
        self.table.setHorizontalHeaderLabels(["Öğretmen", "Tip", "Detay", "Açıklama", "İşlem"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        # Compact columns for Type and Action
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        self.table.setColumnWidth(1, 130) # Slightly wider as requested
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        layout.addWidget(self.table)
        
        # Add Button
        self.add_button = QPushButton("Yeni Namüsaitlik Ekle")
        self.add_button.setStyleSheet("font-weight: bold; font-size: 14px; padding: 10px;")
        self.add_button.clicked.connect(self._on_add_clicked)
        layout.addWidget(self.add_button)
        
        self.setLayout(layout)
        # Note: Do NOT call _on_teacher_changed(0) here because controller is not set yet.
            
    def set_controller(self, controller):
        self.controller = controller
        # Trigger initial load now that we have the controller
        if self.teachers:
             self._on_teacher_changed(0)
        
    def _on_teacher_changed(self, index):
        """Handle filter change"""
        try:
            if hasattr(self, 'controller'):
                teacher_id = self.teacher_combo.currentData()
            if hasattr(self, 'controller'):
                teacher_id = self.teacher_combo.currentData()
                
                # Check for validity
                if teacher_id is None:
                    return
                    
                if not isinstance(teacher_id, int):
                    return

                if teacher_id == -1:
                    self.controller.load_all_teacher_availability()
                else:
                    self.controller.load_teacher_availability(teacher_id)
        except Exception as e:
            print(f"Error in _on_teacher_changed: {e}")
            QMessageBox.critical(self, "Hata", f"Hata: {e}")
            
    def _on_add_clicked(self):
        """Open Add Dialog"""
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
