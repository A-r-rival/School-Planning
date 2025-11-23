import sys
import os
from PyQt5.QtWidgets import QApplication

# Add project root to path
sys.path.append(os.getcwd())

from models.schedule_model import ScheduleModel

def verify():
    print("Starting Verification...")
    
    # Initialize Model (using a test db to avoid messing up real data if possible, 
    # but for now we use the real one as per user request to migrate)
    # We will use a temporary db for safety in this script
    test_db = "test_verification.db"
    if os.path.exists(test_db):
        os.remove(test_db)
        
    model = ScheduleModel(db_path=test_db)
    
    # Connect signals for debugging
    model.error_occurred.connect(lambda msg: print(f"⚠️ Error Signal: {msg}"))
    model.course_added.connect(lambda msg: print(f"ℹ️ Added Signal: {msg}"))
    
    # Test 1: Add Course
    print("\nTest 1: Adding Course...")
    course_data = {
        'ders': 'Advanced Python',
        'hoca': 'Guido van Rossum',
        'gun': 'Pazartesi',
        'baslangic': '10:00',
        'bitis': '12:00'
    }
    
    success = model.add_course_complex(course_data)
    if success:
        print("✅ Course added successfully")
    else:
        print("❌ Failed to add course")
        return

    # Test 2: Get Courses
    print("\nTest 2: Listing Courses...")
    courses = model.get_all_courses_complex()
    print(f"Courses found: {courses}")
    
    expected_str = "Advanced Python - Guido van Rossum - Pazartesi 10:00-12:00"
    if expected_str in courses:
        print("✅ Course listed correctly")
    else:
        print(f"❌ Course not found in list. Expected: {expected_str}")
        return

    # Test 3: Remove Course
    print("\nTest 3: Removing Course...")
    success = model.remove_course_complex(expected_str)
    if success:
        print("✅ Course removed successfully")
    else:
        print("❌ Failed to remove course")
        return

    # Verify removal
    courses_after = model.get_all_courses_complex()
    if len(courses_after) == 0:
        print("✅ Course list empty after removal")
    else:
        print(f"❌ Course list not empty: {courses_after}")

    # Cleanup
    model.close_connections()
    if os.path.exists(test_db):
        os.remove(test_db)
    
    print("\n✨ Verification Complete!")

if __name__ == "__main__":
    # QApplication is needed for signals to work, even if we don't show UI
    app = QApplication(sys.argv)
    verify()
