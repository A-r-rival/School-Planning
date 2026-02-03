import sys
import os
from PyQt5.QtWidgets import QApplication

# Add project root to path (go up one level from subfolder)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.append(project_root)

try:
    from views.schedule_view import ScheduleView
    app = QApplication(sys.argv)
    view = ScheduleView()
    print("Successfully instantiated ScheduleView")
except Exception as e:
    print(f"Error instantiating ScheduleView: {e}")
