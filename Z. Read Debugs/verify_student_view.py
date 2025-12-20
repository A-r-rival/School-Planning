import sys
import os
from PyQt5.QtWidgets import QApplication

# Add project root to path
sys.path.append(os.getcwd())

from models.schedule_model import ScheduleModel
from views.student_view import StudentView

def verify():
    print("Verifying Student Interface Logic...")
    model = ScheduleModel()
    
    # 1. Test get_students
    print("\nTesting get_students...")
    # Test 1: All students
    all_students = model.get_students()
    print(f"Total Students: {len(all_students)}")
    
    # Test 2: Filter by Department (e.g., Bilgisayar Mühendisliği)
    # First find dept ID
    depts = model.get_all_departments()
    comp_eng = next((d for d in depts if "Bilgisayar" in d[1]), None)
    
    if comp_eng:
        print(f"Filtering by {comp_eng[1]} (ID: {comp_eng[0]})...")
        comp_students = model.get_students({'bolum_id': comp_eng[0]})
        print(f"Computer Eng. Students: {len(comp_students)}")
        
        # Test 3: Filter by Year (e.g., 3rd Year)
        year3_students = model.get_students({'bolum_id': comp_eng[0], 'sinif': 3})
        print(f"Year 3 Computer Eng. Students: {len(year3_students)}")
        
        if year3_students:
            sample = year3_students[0]
            print(f"Sample Student: {sample[1]} {sample[2]} ({sample[0]})")
            
            # Test 4: Get Grades
            print("\nTesting get_student_grades...")
            grades = model.get_student_grades(sample[0], show_history=True)
            print(f"Grades found: {len(grades)}")
    else:
        print("Computer Engineering department not found for testing.")

    # 2. Test View Instantiation
    print("\nTesting StudentView Instantiation...")
    try:
        app = QApplication(sys.argv)
        view = StudentView()
        view.set_filter_options(model.get_all_faculties(), model.get_all_departments())
        print("StudentView instantiated successfully.")
    except Exception as e:
        print(f"ERROR instantiating StudentView: {e}")
        import traceback
        traceback.print_exc()
    
    print("\nVerification Complete.")

if __name__ == "__main__":
    verify()
