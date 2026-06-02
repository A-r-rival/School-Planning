from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QPushButton, QMessageBox, QGridLayout,
    QSplitter, QScrollArea, QWidget
)
from PyQt5.QtCore import Qt

from views.calendar_view import CalendarView
from services.calendar_schedule_builder import CalendarScheduleBuilder


class CourseMovePreviewDialog(QDialog):
    def __init__(self, course_data, original_schedule_data, original_metadata, model, versiyon_id, parent=None, active_pools=None, view_type="Öğrenci Grubu", dept_text="", year_text=""):
        super().__init__(parent)
        self.course_data = course_data
        self.original_schedule_data = original_schedule_data
        self.original_metadata = original_metadata
        self.active_pools = active_pools if active_pools is not None else set()
        self.view_type = view_type
        self.dept_text = dept_text
        self.year_text = year_text
        self.model = model
        self.versiyon_id = versiyon_id
        self.builder = CalendarScheduleBuilder(self.model)
        
        self.setWindowTitle(f"Ders Taşı Önizleme: {self.course_data.get('course', 'Bilinmeyen Ders')}")
        self.setMinimumSize(1400, 1200)
        
        self.result_data = None
        
        # To identify teacher from schedule (it's in the extra field or we need to extract from DB)
        self.teacher_id = self._find_teacher_id()
        self.program_id = self.course_data.get('program_id')
        
        self._setup_ui()
        self._populate_data()
        self._load_previews()
        
    def _find_teacher_id(self):
        # course_data['extra'] has "Öğretmen: XXX"
        # Best way is to query DB by program_id to be safe
        p_id = self.course_data.get('program_id')
        if p_id:
            try:
                self.model.c.execute("SELECT ogretmen_id FROM Ders_Programi WHERE program_id = ?", (p_id,))
                row = self.model.c.fetchone()
                if row and row[0]:
                    return row[0]
            except Exception:
                pass
        return None

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        # 1. TOP BAR: Input Controls
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        
        info_label = QLabel(
            f"<h3 style='margin:0;'>{self.course_data.get('course')}</h3>"
            f"<b>Mevcut Zaman:</b> {self.course_data.get('day')} {self.course_data.get('start_str')} - {self.course_data.get('end_str')} | "
            f"<b>Mevcut Detay:</b> {self.course_data.get('extra', '').replace(chr(10), ' | ')}"
        )
        top_layout.addWidget(info_label)
        
        grid = QGridLayout()
        
        grid.addWidget(QLabel("<b>Yeni Gün:</b>"), 0, 0)
        self.combo_day = QComboBox()
        self.combo_day.addItems(["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma"])
        grid.addWidget(self.combo_day, 0, 1)
        
        grid.addWidget(QLabel("<b>Yeni Başlangıç:</b>"), 0, 2)
        self.combo_start = QComboBox()
        grid.addWidget(self.combo_start, 0, 3)
        
        grid.addWidget(QLabel("<b>Yeni Bitiş:</b>"), 0, 4)
        self.combo_end = QComboBox()
        grid.addWidget(self.combo_end, 0, 5)
        
        grid.addWidget(QLabel("<b>Yeni Derslik:</b>"), 0, 6)
        self.combo_room = QComboBox()
        grid.addWidget(self.combo_room, 0, 7)
        
        top_layout.addLayout(grid)
        main_layout.addWidget(top_widget)
        
        # 2. SPLITTER: Left (Original) / Right (Previews)
        splitter = QSplitter(Qt.Horizontal)
        
        # LEFT PANE: Original Schedule
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        title = "Orijinal Program"
        if self.original_metadata and self.original_metadata.get('title'):
            title = f"Orijinal Program ({self.original_metadata['title']})"
        left_layout.addWidget(QLabel(f"<b>{title}</b>"))
        self.cal_original = CalendarView()
        self.cal_original.filter_frame.hide()
        
        # Inject state from parent calendar so checkboxes render correctly
        self.cal_original.view_type_combo.blockSignals(True)
        self.cal_original.view_type_combo.setCurrentText(self.view_type)
        self.cal_original.view_type_combo.blockSignals(False)
        
        if self.dept_text:
            self.cal_original.filter_widget_2.blockSignals(True)
            self.cal_original.filter_widget_2.clear()
            self.cal_original.filter_widget_2.addItem(self.dept_text)
            self.cal_original.filter_widget_2.blockSignals(False)
            
        if self.year_text:
            self.cal_original.filter_widget_3.blockSignals(True)
            self.cal_original.filter_widget_3.clear()
            self.cal_original.filter_widget_3.addItem(self.year_text)
            self.cal_original.filter_widget_3.blockSignals(False)
            
        self.cal_original.active_pools = self.active_pools
        self.cal_original.display_schedule({'schedule': self.original_schedule_data, 'metadata': self.original_metadata})
        left_layout.addWidget(self.cal_original)
        splitter.addWidget(left_widget)
        
        # RIGHT PANE: Scrollable Previews
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        self.right_layout = QVBoxLayout(scroll_content)
        
        # Teacher Preview
        self.right_layout.addWidget(QLabel("<b>Öğretmen Programı</b>"))
        self.cal_teacher = CalendarView()
        self.cal_teacher.filter_frame.hide()
        self.cal_teacher.setMinimumHeight(400)
        self.right_layout.addWidget(self.cal_teacher)
        
        # Classes Preview
        self.right_layout.addWidget(QLabel("<b>Sınıf/Bölüm Programı (Bu dersi alan sınıflar)</b>"))
        self.cal_classes = CalendarView()
        self.cal_classes.filter_frame.hide()
        self.cal_classes.setMinimumHeight(400)
        self.right_layout.addWidget(self.cal_classes)
        
        # Room Preview
        self.right_layout.addWidget(QLabel("<b>Seçilen Yeni Derslik Programı</b>"))
        self.cal_room = CalendarView()
        self.cal_room.filter_frame.hide()
        self.cal_room.setMinimumHeight(400)
        self.right_layout.addWidget(self.cal_room)
        
        scroll_area.setWidget(scroll_content)
        splitter.addWidget(scroll_area)
        
        # Set weights (1:1)
        splitter.setSizes([600, 600])
        main_layout.addWidget(splitter, 1) # stretch factor 1
        
        # 3. BOTTOM BAR: Buttons
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("Taşı ve Kaydet")
        btn_save.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px 15px;")
        btn_save.clicked.connect(self._on_save)
        
        btn_cancel = QPushButton("İptal")
        btn_cancel.setStyleSheet("padding: 8px 15px;")
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        
        main_layout.addLayout(btn_layout)
        
        # Connections
        self.combo_start.currentIndexChanged.connect(self._on_start_changed)
        self.combo_room.currentIndexChanged.connect(self._on_room_changed)

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
        
        # Get current room_id from DB
        current_room_id = None
        if self.program_id:
            try:
                self.model.c.execute("SELECT derslik_id FROM Ders_Programi WHERE program_id = ?", (self.program_id,))
                row = self.model.c.fetchone()
                if row and row[0]:
                    current_room_id = row[0]
            except Exception:
                pass

        # Derslikleri getir
        rooms = self.model.get_all_classrooms_with_ids()
        self.combo_room.addItem("Belirsiz (Atanmamış)", None)
        
        current_room_index = 0
        for i, (room_id, name, capacity) in enumerate(rooms, start=1):
            self.combo_room.addItem(f"{name} (Kapasite: {capacity})", room_id)
            if room_id == current_room_id:
                current_room_index = i
                
        self.combo_room.setCurrentIndex(current_room_index)
            
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

    def _load_previews(self):
        # Teacher Schedule
        if self.teacher_id:
            data = self.builder.build({"teacher_id": self.teacher_id, "versiyon_id": self.versiyon_id})
            self.cal_teacher.display_schedule(data)
            
        # Classes Schedule
        if self.program_id:
            # Try to fetch which department/year this program_id belongs to
            try:
                self.model.c.execute('''
                    SELECT bolum_num, sinif_duzeyi, fakulte_id FROM (
                        SELECT od.bolum_num, od.sinif_duzeyi, b.fakulte_num as fakulte_id
                        FROM Ders_Programi dp
                        JOIN Ders_Sinif_Iliskisi dsi ON dp.ders_adi = dsi.ders_adi AND dp.ders_instance = dsi.ders_instance
                        JOIN Ogrenci_Donemleri od ON dsi.donem_sinif_num = od.donem_sinif_num
                        JOIN Bolumler b ON od.bolum_num = b.bolum_id
                        WHERE dp.program_id = ?
                        
                        UNION
                        
                        SELECT dhi.bolum_id as bolum_num, dhi.sinif_duzeyi, b.fakulte_num as fakulte_id
                        FROM Ders_Programi dp
                        JOIN Ders_Havuz_Iliskisi dhi ON dp.ders_adi = dhi.ders_adi AND dp.ders_instance = dhi.ders_instance
                        JOIN Bolumler b ON dhi.bolum_id = b.bolum_id
                        WHERE dp.program_id = ?
                    ) LIMIT 1
                ''', (self.program_id, self.program_id))
                row = self.model.c.fetchone()
                if row:
                    bolum_id, sinif_duzeyi, fakulte_id = row[0], row[1], row[2]
                    # We need year for the builder. sinif_duzeyi is essentially year.
                    data = self.builder.build({"dept_id": bolum_id, "year": sinif_duzeyi, "faculty_id": fakulte_id, "versiyon_id": self.versiyon_id})
                    self.cal_classes.display_schedule(data)
            except Exception as e:
                print(f"Preview Classes fetch error: {e}")
                
        # Room Schedule - triggers via population
        self._on_room_changed()

    def _on_start_changed(self):
        start_idx = self.combo_start.currentIndex()
        if start_idx >= 0:
            current_end = self.combo_end.currentIndex()
            if current_end <= start_idx:
                end_idx = min(start_idx, self.combo_end.count() - 1)
                self.combo_end.setCurrentIndex(end_idx)

    def _on_room_changed(self):
        room_id = self.combo_room.currentData()
        if room_id:
            data = self.builder.build({"classroom_id": room_id, "versiyon_id": self.versiyon_id})
            self.cal_room.display_schedule(data)
        else:
            self.cal_room.display_schedule({'schedule': [], 'metadata': {}})

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
            'program_id': self.program_id
        }
        self.accept()
