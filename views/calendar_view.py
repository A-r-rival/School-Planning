# -*- coding: utf-8 -*-
"""
📅 CALENDAR VIEW ARCHITECTURE & IMPLEMENTATION LOGIC
====================================================
MVC Pattern - Weekly Schedule Visualization

1. HIERARCHICAL FLOWING TEXT ENGINE:
   - Optimized for L-profiles (Manhattan geometry). Blocks are divided into 
     Manhattan rectangles, and text flows like fluid from one to the next.
   - Coordinate Synchronization: Prevents drift and overlap by updating the 
     painter state based on the ACTUAL last rendered line.

2. ATOMIC TITLE GROUPING:
   - Course titles ([CODE] + Name) are marked 'atomic'. 
   - They MUST fit within a single rectangle segment to preserve identity.
   - If a title would be split across segments, it jumps to the next availablelobe.

3. NARROW SLOT FALLBACK:
   - For extremely narrow columns (e.g., Fridays), a regex-based fallback is triggered.
   - If the full title doesn't fit, it extracts and renders ONLY the [CODE].

4. VISUAL POLISH:
   - Smart Separators: '|' hides automatically if Room/Time wraps onto new lines.
   - Premium Gradients: Linear subtle gradients (5-8% contrast) for 3D depth.
   - Cosmetic Pens: Width=0 pens utilize single-pixel hardware lines for crisp borders.

🔗 DOCUMENTATION SHORTCUT:
   - DETAILED WALKTHROUGH: docs/walkthrough_calendar_modernization_04.04.26.md
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QFrame, QCheckBox, QScrollArea, QLayout, QSizePolicy, QListView, QApplication
)
from PyQt5.QtCore import Qt, QRect, QPoint, QSize, QSignalBlocker, QTimer, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QCursor, QPalette

class FlowLayout(QLayout):
    """
    Standard FlowLayout implementation for PyQt5 to wrap widgets.
    """
    def __init__(self, parent=None, margin=0, spacing=-1):
        super(FlowLayout, self).__init__(parent)
        if parent is not None:
            self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)
        self.items = []

    def __del__(self):
        del self.items

    def addItem(self, item):
        self.items.append(item)

    def count(self):
        return len(self.items)

    def itemAt(self, index):
        if 0 <= index < len(self.items):
            return self.items[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self.items):
            return self.items.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientations(Qt.Horizontal)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        height = self._do_layout(QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        super(FlowLayout, self).setGeometry(rect)
        self._do_layout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self.items:
            size = size.expandedTo(item.minimumSize())
        margin = self.contentsMargins().left()
        size += QSize(2 * margin, 2 * margin)
        return size

    def _do_layout(self, rect, test_only):
        x = rect.x()
        y = rect.y()
        line_height = 0
        margin = self.contentsMargins().left()

        for item in self.items:
            wid = item.widget()
            space_x = max(0, self.spacing())
            space_y = max(0, self.spacing())
            if wid:
                space_x += max(0, wid.style().layoutSpacing(QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Horizontal))
                space_y += max(0, wid.style().layoutSpacing(QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Vertical))
            
            next_x = x + item.sizeHint().width() + space_x
            if next_x - space_x > rect.right() and line_height > 0:
                x = rect.x()
                y = y + line_height + space_y
                next_x = x + item.sizeHint().width() + space_x
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = next_x
            line_height = max(line_height, item.sizeHint().height())

        return y + line_height - rect.y()

from PyQt5.QtGui import QFontMetrics
import hashlib
import sys
import re
import os
# curriculum_data is in database/
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database"))
import curriculum_data
from scripts.curriculum_helpers import identify_pools

# Fixed font sizes — chosen at max column width; never change dynamically
TITLE_PT  = 8   # Course code + full name
DETAIL_PT = 6   # Teacher, room, time

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

class TimeCanvas(QFrame):
    def __init__(self, time_labels):
        super().__init__()
        self.time_labels = time_labels
        self.setMinimumHeight(len(time_labels) * 20)
        
    def paintEvent(self, event):
        super().paintEvent(event)
        from PyQt5.QtGui import QPainter, QFont, QColor, QPen
        from PyQt5.QtCore import Qt, QRectF
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        slot_height = max(20.0, self.height() / len(self.time_labels))
        w = self.width()
        
        is_dark = QApplication.palette().color(QPalette.Window).lightness() < 128
        grid_color1 = QColor("#444444") if is_dark else QColor("#bbbbbb")
        grid_color2 = QColor("#333333") if is_dark else QColor("#eeeeee")
        dash_color = QColor(255, 255, 255, 60) if is_dark else QColor(0, 0, 0, 40)
        text_color = QColor("#dddddd") if is_dark else QColor("#222222")

        # 1. Background Grid (connects seamlessly to DayCanvas grid)
        for i in range(len(self.time_labels) + 1):
            y = i * slot_height
            pen = QPen(grid_color1 if i % 2 == 0 else grid_color2)
            painter.setPen(pen)
            painter.drawLine(0, int(y), int(w), int(y))
            
        # 2. Hourly Overlays (connects seamlessly to DayCanvas dashed lines)
        dash_pen = QPen(dash_color)
        dash_pen.setWidth(1)
        dash_pen.setStyle(Qt.CustomDashLine)
        dash_pen.setDashPattern([1, 5])
        painter.setPen(dash_pen)
        for i in range(1, len(self.time_labels), 2):
            y = i * slot_height
            painter.drawLine(0, int(y), int(w), int(y))
        
        font = painter.font()
        font.setPointSize(9)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(text_color)
        
        for i, t in enumerate(self.time_labels):
            y = i * slot_height
            rect = QRectF(0, y, self.width() - 5, slot_height)
            # Align perfectly in the vertical center of its bounding box lines
            painter.drawText(rect, Qt.AlignVCenter | Qt.AlignRight, t)


class DayCanvas(QFrame):
    """A custom widget for drawing SVG/Polygon calendar events and background grid."""
    def __init__(self, day_name, time_labels):
        super().__init__()
        self.day_name = day_name
        self.time_labels = time_labels
        self.events = [] 
        self.setMinimumWidth(100)
        self.setMinimumHeight(len(time_labels) * 20)
        self.setMouseTracking(True)
        self.hovered_sig = None

        
    def get_slot_height(self):
        return max(20.0, self.height() / len(self.time_labels))
        
    def set_events(self, events):
        self.events = events
        
        # 1. Cluster Pack Algorithm (Google Calendar style base centers)
        events_sorted = sorted(self.events, key=lambda x: (x['start_slot'], -(x['end_slot'] - x['start_slot'])))
        clusters = []
        current_cluster = []
        cluster_end = -1
        
        for e in events_sorted:
            if e['start_slot'] >= cluster_end and current_cluster:
                clusters.append(current_cluster)
                current_cluster = [e]
                cluster_end = e['end_slot']
            else:
                current_cluster.append(e)
                cluster_end = max(cluster_end, e['end_slot'])
        if current_cluster:
            clusters.append(current_cluster)
            
        for cluster in clusters:
            columns = [] 
            for e in cluster:
                placed = False
                for c_idx, col_events in enumerate(columns):
                    if col_events[-1]['end_slot'] <= e['start_slot']:
                        col_events.append(e)
                        e['col_idx'] = c_idx
                        placed = True
                        break
                if not placed:
                    e['col_idx'] = len(columns)
                    columns.append([e])
                    
            max_cols = len(columns)
            for e in cluster:
                e['base_center'] = (e['col_idx'] + 0.5) / max_cols
        
        self.update() # trigger paintEvent
        
    def clear_events(self):
        self.events = []
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Re-calculate the pool checkboxes container height on resize
        if hasattr(self, 'pool_checks_frame') and self.pool_checks_frame.isVisible():
            self._adjust_pool_frame_height()
            
        # No re-solve needed for midpoint heuristic as it is percentage-based
        self.update()


        
    def mouseMoveEvent(self, event):
        if not hasattr(self, 'drawn_paths'):
            return
            
        found = False
        for sig, data_dict in self.drawn_paths.items():
            if data_dict['path'].contains(event.pos()):
                found = True
                if self.hovered_sig != sig:
                    self.hovered_sig = sig
                    from PyQt5.QtWidgets import QToolTip
                    QToolTip.showText(event.globalPos(), data_dict['tooltip'], self)
                    self.update() # redraw hover state
                break
                
        if not found and self.hovered_sig is not None:
            self.hovered_sig = None
            from PyQt5.QtWidgets import QToolTip
            QToolTip.showText(event.globalPos(), "", self)
            QToolTip.hideText()
            self.update()
            
    def leaveEvent(self, event):
        if hasattr(self, 'hovered_sig') and self.hovered_sig is not None:
            self.hovered_sig = None
            from PyQt5.QtWidgets import QToolTip
            # Aggressively kill the tooltip by showing empty string to bypass OS fade animation
            QToolTip.showText(QCursor.pos(), "", self)
            QToolTip.hideText()
            self.update()
        super().leaveEvent(event)
            
    def paintEvent(self, event):
        super().paintEvent(event)
        from PyQt5.QtGui import QPainter, QPen, QColor, QPainterPath, QFont
        from PyQt5.QtCore import Qt, QRectF
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        slot_height = self.get_slot_height()
        w = self.width()
        
        is_dark = QApplication.palette().color(QPalette.Window).lightness() < 128
        grid_color1 = QColor("#444444") if is_dark else QColor("#bbbbbb")
        grid_color2 = QColor("#333333") if is_dark else QColor("#eeeeee")

        # 1. Background Grid
        pen = QPen()
        pen.setWidth(1)
        for i in range(len(self.time_labels) + 1): 
            y = i * slot_height
            if i % 2 == 0:
                pen.setColor(grid_color1)
            else:
                pen.setColor(grid_color2)
            painter.setPen(pen)
            painter.drawLine(0, int(y), w, int(y))
            
        # 2. Assign horizontal slices per slot
        slot_occupants = {i: [] for i in range(18)}
        
        def get_sig(e):
            d = e['course_data']
            return (d['course'], str(d['extra']).strip(), d['start_str'], d['end_str'])
            
        for e in self.events:
            start_i = int(e['start_slot'])
            end_i = int(e['end_slot'])
            for i in range(start_i, end_i):
                if 0 <= i < 18:
                    slot_occupants[i].append(e)
                    
        # 3. Build geometry rects based on dynamic clustering and expansion boundaries
        self.drawn_paths = {}
        event_rects = {}
        
        for i in range(18):
            occupants = slot_occupants[i]
            if not occupants: continue
            
            # Sort by deterministic base center assigned perfectly during packing phase
            occupants.sort(key=lambda x: x['base_center'])
            K = len(occupants)
            
            for j, e in enumerate(occupants):
                sig = get_sig(e)
                if sig not in event_rects:
                    event_rects[sig] = []
                    
                # Use midpoint heuristic for block positioning
                left_bound = 0.0 if j == 0 else (occupants[j-1]['base_center'] + e['base_center']) / 2.0
                right_bound = 1.0 if j == K - 1 else (e['base_center'] + occupants[j+1]['base_center']) / 2.0
                
                # Inset by 0.5px so pen stroke doesn't fall completely outside the widget, giving crisp solid borders
                x = left_bound * (w - 1) + 0.5
                slice_w = (right_bound - left_bound) * (w - 1)
                y = i * slot_height
                
                # We heavily rely on exact rectangle math! 
                rect = QRectF(x, y, slice_w, slot_height)
                event_rects[sig].append((rect, QRectF(rect))) # tuple (geom, original_for_text)
                
        # 4. Paint Polygons (L-Profiles)
        for e in self.events:
            sig = get_sig(e)
            if sig not in event_rects: continue
            if sig in self.drawn_paths: continue
            
            rect_data = event_rects[sig]
            
            # Form contiguous vertical strips to prevent inner horizontal "brick" lines
            merged_rects = []
            curr_rect = QRectF(rect_data[0][1])
            for _, orig_r in rect_data[1:]:
                # If they have same horizontal footprint and are adjacent vertically
                if abs(orig_r.x() - curr_rect.x()) < 1.0 and abs(orig_r.width() - curr_rect.width()) < 1.0:
                    curr_rect = curr_rect.united(orig_r)
                else:
                    merged_rects.append(curr_rect)
                    curr_rect = QRectF(orig_r)
            merged_rects.append(curr_rect)
            
            path = QPainterPath()
            for r in merged_rects:
                # Minimal inflation (0.1px) just enough for Boolean union intersection without ruining border crispness
                inflated_r = r.adjusted(-0.1, -0.1, 0.1, 0.1)
                
                # Create discrete paths and union them properly
                p = QPainterPath()
                p.addRect(inflated_r)
                if path.isEmpty():
                    path = p
                else:
                    path = path.united(p)
            
            path = path.simplified()
            
            data = e['course_data']
            p_colors = data['pool_colors']
            
            if data.get('is_unavailability'):
                bg_color = QColor("#FFC8C8")
            elif p_colors:
                bg_color = p_colors[0]
            else:
                is_dark = QApplication.palette().color(QPalette.Window).lightness() < 128
                bg_color = QColor("#1565c0") if is_dark else QColor("#e3f2fd")
                
            widths = [r.width() for r in merged_rects]
            is_extreme = False
            # Detect multi-lobed shapes with extreme width differentials (fat belly vs thin edges)
            if len(widths) > 1 and max(widths) / max(1.0, min(widths)) >= 1.8:
                is_extreme = True
                
            from PyQt5.QtGui import QLinearGradient, QBrush
            bounds = path.boundingRect()
            gradient = QLinearGradient(bounds.topLeft(), bounds.bottomRight())
            
            if self.hovered_sig == sig:
                gradient.setColorAt(0.0, bg_color.lighter(115))
                gradient.setColorAt(1.0, bg_color.darker(125))
                border_pen = QPen(QColor(0, 0, 0, 180))
                border_pen.setWidth(2)
            else:
                if is_extreme:
                    # Unify extreme profiles visually with a stronger gradient
                    gradient.setColorAt(0.0, bg_color.lighter(120))
                    gradient.setColorAt(1.0, bg_color.darker(120))
                    border_pen = QPen(QColor(0, 0, 0, 140))
                else:
                    gradient.setColorAt(0.0, bg_color.lighter(110))
                    gradient.setColorAt(1.0, bg_color.darker(110))
                    border_pen = QPen(QColor(0, 0, 0, 50))
                border_pen.setWidth(1)
                
            painter.fillPath(path, QBrush(gradient))
            
            # If there are multiple pools, draw stripes in the bottom right corner
            if p_colors and len(p_colors) > 1:
                painter.save()
                painter.setClipPath(path)
                
                bottom_rect = merged_rects[-1]
                bx = bottom_rect.right()
                by = bottom_rect.bottom()
                
                extra_colors = p_colors[1:]
                from PyQt5.QtGui import QPolygonF
                from PyQt5.QtCore import QPointF
                
                for idx, ec in enumerate(reversed(extra_colors)):
                    size = (len(extra_colors) - idx) * 16 + 8
                    poly = QPolygonF([
                        QPointF(bx - size, by),
                        QPointF(bx, by - size),
                        QPointF(bx, by)
                    ])
                    
                    stripe_path = QPainterPath()
                    stripe_path.addPolygon(poly)
                    painter.fillPath(stripe_path, QBrush(ec))
                    
                painter.restore()

            painter.setPen(border_pen)
            painter.drawPath(path)
            
            # 5. Draw Target Text (Dynamically wrapping across L-Profile Lobes)
            formatted_tooltip = f"{data['course']}\n{data['extra']}\n{data['start_str']}-{data['end_str']}"
            
            self.drawn_paths[sig] = {
                'path': path,
                'tooltip': formatted_tooltip,
            }
            
            painter.save()
            painter.setClipPath(path)
            
            font = painter.font()
            is_bold = self.hovered_sig == sig
            # Dynamically choose text color based on background color lightness
            text_fg = QColor("white") if bg_color.lightness() < 130 else QColor("#111111")
            painter.setPen(text_fg)
            
            # Fixed font sizes (TITLE_PT / DETAIL_PT defined at module level)
            title_font = QFont(font)
            title_font.setPointSize(TITLE_PT)
            title_font.setBold(is_bold)
            
            detail_font = QFont(font)
            detail_font.setPointSize(DETAIL_PT)
            detail_font.setBold(False)
            
            # 1. Build hierarchical font blocks (text, QFont)
            # This ensures consistent categorization for both single-rect and L-profiles
            font_blocks = [(f"{data['course']}", title_font)]
            
            # Clean prefixes just for the calendar block, tooltip keeps them
            clean_extra_lines = []
            for l in str(data.get('extra', '')).split('\n'):
                line = l.strip()
                if not line: continue
                if line.startswith("Öğretmen: "):
                    line = line.replace("Öğretmen: ", "", 1)
                elif line.startswith("Oda: "):
                    line = line.replace("Oda: ", "", 1)
                clean_extra_lines.append(line)
                
            extra_lines = clean_extra_lines
            time_str = f"{data['start_str']}-{data['end_str']}"
            
            if extra_lines:
                # Add all except the last line
                for line in extra_lines[:-1]:
                    font_blocks.append((line, detail_font))
                # Merge the last line (Oda) with the time using a separator
                # Our wrapping engine will naturally put them on the same line if they fit
                merged_info = f"{extra_lines[-1]}  |  {time_str}"
                font_blocks.append((merged_info, detail_font))
            else:
                # Fallback if no extra info is present
                font_blocks.append((time_str, detail_font))

            if len(merged_rects) == 1:
                # Still use the flowing engine for single rects to ensure uniform line spacing
                # and to benefit from the same wrap/atomic logic as L-profiles
                self._draw_flowing_text_hier(painter, merged_rects, font_blocks)
            else:
                # L-profile: prioritize single-block rendering in the best rectangle if possible
                # Find the best rectangle for the single-block attempt: prioritize WIDTH
                best_rect = max(merged_rects, key=lambda r: (r.width() ** 1.5) * r.height())
                best_text_rect = best_rect.adjusted(3, 3, -3, -3)
                
                # Simulation: Does EVERYTHING fit in the best_rect?
                total_needed_h = 0
                title_metrics = QFontMetrics(title_font)
                title_br = title_metrics.boundingRect(best_text_rect.toRect(), Qt.AlignTop | Qt.AlignHCenter | Qt.TextWordWrap, data['course'])
                total_needed_h += title_br.height() + 2
                
                detail_metrics = QFontMetrics(detail_font)
                fits_all = True
                for block_text, _f in font_blocks[1:]:
                    block_br = detail_metrics.boundingRect(best_text_rect.toRect(), Qt.AlignTop | Qt.AlignHCenter | Qt.TextWordWrap, block_text)
                    total_needed_h += block_br.height()
                    if total_needed_h > best_text_rect.height():
                        fits_all = False
                        break
                
                if fits_all:
                    # Content fits in best_rect. Render it there using the engine for consistency.
                    self._draw_flowing_text_hier(painter, [best_rect], font_blocks)
                else:
                    # Content is too large for any single rect, use the flowing engine across all
                    self._draw_flowing_text_hier(painter, merged_rects, font_blocks)
                
            painter.restore()
            
        # 6. Draw Horizontal Hour Alignments (Overlay layer on top of all blocks)
        dash_pen = QPen(QColor(0, 0, 0, 40)) # Very subtle dotted black line
        dash_pen.setWidth(1)
        dash_pen.setStyle(Qt.CustomDashLine)
        dash_pen.setDashPattern([1, 5])
        painter.setPen(dash_pen)
        
        # 1 corresponds to 09:00, 3 to 10:00, 5 to 11:00 etc in our 18 slot grid starting at 08:30
        for i in range(1, 18, 2):
            y = i * slot_height
            painter.drawLine(0, int(y), int(w), int(y))
            
        # 7. Draw ultra-thin jet black boundary for the Day Column
        # We use setWidth(0) to create a 'cosmetic pen' which is exactly 1 hardware pixel, bypassing High-DPI scaling thickness
        edge_pen = QPen(QColor("#000000"))
        edge_pen.setWidth(0)
        painter.setPen(edge_pen)
        painter.drawLine(int(w) - 1, 0, int(w) - 1, self.height())

    def _draw_flowing_text_hier(self, painter, merged_rects, font_blocks):
        """
        Hierarchical flowing text engine.
        font_blocks: list of (text, QFont) tuples.
        Each block flows across merged_rects with its own font size.
        Blocks are tested with lookahead: if a block doesn't fully fit, it's skipped entirely.
        """
        from PyQt5.QtGui import QFontMetrics
        
        if not merged_rects: return
        
        # Start at the first reasonably wide section
        start_idx = 0
        for i, r in enumerate(merged_rects):
            if r.width() >= 50:
                start_idx = i
                break  # Use the FIRST wide rect, not the last
                
        current_rect_idx = start_idx
        current_y = merged_rects[current_rect_idx].y() + 2
        
        def paint_line(line_words, r, y, metrics):
            """
            Draws a single line of centered text, handling smart separator hiding.
            The separator '|' is hidden if it wraps to the start or end of a line.
            """
            clean_words = [w for w in line_words if w.strip()]
            if not clean_words: return
            
            # Smart Separator: Hide '|' if it's the first or last word of a wrapped line
            if clean_words[0] == "|":
                clean_words = clean_words[1:]
            if clean_words and clean_words[-1] == "|":
                clean_words = clean_words[:-1]
                
            line_text = " ".join(clean_words).strip()
            if not line_text: return
            
            # Horizontal centering
            if hasattr(metrics, 'horizontalAdvance'):
                text_w = metrics.horizontalAdvance(line_text)
            else:
                text_w = metrics.width(line_text)
            text_x = r.x() + (r.width() - text_w) / 2.0
            
            # Clip horizontal rendering to the rectangle bounds to prevent bleeding into adjacent blocks
            painter.save()
            painter.setClipRect(r.adjusted(2, 0, -2, 0)) # Slight padding
            painter.drawText(int(text_x), int(y + metrics.ascent()), line_text)
            painter.restore()
            
        def layout_block(text, block_font, r_idx, y, commit=False, atomic=False):
            metrics = QFontMetrics(block_font)
            line_height = metrics.lineSpacing()
            
            # ATOMIC BLOCK CHECK: If the entire block doesn't fit in the CURRENT rectangle's remaining space,
            # but COULD fit fully in the NEXT rectangle, jump to the next rectangle first.
            while r_idx + 1 < len(merged_rects):
                r_current = merged_rects[r_idx]
                remaining_h = r_current.bottom() - y
                
                # Measure height needed for this block's text at current width
                # Use a slightly smaller width check to be safe (-8 for padding)
                needed_br = metrics.boundingRect(
                    QRect(0, 0, int(r_current.width() - 8), 1000),
                    Qt.AlignTop | Qt.AlignHCenter | Qt.TextWordWrap,
                    text
                )
                
                if needed_br.height() > remaining_h:
                    # It doesn't fit here. Check if it fits better in the next rectangle
                    r_next = merged_rects[r_idx + 1]
                    next_needed_br = metrics.boundingRect(
                        QRect(0, 0, int(r_next.width() - 8), 1000),
                        Qt.AlignTop | Qt.AlignHCenter | Qt.TextWordWrap,
                        text
                    )
                    if next_needed_br.height() <= r_next.height():
                        r_idx += 1
                        y = merged_rects[r_idx].y()
                        continue
                break

            # Smart split: keep '|' as its own word so we can hide it if it wraps
            words = []
            for t in text.split(' '):
                if not t.strip(): continue
                if t == "|":
                    words.append("|")
                elif "|" in t:
                    parts = t.split("|")
                    for k, p in enumerate(parts):
                        if p: words.append(p)
                        if k < len(parts) - 1: words.append("|")
                else:
                    words.append(t)
            if commit:
                painter.setFont(block_font)
                    
            curr_line = []
            word_idx = 0
            while word_idx < len(words):
                if r_idx >= len(merged_rects): return False, r_idx, y
                r = merged_rects[r_idx]
                
                # Check if current line fits in this rect
                if y + line_height > r.y() + r.height():
                    if atomic: return False, r_idx, y # Atomic block MUST fit in one rect
                    
                    if curr_line:
                        if commit: paint_line(curr_line, r, y, metrics)
                        curr_line = []
                        y += line_height
                        continue
                    else:
                        r_idx += 1
                        if r_idx >= len(merged_rects): return False, r_idx, y
                        next_top = merged_rects[r_idx].y()
                        if next_top > y:
                            y = next_top
                        continue
                        
                word = words[word_idx]
                test_line = " ".join(curr_line + [word])
                w_line = metrics.horizontalAdvance(test_line) if hasattr(metrics, 'horizontalAdvance') else metrics.width(test_line)
                    
                if w_line <= r.width() - 8 or not curr_line:
                    curr_line.append(word)
                    word_idx += 1
                else:
                    if commit: paint_line(curr_line, r, y, metrics)
                    curr_line = []
                    y += line_height
                    
            if curr_line:
                if y + line_height > merged_rects[r_idx].bottom():
                    if atomic: return False, r_idx, y
                    r_idx += 1
                    if r_idx >= len(merged_rects): return False, r_idx, y
                    y = merged_rects[r_idx].y()
                    if commit: paint_line(curr_line, merged_rects[r_idx], y, metrics)
                    return True, r_idx, y + line_height
                else:
                    if commit: paint_line(curr_line, merged_rects[r_idx], y, metrics)
                    y += line_height
            return True, r_idx, y

        for i, (block_text, block_font) in enumerate(font_blocks):
            # Title wraps within its rect but never jumps to another rect.
            # Passing atomic=False lets word-wrap happen; the jump-prevention
            # is handled by layout_block's pre-check loop (it only jumps when
            # the whole block fits better in the next rect).
            is_title = (i == 0)
            fits, sim_idx, sim_y = layout_block(block_text, block_font, current_rect_idx, current_y, commit=False, atomic=False)
            
            if fits or is_title:
                _, current_rect_idx, current_y = layout_block(block_text, block_font, current_rect_idx, current_y, commit=True, atomic=False)
            else:
                break  # Nothing left to render
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
        self.view_type_combo.addItems(["Öğrenci Grubu", "Öğretmen", "Derslik"])
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
        
        # Semester Info Label (e.g., "Bahar Dönemi")
        self.semester_info_label = QLabel("")
        self.semester_info_label.setStyleSheet("font-weight: bold; color: #1565c0; margin-left: 10px; font-size: 10pt;")
        self.semester_info_label.hide()
        filter_layout.addWidget(self.semester_info_label)
        
        filter_layout.addStretch()
        layout.addWidget(filter_frame)
        
        # Dynamic Pool Checkboxes Container (In a new row for proper wrap-around)
        self.pool_checks_frame = QWidget()
        self.pool_checks_frame.hide()
        self.pool_checks_layout = FlowLayout(self.pool_checks_frame, margin=5, spacing=15)
        layout.addWidget(self.pool_checks_frame)

        # Constraint Label (for Teacher View metadata)
        self.constraint_label = QLabel("")
        self.constraint_label.setStyleSheet("color: #d32f2f; font-weight: bold; font-size: 11pt; margin-left: 15px; margin-bottom: 5px;")
        self.constraint_label.hide() # Hide by default to save space
        layout.addWidget(self.constraint_label)
        
        # Calendar Grid
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background-color: transparent; border: none;")
        
        self.calendar_container = QWidget()
        self.calendar_layout = QHBoxLayout(self.calendar_container)
        self.calendar_layout.setContentsMargins(0, 0, 0, 0)
        self.calendar_layout.setSpacing(0)
        
        self._setup_calendar_grid()
        self.scroll_area.setWidget(self.calendar_container)
        layout.addWidget(self.scroll_area)
        
        # Legend Widget
        self.legend = LegendWidget()
        layout.addWidget(self.legend)
        
        self.setLayout(layout)
        
        # Store dynamically created checkboxes: {pool_name: QCheckBox}
        self.pool_checkboxes = {}
        
        # Store last schedule data for client-side filtering
        self.last_schedule_data = []
        
    def _setup_calendar_grid(self):
        """Setup the custom absolute-positioned calendar grid."""
        days = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma"]
        
        self.time_labels = []
        start_h, start_m = 8, 30
        for _ in range(18):
            self.time_labels.append(f"{start_h:02d}:{start_m:02d}")
            start_m += 30
            if start_m >= 60:
                start_m -= 60
                start_h += 1 
                
        self.day_columns = {}
        
        # 1. Time Column
        time_container = QWidget()
        time_container.setFixedWidth(60)
        time_layout = QVBoxLayout(time_container)
        time_layout.setContentsMargins(0, 0, 5, 0) 
        time_layout.setSpacing(0)
        
        header_spacer = QLabel()
        header_spacer.setFixedHeight(30)
        time_layout.addWidget(header_spacer)
        
        self.time_canvas = TimeCanvas(self.time_labels)
        time_layout.addWidget(self.time_canvas)
        # Note: No addStretch() so it fills naturally matching DayCanvas!
        self.calendar_layout.addWidget(time_container)
        
        # 2. Day Columns
        for day in days:
            day_widget = QWidget()
            day_layout = QVBoxLayout(day_widget)
            day_layout.setContentsMargins(0, 0, 0, 0)
            day_layout.setSpacing(0)
            
            header = QLabel(day)
            header.setAlignment(Qt.AlignCenter)
            header.setStyleSheet("font-weight: bold; border-bottom: 2px solid #000; border-right: 1px solid #000;")
            header.setFixedHeight(30)
            day_layout.addWidget(header)
            
            canvas = DayCanvas(day, self.time_labels)
            # Remove thick CSS border, handled by ultra-thin QPainter line in canvas
            canvas.setStyleSheet("background-color: transparent;")
            
            day_layout.addWidget(canvas)
            # Note: No addStretch() so DayCanvas dynamically fills the vertical space!
            
            self.calendar_layout.addWidget(day_widget)
            self.day_columns[day] = canvas

    def _on_view_type_changed(self, idx=None):
        """Handle view type change"""
        view_type = self.view_type_combo.currentText()
        
        # Reset filters with signal blocking
        self.filter_widget_1.blockSignals(True)
        self.filter_widget_2.blockSignals(True)
        self.filter_widget_3.blockSignals(True)
        
        self.filter_widget_1.clear()
        self.filter_widget_2.clear()
        self.filter_widget_3.clear()
        
        self.filter_widget_1.show() # Ensure visible
        
        if view_type == "Öğrenci Grubu":
            self.filter_widget_2.show()
            self.filter_widget_3.show()
            self.filter_widget_3.addItem("Seçiniz...", None)
            self.filter_widget_3.addItems([str(i) for i in range(1, 5)]) # Years 1-4
        else:
            self.filter_widget_2.hide()
            self.filter_widget_3.hide()
            self.semester_info_label.hide()
            self.pool_checks_frame.hide()
            self.constraint_label.setText("") # Clear constraint label
            self._clear_pool_checkboxes()
            
        self.filter_widget_1.blockSignals(False)
        self.filter_widget_2.blockSignals(False)
        self.filter_widget_3.blockSignals(False)
            
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
                self.semester_info_label.hide()
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
                                found_pools.add(pc.upper().strip())

            # Get internship/project info from curriculum_data, and pool AKTS
            dept_name = dept_text.split('(')[0].strip()
            # Use a dict for stats to avoid nonlocal scope issues in older Python or nested try/except
            stats = {'internship_akts': 0}
            project_courses = []
            pool_current_akts = {} # AKTS in current selected semester
            # We no longer scan other semesters for asterisk logic (semester-specific)
            # Store valid pools for this semester to filter the calendar grid later
            self.current_semester_pools = set()
            
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
                    
                    # Helper to extract pool AKTS and USD/projects
                    def process_semester_courses(courses_list, is_current_sem):
                        for course in courses_list:
                            if len(course) < 3: continue
                            code, name, akts = course[0], course[1], course[2]
                            
                            is_matched_pool = False
                            
                            # Normalize code for matching (e.g., 'ZSD I' -> 'ZSD')
                            import re
                            normalized = re.sub(r'\s*(I|II|III|IV|V|VI|VII|VIII)$', '', code).strip().upper()
                            code_upper = code.upper().strip()

                            # Check match in found_pools (Must be in current semester to count)
                            if code_upper in found_pools:
                                pool_current_akts[code_upper] = pool_current_akts.get(code_upper, 0) + akts
                                is_matched_pool = True
                            elif normalized in found_pools:
                                pool_current_akts[normalized] = pool_current_akts.get(normalized, 0) + akts
                                is_matched_pool = True
                                    
                            # Capture special elements
                            if is_current_sem:
                                is_internship = code.startswith("PRK") or "Staj" in name or "Internship" in name
                                is_elective_kw = "seçmeli" in name.lower() or "elective" in name.lower() or "havuz" in name.lower()
                                is_project = any(x in name.lower() for x in ["proje", "project", "tez", "thesis", "bitirme"]) and not is_elective_kw
                                is_usd = "usd" in code.lower() or "üsd" in code.lower() or "üniversite seçmeli" in name.lower() or "university elective" in name.lower()
                                
                                if is_internship:
                                    stats['internship_akts'] += akts
                                elif is_project:
                                    project_courses.append((code, name, akts))
                                elif is_usd:
                                    found_pools.add(code_upper)
                                    pool_current_akts[code_upper] = pool_current_akts.get(code_upper, 0) + akts
                                elif not is_matched_pool:
                                    # If it's an unmatched elective pool in the current semester (e.g. SDVIII)
                                    # we show it as a checkbox by adding it to found_pools!
                                    if is_elective_kw:
                                        found_pools.add(code_upper)
                                        pool_current_akts[code_upper] = pool_current_akts.get(code_upper, 0) + akts

                    # 1. Process CURRENT semester only
                    current_courses = dept_data['curriculum'].get(sem_key, [])
                    process_semester_courses(current_courses, is_current_sem=True)
                    
                    # Track valid pools for filtering the grid
                    self.current_semester_pools = {p.upper().strip() for p in pool_current_akts.keys()}
                            
            except (ValueError, Exception) as e:
                print(f"DEBUG: Error parsing curriculum for pool AKTS: {e}")

            # Get semester name for context
            from datetime import datetime
            current_month = datetime.now().month
            is_fall = current_month in [8, 9, 10, 11, 12, 1]
            semester_name = "Güz" if is_fall else "Bahar"

            # Track filter context to detect changes and reset checkbox states if department/year/semester changes
            current_context = (dept_text.strip(), year_text.strip(), semester_name)
            if not hasattr(self, '_last_checkbox_context') or self._last_checkbox_context != current_context:
                existing_states = {}
                self._last_checkbox_context = current_context
            else:
                existing_states = {code.upper().strip(): chk.isChecked() for code, chk in self.pool_checkboxes.items()}
            
            # Remove the early return so that labels (like AKTS counts) get updated correctly 
            # even if the set of pools is exactly the same as the previous view.

            # Detect sub-pools: pool_b is a sub-pool if another pool_a is a prefix of it
            # Or if pool_b is a sub-pool of a required curriculum wildcard (like SDUX -> SDUa)
            sub_pools = set()
            
            all_req_codes = [pc[0].upper().strip() for pc in project_courses] + list(pool_current_akts.keys())
            
            for pool_b in found_pools:
                pool_b_upper = pool_b.upper().strip()
                
                # Check wildcard matching (e.g., SDUX requires SDUA, SDUB...)
                for req_code in all_req_codes:
                    if req_code.endswith('X'):
                        prefix = req_code[:-1]
                        if pool_b_upper.startswith(prefix) and pool_b_upper != req_code:
                            sub_pools.add(pool_b_upper)
                            break
                            
                for pool_a in found_pools:
                    if pool_a != pool_b and pool_b.startswith(pool_a):
                        # Prevent Roman numeral suffixes from being considered sub-pools (e.g. ZSDII is not a sub-pool of ZSDI)
                        remainder = pool_b[len(pool_a):]
                        if not all(c in 'IVX ' for c in remainder):
                            sub_pools.add(pool_b_upper)

            self._clear_pool_checkboxes()

            # Update the main filter bar's semester info label
            self.semester_info_label.setText(f"| {semester_name} Dönemi")
            self.semester_info_label.show()

            if not found_pools and stats['internship_akts'] == 0 and not project_courses:
                self.pool_checks_frame.hide()
                return

            self.pool_checks_frame.show()

            for pool_code in sorted(found_pools):
                pool_code_upper = pool_code.upper().strip()
                color = self._generate_color(pool_code_upper)
                color_hex = color.name()
                
                is_sub_pool = pool_code_upper in sub_pools
                current_akts = pool_current_akts.get(pool_code_upper, 0)

                # Do not show checkboxes for pools that have 0 AKTS in this semester and are not sub-pools.
                if current_akts == 0 and not is_sub_pool:
                    continue

                # Sub-pool ise AKTS'in yanına * ekle (hangi üst poola dahil olduğunu işaret eder)
                if is_sub_pool:
                    akts_text = f" ({current_akts}* AKTS)"
                else:
                    akts_text = f" ({current_akts} AKTS)"
                
                chk = QCheckBox(f"{pool_code_upper}{akts_text}")
                # Simple but clean style
                chk.setCursor(Qt.PointingHandCursor)
                
                # Apply pool color to the checkbox text
                style = f"""
                    QCheckBox {{
                        color: {color_hex};
                        font-weight: bold;
                        font-size: 9pt;
                        margin-right: 5px;
                    }}
                    QCheckBox:unchecked {{
                        color: #999;
                    }}
                """
                chk.setStyleSheet(style)
                
                with QSignalBlocker(chk):
                    # Checked eğer: AKTS > 0 VEYA yıldız varsa (sub-pool)
                    # İkisi de yoksa unchecked gelir
                    default_checked = (current_akts > 0) or is_sub_pool
                    chk.setChecked(existing_states.get(pool_code_upper, default_checked))
                    
                # Store color in property for toggling
                chk.setProperty("tag_color", color_hex)
                
                chk.toggled.connect(self._on_pool_toggled)
                self.pool_checks_layout.addWidget(chk)
                self.pool_checkboxes[pool_code_upper] = chk

            is_dark = QApplication.palette().color(QPalette.Window).lightness() < 128
            label_color = "white" if is_dark else "black"
            project_color = "#ccc" if is_dark else "#444"

            if stats['internship_akts'] > 0:
                lbl = QLabel(f"Staj ({stats['internship_akts']} AKTS)")
                lbl.setStyleSheet(f"font-weight: bold; color: {label_color}; margin-left: 10px;")
                self.pool_checks_layout.addWidget(lbl)

            for code, name, akts in project_courses:
                lbl = QLabel(f"[{code}] {name} ({akts} AKTS)")
                lbl.setStyleSheet(f"font-weight: bold; color: {project_color}; margin-left: 10px; font-size: 9pt;")
                self.pool_checks_layout.addWidget(lbl)
                
            # Force the frame to allocate vertical space for the FlowLayout so it doesn't overlap the calendar
            QTimer.singleShot(0, self._adjust_pool_frame_height)

        except Exception as e:
            print(f"ERROR in update_pool_checkboxes: {e}")
            import traceback
            traceback.print_exc()

    def _adjust_pool_frame_height(self):
        """Calculates and sets the proper height for the FlowLayout container to prevent overlapping."""
        if not self.pool_checks_frame.isVisible() or self.pool_checks_layout.count() == 0:
            return
        
        # Calculate height based on current width minus some margins
        target_width = self.pool_checks_frame.width()
        if target_width <= 0:
            target_width = self.width() - 40
            
        needed_height = self.pool_checks_layout.heightForWidth(target_width)
        
        # Add layout margins
        margins = self.pool_checks_layout.contentsMargins()
        needed_height += margins.top() + margins.bottom()
        
        # Set minimum height so the QVBoxLayout allocates space for it
        self.pool_checks_frame.setMinimumHeight(needed_height)

    def _on_pool_toggled(self, checked):
        # Update styling of the sender
        chk = self.sender()
        if isinstance(chk, QCheckBox):
            color_hex = chk.property("tag_color")
            if color_hex:
                text_color = color_hex if checked else "#999"
                chk.setStyleSheet(f"QCheckBox {{ color: {text_color}; font-weight: bold; font-size: 9pt; margin-right: 5px; }}")

        if self.last_schedule_data:
            self.display_schedule(self.last_schedule_data, refresh_checkboxes=False)
    
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
            self.pool_checks_frame.hide()
            self.semester_info_label.hide()
            self._clear_pool_checkboxes()
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

    def display_schedule(self, schedule_data, refresh_checkboxes=True):
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
            if refresh_checkboxes:
                self.update_pool_checkboxes()
            
            # Update metadata UI (Day Span)
            if 'day_span' in metadata and metadata['day_span'] > 0:
                self.constraint_label.setText(f"Haftalık Gün Kısıtı: {metadata['day_span']} Gün")
                self.constraint_label.show()
            else:
                self.constraint_label.setText("")
                self.constraint_label.hide()

            # 1. Prepare
            slots = self._prepare_slots(schedule_data)
            
            # 2. Filter
            filtered_slots, seen_pools = self._filter_slots(slots)
            
            # 3. Render
            self._render_grid(filtered_slots, seen_pools)
            
            # 4. Enforce Legend visibility
            # If in Student Group view, we keep bottom legend hidden because we have checkboxes at top
            if self.view_type_combo.currentText() == "Öğrenci Grubu":
                self.legend.hide()
            else:
                # In Teacher/Room view, show legend only if it's not already empty
                if seen_pools:
                    self.legend.show()
                else:
                    self.legend.hide()
            
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

        # Parse Start/End Time
        def time_str_to_min(t_str):
            h, m = map(int, t_str.split(':'))
            return h * 60 + m

        for item in schedule_data:
            if len(item) < 4: continue
            day, start, end, course = item[0], item[1], item[2], item[3]
            extra = item[4] if len(item) > 4 else ""
            
            # Unpack extended data if available
            is_elective = False
            pool_codes = set()
            is_unavailability = False
            
            # Identify Unavailability (always at index 6 if present)
            if len(item) > 6 and item[6] is not None:
                is_unavailability = (str(item[6]) == "UNAVAILABLE")
                
            if len(item) > 8: 
                is_elective = item[5]
                pool_codes = {pc.upper().strip() for pc in item[8] if pc} if item[8] else set()
            
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
                    pools_found = {p.upper().strip() for p in identify_pools(search_text, current_dept_name) if p}
            
            if day not in day_map: continue
            
            try:
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
                        
                        if pools:
                            # It belongs to some pools. Check if any of these pools are active (have checkboxes)
                            if self.pool_checkboxes:
                                course_checkbox_pools = {p.upper().strip() for p in pools if p and p.upper().strip() in self.pool_checkboxes}
                                
                                if course_checkbox_pools:
                                    # Intersect with checked boxes
                                    checked_pools = {name for name, chk in self.pool_checkboxes.items() if chk.isChecked()}
                                    if not course_checkbox_pools.intersection(checked_pools):
                                        continue
                                else:
                                    # Course belongs to pools, but NONE are relevant to this semester (no checkboxes).
                                    continue
                            else:
                                # There are no elective checkboxes for this semester at all.
                                continue
                        else:
                            # Elective with no pool identified - probably just show it as fallback
                            pass
                    
                    
                    # Prepare colors for display
                    pool_colors = []
                    if data['pools_found']:
                        pools_to_color = data['pools_found']
                        if is_student_view and self.pool_checkboxes and data.get('is_elective'):
                            relevant = {p for p in pools_to_color if p.upper().strip() in self.pool_checkboxes}
                            if relevant:
                                pools_to_color = relevant

                        for p_name in sorted(pools_to_color):
                            p_name_upper = p_name.upper().strip()
                            color = self._generate_color(p_name_upper)
                            seen_pools[p_name_upper] = color
                            pool_colors.append(color)
                    
                    data['pool_colors'] = pool_colors
                    visible_courses.append(data)
                
                print(f"DEBUG: _filter_slots -> Day {day} Hour {hour}: {len(visible_courses)} visible out of {len(course_list)}.")
                if visible_courses:
                    filtered_slots[day][hour] = visible_courses
                    
        return filtered_slots, seen_pools

    def _render_grid(self, slots, seen_pools):
        """
        Phase 3: Dispatch events to the custom Polygon renderer (DayCanvas).
        """
        for canvas in self.day_columns.values():
            canvas.clear_events()
            
        def time_to_slot(t_str):
            h, m = map(int, t_str.split(':'))
            return ((h * 60 + m) - 510) / 30.0 # 510 is 08:30

        for day_name, day_slots in slots.items():
            if day_name not in self.day_columns: continue
            canvas = self.day_columns[day_name]
            
            # Extract unique blocks to prevent duplication across 30-min slots
            unique_blocks = {}
            for start_str, courses in day_slots.items():
                for c in courses:
                    # A block is uniquely defined by its name, extra details, and exact start/end time.
                    sig = (c['course'], str(c['extra']).strip(), c['start_str'], c['end_str'])
                    if sig not in unique_blocks:
                        unique_blocks[sig] = c
                        
            events_flat = []
            for sig, data in unique_blocks.items():
                start_slot = time_to_slot(data['start_str'])
                end_slot = time_to_slot(data['end_str'])
                if end_slot <= start_slot:
                    end_slot = start_slot + 1 # fallback safe duration
                    
                events_flat.append({
                    'course_data': data,
                    'start_slot': start_slot,
                    'end_slot': end_slot
                })
                
            # Render using Polygon Architecture natively!
            canvas.set_events(events_flat)
        
        # 6. Update Legend after all canvases are rendered
        self.legend.update_legend(seen_pools)

    def _generate_color(self, seed_text):
        """Generate a consistent pastel color from text string."""
        import hashlib
        normalized = str(seed_text).upper().strip()
        hash_val = int(hashlib.md5(normalized.encode()).hexdigest(), 16)
        hue = hash_val % 360
        
        # Check if dark theme is active
        is_dark = QApplication.palette().color(QPalette.Window).lightness() < 128
        if is_dark:
            # Lower brightness (150) and slightly higher saturation (180) for dark mode contrast
            return QColor.fromHsv(hue, 180, 150)
        
        # Saturation 150, Value 240 for vibrant but readable colors in light mode
        return QColor.fromHsv(hue, 150, 240)