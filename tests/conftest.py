# -*- coding: utf-8 -*-
"""
Test configuration for pytest.
Sets up in-memory SQLite database and common fixtures.
"""
import pytest
import sqlite3
from typing import Generator

from models.repositories.migration import DatabaseMigration
from models.repositories import TeacherRepository, CourseRepository, ScheduleRepository
from models.services import ScheduleService


@pytest.fixture
def db_conn() -> Generator[sqlite3.Connection, None, None]:
    """
    Create an in-memory SQLite database for testing.
    
    Yields:
        Fresh database connection with schema initialized
    """
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    
    # Run migrations to create schema
    migration = DatabaseMigration(conn)
    migration.run_all()
    
    yield conn
    
    conn.close()


@pytest.fixture
def teacher_repo(db_conn) -> TeacherRepository:
    """Create TeacherRepository instance."""
    cursor = db_conn.cursor()
    return TeacherRepository(cursor)


@pytest.fixture
def course_repo(db_conn) -> CourseRepository:
    """Create CourseRepository instance."""
    cursor = db_conn.cursor()
    return CourseRepository(cursor)


@pytest.fixture
def schedule_repo(db_conn) -> ScheduleRepository:
    """Create ScheduleRepository instance."""
    cursor = db_conn.cursor()
    return ScheduleRepository(cursor)


@pytest.fixture
def schedule_service(
    db_conn,
    teacher_repo,
    course_repo,
    schedule_repo
) -> ScheduleService:
    """
    Create ScheduleService instance with all dependencies.
    
    This is the main fixture for testing business logic.
    """
    return ScheduleService(
        conn=db_conn,
        teacher_repo=teacher_repo,
        course_repo=course_repo,
        schedule_repo=schedule_repo
    )
