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
import sys
import os
# curriculum_data is in database/
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database"))
import curriculum_data
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
        # Constraint Label (for Teacher View metadata)
        self.constraint_label = QLabel("")
        self.constraint_label.setStyleSheet("color: #d32f2f; font-weight: bold; font-size: 11pt; margin-right: 15px;")
        filter_layout.addWidget(self.constraint_label)
        
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
        
        # New Standard: 30-minute slots from 08:30 to 17:30 (18 slots)
        self.time_labels = []
        start_h, start_m = 8, 30
        for _ in range(18):
            self.time_labels.append(f"{start_h:02d}:{start_m:02d}")
            start_m += 30
            if start_m >= 60:
                start_m -= 60
                start_h += 1 
        
        self.calendar_table.setColumnCount(len(days))
        self.calendar_table.setRowCount(len(self.time_labels))
        
        self.calendar_table.setHorizontalHeaderLabels(days)
        self.calendar_table.setVerticalHeaderLabels(self.time_labels)
        
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
            self.constraint_label.setText("") # Clear constraint label
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
            
        self.filter_changed.emit("filter_selected", data)
    
    def _clear_pool_checkboxes(self):
        """Remove all dynamic pool checkboxes"""
        while self.pool_checks_layout.count():
            item = self.pool_checks_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.pool_checkboxes = {}
    
    def update_pool_checkboxes(self):
        """Create color-coded checkboxes for each elective pool found in actual schedule data.
        
        Uses DB truth (havuz_kodu from schedule data) instead of curriculum_data
        to guarantee checkbox names match filter keys exactly.
        """
        try:
            if self.view_type_combo.currentText() != "Öğrenci Grubu":
                return

            dept_text = self.filter_widget_2.currentText()
            year_text = self.filter_widget_3.currentText()

            if not dept_text or not year_text or year_text == "Seçiniz...":
                self.pool_checks_frame.hide()
                self._clear_pool_checkboxes()
                return

            # Extract unique pool codes from actual schedule data (DB truth)
            found_pools = set()
            for item in self.last_schedule_data:
                if len(item) > 8 and item[5]:  # is_elective = True
                    pool_codes = item[8]  # list of pool codes
                    if pool_codes:
                        for pc in pool_codes:
                            if pc:
                                found_pools.add(pc)

            # Get internship/project info from curriculum_data
            dept_name = dept_text.split('(')[0].strip()
            internship_akts = 0
            project_courses = []
            try:
                year = int(year_text)
                dept_data = curriculum_data.DEPARTMENTS_DATA.get(dept_name)
                if dept_data and 'curriculum' in dept_data:
                    from datetime import datetime
                    current_month = datetime.now().month
                    is_fall = current_month in [8, 9, 10, 11, 12, 1]
                    semester_num = (year - 1) * 2 + (1 if is_fall else 2)
                    sem_year = (semester_num + 1) // 2
                    sem_season = "Güz" if semester_num % 2 != 0 else "Bahar"
                    sem_key = f"{semester_num}. Dönem / {sem_year}. Yıl {sem_season} Dönemi"
                    for course in dept_data['curriculum'].get(sem_key, []):
                        if len(course) < 3: continue
                        code, name, akts = course[0], course[1], course[2]
                        if code.startswith("PRK") or "Staj" in name or "Internship" in name:
                            internship_akts += akts
                        elif any(x in name.lower() for x in ["proje", "project", "tez"]):
                            project_courses.append((code, name, akts))
            except (ValueError, Exception):
                pass

            # If checkboxes already exist for the same set of pools, preserve their state
            existing_states = {code: chk.isChecked() for code, chk in self.pool_checkboxes.items()}
            
            if found_pools == set(existing_states.keys()):
                # Same pools, no need to recreate — just ensure labels are there
                return

            self._clear_pool_checkboxes()

            if not found_pools and internship_akts == 0 and not project_courses:
                self.pool_checks_frame.hide()
                return

            self.pool_checks_frame.show()

            # Auto-detect Semester for label
            from datetime import datetime
            current_month = datetime.now().month
            is_fall = current_month in [8, 9, 10, 11, 12, 1]
            semester_name = "Güz" if is_fall else "Bahar"

            label = QLabel(f"{semester_name} Seçmelileri:")
            label.setStyleSheet("font-weight: bold; margin-right: 5px;")
            self.pool_checks_layout.addWidget(label)

            for pool_code in sorted(found_pools):
                color = self._generate_color(pool_code)
                chk = QCheckBox(f"{pool_code}")
                chk.setStyleSheet(f"font-weight: bold; color: {color.name()};")
                # Preserve old state if existed, default True for new
                old_state = existing_states.get(pool_code, True)
                with QSignalBlocker(chk):
                    chk.setChecked(old_state)
                chk.toggled.connect(self._on_pool_toggled)
                self.pool_checks_layout.addWidget(chk)
                self.pool_checkboxes[pool_code] = chk

            if internship_akts > 0:
                lbl = QLabel(f"Staj ({internship_akts} AKTS)")
                lbl.setStyleSheet("font-weight: bold; color: black; margin-left: 10px;")
                self.pool_checks_layout.addWidget(lbl)

            for code, name, akts in project_courses:
                lbl = QLabel(f"  [{code}] {name} ({akts} AKTS)")
                lbl.setStyleSheet("font-weight: bold; color: #444; margin-left: 10px; font-size: 9pt;")
                self.pool_checks_layout.addWidget(lbl)

        except Exception as e:
            print(f"ERROR in update_pool_checkboxes: {e}")
            import traceback
            traceback.print_exc()

    def _on_pool_toggled(self, checked):
        print(f"DEBUG: Checkbox toggled. State: {checked}")
        if self.last_schedule_data:
            print("DEBUG: Calling display_schedule with last_schedule_data.")
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
                for item in items:
                    try:
                        if len(item) == 2:
                            item_id, name = item
                            widget.addItem(str(name), item_id)
                        elif len(item) == 3:
                            # (id, name, extra_field) — e.g. teachers have room_preference
                            item_id, name, _ = item
                            widget.addItem(str(name), item_id)
                        elif len(item) > 3:
                            print(f"DEBUG error: Skipping malformed item: {item}")
                    except Exception as loop_e:
                        print(f"DEBUG loop error handling item {item}: {loop_e}")
                widget.setCurrentIndex(0)
                widget.blockSignals(False)
                widget.show()
                print(f"DEBUG: update_filter_options populated {len(items)} items")
        except Exception as e:
            print(f"ERROR in update_filter_options: {e}")
            import traceback
            traceback.print_exc()

    def display_schedule(self, schedule_data):
        """
        Display schedule using Prepare-Filter-Render pipeline
        """
        try:
            # Handle dictionary input (with metadata)
            metadata = {}
            if isinstance(schedule_data, dict):
                metadata = schedule_data.get('metadata', {})
                schedule_data = schedule_data.get('schedule', [])

            print(f"DEBUG: display_schedule started. Items: {len(schedule_data)}")
            # Store for client-side filtering when checkboxes change
            self.last_schedule_data = schedule_data
            
            # Update pool checkboxes from actual schedule data (DB truth)
            self.update_pool_checkboxes()
            
            # Update metadata UI (Day Span)
            if 'day_span' in metadata and metadata['day_span'] > 0:
                self.constraint_label.setText(f"Haftalık Gün Kısıtı: {metadata['day_span']} Gün")
            else:
                self.constraint_label.setText("")

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
            is_unavailability = False
            
            # Identify Unavailability (always at index 6 if present)
            if len(item) > 6:
                is_unavailability = (item[6] == "UNAVAILABLE")
                
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
                # Parse Start/End Time
                def time_str_to_min(t_str):
                    h, m = map(int, t_str.split(':'))
                    return h * 60 + m
                
                start_min = time_str_to_min(start)
                end_min = time_str_to_min(end)
                
                # Base Time: 08:30 (510 min)
                base_min = 8 * 60 + 30
                
                # Calculate start slot index
                start_slot_idx = (start_min - base_min) // 30
                end_slot_idx = (end_min - base_min) // 30 # Exclusive end
                
                # Correction for rounding or slightly off times?
                # Assume strictly 30-min aligned input for now.
                
                for slot_idx in range(start_slot_idx, end_slot_idx):
                    # Valid slot range: 0 to 17
                    if 0 <= slot_idx < 18:
                         # Map back to HH:MM label for key? Or just use index?
                         # Using label as key compatible with existing logic
                         if slot_idx < len(self.time_labels):
                             label = self.time_labels[slot_idx]
                             if label not in slots[day]:
                                 slots[day][label] = []
                             
                             slots[day][label].append({
                                 'start_str': start, 
                                 'end_str': end, 
                                 'course': course, 
                                 'extra': extra,
                                 'pools_found': pools_found,
                                 'is_elective': is_elective,
                                 'is_unavailability': is_unavailability
                             })

            except Exception as e:
                print(f"DEBUG: Error parsing time {start}-{end}: {e}")
                continue
                
        print(f"DEBUG: _prepare_slots created {sum(len(v) for day in slots.values() for v in day.values())} total valid slots.")
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
                    # Default: show ALL courses (including electives)
                    # When checkboxes exist and some are unchecked, hide those pools
                    if is_student_view and data['is_elective']:
                        pools = data['pools_found']
                        if self.pool_checkboxes:  # Only filter if checkboxes exist
                            unchecked_pools = {name for name, chk in self.pool_checkboxes.items() if not chk.isChecked()}
                            if pools:
                                # If ALL of this course's pools are unchecked, hide it
                                if pools.issubset(unchecked_pools) if isinstance(pools, set) else all(p in unchecked_pools for p in pools):
                                    continue
                            else:
                                # Elective with no pool identified - show it always
                                pass
                    
                    
                    # Prepare colors for display
                    pool_colors = []
                    if data['pools_found']:
                        for p_name in sorted(data['pools_found']):
                            color = self._generate_color(p_name)
                            seen_pools[p_name] = color
                            pool_colors.append(color)
                    
                    data['pool_colors'] = pool_colors
                    visible_courses.append(data)
                
                print(f"DEBUG: _filter_slots -> Day {day} Hour {hour}: {len(visible_courses)} visible out of {len(course_list)}.")
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
                
                row = -1
                try:
                    row = self.time_labels.index(current_start)
                except ValueError:
                    i += 1
                    continue

                if row < 0 or row >= self.calendar_table.rowCount():
                    i += 1
                    continue
                
                # Unified Merge Logic
                def get_sig(c_list):
                    return tuple(sorted((c['course'], str(c['extra']).strip()) for c in c_list))
                
                curr_sig = get_sig(courses_in_slot)
                
                span = 1
                next_check_idx = i + 1
                
                while next_check_idx < len(start_hours):
                    next_start = start_hours[next_check_idx]
                    if next_start not in day_slots: break
                    next_courses = day_slots[next_start]
                    
                    next_sig = get_sig(next_courses)
                    
                    if (row + span < self.calendar_table.rowCount() and
                        row + span == self.time_labels.index(next_start) and 
                        curr_sig == next_sig):
                        span += 1
                        next_check_idx += 1
                    else:
                        break
                
                # RENDER STRATEGY
                # 1. Multiple Courses -> Horizontal Container
                if len(courses_in_slot) > 1:
                    container = QWidget()
                    hlayout = QHBoxLayout(container)
                    hlayout.setContentsMargins(1, 1, 1, 1)
                    hlayout.setSpacing(2)
                    
                    for course_data in courses_in_slot:
                        # Find the final end string for this specific course in the last slot of the span
                        final_end_str = course_data['end_str']
                        if span > 1:
                            last_slot_courses = day_slots[start_hours[i + span - 1]]
                            for lsc in last_slot_courses:
                                if lsc['course'] == course_data['course'] and str(lsc['extra']).strip() == str(course_data['extra']).strip():
                                    final_end_str = lsc['end_str']
                                    break
                                    
                        text = f"{course_data['course']}"
                        if course_data['start_str']:
                            text += f"\n{course_data['start_str']}-{final_end_str}"
                        
                        lbl = QLabel(text)
                        lbl.setAlignment(Qt.AlignCenter)
                        lbl.setWordWrap(True)
                        
                        full_tooltip = f"{course_data['course']}\n{course_data['extra']}\n{course_data['start_str']}-{final_end_str}"
                        lbl.setToolTip(full_tooltip)
                        
                        p_colors = course_data['pool_colors']
                        if course_data.get('is_unavailability'):
                            bg_color = "#FFC8C8" # Light Red
                        elif p_colors:
                            bg_color = p_colors[0].name()
                        else:
                            bg_color = "#E3F2FD"
                        
                        lbl.setStyleSheet(f"background-color: {bg_color}; border: 1px solid #aaa; padding: 2px; font-size: 8pt;")
                        hlayout.addWidget(lbl)
                    
                    self.calendar_table.setCellWidget(row, col, container)
                    if span > 1:
                        self.calendar_table.setSpan(row, col, span, 1)
                    
                # 2. Single Course -> Standard Item
                else:
                    current_data = courses_in_slot[0]
                    
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
                    if current_data.get('is_unavailability'):
                        item.setBackground(QColor(255, 200, 200)) # Light Red (#FFC8C8)
                    elif p_colors:
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