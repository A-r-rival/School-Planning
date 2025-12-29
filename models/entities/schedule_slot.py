# -*- coding: utf-8 -*-
"""
ScheduleSlot - Immutable time slot entity
Replaces string-based time conflict detection with proper type safety
"""
from dataclasses import dataclass
from datetime import time, datetime
from typing import ClassVar


@dataclass(frozen=True)
class ScheduleSlot:
    """
    Immutable representation of a scheduled time slot.
    Provides type-safe time comparison and conflict detection.
    """
    day: str
    start: time
    end: time
    
    # Valid day names for validation
    VALID_DAYS: ClassVar[list[str]] = [
        "Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"
    ]

    def __post_init__(self):
        """Validate slot on creation"""
        if self.day not in self.VALID_DAYS:
            raise ValueError(f"Invalid day: {self.day}. Must be one of {self.VALID_DAYS}")
        
        if self.start >= self.end:
            raise ValueError(f"Start time ({self.start}) must be before end time ({self.end})")

    @classmethod
    def from_strings(cls, day: str, start_str: str, end_str: str) -> "ScheduleSlot":
        """
        Factory method: Create from HH:MM string format.
        
        Args:
            day: Day of the week (e.g., "Pazartesi")
            start_str: Start time in HH:MM format (e.g., "09:00")
            end_str: End time in HH:MM format (e.g., "10:50")
            
        Returns:
            ScheduleSlot instance
            
        Raises:
            ValueError: If time strings are invalid
        """
        try:
            start_time = datetime.strptime(start_str, "%H:%M").time()
            end_time = datetime.strptime(end_str, "%H:%M").time()
            return cls(day=day, start=start_time, end=end_time)
        except ValueError as e:
            raise ValueError(f"Invalid time format. Expected HH:MM, got '{start_str}'-'{end_str}': {e}")

    def overlaps(self, other: "ScheduleSlot") -> bool:
        """
        Check if this slot overlaps with another slot.
        Two slots overlap if they're on the same day and their time ranges intersect.
        
        Args:
            other: Another ScheduleSlot to check against
            
        Returns:
            True if slots overlap, False otherwise
            
        Example:
            >>> slot1 = ScheduleSlot.from_strings("Pazartesi", "09:00", "10:50")
            >>> slot2 = ScheduleSlot.from_strings("Pazartesi", "10:00", "11:50")
            >>> slot1.overlaps(slot2)
            True
        """
        return (
            self.day == other.day and
            self.start < other.end and
            self.end > other.start
        )

    def to_display_string(self) -> str:
        """
        Format slot for display in UI.
        
        Returns:
            Formatted string like "09:00-10:50"
        """
        return f"{self.start.strftime('%H:%M')}-{self.end.strftime('%H:%M')}"

    def to_db_tuple(self) -> tuple[str, str, str]:
        """
        Convert to database-friendly tuple.
        
        Returns:
            (day, start_str, end_str) tuple ready for SQL insertion
        """
        return (
            self.day,
            self.start.strftime("%H:%M"),
            self.end.strftime("%H:%M")
        )
