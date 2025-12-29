# -*- coding: utf-8 -*-
"""
ScheduleService - Business logic layer
Separates business rules from UI (Qt) and data access (repositories)
"""
import sqlite3
from typing import TYPE_CHECKING, List

from models.entities import ScheduleSlot, CourseInput, ScheduledCourse
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
    - Format strings for display (that's Formatter's job)
    
    Design:
    - No Qt dependency → fully testable
    - No Formatter dependency → pure business logic
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
    
    def add_course(self, course: CourseInput) -> ScheduledCourse:
        """
        Add a course to the schedule.
        
        Args:
            course: Validated course input
        
        Returns:
            ScheduledCourse entity (NOT formatted string - let Model/Controller format)
            
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
                # Create new course instance via repository
                try:
                    instance = self._course_repo.create_instance(
                        course.ders,
                        course_result.code
                    )
                except Exception as e:
                    raise CourseCreationError(
                        f"Failed to create course '{course.ders}': {e}"
                    )
            else:
                instance = course_result.instance
            
            # 4. Extract time slot
            gun, baslangic, bitis = slot.to_db_tuple()
            
            # 5. Insert into schedule via repository
            program_id = self._schedule_repo.add_from_components(
                ders_adi=course.ders,
                instance=instance,
                teacher_id=teacher_id,
                slot=slot
            )
            
            # Transaction commits automatically here
        
        # Return entity - let Model/Controller format for UI
        return ScheduledCourse(
            program_id=program_id,
            ders_adi=course.ders,
            ders_instance=instance,
            ders_kodu=course_result.code,
            hoca=course.hoca,
            gun=gun,
            baslangic=baslangic,
            bitis=bitis
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
    
    # ---------- Query methods ----------
    
    def get_all_courses(self) -> List[ScheduledCourse]:
        """
        Get all scheduled courses.
        
        Returns:
            List of all courses in schedule
        """
        return self._schedule_repo.get_all()
    
    def get_courses_by_teacher(self, teacher_id: int) -> List[ScheduledCourse]:
        """
        Get all courses for a specific teacher.
        
        Args:
            teacher_id: Teacher database ID
        
        Returns:
            List of courses for this teacher
        """
        return self._schedule_repo.get_by_teacher(teacher_id)
