import sys
sys.path.append('d:/Git_Projects/School-Planning')
from models.schedule_model import ScheduleModel
from services.calendar_schedule_builder import CalendarScheduleBuilder

def check_db():
    model = ScheduleModel("database/okul_veritabani.db")
    depts = model.get_all_departments()
    dept_id = next(d[0] for d in depts if "Bilgisayar" in d[1])
    fac_id = next(f[0] for f in model.get_faculties() if "Mühendislik" in f[1])
            
    data = {
        "faculty_id": fac_id,
        "dept_id": dept_id,
        "year": 3,
        "semester": "Bahar"
    }
    
    builder = CalendarScheduleBuilder(model)
    result = builder.build(data)
    
    print("\n--- NON-ELECTIVE COURSES ---")
    schedule = result.get('schedule', [])
    count = 0
    for item in schedule:
        # For student group view, _post_process_student_view strips non-electives to 5-tuples.
        # But wait, if it's a 5-tuple, len(item) == 5.
        if len(item) == 5:
            print("MANDATORY (5-tuple):", item)
            count += 1
        elif len(item) > 8 and not item[5]: # is_elective is False
            print("MANDATORY (9-tuple):", item)
            count += 1
            
    print(f"Total mandatory courses in schedule data: {count}")

if __name__ == '__main__':
    check_db()
