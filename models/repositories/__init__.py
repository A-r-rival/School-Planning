# -*- coding: utf-8 -*-
"""
Repository classes for data access layer
"""
from .teacher_repo import TeacherRepository
from .schedule_repo import ScheduleRepository
from .course_repo import CourseRepository
from .room_repo import RoomRepository
from .student_repo import StudentRepository
from .faculty_dept_repo import FacultyDepartmentRepository

__all__ = [
    'TeacherRepository', 
    'ScheduleRepository', 
    'CourseRepository',
    'RoomRepository',
    'StudentRepository',
    'FacultyDepartmentRepository'
]
