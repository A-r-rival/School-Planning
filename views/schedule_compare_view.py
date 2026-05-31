import copy
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, 
    QLabel, QPushButton, QSplitter, QMessageBox
)
from PyQt5.QtCore import Qt
from views.calendar_view import CalendarView

class ScheduleCompareView(QWidget):
    def __init__(self, model):
        super().__init__()
        self.model = model
        self.schedule_v1 = []
        self.schedule_v2 = []
        self.selected_course_data = None
        self._setup_ui()
        self._load_versions()
        
        # Trigger initial population after versions are loaded
        self.cal_v1._on_view_type_changed()
        self.cal_v2._on_view_type_changed()

    def _setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Top controls
        top_bar = QHBoxLayout()
        
        top_bar.addWidget(QLabel("Eski Versiyon:"))
        self.combo_v1 = QComboBox()
        top_bar.addWidget(self.combo_v1)
        
        top_bar.addWidget(QLabel("Yeni Versiyon:"))
        self.combo_v2 = QComboBox()
        top_bar.addWidget(self.combo_v2)
        
        self.btn_compare = QPushButton("Karşılaştır")
        self.btn_compare.clicked.connect(self._on_compare)
        self.btn_compare.setStyleSheet("background-color: #2196F3; color: white;")
        top_bar.addWidget(self.btn_compare)
        
        self.btn_manual_edit = QPushButton("Seçili Dersi Taşı (Manuel Düzenle)")
        self.btn_manual_edit.clicked.connect(self._open_manual_edit_dialog)
        self.btn_manual_edit.setStyleSheet("background-color: #9C27B0; color: white;")
        self.btn_manual_edit.setEnabled(False)
        top_bar.addWidget(self.btn_manual_edit)
        
        top_bar.addSpacing(20)
        
        # Copy Filter Buttons
        self.btn_copy_l2r = QPushButton("➡️")
        self.btn_copy_l2r.setToolTip("Filtreleri Sağa Taşı")
        self.btn_copy_l2r.clicked.connect(self._copy_filters_l2r)
        self.btn_copy_l2r.setStyleSheet("background-color: #607D8B; color: white; font-size: 16px; font-weight: bold; width: 40px;")
        top_bar.addWidget(self.btn_copy_l2r)
        
        self.btn_copy_r2l = QPushButton("⬅️")
        self.btn_copy_r2l.setToolTip("Filtreleri Sola Taşı")
        self.btn_copy_r2l.clicked.connect(self._copy_filters_r2l)
        self.btn_copy_r2l.setStyleSheet("background-color: #607D8B; color: white; font-size: 16px; font-weight: bold; width: 40px;")
        top_bar.addWidget(self.btn_copy_r2l)
        
        top_bar.addStretch()
        layout.addLayout(top_bar)
        
        # Since CalendarView requires controller to feed data based on its combo boxes,
        # we will use Master Schedule View or directly fetch all data for a selected view.
        # For simplicity, we will instantiate a simplified view or wire it carefully.
        self.splitter = QSplitter(Qt.Horizontal)
        
        self.cal_v1 = CalendarView()
        self.cal_v2 = CalendarView()
        
        self.splitter.addWidget(self.cal_v1)
        self.splitter.addWidget(self.cal_v2)
        layout.addWidget(self.splitter)
        
        # Connect signals for both calendars
        self.cal_v1.filter_changed.connect(self._on_cal_v1_filter_changed)
        self.cal_v2.filter_changed.connect(self._on_cal_v2_filter_changed)
        
        self.cal_v1.course_selected.connect(self._on_course_selected)
        self.cal_v2.course_selected.connect(self._on_course_selected)
        
        # Initialize builder
        from services.calendar_schedule_builder import CalendarScheduleBuilder
        self.builder = CalendarScheduleBuilder(self.model)

    def _load_versions(self):
        self.combo_v1.clear()
        self.combo_v2.clear()
        versions = self.model.get_all_schedule_versions()
        for v in versions:
            v_id = v["versiyon_id"]
            ad = v["ad"]
            tarih = v["tarih"]
            active = v["is_active"]
            text = f"{ad} ({tarih})"
            if active: text += " [Aktif]"
            self.combo_v1.addItem(text, v_id)
            self.combo_v2.addItem(text, v_id)
            
        if self.combo_v1.count() >= 2:
            self.combo_v1.setCurrentIndex(1)
            self.combo_v2.setCurrentIndex(0)
            
    def _on_cal_v1_filter_changed(self, event_type, data):
        self._handle_calendar_filter(self.cal_v1, self.combo_v1.currentData(), event_type, data)
        
    def _on_cal_v2_filter_changed(self, event_type, data):
        self._handle_calendar_filter(self.cal_v2, self.combo_v2.currentData(), event_type, data)
        
    def _handle_calendar_filter(self, cal_widget, versiyon_id, event_type, data):
        if event_type == "type_changed":
            result = self.builder.build_for_type_change(data["type"])
            if result:
                filter_level, items = result
                cal_widget.update_filter_options(filter_level, items)
                
        elif event_type == "filter_selected":
            if "faculty_id" in data and ("dept_id" not in data or not data["dept_id"]):
                items = self.builder.get_departments_for_faculty(data["faculty_id"])
                cal_widget.update_filter_options(2, items)
                return

            # Fetch the data
            if not versiyon_id:
                return
            data["versiyon_id"] = versiyon_id
            
            # Use current semester as 'Güz' by default or we can leave it
            if "year" not in data:
                data["year"] = 1 # fallback
                
            schedule_data = self.builder.build(data)
            cal_widget.display_schedule(schedule_data)
            
    def _on_compare(self):
        v1_id = self.combo_v1.currentData()
        v2_id = self.combo_v2.currentData()
        
        if not v1_id or not v2_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen iki versiyon seçin.")
            return
            
        # Get current filter data from calendars
        # Assuming both calendars have the SAME view type and filter for comparison
        view_type = self.cal_v2.view_type_combo.currentText()
        
        data_base = {"type": view_type}
        if view_type == "Öğretmen":
            data_base["teacher_id"] = self.cal_v2.filter_widget_1.currentData()
        elif view_type == "Derslik":
            data_base["classroom_id"] = self.cal_v2.filter_widget_1.currentData()
        elif view_type == "Öğrenci Grubu":
            data_base["faculty_id"] = self.cal_v2.filter_widget_1.currentData()
            data_base["dept_id"] = self.cal_v2.filter_widget_2.currentData()
            data_base["year"] = self.cal_v2.filter_widget_3.currentText()
            # In student group view, filter_widget_2 can be None initially
            if not data_base["dept_id"] or not data_base["year"] or data_base["year"] == "Seçiniz...":
                QMessageBox.warning(self, "Uyarı", "Lütfen tam bir filtre (Fakülte, Bölüm, Sınıf) seçin.")
                return
                
        # Build V1
        data_v1 = copy.deepcopy(data_base)
        data_v1["versiyon_id"] = v1_id
        res_v1 = self.builder.build(data_v1)
        sched_v1 = res_v1.get("schedule", [])
        
        # Build V2
        data_v2 = copy.deepcopy(data_base)
        data_v2["versiyon_id"] = v2_id
        res_v2 = self.builder.build(data_v2)
        sched_v2 = res_v2.get("schedule", [])
        
        # Helper to extract signature of a course (ignores day/time/room)
        def get_course_sig(item):
            # item could be 5-tuple or 9-tuple.
            # display string (item[3]) usually contains code and name.
            # extra (item[4]) contains room/teacher.
            return item[3] # Just the display name "[Code] Name"
            
        # Helper to extract full signature including time
        def get_full_sig(item):
            # day, start, end, display
            return (item[0], item[1], item[2], item[3])
            
        # Dictionaries mapping course_sig -> full item
        v1_courses = {get_course_sig(x): x for x in sched_v1}
        v2_courses = {get_course_sig(x): x for x in sched_v2}
        
        # Construct dictionaries to easily find matching full signatures
        # A full signature is (day, start, end, course_display)
        # We will use this to identify exactly what has moved, added, or removed.
        v1_items = {get_full_sig(x): x for x in sched_v1}
        v2_items = {get_full_sig(x): x for x in sched_v2}
        
        # Output lists
        final_v1 = []
        final_v2 = []
        
        # Compare V1 against V2
        for sig, item in v1_items.items():
            # If the exact same slot+course is in V2, it's unchanged.
            if sig in v2_items:
                # Add without diff color
                final_v1.append(item)
            else:
                # Not in V2. Did it move?
                c_sig = get_course_sig(item)
                if c_sig in v2_courses:
                    # Moved! Yellow.
                    new_item = list(item)
                    while len(new_item) < 9: new_item.append(None)
                    new_item.append("#FFD54F") # Yellow
                    final_v1.append(tuple(new_item))
                else:
                    # Removed completely! Red.
                    new_item = list(item)
                    while len(new_item) < 9: new_item.append(None)
                    new_item.append("#EF5350") # Red
                    final_v1.append(tuple(new_item))
                    
        # Compare V2 against V1
        for sig, item in v2_items.items():
            if sig in v1_items:
                final_v2.append(item)
            else:
                c_sig = get_course_sig(item)
                if c_sig in v1_courses:
                    # Moved! Yellow.
                    new_item = list(item)
                    while len(new_item) < 9: new_item.append(None)
                    new_item.append("#FFD54F") # Yellow
                    final_v2.append(tuple(new_item))
                else:
                    # Added completely! Green.
                    new_item = list(item)
                    while len(new_item) < 9: new_item.append(None)
                    new_item.append("#66BB6A") # Green
                    final_v2.append(tuple(new_item))
                    
        # Replace the schedule lists in results
        res_v1["schedule"] = final_v1
        res_v2["schedule"] = final_v2
        
        self.cal_v1.display_schedule(res_v1)
        self.cal_v2.display_schedule(res_v2)
        
    def _on_course_selected(self, data):
        self.selected_course_data = data
        if self.selected_course_data and self.selected_course_data.get('program_id'):
            self.btn_manual_edit.setEnabled(True)
            self.btn_manual_edit.setText(f"Taşı: {data.get('course')}")
        else:
            self.btn_manual_edit.setEnabled(False)
            self.btn_manual_edit.setText("Seçili Dersi Taşı (Manuel Düzenle)")

    def _open_manual_edit_dialog(self):
        if not self.selected_course_data or not self.selected_course_data.get('program_id'):
            QMessageBox.warning(self, "Uyarı", "Geçerli bir ders seçilmedi veya dersin ID'si yok.")
            return
            
        from views.manual_edit_dialog import ManualEditDialog
        dialog = ManualEditDialog(self.selected_course_data, self.model, self)
        
        if dialog.exec_():
            result = dialog.result_data
            if result:
                # Call controller to update
                # ScheduleCompareView doesn't have direct access to controller,
                # but we can emit a signal or call a global method.
                # Actually, wait. We can just use the model repository directly if it's safe,
                # or better, use a signal.
                # Wait, I'll update the database directly here using a repository if needed,
                # but let's check what controller we have access to.
                # I'll just import schedule_repo directly or use self.model.
                success = self._update_course_slot(result)
                if success:
                    QMessageBox.information(self, "Başarılı", "Ders başarıyla taşındı.")
                    self._on_compare() # Refresh views
                else:
                    QMessageBox.warning(self, "Hata", "Ders taşınırken bir hata oluştu veya çakışma var.")

    def _update_course_slot(self, result):
        # Result has: 'day', 'start', 'end', 'room_id', 'program_id'
        program_id = result['program_id']
        day = result['day']
        start = result['start']
        end = result['end']
        room_id = result['room_id']
        
        # Conflict check
        from models.repositories.schedule_repo import ScheduleRepository
        repo = ScheduleRepository(self.model.conn)
        
        # Get teacher of the course
        cursor = self.model.conn.cursor()
        cursor.execute("SELECT ogretmen_id FROM Ders_Programi WHERE program_id = ?", (program_id,))
        row = cursor.fetchone()
        
        if row and row[0]:
            teacher_id = row[0]
            from models.entities import ScheduleSlot
            # repo.has_conflict expects a ScheduleSlot object for the first argument!
            slot = ScheduleSlot(day=day, start_str=start, end_str=end)
            conflict = repo.has_conflict(slot, teacher_id=teacher_id, exclude_id=program_id)
            if conflict:
                return False
                
        if room_id:
            slot = ScheduleSlot(day=day, start_str=start, end_str=end)
            conflict = repo.has_conflict(slot, room_id=room_id, exclude_id=program_id)
            if conflict:
                return False
                
        return repo.update_slot(program_id, day, start, end, room_id)


    def _copy_calendar_filters(self, source_cal, target_cal):
        """Helper to copy filters from source calendar to target calendar"""
        # 1. View Type
        idx = target_cal.view_type_combo.findText(source_cal.view_type_combo.currentText())
        if idx >= 0: target_cal.view_type_combo.setCurrentIndex(idx)
        
        # 2. Filter 1 (Faculty / Teacher / Room)
        idx = target_cal.filter_widget_1.findText(source_cal.filter_widget_1.currentText())
        if idx >= 0: target_cal.filter_widget_1.setCurrentIndex(idx)
        
        # 3. Filter 2 (Dept)
        if hasattr(source_cal, 'filter_widget_2') and source_cal.filter_widget_2.isVisible():
            idx = target_cal.filter_widget_2.findText(source_cal.filter_widget_2.currentText())
            if idx >= 0: target_cal.filter_widget_2.setCurrentIndex(idx)
            
        # 4. Filter 3 (Year)
        if hasattr(source_cal, 'filter_widget_3') and source_cal.filter_widget_3.isVisible():
            idx = target_cal.filter_widget_3.findText(source_cal.filter_widget_3.currentText())
            if idx >= 0: target_cal.filter_widget_3.setCurrentIndex(idx)

    def _copy_filters_l2r(self):
        self._copy_calendar_filters(self.cal_v1, self.cal_v2)

    def _copy_filters_r2l(self):
        self._copy_calendar_filters(self.cal_v2, self.cal_v1)
