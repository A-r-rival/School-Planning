# -*- coding: utf-8 -*-
"""
Service layer exceptions
Clean error handling without Qt dependencies
"""


class ScheduleServiceError(Exception):
    """Base exception for schedule service errors."""
    pass


class ScheduleConflictError(ScheduleServiceError):
    """Raised when a time slot conflict is detected."""
    pass


class CourseCreationError(ScheduleServiceError):
    """Raised when course creation fails."""
    pass


class CourseNotFoundError(ScheduleServiceError):
    """Raised when course is not found."""
    pass
