import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

try:
    from controllers.schedule_controller import ScheduleController
    print("Successfully imported ScheduleController")
except Exception as e:
    print(f"Error importing ScheduleController: {e}")
