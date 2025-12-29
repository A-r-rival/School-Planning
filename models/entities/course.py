# -*- coding: utf-8 -*-
"""
Course entity classes for type-safe course data handling
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class CourseInput:
    """
    Validated input for adding a course to the schedule.
    Replaces Dict[str, str] with type-safe validation.
    """
    ders: str
    hoca: str
    gun: str
    baslangic: str
    bitis: str
    ders_tipi: str = "Ders"

    def __post_init__(self):
        """
        Validate fields on construction.
        Raises ValueError with specific missing fields for better UI error messages.
        """
        fields = {
            "ders": self.ders,
            "hoca": self.hoca,
            "gun": self.gun,
            "baslangic": self.baslangic,
            "bitis": self.bitis,
        }
        missing = [k for k, v in fields.items() if not v or not str(v).strip()]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
        
        # Trim whitespace
        self.ders = self.ders.strip()
        self.hoca = self.hoca.strip()
        self.gun = self.gun.strip()
        self.baslangic = self.baslangic.strip()
        self.bitis = self.bitis.strip()


@dataclass
class ScheduledCourse:
    """
    Complete representation of a scheduled course with all metadata.
    Used for queries that return full course information.
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
    
    def to_display_string(self) -> str:
        """
        Format for display in UI list.
        Format: [CODE] Name - Teacher (Day Time) [Classes]
        """
        saat = f"{self.baslangic}-{self.bitis}"
        result = f"[{self.ders_kodu}] {self.ders_adi}"
        
        if self.havuz_kodlari:
            result += f" [{self.havuz_kodlari}]"
        
        result += f" - {self.hoca} ({self.gun} {saat})"
        
        if self.siniflar:
            result += f" [{self.siniflar}]"
        
        return result
