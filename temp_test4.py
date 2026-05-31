import sys
import sqlite3
import os

sys.path.append(os.path.abspath('database'))
sys.path.append(os.path.abspath('controllers'))
sys.path.append(os.path.abspath('.'))

from models.schedule_model import ScheduleModel
from controllers.scheduler_services import SchedulerCourseRepository, CourseMerger, CurriculumResolver

model = ScheduleModel()
repo = SchedulerCourseRepository(model)
raw_rows = repo.fetch_course_rows()

merger = CourseMerger()
resolver = CurriculumResolver()

merged = merger.merge(raw_rows, resolver)
for m in merged:
    if 'Türkçe 2' in m.name or 'Özdevinirler' in m.name:
        print(f"{m.name} -> group_ids={m.group_ids}, contexts={m.contexts}")

