# -*- coding: utf-8 -*-
"""
Unit tests for ScheduleService.
Demonstrates clean, fast testing with in-memory database.
"""
import pytest

from models.entities import CourseInput, ScheduleSlot
from models.services.exceptions import ScheduleConflictError, CourseCreationError


class TestScheduleServiceAddCourse:
    """Tests for ScheduleService.add_course()"""
    
    def test_add_course_success(self, schedule_service):
        """Adding a course should succeed and return formatted string."""
        course_input = CourseInput(
            ders="Matematik",
            hoca="Dr. Ahmet Yılmaz",
            gun="Pazartesi",
            baslangic="09:00",
            bitis="10:50",
            ders_tipi="Ders"
        )
        
        result = schedule_service.add_course(course_input)
        
        # Should return formatted string
        assert "Matematik" in result
        assert "Dr. Ahmet Yılmaz" in result
        assert "Pazartesi" in result
    
    def test_teacher_conflict_raises_error(self, schedule_service):
        """Same teacher at same time should raise ScheduleConflictError."""
        # Add first course
        course1 = CourseInput(
            ders="Matematik",
            hoca="Dr. Ahmet Yılmaz",
            gun="Pazartesi",
            baslangic="09:00",
            bitis="10:50"
        )
        schedule_service.add_course(course1)
        
        # Try to add second course with same teacher at same time
        course2 = CourseInput(
            ders="Fizik",
            hoca="Dr. Ahmet Yılmaz",  # Same teacher!
            gun="Pazartesi",          # Same day!
            baslangic="09:00",        # Same time!
            bitis="10:50"
        )
        
        with pytest.raises(ScheduleConflictError) as exc_info:
            schedule_service.add_course(course2)
        
        assert "Dr. Ahmet Yılmaz" in str(exc_info.value)
        assert "Pazartesi" in str(exc_info.value)
    
    def test_different_teachers_same_time_succeeds(self, schedule_service):
        """Different teachers at same time should succeed (no conflict)."""
        # Add first course
        course1 = CourseInput(
            ders="Matematik",
            hoca="Dr. Ahmet Yılmaz",
            gun="Pazartesi",
            baslangic="09:00",
            bitis="10:50"
        )
        schedule_service.add_course(course1)
        
        # Add second course with different teacher at same time
        course2 = CourseInput(
            ders="Fizik",
            hoca="Dr. Mehmet Demir",  # Different teacher!
            gun="Pazartesi",
            baslangic="09:00",
            bitis="10:50"
        )
        
        # Should NOT raise
        result = schedule_service.add_course(course2)
        assert "Fizik" in result
    
    def test_same_teacher_different_time_succeeds(self, schedule_service):
        """Same teacher at different time should succeed."""
        # Add first course
        course1 = CourseInput(
            ders="Matematik",
            hoca="Dr. Ahmet Yılmaz",
            gun="Pazartesi",
            baslangic="09:00",
            bitis="10:50"
        )
        schedule_service.add_course(course1)
        
        # Add second course same teacher, different time
        course2 = CourseInput(
            ders="İstatistik",
            hoca="Dr. Ahmet Yılmaz",
            gun="Pazartesi",
            baslangic="11:00",  # Different time!
            bitis="12:50"
        )
        
        result = schedule_service.add_course(course2)
        assert "İstatistik" in result


class TestScheduleServiceQueryMethods:
    """Tests for query methods"""
    
    def test_get_all_courses_empty(self, schedule_service):
        """Empty schedule returns empty list."""
        courses = schedule_service.get_all_courses()
        assert courses == []
    
    def test_get_all_courses_returns_added(self, schedule_service):
        """Added courses appear in get_all_courses."""
        # Add a course
        course_input = CourseInput(
            ders="Matematik",
            hoca="Dr. Ahmet Yılmaz",
            gun="Pazartesi",
            baslangic="09:00",
            bitis="10:50"
        )
        schedule_service.add_course(course_input)
        
        courses = schedule_service.get_all_courses()
        assert len(courses) == 1
        assert courses[0].ders_adi == "Matematik"
        assert courses[0].hoca == "Dr. Ahmet Yılmaz"


class TestScheduleServiceRemoveCourse:
    """Tests for remove_course"""
    
    def test_remove_nonexistent_course_raises(self, schedule_service):
        """Removing non-existent course raises CourseNotFoundError."""
        from models.services.exceptions import CourseNotFoundError
        
        with pytest.raises(CourseNotFoundError):
            schedule_service.remove_course(999)
