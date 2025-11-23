import sys
import os
from PyQt5.QtWidgets import QApplication

sys.path.append(os.getcwd())

from models.schedule_model import ScheduleModel
from views.calendar_view import CalendarView

def verify():
    print("Starting Calendar Verification...")
    app = QApplication(sys.argv)
    
    # 1. Test Model Logic
    model = ScheduleModel()
    
    # Add a test course to ensure we have data
    print("Adding test data...")
    model.add_course({
        'ders': 'Calendar Test 101',
        'hoca': 'Test Teacher',
        'gun': 'Pazartesi',
        'baslangic': '10:00',
        'bitis': '12:00'
    })
    
    # Get Teacher ID
    teachers = model.get_all_teachers_with_ids()
    teacher_id = next((id for id, name in teachers if "Test Teacher" in name), None)
    
    if teacher_id:
        print(f"✅ Found Teacher ID: {teacher_id}")
        
        # Test Fetch
        schedule = model.get_schedule_by_teacher(teacher_id)
        print(f"Schedule found: {schedule}")
        
        if len(schedule) > 0 and schedule[0][3] == 'Calendar Test 101':
            print("✅ get_schedule_by_teacher working")
        else:
            print("❌ get_schedule_by_teacher failed")
    else:
        print("❌ Could not find test teacher")

    # 2. Test View Instantiation
    try:
        view = CalendarView()
        view.show()
        print("✅ CalendarView instantiated successfully")
        view.close()
    except Exception as e:
        print(f"❌ CalendarView instantiation failed: {e}")

    # Cleanup
    model.remove_course("Calendar Test 101 - Test Teacher - Pazartesi 10:00-12:00")
    model.close_connections()
    print("\n✨ Verification Complete!")

if __name__ == "__main__":
    verify()
