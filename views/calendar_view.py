# -*- coding: utf-8 -*-
"""
Calendar View - MVC Pattern
Displays weekly schedule grid with filtering options
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel, 
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QCheckBox,
    QListView
)
from PyQt5.QtCore import Qt, pyqtSignal, QSignalBlocker
from PyQt5.QtGui import QColor, QBrush
import hashlib
from scripts import curriculum_data
from scripts.curriculum_helpers import identify_pools

class LegendWidget(QWidget):
    """Dynamic Legend Widget for Elective Pools"""
    def __init__(self):
        super().__init__()
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 5, 0, 5)
        self.setLayout(self.layout)
        self.setStyleSheet("background-color: transparent;")
        
    def update_legend(self, pool_colors):
        """
        pool_colors: dict {pool_name: QColor}
        """
        # Clear existing
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not pool_colors:
            self.hide()
            return
            
        self.show()
        self.layout.addWidget(QLabel("<b>Lejant:</b>"))
        
        for name, color in pool_colors.items():
            lbl = QLabel(f"  {name}  ")
            # Determine text color (white for dark backgrounds)
            fg_color = "white" if color.lightness() < 128 else "black"
            lbl.setStyleSheet(f"background-color: {color.name()}; color: {fg_color}; border-radius: 4px; padding: 2px;")
            self.layout.addWidget(lbl)
            
        self.layout.addStretch()

class CalendarView(QWidget):
    """
    Weekly Calendar View Widget
    """
    # Signals
    filter_changed = pyqtSignal(str, dict) # filter_type, filter_data
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Haftalık Ders Programı")
        self.setGeometry(100, 100, 1400, 900)
        
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout()
        
        # Filter Section
        filter_frame = QFrame()
        filter_frame.setFrameShape(QFrame.StyledPanel)
        # Style removed entirely to diagnose "detached window" issue
        # filter_frame.setStyleSheet("#FilterFrame { background-color: #f5f5f5; border-radius: 5px; }")
        filter_layout = QHBoxLayout(filter_frame)
        
        # Filter Type Selection
        filter_layout.addWidget(QLabel("Görünüm:"))
        self.view_type_combo = QComboBox()
        self.view_type_combo.setView(QListView())  # Prevent popup window
        self.view_type_combo.addItems(["Öğretmen", "Derslik", "Öğrenci Grubu"])
        self.view_type_combo.currentIndexChanged.connect(self._on_view_type_changed)
        filter_layout.addWidget(self.view_type_combo)
        
        # Dynamic Filters
        self.filter_widget_1 = QComboBox() # Teacher/Classroom/Faculty
        self.filter_widget_2 = QComboBox() # Dept (for Student)
        self.filter_widget_3 = QComboBox() # Year (for Student)

        # Prevent popup windows by using QListView
        self.filter_widget_1.setView(QListView())
        self.filter_widget_2.setView(QListView())
        self.filter_widget_3.setView(QListView())
        
        # Force dropdown style (not popup) - Critical fix for Windows
        combo_style = """
            QComboBox {
                combobox-popup: 0;
            }
            QComboBox QAbstractItemView {
                border: 1px solid gray;
                selection-background-color: lightblue;
            }
        """
        self.view_type_combo.setStyleSheet(combo_style)
        self.filter_widget_1.setStyleSheet(combo_style)
        self.filter_widget_2.setStyleSheet(combo_style)
        self.filter_widget_3.setStyleSheet(combo_style)
        
        # UI fix: Increase width
        self.filter_widget_1.setMinimumWidth(200)
        self.filter_widget_2.setMinimumWidth(200)
        self.filter_widget_3.setMinimumWidth(100)
        
        # Enforce scrollbars by limiting visible items
        self.filter_widget_1.setMaxVisibleItems(20)
        self.filter_widget_2.setMaxVisibleItems(20)
        self.filter_widget_3.setMaxVisibleItems(20)
        
        # Connect change handlers
        self.filter_widget_1.currentIndexChanged.connect(self._on_filter_1_changed)
        self.filter_widget_2.currentIndexChanged.connect(self._on_filter_2_changed)
        self.filter_widget_3.currentIndexChanged.connect(self._on_filter_3_changed)
        
        # Add filter widgets to layout
        filter_layout.addWidget(self.filter_widget_1)
        filter_layout.addWidget(self.filter_widget_2)
        filter_layout.addWidget(self.filter_widget_3)
        
        # Dynamic Pool Checkboxes Container
        self.pool_checks_frame = QFrame()
        self.pool_checks_layout = QHBoxLayout(self.pool_checks_frame)
        self.pool_checks_layout.setContentsMargins(0, 0, 0, 0)
        self.pool_checks_layout.setSpacing(10)
        self.pool_checks_frame.hide()  # Hidden by default
        filter_layout.addWidget(self.pool_checks_frame)
        filter_layout.addStretch()
        layout.addWidget(filter_frame)
        
        # Calendar Grid
        self.calendar_table = QTableWidget()
        self._setup_calendar_grid()
        layout.addWidget(self.calendar_table)
        
        # Legend Widget
        self.legend = LegendWidget()
        layout.addWidget(self.legend)
        
        self.setLayout(layout)
        
        # Store dynamically created checkboxes: {pool_name: QCheckBox}
        self.pool_checkboxes = {}
        
        # Store last schedule data for client-side filtering
        self.last_schedule_data = []
        
    def _setup_calendar_grid(self):
        """Setup the table widget as a calendar"""
        days = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma"]
        hours = [f"{h:02d}:00" for h in range(8, 17)] # 08:00 to 16:00 (End 17:00)
        
        self.calendar_table.setColumnCount(len(days))
        self.calendar_table.setRowCount(len(hours))
        
        self.calendar_table.setHorizontalHeaderLabels(days)
        self.calendar_table.setVerticalHeaderLabels(hours)
        
        # Styling
        self.calendar_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.calendar_table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.calendar_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.calendar_table.setSelectionMode(QTableWidget.NoSelection)

    def _on_view_type_changed(self, idx=None):
        """Handle view type change"""
        view_type = self.view_type_combo.currentText()
        
        # Reset filters
        self.filter_widget_1.blockSignals(True)
        self.filter_widget_1.clear()
        self.filter_widget_1.blockSignals(False)
        self.filter_widget_1.show() # Ensure visible
        
        self.filter_widget_2.clear()
        self.filter_widget_3.clear()
        
        if view_type == "Öğrenci Grubu":
            self.filter_widget_2.show()
            self.filter_widget_3.show()
            self.filter_widget_3.addItems([str(i) for i in range(1, 5)]) # Years 1-4
        else:
            self.filter_widget_2.hide()
            self.filter_widget_3.hide()
            self.pool_checks_frame.hide()
            self._clear_pool_checkboxes()
            
        # Emit signal to request data for filters
        self.filter_changed.emit("type_changed", {"type": view_type})
        
    def _on_filter_changed(self):
        """Handle specific filter selection"""
        view_type = self.view_type_combo.currentText()
        data = {}
        
        if view_type == "Öğretmen":
            data["teacher_id"] = self.filter_widget_1.currentData()
        elif view_type == "Derslik":
            data["classroom_id"] = self.filter_widget_1.currentData()
        elif view_type == "Öğrenci Grubu":
            data["faculty_id"] = self.filter_widget_1.currentData()
            data["dept_id"] = self.filter_widget_2.currentData()
            data["year"] = self.filter_widget_3.currentText()
            data["selected_pools"] = [name for name, chk in self.pool_checkboxes.items() if chk.isChecked()]
            
            self.update_pool_checkboxes()
            
        self.filter_changed.emit("filter_selected", data)
    
    def _clear_pool_checkboxes(self):
        """Remove all dynamic pool checkboxes"""
        while self.pool_checks_layout.count():
            item = self.pool_checks_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.pool_checkboxes = {}
    
    def update_pool_checkboxes(self):
        """Create color-coded checkboxes for each elective pool in current semester"""
        try:
            print("DEBUG: update_pool_checkboxes started")
            if self.view_type_combo.currentText() != "Öğrenci Grubu":
                return

            dept_text = self.filter_widget_2.currentText()
            year_text = self.filter_widget_3.currentText()

            if not dept_text or not year_text or year_text == "Seçiniz...":
                self.pool_checks_frame.hide()
                self._clear_pool_checkboxes()
                return

            # Clean dept name
            dept_name = dept_text.split('(')[0].strip()
            print(f"DEBUG: Processing pool checkboxes for Dept: {dept_name}, Year: {year_text}")
            
            try:
                year = int(year_text)
            except ValueError:
                return

            # Get curriculum data
            dept_data = curriculum_data.DEPARTMENTS_DATA.get(dept_name)
            if not dept_data or 'curriculum' not in dept_data:
                print(f"DEBUG: No curriculum data found for {dept_name}")
                return

            # Auto-detect Semester
            from datetime import datetime
            current_month = datetime.now().month
            
            is_fall = current_month in [8, 9, 10, 11, 12, 1]
            
            semester_num = (year - 1) * 2 + (1 if is_fall else 2)
            semester_name = "Güz" if is_fall else "Bahar"
            
            sem_courses = dept_data['curriculum'].get(str(semester_num), [])
            print(f"DEBUG: Found {len(sem_courses)} courses in curriculum for Sem {semester_num}")
            
            required_pools = {}
            internship_akts = 0
            project_courses = []
            
            for course in sem_courses:
                if len(course) < 3: continue
                code, name, akts = course[0], course[1], course[2]
                
            # Check for internship first
                if code.startswith("PRK") or "Staj" in name or "Internship" in name:
                    internship_akts += akts
                    continue
                
            # Check for excluded project courses (matching scheduler logic)
                name_lower = name.lower()
                if any(x in name_lower for x in ["proje", "project"]):
                    project_courses.append((code, name, akts))
                    continue
                
                pool_type = None
                if code.startswith("ZSD"): pool_type = "ZSD"
                elif code.startswith("USD") or code.startswith("ÜSD"): pool_type = "ÜSD"
                elif code.startswith("SD"): pool_type = code # Keep specific code
                
                if "Seçmeli Ders" in name and not pool_type: pool_type = "SD"
                
                if pool_type:
                    required_pools[pool_type] = required_pools.get(pool_type, 0) + akts

            self._clear_pool_checkboxes()
            
            if not required_pools and internship_akts == 0 and not project_courses:
                self.pool_checks_frame.hide()
                return
            
            self.pool_checks_frame.show()
            label = QLabel(f"{semester_name} Seçmelileri:")
            label.setStyleSheet("font-weight: bold; margin-right: 5px;")
            self.pool_checks_layout.addWidget(label)
            
            print(f"DEBUG: Adding checkboxes for pools: {list(required_pools.keys())}")
            for pool_type in sorted(required_pools.keys()):
                akts = required_pools[pool_type]
                color = self._generate_color(pool_type)
                
                chk = QCheckBox(f"{pool_type} ({akts} AKTS)")
                chk.setStyleSheet(f"font-weight: bold; color: {color.name()};")
                # Block signals to prevent triggering toggle immediately
                with  QSignalBlocker(chk):
                     chk.setChecked(False)
                chk.toggled.connect(self._on_pool_toggled)
                self.pool_checks_layout.addWidget(chk)
                self.pool_checkboxes[pool_type] = chk
            
            if internship_akts > 0:
                lbl = QLabel(f"Staj ({internship_akts} AKTS)")
                lbl.setStyleSheet("font-weight: bold; color: black; margin-left: 10px;")
                self.pool_checks_layout.addWidget(lbl)
        
            for code, name, akts in project_courses:
                lbl = QLabel(f"  [{code}] {name} ({akts} AKTS)")
                lbl.setStyleSheet("font-weight: bold; color: #444; margin-left: 10px; font-size: 9pt;")
                self.pool_checks_layout.addWidget(lbl)
                
            print("DEBUG: update_pool_checkboxes complete")
        except Exception as e:
            print(f"ERROR in update_pool_checkboxes: {e}")
            import traceback
            traceback.print_exc()

    def _on_pool_toggled(self, checked):
        if self.last_schedule_data:
            self.display_schedule(self.last_schedule_data)
    
    def _on_filter_1_changed(self):
        view_type = self.view_type_combo.currentText()
        if view_type == "Öğrenci Grubu":
            self.filter_widget_2.blockSignals(True)
            self.filter_widget_3.blockSignals(True)
            self.filter_widget_2.clear()
            self.filter_widget_3.clear()
            self.filter_widget_3.addItem("Seçiniz...", None)
            self.filter_widget_3.addItems([str(i) for i in range(1, 5)])
            self.filter_widget_2.blockSignals(False)
            self.filter_widget_3.blockSignals(False)
        self._on_filter_changed()

    def _on_filter_2_changed(self):
        self._on_filter_changed()

    def _on_filter_3_changed(self):
        self._on_filter_changed()

    def update_filter_options(self, widget_index, items):
        try:
            widget = None
            if widget_index == 1: widget = self.filter_widget_1
            elif widget_index == 2: widget = self.filter_widget_2
                
            if widget is not None:
                widget.blockSignals(True)
                widget.clear()
                widget.addItem("Seçiniz...", None)
                for item_id, name in items:
                    widget.addItem(str(name), item_id)
                widget.setCurrentIndex(0)
                widget.blockSignals(False)
                widget.show()
        except Exception:
            pass

    def display_schedule(self, schedule_data):
        """
        Display schedule using Prepare-Filter-Render pipeline
        """
        try:
            print(f"DEBUG: display_schedule started. Items: {len(schedule_data)}")
            # Store for client-side filtering when checkboxes change
            self.last_schedule_data = schedule_data
            
            # 1. Prepare
            slots = self._prepare_slots(schedule_data)
            
            # 2. Filter
            filtered_slots, seen_pools = self._filter_slots(slots)
            
            # 3. Render
            self._render_grid(filtered_slots, seen_pools)
            
            print("DEBUG: display_schedule complete")
        except Exception as e:
            print(f"ERROR in display_schedule: {e}")
            import traceback
            traceback.print_exc()

    def _prepare_slots(self, schedule_data):
        """
        Phase 1: Process raw data into time slots and identify pools.
        Returns: slots dict {day: {hour: [course_data, ...]}}
        """
        day_map = {
            "Pazartesi": 0, "Salı": 1, "Çarşamba": 2, "Perşembe": 3, "Cuma": 4
        }
        slots = {d: {} for d in day_map}
        
        # Helper to get current context (Dept Name) for pool ID
        current_dept_name = None
        if self.view_type_combo.currentText() == "Öğrenci Grubu":
            full_text = self.filter_widget_2.currentText() 
            current_dept_name = full_text.split('(')[0].strip()

        for item in schedule_data:
            if len(item) < 4: continue
            day, start, end, course = item[0], item[1], item[2], item[3]
            extra = item[4] if len(item) > 4 else ""
            
            # Unpack extended data if available
            is_elective = False
            pool_codes = set()
            if len(item) > 8: 
                is_elective = item[5]
                pool_codes = set(item[8]) if item[8] else set()
            
            # Identify Pools using Helper
            pools_found = set()
            if is_elective and current_dept_name:
                if pool_codes:
                    pools_found = pool_codes
                else:
                    search_text = course
                    if isinstance(extra, str):
                        search_text += " " + extra
                    # Use imported helper
                    pools_found = identify_pools(search_text, current_dept_name)
            
            if day not in day_map: continue
            
            try:
                start_hour = int(start.split(':')[0])
                end_hour = int(end.split(':')[0])
                
                # Create slot entries for ALL hours the course spans
                # This allows the merge logic to correctly span consecutive hours
                for hour in range(start_hour, end_hour):
                    if hour not in slots[day]:
                        slots[day][hour] = []
                    
                    slots[day][hour].append({
                        'start_str': start, 
                        'end_str': end, 
                        'course': course, 
                        'extra': extra,
                        'pools_found': pools_found, # Store raw pools, resolve colors later
                        'is_elective': is_elective
                    })
            except:
                continue
                
        return slots

    def _filter_slots(self, slots):
        """
        Phase 2: Apply active filters (checkboxes, view types).
        Returns: (filtered_slots, seen_pools_with_colors)
        """
        active_pools = {name for name, chk in self.pool_checkboxes.items() if chk.isChecked()}
        
        filtered_slots = {d: {} for d in slots}
        seen_pools = {} # {name: color}
        
        is_student_view = (self.view_type_combo.currentText() == "Öğrenci Grubu")
        
        for day, hours in slots.items():
            for hour, course_list in hours.items():
                visible_courses = []
                for data in course_list:
                    
                    # Student View Filtering Logic
                    if is_student_view and data['is_elective']:
                        pools = data['pools_found']
                        if not pools:
                            # If no pools identified but it is elective,
                            # hide it if *any* filter is active (show if no filter active)
                            if active_pools:
                                continue
                        else:
                            # If pools identified, must match at least one active filter
                            if not any(p in active_pools for p in pools):
                                continue
                    
                    # Prepare colors for display
                    pool_colors = []
                    if data['pools_found']:
                        for p_name in sorted(data['pools_found']):
                            color = self._generate_color(p_name)
                            seen_pools[p_name] = color
                            pool_colors.append(color)
                    
                    data['pool_colors'] = pool_colors
                    visible_courses.append(data)
                
                if visible_courses:
                    filtered_slots[day][hour] = visible_courses
                    
        return filtered_slots, seen_pools

    def _render_grid(self, slots, seen_pools):
        """
        Phase 3: Render widgets to QTableWidget.
        """
        self.calendar_table.clearContents()
        self.calendar_table.clearSpans()
        
        day_map = {
            "Pazartesi": 0, "Salı": 1, "Çarşamba": 2, "Perşembe": 3, "Cuma": 4
        }
        
        from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel
        
        for day_name, day_slots in slots.items():
            if day_name not in day_map: continue 
            col = day_map[day_name]
            
            start_hours = sorted(day_slots.keys())
            if not start_hours:
                continue
            
            i = 0
            while i < len(start_hours):
                current_start = start_hours[i]
                courses_in_slot = day_slots[current_start] 
                
                row = current_start - 8 
                if row < 0 or row >= self.calendar_table.rowCount():
                    i += 1
                    continue
                
                # RENDER STRATEGY
                # 1. Multiple Courses -> Horizontal Container
                if len(courses_in_slot) > 1:
                    container = QWidget()
                    hlayout = QHBoxLayout(container)
                    hlayout.setContentsMargins(1, 1, 1, 1)
                    hlayout.setSpacing(2)
                    
                    for course_data in courses_in_slot:
                        text = f"{course_data['course']}"
                        if course_data['start_str']:
                            text += f"\n{course_data['start_str']}-{course_data['end_str']}"
                        
                        lbl = QLabel(text)
                        lbl.setAlignment(Qt.AlignCenter)
                        lbl.setWordWrap(True)
                        
                        full_tooltip = f"{course_data['course']}\n{course_data['extra']}\n{course_data['start_str']}-{course_data['end_str']}"
                        lbl.setToolTip(full_tooltip)
                        
                        p_colors = course_data['pool_colors']
                        bg_color = p_colors[0].name() if p_colors else "#E3F2FD"
                        
                        lbl.setStyleSheet(f"background-color: {bg_color}; border: 1px solid #aaa; padding: 2px; font-size: 8pt;")
                        hlayout.addWidget(lbl)
                    
                    self.calendar_table.setCellWidget(row, col, container)
                    i += 1
                    
                # 2. Single Course -> Standard Item (with Merge Check)
                else:
                    current_data = courses_in_slot[0]
                    
                    # Merge Logic
                    span = 1
                    next_check_idx = i + 1
                    
                    while next_check_idx < len(start_hours):
                        next_start = start_hours[next_check_idx]
                        if next_start not in day_slots: break # Should not happen if in keys
                        next_courses = day_slots[next_start]
                        
                        if len(next_courses) == 1:
                            next_data = next_courses[0]
                            # Check continuity and identity
                            if (current_start + span == next_start and 
                                current_data['course'] == next_data['course'] and 
                                str(current_data['extra']) == str(next_data['extra'])):
                                span += 1
                                next_check_idx += 1
                            else:
                                break
                        else:
                            break
                    
                    # Determination of End Time
                    if span > 1:
                        final_end_str = day_slots[start_hours[i + span - 1]][0]['end_str']
                    else:
                        final_end_str = current_data['end_str']
                    
                    text = f"{current_data['course']}\n{current_data['extra']}"
                    if current_data['start_str']:
                        text += f"\n{current_data['start_str']}-{final_end_str}"
                    
                    item = QTableWidgetItem(text)
                    item.setTextAlignment(Qt.AlignCenter)
                    item.setToolTip(text.replace('\n', '<br>'))
                    
                    # Coloring
                    p_colors = current_data['pool_colors']
                    if p_colors:
                        if len(p_colors) == 1:
                            item.setBackground(p_colors[0])
                        else:
                            brush = QBrush(p_colors[0], Qt.FDiagPattern)
                            item.setBackground(brush)
                    else:
                        item.setBackground(QColor(227, 242, 253))
                    
                    self.calendar_table.setItem(row, col, item)
                    if span > 1:
                        self.calendar_table.setSpan(row, col, span, 1)
                    
                    i += span

        self.legend.update_legend(seen_pools)
        
    def _generate_color(self, seed_text):
        """Generate a consistent pastel color from text string."""
        hash_val = int(hashlib.md5(seed_text.encode()).hexdigest(), 16)
        hue = hash_val % 360
        # Saturation 60-100, Value 90-100 for pastel/light
        return QColor.fromHsv(hue, 150, 240)