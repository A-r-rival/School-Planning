from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QPushButton, QMessageBox, QGridLayout
)
from PyQt5.QtCore import Qt

class ManualEditDialog(QDialog):
    def __init__(self, course_data, model, parent=None):
        super().__init__(parent)
        self.course_data = course_data
        self.model = model
        self.setWindowTitle(f"Ders Taşı: {self.course_data.get('course', 'Bilinmeyen Ders')}")
        self.setMinimumWidth(400)
        
        self.result_data = None
        
        self._setup_ui()
        self._populate_data()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Info header
        info_label = QLabel(
            f"<b>Ders:</b> {self.course_data.get('course')}<br>"
            f"<b>Mevcut Zaman:</b> {self.course_data.get('day')} {self.course_data.get('start_str')} - {self.course_data.get('end_str')}<br>"
            f"<b>Detay:</b> {self.course_data.get('extra', '')}"
        )
        layout.addWidget(info_label)
        
        layout.addSpacing(10)
        
        grid = QGridLayout()
        
        # Gün
        grid.addWidget(QLabel("Yeni Gün:"), 0, 0)
        self.combo_day = QComboBox()
        self.combo_day.addItems(["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma"])
        grid.addWidget(self.combo_day, 0, 1)
        
        # Başlangıç Saati
        grid.addWidget(QLabel("Yeni Başlangıç:"), 1, 0)
        self.combo_start = QComboBox()
        grid.addWidget(self.combo_start, 1, 1)
        
        # Bitiş Saati
        grid.addWidget(QLabel("Yeni Bitiş:"), 2, 0)
        self.combo_end = QComboBox()
        grid.addWidget(self.combo_end, 2, 1)
        
        # Derslik
        grid.addWidget(QLabel("Yeni Derslik:"), 3, 0)
        self.combo_room = QComboBox()
        grid.addWidget(self.combo_room, 3, 1)
        
        layout.addLayout(grid)
        
        layout.addSpacing(15)
        
        # Butonlar
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("Kaydet")
        btn_save.setStyleSheet("background-color: #4CAF50; color: white;")
        btn_save.clicked.connect(self._on_save)
        
        btn_cancel = QPushButton("İptal")
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        
        layout.addLayout(btn_layout)
        
        self.combo_start.currentIndexChanged.connect(self._on_start_changed)
        
    def _populate_data(self):
        # Saatleri oluştur (08:30 - 17:30)
        times = []
        h, m = 8, 30
        for _ in range(18):
            times.append(f"{h:02d}:{m:02d}")
            m += 30
            if m >= 60:
                m -= 60
                h += 1
        
        self.combo_start.addItems(times[:-1]) # Son saat başlangıç olamaz
        self.combo_end.addItems(times[1:])    # İlk saat bitiş olamaz
        
        # Derslikleri getir
        rooms = self.model.get_all_classrooms_with_ids()
        self.combo_room.addItem("Belirsiz (Atanmamış)", None)
        for room_id, name, capacity in rooms:
            self.combo_room.addItem(f"{name} (Kapasite: {capacity})", room_id)
            
        # Mevcut verileri seç
        day_idx = self.combo_day.findText(self.course_data.get('day', ''))
        if day_idx >= 0:
            self.combo_day.setCurrentIndex(day_idx)
            
        start_idx = self.combo_start.findText(self.course_data.get('start_str', ''))
        if start_idx >= 0:
            self.combo_start.setCurrentIndex(start_idx)
            
        end_idx = self.combo_end.findText(self.course_data.get('end_str', ''))
        if end_idx >= 0:
            self.combo_end.setCurrentIndex(end_idx)
            
    def _on_start_changed(self):
        start_idx = self.combo_start.currentIndex()
        if start_idx >= 0:
            # Sadece 1 saat sonrasını varsayılan yapmak için (eğer bitiş seçilmemişse veya küçükse)
            current_end = self.combo_end.currentIndex()
            if current_end <= start_idx:
                end_idx = min(start_idx, self.combo_end.count() - 1)
                self.combo_end.setCurrentIndex(end_idx)
            
    def _on_save(self):
        day = self.combo_day.currentText()
        start = self.combo_start.currentText()
        end = self.combo_end.currentText()
        room_id = self.combo_room.currentData()
        
        if start >= end:
            QMessageBox.warning(self, "Hata", "Bitiş saati başlangıç saatinden büyük olmalıdır.")
            return
            
        self.result_data = {
            'day': day,
            'start': start,
            'end': end,
            'room_id': room_id,
            'program_id': self.course_data.get('program_id')
        }
        self.accept()
