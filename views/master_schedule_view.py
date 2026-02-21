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
        # Day config
        self.days = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma"]
        
        # New Standard: 30-minute slots from 08:30 to 17:30 (18 slots)
        self.time_labels = []
        start_h, start_m = 8, 30
        for _ in range(18):
            self.time_labels.append(f"{start_h:02d}:{start_m:02d}")
            start_m += 30
            if start_m >= 60:
                start_m -= 60
                start_h += 1 
        
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
        # 2. Main Grid
        self.table = QTableWidget()
        self.total_slots = len(self.days) * len(self.time_labels)
        self.table.setColumnCount(self.total_slots + 1) # First column for resource names
        
        # Headers
        headers = ["İsim / Oda"]
        for day in self.days:
            for label in self.time_labels:
                # Abbreviated header: "Pzt 08:30"
                headers.append(f"{day[:3]} {label}")
                
        self.table.setHorizontalHeaderLabels(headers)
        
        # UI Tweaks
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().hide() # Hide row numbers
        
        # Sticky first column feel
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.setColumnWidth(0, 180)
        
        layout.addWidget(self.table)
        
        # Legend / Info
        legend_layout = QHBoxLayout()
        self.legend_frame = QFrame()
        self.legend_layout = QHBoxLayout(self.legend_frame)
        self.legend_layout.setContentsMargins(0, 0, 0, 0)
        
        # Room Type Legend Colors (Ultra-High Contrast)
        self.type_colors = {
            "Laboratuvar": "#D81B60", # Vibrant Magenta-Pink
            "Amfi": "#00C853",        # Neon Green
            "Derslik": "#2962FF"      # Bright Blue
        }
        
        self.legend_label = QLabel("<b>Renk Lejantı:</b> ")
        self.legend_layout.addWidget(self.legend_label)
        
        for t_name, t_color in self.type_colors.items():
            lbl = QLabel(f" ■ {t_name} ")
            lbl.setStyleSheet(f"color: {t_color}; font-weight: bold;")
            self.legend_layout.addWidget(lbl)
            
        legend_layout.addWidget(self.legend_frame)
        legend_layout.addStretch()
        
        info_label = QLabel("İpucu: Hücrelerin üzerine gelerek detayları görebilirsiniz.")
        legend_layout.addWidget(info_label)
        
        layout.addLayout(legend_layout)
        
        if self.mode != 'classroom':
            self.legend_frame.hide()

        self.setLayout(layout)
        
    def _load_data(self):
        try:
            # 1. Fetch All Schedule Data
            schedule_data = self.controller.model.get_master_schedule_data()
            
            # 2. Fetch All Active Resources (to show empty ones)
            if self.mode == 'teacher':
                resources = self.controller.model.get_all_teachers_with_ids()
                # (id, name, pref)
                full_resource_map = {r[0]: r[1] for r in resources}
                full_type_map = {}
            else:
                resources = self.controller.model.aktif_derslikleri_getir()
                # (id, name, type, cap, floor)
                full_resource_map = {r[0]: r[1] for r in resources}
                full_type_map = {r[0]: r[2] for r in resources}

            self._render_data(schedule_data, full_resource_map, full_type_map)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veri yüklenirken hata: {e}")
            import traceback
            traceback.print_exc()
 
    def update_schedule(self, data):
        """Used for external refreshes, fallback to standard load if maps missing"""
        self._load_data()

    def _render_data(self, data, full_resource_map=None, full_type_map=None):
        try:
            # 2. Organize by Row Entity
            self.row_map = {}
            self.resource_names = full_resource_map or {}
            self.resource_types = full_type_map or {}
            
            # Initialize row_map for all resources to ensure they exist
            for rid in self.resource_names:
                self.row_map[rid] = {}

            for item in data:
                # ... (normalization skipped for brevity)
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
                    rname = item.get('teacher_name') or f"Öğretmen {rid}"
                else:
                    rid = item.get('classroom_id')
                    # Robust type handling: default to 'Derslik' if None or empty
                    rtype = item.get('classroom_type') or 'Derslik'
                    rname = item.get('classroom_name') or f"Oda {rid}"
                    self.resource_types[rid] = rtype
                
                if not rid: continue 
                
                if rid not in self.row_map:
                    self.row_map[rid] = {}
                    self.resource_names[rid] = rname
                
                # Time parsing
                # Time parsing
                try:
                     # Item: day='Pazartesi', start='09:00', end='10:00'
                     day_idx = self.days.index(item['day'])
                     
                     # Item start/end are strings "HH:MM".
                     # We need to map them to our slots. 
                     # Our slots start at 08:30, 30 min intervals.
                     
                     def time_str_to_min(t_str):
                         h, m = map(int, t_str.split(':'))
                         return h * 60 + m
                     
                     item_start_min = time_str_to_min(item['start'])
                     item_end_min = time_str_to_min(item['end'])
                     
                     base_start_min = 8 * 60 + 30 # 510
                     
                     # Calculate start slot index
                     # (Start - Base) / 30
                     start_slot_idx = (item_start_min - base_start_min) // 30
                     duration_slots = (item_end_min - item_start_min) // 30
                     
                     for s in range(duration_slots):
                         slot_idx = start_slot_idx + s
                         if 0 <= slot_idx < len(self.time_labels):
                             key = (day_idx, slot_idx)
                             if key not in self.row_map[rid]:
                                 self.row_map[rid][key] = []
                             self.row_map[rid][key].append(item)
                except (ValueError, IndexError):
                    continue

            # 3. Render Rows
            if self.mode == 'classroom':
                def natural_sort_key(s):
                    import re
                    return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s)]
                
                # Priority: Amfi (0), Derslik (1), Lab (2)
                type_priority = {"Amfi": 0, "Derslik": 1, "Laboratuvar": 2}
                
                def master_sort_key(rid):
                    raw_type = self.resource_types.get(rid, "Derslik")
                    type_str = (str(raw_type) or "").lower()
                    
                    if "amfi" in type_str: p = 0
                    elif "lab" in type_str: p = 2
                    else: p = 1 # Derslik is middle
                    
                    return (p, natural_sort_key(str(self.resource_names.get(rid) or "")))
                
                sorted_ids = sorted(self.resource_names.keys(), key=master_sort_key)
            else:
                sorted_ids = sorted(self.resource_names.keys(), key=lambda k: str(self.resource_names.get(k) or ""))
            
            self.table.setRowCount(len(sorted_ids))
            
            for row_idx, rid in enumerate(sorted_ids):
                # Column 0: Resource Name (Label for guaranteed CSS color)
                r_name = self.resource_names[rid]
                
                # Space Saving: Shorten long names
                r_name = r_name.replace("Elektrik_Elektronik", "⚡ & Elektronik").replace("Laboratuvar", "Lab")
                
                if self.mode == 'classroom':
                    r_raw_type = self.resource_types.get(rid)
                    rtype_str = (str(r_raw_type) or "").strip().lower()
                    
                    # Robust mapping (handles "lab", "amfi", or messy database strings)
                    if "lab" in rtype_str:
                        color_hex = self.type_colors["Laboratuvar"]
                    elif "amfi" in rtype_str:
                        color_hex = self.type_colors["Amfi"]
                    elif "derslik" in rtype_str or not r_raw_type:
                        color_hex = self.type_colors["Derslik"]
                    else:
                        # Fallback for unexpected types
                        color_hex = self.type_colors["Derslik"]
                else:
                    color_hex = "#212121" # Teachers are always black
                
                # Create a container widget for padding
                container = QWidget()
                c_layout = QHBoxLayout(container)
                c_layout.setContentsMargins(5, 2, 5, 2)
                
                label = QLabel(r_name)
                # Force color via CSS - Most robust way on Windows
                label.setStyleSheet(f"color: {color_hex}; font-weight: bold; font-size: 13px; background: transparent;")
                c_layout.addWidget(label)
                
                # We still need an item for background/selection if needed
                name_item = QTableWidgetItem()
                name_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                name_item.setBackground(QColor("#FAFAFA"))
                
                self.table.setItem(row_idx, 0, name_item)
                self.table.setCellWidget(row_idx, 0, container)

                schedule = self.row_map[rid]
                
                for day_idx in range(len(self.days)):
                    h_idx = 0
                    while h_idx < len(self.time_labels):
                        current_key = (day_idx, h_idx)
                        if current_key not in schedule:
                            h_idx += 1
                            continue

                        items = schedule[current_key]
                        
                        # Calculate Span
                        span = 1
                        for next_h in range(h_idx + 1, len(self.time_labels)):
                            next_key = (day_idx, next_h)
                            if next_key not in schedule:
                                break
                            
                            next_items = schedule[next_key]
                            if items != next_items:
                                break
                            span += 1
                        
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
                        
                        # Calculate Column Index (+1 for the Name column)
                        col_idx = 1 + (day_idx * len(self.time_labels)) + h_idx
                        
                        item = QTableWidgetItem(cell_text)
                        item.setToolTip("\n---\n".join(tooltips))
                        if bg_color:
                            item.setBackground(bg_color)
                        item.setTextAlignment(Qt.AlignCenter)
                        
                        self.table.setItem(row_idx, col_idx, item)
                        
                        if span > 1:
                            self.table.setSpan(row_idx, col_idx, 1, span)
                        
                        # Advance by span
                        h_idx += span

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
        slots_per_day = len(self.time_labels)
        start_col = 1 + (day_idx * slots_per_day) # +1 offset
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
