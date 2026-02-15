# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QCheckBox, QTableWidget, 
    QTableWidgetItem, QHeaderView, QLabel, QFrame, QWidget, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont

class MasterScheduleView(QDialog):
    """
    Master View displaying ALL resources (Teachers/Classrooms) 
    against ALL Time Slots (Mon-Fri) side-by-side.
    """
    def __init__(self, controller, mode='teacher', parent=None):
        super().__init__(parent)
        self.controller = controller
        self.mode = mode # 'teacher' or 'classroom'
        
        title_map = {'teacher': "Öğretmenler Genel Takvimi", 'classroom': "Derslikler Genel Takvimi"}
        self.setWindowTitle(title_map.get(mode, "Genel Takvim"))
        self.setGeometry(50, 50, 1500, 900)
        
        # Day config
        self.days = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma"]
        self.hours = [f"{h:02d}:00" for h in range(9, 18)] # 09:00 - 17:00 (9 slots)
        # Assuming 9 slots per day based on previous views (09-17)
        # Let's double check standard: usually 08:00 or 09:00. 
        # Previous views used 08-16? Let's check: 
        # calendar_view.py uses 8..17 (9 hours: 8,9,10,11,12,13,14,15,16).
        self.hours = [f"{h:02d}:00" for h in range(8, 17)] 
        
        self._setup_ui()
        self._load_data()
        
    def _setup_ui(self):
        layout = QVBoxLayout()
        
        # 1. Top Bar: Day Toggles
        toggle_frame = QFrame()
        toggle_layout = QHBoxLayout(toggle_frame)
        toggle_layout.addWidget(QLabel("<b>Günler:</b>"))
        
        self.day_checks = {}
        for i, day in enumerate(self.days):
            chk = QCheckBox(day)
            chk.setChecked(True)
            chk.toggled.connect(lambda checked, d_idx=i: self._toggle_day_columns(d_idx, checked))
            toggle_layout.addWidget(chk)
            self.day_checks[i] = chk
            
        toggle_layout.addStretch()
        layout.addWidget(toggle_frame)
        
        # 2. Main Grid
        self.table = QTableWidget()
        self.total_slots = len(self.days) * len(self.hours)
        self.table.setColumnCount(self.total_slots)
        
        # Headers
        headers = []
        for day in self.days:
            for hour in self.hours:
                # Abbreviated header: "Pzt 08"
                headers.append(f"{day[:3]} {hour[:2]}")
                
        self.table.setHorizontalHeaderLabels(headers)
        
        # Coloring Headers (Visual separation)
        header_view = self.table.horizontalHeader()
        # Note: Coloring individual header items is tricky in standard Qt without delegates/proxies
        # We will rely on vertical borders or alternating colors for now.
        
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)
        
        # Legend / Info
        info_label = QLabel("İpucu: Hücrelerin üzerine gelerek detayları görebilirsiniz.")
        layout.addWidget(info_label)
        
        self.setLayout(layout)
        
    def _load_data(self):
        try:
            # 1. Fetch All Data
            data = self.controller.model.get_master_schedule_data()
            self.update_schedule(data)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veri yüklenirken hata: {e}")
            import traceback
            traceback.print_exc()

    def update_schedule(self, data):
        """Render data to the table"""
        self._render_data(data)

    def _render_data(self, data):
        try:
            # 2. Organize by Row Entity
            # row_map: { resource_id: { (day_idx, hour_idx): [courses] } }
            self.row_map = {}
            self.resource_names = {}
            
            for item in data:
                # Normalization for Legacy Snapshots (Raw DB Dump)
                if 'teacher_id' not in item and 'ogretmen_id' in item:
                    item['teacher_id'] = item['ogretmen_id']
                    item['teacher_name'] = f"Öğretmen {item['ogretmen_id']}"
                if 'classroom_id' not in item and 'derslik_id' in item:
                    item['classroom_id'] = item['derslik_id']
                    item['classroom_name'] = f"Derslik {item['derslik_id']}"
                if 'day' not in item and 'gun' in item:
                    item['day'] = item['gun']
                if 'start' not in item and 'baslangic' in item:
                    item['start'] = item['baslangic']
                if 'end' not in item and 'bitis' in item:
                    item['end'] = item['bitis']
                if 'code' not in item and 'ders_adi' in item:
                    item['code'] = item['ders_adi']
                if 'course_name' not in item and 'ders_adi' in item:
                    item['course_name'] = item['ders_adi']
                if 'groups' not in item:
                    item['groups'] = ""

                # Key determination
                if self.mode == 'teacher':
                    rid = item.get('teacher_id')
                    rname = item.get('teacher_name', f"Öğretmen {rid}")
                else:
                    rid = item.get('classroom_id')
                    rname = item.get('classroom_name', f"Derslik {rid}")
                
                if not rid: continue # Skip if no resource (e.g. unassigned teacher/room)
                
                if rid not in self.row_map:
                    self.row_map[rid] = {}
                    self.resource_names[rid] = rname
                
                # Time parsing
                try:
                     # Item: day='Pazartesi', start='09:00', end='10:00'
                     day_idx = self.days.index(item['day'])
                     start_h = int(item['start'].split(':')[0])
                     end_h = int(item['end'].split(':')[0])
                     
                     # Map hours to 0..N indices
                     # Base hour is 8
                     base_hour = 8
                     
                     for h in range(start_h, end_h):
                         h_idx = h - base_hour
                         if 0 <= h_idx < len(self.hours):
                             key = (day_idx, h_idx)
                             if key not in self.row_map[rid]:
                                 self.row_map[rid][key] = []
                             self.row_map[rid][key].append(item)
                except (ValueError, IndexError):
                    continue

            # 3. Render Rows
            sorted_ids = sorted(self.resource_names.keys(), key=lambda k: self.resource_names[k])
            self.table.setRowCount(len(sorted_ids))
            self.table.setVerticalHeaderLabels([self.resource_names[k] for k in sorted_ids])
            
            for row_idx, rid in enumerate(sorted_ids):
                schedule = self.row_map[rid]
                
                for day_idx in range(len(self.days)):
                    for h_idx in range(len(self.hours)):
                        if (day_idx, h_idx) in schedule:
                            items = schedule[(day_idx, h_idx)]
                            
                            # Content
                            # If multiple, stack? or Join?
                            # For master view, concise is better: "MAT101 (G2)"
                            
                            text_lines = []
                            tooltips = []
                            bg_color = None
                            
                            for it in items:
                                code = it['code'] if it['code'] else it['course_name']
                                groups = it['groups'] if it['groups'] else ""
                                # Shorten groups: "Bilgisayar 1. Sınıf" -> "Bil 1"
                                short_groups = groups.replace("Mühendisliği", "").replace(". Sınıf", "").replace("Sınıf", "")
                                
                                line = f"{code}"
                                if self.mode == 'teacher' and it['classroom_name']:
                                     line += f" [{it['classroom_name']}]"
                                elif self.mode == 'classroom' and it['teacher_name']:
                                     # Last name only for brevity?
                                     t_parts = it['teacher_name'].split()
                                     t_short = t_parts[-1] if t_parts else ""
                                     line += f" ({t_short})"
                                     
                                text_lines.append(line)
                                tooltips.append(f"{it['course_name']}\n{it['groups']}\n{it['start']}-{it['end']}")
                                
                                # Color logic (simple: pastel based on course name hash)
                                if not bg_color:
                                     bg_color = self._generate_color(it['course_name'])
                            
                            cell_text = "\n".join(text_lines)
                            
                            # Calculate Column Index
                            # Col = (DayIndex * SlotsPerDay) + HourIndex
                            col_idx = (day_idx * len(self.hours)) + h_idx
                            
                            item = QTableWidgetItem(cell_text)
                            item.setToolTip("\n---\n".join(tooltips))
                            if bg_color:
                                item.setBackground(bg_color)
                            item.setTextAlignment(Qt.AlignCenter)
                            self.table.setItem(row_idx, col_idx, item)

            self.table.resizeColumnsToContents()
            # Enforce max width for readabilty
            for c in range(self.table.columnCount()):
                if self.table.columnWidth(c) > 150:
                    self.table.setColumnWidth(c, 150)
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veri yüklenirken hata: {e}")
            import traceback
            traceback.print_exc()

    def _toggle_day_columns(self, day_idx, visible):
        """Hide/Show all columns belonging to a specific day"""
        slots_per_day = len(self.hours)
        start_col = day_idx * slots_per_day
        end_col = start_col + slots_per_day
        
        for col in range(start_col, end_col):
            if visible:
                self.table.showColumn(col)
            else:
                self.table.hideColumn(col)

    def _generate_color(self, seed_text):
        if not seed_text: return QColor("#FFFFFF")
        import hashlib
        hash_val = int(hashlib.md5(seed_text.encode()).hexdigest(), 16)
        hue = hash_val % 360
        return QColor.fromHsv(hue, 100, 240) # Pastel
