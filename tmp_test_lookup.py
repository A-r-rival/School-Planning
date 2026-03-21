import sys
import os

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from models.schedule_model import ScheduleModel

model = ScheduleModel("database/okul_veritabani.db")

print("Global MAT108 map:", model.semester_lookup.get("MAT108"))
print("Makine Müh MAT108 map:", model.semester_lookup_by_dept.get(("Makine Müh", "MAT108")))
print("Bilgisayar Müh MAT108 map:", model.semester_lookup_by_dept.get(("Bilgisayar Müh", "MAT108")))
print("İnşaat Müh MAT108 map:", model.semester_lookup_by_dept.get(("İnşaat Müh", "MAT108")))
