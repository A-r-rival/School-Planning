# -*- coding: utf-8 -*-
"""
Calendar View - MVC Pattern
Displays weekly schedule grid with filtering options
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel, 
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QBrush

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
        filter_frame.setStyleSheet("background-color: #f5f5f5; border-radius: 5px; padding: 10px;")
        filter_layout = QHBoxLayout(filter_frame)
        
        # Filter Type Selection
        filter_layout.addWidget(QLabel("Görünüm:"))
        self.view_type_combo = QComboBox()
        self.view_type_combo.addItems(["Öğretmen", "Derslik", "Öğrenci Grubu"])
        self.view_type_combo.currentIndexChanged.connect(self._on_view_type_changed)
        filter_layout.addWidget(self.view_type_combo)
        
        # Dynamic Filters
        self.filter_widget_1 = QComboBox() # Teacher/Classroom/Faculty
        self.filter_widget_2 = QComboBox() # Dept (for Student)
        self.filter_widget_3 = QComboBox() # Year (for Student)
        
        # UI fix: Increase width
        self.filter_widget_1.setMinimumWidth(200)
        self.filter_widget_2.setMinimumWidth(200)
        self.filter_widget_3.setMinimumWidth(100)
        
        # Enforce scrollbars by limiting visible items
        self.filter_widget_1.setMaxVisibleItems(20)
        self.filter_widget_2.setMaxVisibleItems(20)
        self.filter_widget_3.setMaxVisibleItems(20)
        
        # Style needed for some OS/Qt versions to ensure scrollbar visibility matches theme
        self.filter_widget_1.setStyleSheet("QComboBox { combobox-popup: 0; }")
        self.filter_widget_2.setStyleSheet("QComboBox { combobox-popup: 0; }")
        self.filter_widget_3.setStyleSheet("QComboBox { combobox-popup: 0; }")
        
        self.filter_widget_1.currentIndexChanged.connect(self._on_filter_1_changed)
        self.filter_widget_2.currentIndexChanged.connect(self._on_filter_2_changed)
        self.filter_widget_3.currentIndexChanged.connect(self._on_filter_3_changed)
        
        filter_layout.addWidget(self.filter_widget_1)
        filter_layout.addWidget(self.filter_widget_2)
        filter_layout.addWidget(self.filter_widget_3)
        
        # Initial visibility
        self.filter_widget_2.hide()
        self.filter_widget_3.hide()
        
        filter_layout.addStretch()
        layout.addWidget(filter_frame)
        
        # Calendar Grid
        self.calendar_table = QTableWidget()
        self._setup_calendar_grid()
        layout.addWidget(self.calendar_table)
        
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
        self.filter_widget_1.clear()
        self.filter_widget_2.clear()
        self.filter_widget_3.clear()
        
        if view_type == "Öğrenci Grubu":
            self.filter_widget_2.show()
            self.filter_widget_3.show()
            self.filter_widget_3.addItems([str(i) for i in range(1, 5)]) # Years 1-4
        else:
            self.filter_widget_2.hide()
            self.filter_widget_3.hide()
            
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
            
        self.filter_changed.emit("filter_selected", data)
    
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
                widget.blockSignals(False)
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
        
        # 1. Organize data onto a grid structure: slot[day_name][start_hour]
        slots = {d: {} for d in day_map}

        for item in schedule_data:
            day, start, end, course, extra = item
            if day not in day_map: continue
            
            try:
                start_hour = int(start.split(':')[0])
                slots[day][start_hour] = {
                    'start_str': start, 
                    'end_str': end, 
                    'course': course, 
                    'extra': extra
                }
            except:
                continue

        # 2. Iterate each day and merge consecutive identical courses
        for day_name, day_slots in slots.items():
            col = day_map[day_name]
            
            # Sorted start hours for this day
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
                        current_data['extra'] == next_data['extra']):
                        
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
                
                text = f"{current_data['course']}\n{current_data['extra']}\n{display_start}-{display_end}"
                item = QTableWidgetItem(text)
                
                item.setBackground(QColor(227, 242, 253)) # Light Blue
                item.setTextAlignment(Qt.AlignCenter)
                tooltip = f"<b>Ders:</b> {current_data['course']}<br><b>Bilgi:</b> {current_data['extra']}<br><b>Saat:</b> {display_start}-{display_end}"
                item.setToolTip(tooltip)
                
                if 0 <= row < self.calendar_table.rowCount():
                    self.calendar_table.setItem(row, col, item)
                    if span > 1:
                        self.calendar_table.setSpan(row, col, span, 1)
                
                i += span
