# -*- coding: utf-8 -*-
"""
ScheduleSlot - Immutable time slot entity
Type-safe time handling and overlap detection
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import time, datetime
from typing import ClassVar, Tuple


@dataclass(frozen=True, slots=True)
class ScheduleSlot:
    """Immutable representation of a scheduled time slot."""
    
    day: str
    start: time
    end: time

    VALID_DAYS: ClassVar[Tuple[str, ...]] = (
        "Pazartesi", "Salı", "Çarşamba",
        "Perşembe", "Cuma", "Cumartesi", "Pazar"
    )

    TIME_FMT: ClassVar[str] = "%H:%M"

    # ---------- Lifecycle ----------

    def __post_init__(self) -> None:
        self._validate_day()
        self._validate_time_range()

    # ---------- Validation ----------

    def _validate_day(self) -> None:
        if self.day not in self.VALID_DAYS:
            raise ValueError(
                f"Invalid day '{self.day}'. Must be one of {self.VALID_DAYS}"
            )

    def _validate_time_range(self) -> None:
        if self.start >= self.end:
            raise ValueError(
                f"Start time ({self.start}) must be before end time ({self.end})"
            )

    # ---------- Factories ----------

    @classmethod
    def from_strings(
        cls,
        day: str,
        start: str,
        end: str,
    ) -> ScheduleSlot:
        """
        Create ScheduleSlot from HH:MM strings.
        Whitespace-safe and UI-friendly.
        """
        try:
            return cls(
                day=day.strip(),
                start=cls._parse_time(start),
                end=cls._parse_time(end),
            )
        except ValueError as exc:
            raise ValueError(
                f"Invalid time format (expected HH:MM): '{start}' - '{end}'"
            ) from exc

    @staticmethod
    def _parse_time(value: str) -> time:
        return datetime.strptime(value.strip(), ScheduleSlot.TIME_FMT).time()

    # ---------- Domain Logic ----------

    def overlaps(self, other: ScheduleSlot) -> bool:
        """Check whether two slots overlap on the same day."""
        if self.day != other.day:
            return False
        return self.start < other.end and self.end > other.start

    # ---------- Persistence Helpers ----------

    def overlaps_sql_condition(self) -> tuple[str, tuple[str, str, str]]:
        """
        SQL WHERE fragment for overlap detection.
        """
        return (
            "gun = ? AND baslangic < ? AND bitis > ?",
            (self.day, self.end_str, self.start_str),
        )

    def to_db_tuple(self) -> tuple[str, str, str]:
        """Database-ready tuple."""
        return (self.day, self.start_str, self.end_str)

    # ---------- Presentation ----------

    @property
    def start_str(self) -> str:
        return self.start.strftime(self.TIME_FMT)

    @property
    def end_str(self) -> str:
        return self.end.strftime(self.TIME_FMT)

    def to_display_string(self) -> str:
        return f"{self.start_str}-{self.end_str}"
