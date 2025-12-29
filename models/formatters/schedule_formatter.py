# -*- coding: utf-8 -*-
"""
ScheduleFormatter - Handles UI string formatting for schedule display
Separates presentation logic from domain/data layer
"""
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from models.entities import ScheduledCourse

__all__ = ["ScheduleFormatter"]


class ScheduleFormatter:
    """
    Formatter for schedule-related UI strings.
    
    Principle: Model returns data, Formatter handles display.
    """

    @staticmethod
    def format_time_range(start: str, end: str) -> str:
        """
        Format a time range.
        
        Args:
            start: Start time (HH:MM)
            end: End time (HH:MM)
        
        Returns:
            Formatted time range (e.g., "09:00-10:50")
        """
        return f"{start}-{end}"

    @staticmethod
    def format_day_time(day: str, start: str, end: str) -> str:
        """
        Format day and time.
        
        Args:
            day: Day of week
            start: Start time
            end: End time
        
        Returns:
            Formatted day-time string (e.g., "Pazartesi 09:00-10:50")
        """
        return f"{day} {ScheduleFormatter.format_time_range(start, end)}"

    @staticmethod
    def format_course(
        code: str,
        name: str,
        teacher: str,
        day: str,
        start: str,
        end: str,
        classes: Optional[str] = None,
        pools: Optional[str] = None
    ) -> str:
        """
        Format a course for UI display.
        
        Format: [CODE] Name [Pools] - Teacher (Day Time) [Classes]
        
        Args:
            code: Course code (e.g., "MAT101")
            name: Course name (e.g., "Matematik")
            teacher: Teacher name
            day: Day of week
            start: Start time (HH:MM)
            end: End time (HH:MM)
            classes: Optional class list
            pools: Optional pool codes
        
        Returns:
            Formatted string for display
        
        Example:
            >>> format_course("MAT101", "Matematik", "Prof. Dr. Ali", 
            ...               "Pazartesi", "09:00", "10:50", 
            ...               classes="Bilgisayar Müh. 3. Sınıf")
            "[MAT101] Matematik - Prof. Dr. Ali (Pazartesi 09:00-10:50) [Bilgisayar Müh. 3. Sınıf]"
        """
        parts = [f"[{code}] {name}"]
        
        if pools:
            parts.append(f"[{pools}]")
        
        # DRY: Use format_day_time helper
        parts.append(
            f"- {teacher} ({ScheduleFormatter.format_day_time(day, start, end)})"
        )
        
        if classes:
            parts.append(f"[{classes}]")
        
        return " ".join(parts)

    @staticmethod
    def from_scheduled_course(course: "ScheduledCourse") -> str:
        """
        Format a ScheduledCourse entity for display.
        Entity-aware convenience method.
        
        Args:
            course: ScheduledCourse entity from repository
        
        Returns:
            Formatted string for UI
        
        Example:
            >>> course = repo.get_by_id(123)
            >>> display = ScheduleFormatter.from_scheduled_course(course)
        
        Note:
            Repository stays UI-agnostic. Formatter bridges entity → display.
        """
        return ScheduleFormatter.format_course(
            code=course.ders_kodu,
            name=course.ders_adi,
            teacher=course.hoca,
            day=course.gun,
            start=course.baslangic,
            end=course.bitis,
            classes=course.siniflar,
            pools=course.havuz_kodlari
        )
