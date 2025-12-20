
import sys
import os

# Import ORTools first to avoid conflict (just in case main.py logic applies here too)
try:
    from ortools.sat.python import cp_model
except ImportError:
    pass

from PyQt5.QtWidgets import QApplication
from views.schedule_view import ScheduleView

def main():
    app = QApplication(sys.argv)
    view = ScheduleView()
    
    # Add a dummy item
    dummy_course = "Test Item"
    view.ders_listesi.addItem(dummy_course)
    
    print("Attempting to remove course...")
    try:
        view.remove_course_from_list(dummy_course)
        print("Successfully removed course without crash.")
    except Exception as e:
        print(f"Failed to remove course: {e}")
        sys.exit(1)
        
    sys.exit(0)

if __name__ == "__main__":
    main()
