# -*- coding: utf-8 -*-
"""
Course entity classes for type-safe course data handling
"""
from dataclasses import dataclass
from typing import Optional


# ---------- helpers ----------

def _clean(value: str) -> str:
    return value.strip()


def _require_fields(**fields: str) -> None:
    missing = [name for name, value in fields.items() if not value or not value.strip()]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")


# ---------- entities ----------

@dataclass(slots=True, frozen=True)
class CourseInput:
    """
    Validated input for adding a course to the schedule.
    Immutable, type-safe replacement for Dict[str, str].
    """
    ders: str
    hoca: str
    gun: str
    baslangic: str
    bitis: str
    ders_tipi: str = "Ders"

    def __post_init__(self):
        _require_fields(
            ders=self.ders,
            hoca=self.hoca,
            gun=self.gun,
            baslangic=self.baslangic,
            bitis=self.bitis,
        )

        # Normalize values (immutable-safe)
        object.__setattr__(self, "ders", _clean(self.ders))
        object.__setattr__(self, "hoca", _clean(self.hoca))
        object.__setattr__(self, "gun", _clean(self.gun))
        object.__setattr__(self, "baslangic", _clean(self.baslangic))
        object.__setattr__(self, "bitis", _clean(self.bitis))
        object.__setattr__(self, "ders_tipi", _clean(self.ders_tipi))


@dataclass(slots=True)
class ScheduledCourse:
    """
    Complete representation of a scheduled course with all metadata.
    Returned from repository/query layer.
    """
    program_id: int
    ders_adi: str
    ders_instance: int
    ders_kodu: str
    hoca: str
    gun: str
    baslangic: str
    bitis: str
    siniflar: Optional[str] = None
    havuz_kodlari: Optional[str] = None

    @property
    def time_range(self) -> str:
        return f"{self.baslangic}-{self.bitis}"

    def to_display_string(self) -> str:
        """
        UI display format:
        [CODE] Name [Pools] - Teacher (Day Time) [Classes]
        """
        parts = [f"[{self.ders_kodu}] {self.ders_adi}"]

        if self.havuz_kodlari:
            parts.append(f"[{self.havuz_kodlari}]")

        parts.append(f"- {self.hoca} ({self.gun} {self.time_range})")

        if self.siniflar:
            parts.append(f"[{self.siniflar}]")

        return " ".join(parts)
