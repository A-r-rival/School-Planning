import copy
import re
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, 
    QLabel, QPushButton, QSplitter, QMessageBox
)
from PyQt5.QtCore import Qt
from views.calendar_view import CalendarView
from services.calendar_schedule_builder import CalendarScheduleBuilder
from views.course_move_preview_dialog import CourseMovePreviewDialog

class ScheduleCompareView(QWidget):
    def __init__(self, model, controller=None):
        super().__init__()
        self.model = model
        self.controller = controller
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
        self.btn_copy_r2l = QPushButton("⬅️")
        self.btn_copy_r2l.setToolTip("Filtreleri Sola Taşı (Eskiden Yeniye)")
        self.btn_copy_r2l.clicked.connect(lambda: self._copy_calendar_filters(self.cal_v1, self.cal_v2))
        self.btn_copy_r2l.setStyleSheet("background-color: #607D8B; color: white; font-size: 16px; font-weight: bold; width: 40px;")
        top_bar.addWidget(self.btn_copy_r2l)
        
        self.btn_copy_l2r = QPushButton("➡️")
        self.btn_copy_l2r.setToolTip("Filtreleri Sağa Taşı (Yeniden Eskiye)")
        self.btn_copy_l2r.clicked.connect(lambda: self._copy_calendar_filters(self.cal_v2, self.cal_v1))
        self.btn_copy_l2r.setStyleSheet("background-color: #607D8B; color: white; font-size: 16px; font-weight: bold; width: 40px;")
        top_bar.addWidget(self.btn_copy_l2r)
        
        top_bar.addStretch()
        
        top_bar.addWidget(QLabel("Eski Versiyon (Karşılaştırma):"))
        self.combo_v1 = QComboBox()
        top_bar.addWidget(self.combo_v1)
        
        layout.addLayout(top_bar)
        
        # Since CalendarView requires controller to feed data based on its combo boxes,
        # we will use Master Schedule View or directly fetch all data for a selected view.
        # For simplicity, we will instantiate a simplified view or wire it carefully.
        self.splitter = QSplitter(Qt.Horizontal)
        
        self.cal_v1 = CalendarView()
        self.cal_v2 = CalendarView()
        
        self.splitter.addWidget(self.cal_v2) # Yeni (Sol)
        self.splitter.addWidget(self.cal_v1) # Eski (Sağ)
        layout.addWidget(self.splitter)
        
        # Connect signals for both calendars
        self.cal_v1.filter_changed.connect(self._on_cal_v1_filter_changed)
        self.cal_v2.filter_changed.connect(self._on_cal_v2_filter_changed)
        
        self.cal_v1.course_selected.connect(lambda data: self._on_course_selected(data, self.cal_v1))
        self.cal_v2.course_selected.connect(lambda data: self._on_course_selected(data, self.cal_v2))
        
        # Initialize builder
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
            
            # If version name already contains a date like (YYYY-MM-DD HH:MM), use it directly.
            # Otherwise, append the database creation date/time.
            if re.search(r'\(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}\)', ad):
                text = ad
            else:
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
            # Ensure it is at least an 11-tuple for uniform parsing
            new_item = list(item)
            while len(new_item) < 11: new_item.append(None)
            
            # If the exact same slot+course is in V2, it's unchanged.
            if sig in v2_items:
                # Add without diff color
                final_v1.append(tuple(new_item))
            else:
                # Not in V2. Did it move?
                c_sig = get_course_sig(item)
                if c_sig in v2_courses:
                    # Moved! Yellow.
                    new_item[9] = "#FFD54F" # Yellow
                    final_v1.append(tuple(new_item))
                else:
                    # Removed completely! Red.
                    new_item[9] = "#EF5350" # Red
                    final_v1.append(tuple(new_item))
                    
        # Compare V2 against V1
        for sig, item in v2_items.items():
            new_item = list(item)
            while len(new_item) < 11: new_item.append(None)
            
            if sig in v1_items:
                final_v2.append(tuple(new_item))
            else:
                c_sig = get_course_sig(item)
                if c_sig in v1_courses:
                    # Moved! Yellow.
                    new_item[9] = "#FFD54F" # Yellow
                    final_v2.append(tuple(new_item))
                else:
                    # Added completely! Green.
                    new_item[9] = "#66BB6A" # Green
                    final_v2.append(tuple(new_item))
                    
        # Replace the schedule lists in results
        res_v1["schedule"] = final_v1
        res_v2["schedule"] = final_v2
        
        self.cal_v1.display_schedule(res_v1)
        self.cal_v2.display_schedule(res_v2)
        
    def _on_course_selected(self, data, sender_cal):
        self.selected_course_data = data
        self.last_clicked_cal = sender_cal
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
            
        cal = getattr(self, 'last_clicked_cal', self.cal_v2)
        orig_schedule = getattr(cal, 'last_schedule_data', [])
        orig_metadata = getattr(cal, 'last_metadata', {})
        active_pools = getattr(cal, 'active_pools', set())
        
        view_type = cal.view_type_combo.currentText()
        dept_text = cal.filter_widget_2.currentText()
        year_text = cal.filter_widget_3.currentText()
        
        v_id = self.combo_v1.currentData() if cal == self.cal_v1 else self.combo_v2.currentData()
        
        dialog = CourseMovePreviewDialog(
            self.selected_course_data, 
            orig_schedule, 
            orig_metadata, 
            self.model, 
            v_id,
            self,
            active_pools=active_pools,
            view_type=view_type,
            dept_text=dept_text,
            year_text=year_text
        )
        
        if dialog.exec_():
            result = dialog.result_data
            if result:
                if self.controller and hasattr(self.controller, 'move_course_slot'):
                    success = self.controller.move_course_slot(
                        result['program_id'], 
                        result['day'], 
                        result['start'], 
                        result['end'], 
                        result['room_id']
                    )
                else:
                    QMessageBox.warning(self, "Hata", "Controller move_course_slot desteği yok.")
                    return
                    
                if success:
                    QMessageBox.information(self, "Başarılı", "Ders başarıyla taşındı.")
                    self._on_compare() # Refresh views
                else:
                    QMessageBox.warning(self, "Hata", "Ders taşınırken bir hata oluştu veya çakışma var.")


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

