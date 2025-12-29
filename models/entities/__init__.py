# -*- coding: utf-8 -*-
"""
Entity classes for type-safe domain modeling
"""
from .schedule_slot import ScheduleSlot
from .course import CourseInput, ScheduledCourse

__all__ = ['ScheduleSlot', 'CourseInput', 'ScheduledCourse']
