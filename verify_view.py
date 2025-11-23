import sys
import os
from PyQt5.QtWidgets import QApplication

# Add project root to path
sys.path.append(os.getcwd())

try:
    from views.schedule_view import ScheduleView
    app = QApplication(sys.argv)
    view = ScheduleView()
    print("Successfully instantiated ScheduleView")
except Exception as e:
    print(f"Error instantiating ScheduleView: {e}")
