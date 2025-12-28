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
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QBrush, QPainter, QPen
import hashlib
from scripts import curriculum_data

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
        
        # Elective Filter (Checkbox)
        self.show_electives_chk = QCheckBox("Seçmeli Dersleri Göster")
        self.show_electives_chk.setChecked(False) # Default off
        self.show_electives_chk.hide()
        self.show_electives_chk.toggled.connect(self._on_filter_changed)
        
        # Add filter widgets to layout
        filter_layout.addWidget(self.filter_widget_1)
        filter_layout.addWidget(self.filter_widget_2)
        filter_layout.addWidget(self.filter_widget_3)
        filter_layout.addWidget(self.show_electives_chk)
        # filter_layout.addWidget(self.elective_label) # Removed
        # filter_layout.addWidget(self.elective_filter_combo) # Removed
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
        
    def _setup_calendar_grid(self):
        """Setup the table widget as a calendar"""
        days = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma"]
        hours = [f"{h:02d}:00" for h in range(8, 18)] # 08:00 to 17:00
        
        self.calendar_table.setColumnCount(len(days))
        self.calendar_table.setRowCount(len(hours))
        
        self.calendar_table.setHorizontalHeaderLabels(days)
        self.calendar_table.setVerticalHeaderLabels(hours)
        
        # Styling
        self.calendar_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.calendar_table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.calendar_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.calendar_table.setSelectionMode(QTableWidget.NoSelection)
        
    def _on_view_type_changed(self):
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
            self.show_electives_chk.show()
            self.filter_widget_3.addItems([str(i) for i in range(1, 5)]) # Years 1-4
        else:
            self.filter_widget_2.hide()
            self.filter_widget_3.hide()
            self.show_electives_chk.hide()
            
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
            data["show_electives"] = self.show_electives_chk.isChecked() # Handled in display logic now
            
            # Trigger update when ready
            if data["dept_id"] and data["year"] and data["year"] != "Seçiniz...":
                 pass # No special action needed for checkbox
            
        self.filter_changed.emit("filter_selected", data)

    # Removed _on_elective_filter_changed and _update_elective_options
    # Replaced by simple CheckBox logic

    
    def _on_filter_1_changed(self):
        """Handle first filter change (Teacher/Classroom/Faculty)"""
        view_type = self.view_type_combo.currentText()
        
        # If Student Group (Faculty changed), reset Dept and Year
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
        """Handle second filter change (Dept)"""
        view_type = self.view_type_combo.currentText()
        # If Student Group (Dept changed), reset Year? 
        # Actually year is static 1-4, maybe just let it be.
        # But we need to ensure the correct signals flow.
        self._on_filter_changed()

    def _on_filter_3_changed(self):
        self._on_filter_changed()

    def update_filter_options(self, widget_index, items):
        """
        Update items in a filter combobox
        items: List of (id, name) tuples
        """
        print(f"DEBUG: update_filter_options called with index {widget_index}, {len(items)} items")
        try:
            print(f"DEBUG: widget_index type: {type(widget_index)}")
            widget = None
            if widget_index == 1:
                widget = self.filter_widget_1
            elif widget_index == 2:
                widget = self.filter_widget_2
            
            print(f"DEBUG: Selected widget: {widget}")
                
            if widget is not None:
                print(f"DEBUG: Found widget for index {widget_index}, populating...")
                widget.blockSignals(True)
                widget.clear()
                widget.addItem("Seçiniz...", None)
                for item_id, name in items:
                    widget.addItem(str(name), item_id)
                widget.setCurrentIndex(0) # Select "Seçiniz..." explicitly
                widget.show() # Force visibility (Critical fix)
                widget.blockSignals(False)
                widget.show() # Force Show (Fix for missing dropdown)
                print(f"DEBUG: Population complete. Widget visible: {widget.isVisible()}")
                print("DEBUG: Population complete.")
            else:
                print(f"DEBUG: No widget found for index {widget_index}")
        except Exception as e:
            print(f"ERROR in update_filter_options: {e}")
            import traceback
            traceback.print_exc()

    def display_schedule(self, schedule_data):
        """
        Display schedule on the grid with merged blocks for consecutive hours
        schedule_data: List of tuples (Day, Start, End, CourseName, ExtraInfo)
        """
        self.calendar_table.clearContents()
        self.calendar_table.clearSpans()
        
        day_map = {
            "Pazartesi": 0, "Salı": 1, "Çarşamba": 2, "Perşembe": 3, 
            "Cuma": 4
        }
        
        # Determine Context (Dept Name) for Pool Lookup
        # Determine Context (Dept Name) for Pool Lookup
        current_dept_name = None
        if self.view_type_combo.currentText() == "Öğrenci Grubu":
             # Widget 2 is Department in Student Group View
             full_text = self.filter_widget_2.currentText() 
             # Remove count e.g. "Computer Eng (40)" -> "Computer Eng"
             current_dept_name = full_text.split('(')[0].strip()
        
        # 1. Organize data onto a grid structure: slot[day_name][start_hour]
        slots = {d: {} for d in day_map}
        seen_pools = {} # name -> color

        for item in schedule_data:
            if len(item) < 4: continue
            day, start, end, course = item[0], item[1], item[2], item[3]
            extra = item[4] if len(item) > 4 else ""
            
            # Unpack extended data if available
            is_elective = False
            pool_codes = set()
            if len(item) > 8: # (day, start, end, display, extra, is_e, real_name, code, pool_codes)
                 is_elective = item[5]
                 pool_codes = set(item[8]) if item[8] else set()
            
            # --- FILTERING ---
            if self.view_type_combo.currentText() == "Öğrenci Grubu":
                if is_elective:
                    if not self.show_electives_chk.isChecked():
                        continue # Skip elective if check is off
                    # If check is on, show all electives (Core + Elective)
            
            if day not in day_map: continue
            
            # Pool Identification (for Coloring)
            pools_found = set()
            if is_elective and current_dept_name:
                if pool_codes:
                     pools_found = pool_codes
                else:
                     # Fallback to text search if pool_codes missing
                     search_text = course
                     if isinstance(extra, str):
                         search_text += " " + extra
                     pools_found = self._identify_pools(search_text, current_dept_name)
            
            pool_colors = []
            if pools_found:
                for p_name in sorted(pools_found):
                    color = self._generate_color(p_name)
                    seen_pools[p_name] = color
                    pool_colors.append(color)

            try:
                start_hour = int(start.split(':')[0])
                slots[day][start_hour] = {
                    'start_str': start, 
                    'end_str': end, 
                    'course': course, 
                    'extra': extra,
                    'pool_colors': pool_colors
                }
            except:
                continue

        # 2. Iterate each day and merge consecutive identical courses
        for day_name, day_slots in slots.items():
            if day_name not in day_map: continue 
            col = day_map[day_name]
            
            start_hours = sorted(day_slots.keys())
            if not start_hours:
                continue
                
            i = 0
            while i < len(start_hours):
                current_start = start_hours[i]
                current_data = day_slots[current_start]
                
                # Check for consecutive blocks
                span = 1
                next_check_idx = i + 1
                
                while next_check_idx < len(start_hours):
                    next_start = start_hours[next_check_idx]
                    next_data = day_slots[next_start]
                    
                    # Criteria: Consecutive Hour AND Identical Course AND Identical Info
                    if (current_start + span == next_start and 
                        current_data['course'] == next_data['course'] and 
                        str(current_data['extra']) == str(next_data['extra'])):
                        
                        span += 1
                        next_check_idx += 1
                    else:
                        break
                
                # Finalize Block
                row = current_start - 8 # 08:00 is row 0
                
                # Last block determines end time
                last_block_start = start_hours[i + span - 1]
                final_end_str = day_slots[last_block_start]['end_str']
                
                display_start = current_data['start_str']
                display_end = final_end_str
                
                text = f"{current_data['course']}\n{current_data['extra']}"
                if current_data['start_str'] and current_data['end_str']:
                     text += f"\n{current_data['start_str']}-{final_end_str}"
                
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)
                item.setToolTip(text.replace('\n', '<br>'))
                
                # Apply Colors
                p_colors = current_data['pool_colors']
                if p_colors:
                     if len(p_colors) == 1:
                         item.setBackground(p_colors[0])
                     else:
                         c1 = p_colors[0]
                         c2 = p_colors[1] if len(p_colors) > 1 else Qt.white
                         brush = QBrush(c1, Qt.FDiagPattern)
                         item.setBackground(brush) # Pattern Lines (C1) on White
                         # If we want C2 background + C1 lines, we need Delegate or more complex brush.
                         # Current: Lines on White is acceptable for "Striped".
                else:
                     item.setBackground(QColor(227, 242, 253)) # Light Blue
                
                if 0 <= row < self.calendar_table.rowCount():
                    self.calendar_table.setItem(row, col, item)
                    if span > 1:
                        self.calendar_table.setSpan(row, col, span, 1)
                
                i += span

        self.legend.update_legend(seen_pools)

    def _identify_pools(self, text, dept_name):
        """Identify which pools the courses in 'text' belong to."""
        found = set()
        dept_data = curriculum_data.DEPARTMENTS_DATA.get(dept_name)
        if not dept_data or 'pools' not in dept_data:
            return found
            
        lower_text = text.lower()
        
        for pool_key, pool_courses in dept_data['pools'].items():
            # Check if any course name exists in text
            for _, p_name, _, _, _, _ in pool_courses:
                if p_name.lower() in lower_text:
                    found.add(pool_key)
                    break 
        return found
        
    def _generate_color(self, seed_text):
        """Generate a consistent pastel color from text string."""
        hash_val = int(hashlib.md5(seed_text.encode()).hexdigest(), 16)
        hue = hash_val % 360
        # Saturation 60-100, Value 90-100 for pastel/light
        return QColor.fromHsv(hue, 150, 240)
