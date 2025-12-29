# -*- coding: utf-8 -*-
"""
ScheduleService - Business logic layer
Separates business rules from UI (Qt) and data access (repositories)
"""
import sqlite3
from typing import TYPE_CHECKING

from models.entities import ScheduleSlot, CourseInput
from models.formatters import ScheduleFormatter
from .exceptions import (
    ScheduleConflictError,
    CourseCreationError,
    CourseNotFoundError
)

if TYPE_CHECKING:
    from models.repositories import TeacherRepository, CourseRepository, ScheduleRepository


class ScheduleService:
    """
    Business logic for schedule operations.
    
    Responsibilities:
    - Transaction management (with context managers)
    - Business rule validation
    - Repository orchestration
    - Error handling with custom exceptions
    
    Does NOT:
    - Emit Qt signals (that's ScheduleModel's job)
    - Know about UI
    - Directly access database (uses repositories)
    
    Design:
    - No Qt dependency → fully testable
    - Fail-fast with exceptions
    - Transaction boundaries clearly defined
    """
    
    def __init__(
        self,
        conn: sqlite3.Connection,
        teacher_repo: "TeacherRepository",
        course_repo: "CourseRepository",
        schedule_repo: "ScheduleRepository"
    ):
        self._conn = conn
        self._teacher_repo = teacher_repo
        self._course_repo = course_repo
        self._schedule_repo = schedule_repo
    
    def add_course(self, course: CourseInput) -> str:
        """
        Add a course to the schedule.
        
        Args:
            course: Validated course input
        
        Returns:
            Formatted course info string for UI display
            
        Raises:
            ScheduleConflictError: Time slot conflict detected
            CourseCreationError: Failed to create course instance
        """
        # Create time slot entity
        slot = ScheduleSlot.from_strings(
            course.gun,
            course.baslangic,
            course.bitis
        )
        
        # Transaction: all operations atomic
        with self._conn:
            # 1. Get or create teacher FIRST (needed for conflict check)
            teacher_id = self._teacher_repo.get_or_create(course.hoca)
            
            # 2. Business rule: Check for teacher conflicts
            if self._schedule_repo.has_conflict(slot, teacher_id=teacher_id):
                raise ScheduleConflictError(
                    f"Teacher '{course.hoca}' already has a course at {slot.day} {slot.to_display_string()}"
                )
            
            # 3. Get or create course
            # TODO: Course code generation logic needed here instead of "CODE" placeholder
            course_result = self._course_repo.get_or_create(course.ders, "CODE")
            
            if not course_result.exists:
                # Create new course instance
                try:
                    instance = self._create_course_instance(
                        course.ders,
                        course_result.code
                    )
                except Exception as e:
                    raise CourseCreationError(
                        f"Failed to create course '{course.ders}': {e}"
                    )
            else:
                instance = course_result.instance
            
            # 4. Extract time strings
            gun, baslangic, bitis = slot.to_db_tuple()
            
            # 5. Insert into schedule via repository
            # Note: Using ders_adi (course name) not ders_id - matches schema
            self._schedule_repo.add_raw(
                ders_adi=course.ders,
                instance=instance,
                teacher_id=teacher_id,
                gun=gun,
                baslangic=baslangic,
                bitis=bitis
            )
            
            # Transaction commits automatically here
        
        # Format for UI display
        return ScheduleFormatter.format_course(
            code=course_result.code,
            name=course.ders,
            teacher=course.hoca,
            day=gun,
            start=baslangic,
            end=bitis
        )
    
    def remove_course(self, program_id: int) -> None:
        """
        Remove a course from schedule.
        Fail-fast: raises exception if course not found.
        
        Args:
            program_id: Database ID of schedule entry
            
        Raises:
            CourseNotFoundError: Course doesn't exist
        """
        with self._conn:
            if not self._schedule_repo.remove_by_id(program_id):
                raise CourseNotFoundError(
                    f"Course with program_id={program_id} not found"
                )
    
    # ---------- Private helpers ----------
    
    def _create_course_instance(self, name: str, code: str) -> int:
        """
        Create a new course instance in Dersler table.
        Properly calculates next instance number to avoid conflicts.
        
        Note: This is a temporary method. Will be replaced when
        CourseRepository gets a proper create() method.
        """
        cursor = self._conn.cursor()
        
        # Calculate next instance number
        cursor.execute(
            """
            SELECT MAX(ders_instance)
            FROM Dersler
            WHERE ders_adi = ?
            """,
            (name,)
        )
        row = cursor.fetchone()
        next_instance = (row[0] or 0) + 1
        
        # Create new instance
        cursor.execute(
            """
            INSERT INTO Dersler (ders_adi, ders_instance, ders_kodu)
            VALUES (?, ?, ?)
            """,
            (name, next_instance, code)
        )
        
        return next_instance
