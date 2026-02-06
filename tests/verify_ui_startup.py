import sys
import os
from PyQt5.QtWidgets import QApplication

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from views.teacher_availability_view import TeacherAvailabilityView, AddUnavailabilityDialog
from views.schedule_view import ScheduleView

def verify_ui():
    app = QApplication(sys.argv)
    
    print("1. Testing TeacherAvailabilityView instantiation...")
    try:
        # Mock teachers list
        teachers = [(1, "Test Teacher")]
        view = TeacherAvailabilityView(teachers=teachers)
        
        # Check for attributes that caused crashes
        if not hasattr(view, 'course_combo'):
            print("   [FAIL] course_combo attribute missing!")
        elif not hasattr(view, 'tab_assignments'):
            print("   [FAIL] tab_assignments attribute missing!")
        else:
            print("   [PASS] TeacherAvailabilityView instantiated with required attributes.")
            
    except Exception as e:
        print(f"   [CRASH] TeacherAvailabilityView failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n2. Testing ScheduleView instantiation...")
    try:
        # ScheduleView might need a controller or model, but let's try basic init
        # It usually takes a controller in set_controller, so init might be safe
        view = ScheduleView()
        print("   [PASS] ScheduleView instantiated.")
    except Exception as e:
        print(f"   [CRASH] ScheduleView failed: {e}")
        import traceback
        traceback.print_exc()

    print("\nDone.")

if __name__ == "__main__":
    verify_ui()
