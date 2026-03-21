import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'models/repositories'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'controllers'))
from database_setup import Model
from scheduler_services import CourseRepository

db = Model()
repo = CourseRepository(db)
rows = repo.fetch_course_rows()
print(f"Total rows fetched: {len(rows)}")
