from models.schedule_model import ScheduleModel

def debug_teachers():
    try:
        import models.schedule_model
        print(f"Module file: {models.schedule_model.__file__}")
        model = ScheduleModel()
        teachers = model.get_all_teachers_with_ids()
        print(f"Total teachers: {len(teachers)}")
        if teachers:
            first_teacher = teachers[0]
            print(f"First teacher: {first_teacher}")
            print(f"Type: {type(first_teacher)}")
            print(f"Length: {len(first_teacher)}")
            
            for i, t in enumerate(teachers):
                if len(t) != 2:
                    print(f"Row {i} has unexpected length {len(t)}: {t}")
                    break
        else:
            print("No teachers found.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_teachers()
