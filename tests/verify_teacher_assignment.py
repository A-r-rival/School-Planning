import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.schedule_model import ScheduleModel
from PyQt5.QtWidgets import QApplication

def verify_backend():
    # Helper to clean up test data
    def cleanup(model):
        model.c.execute("DELETE FROM Dersler WHERE ders_adi = 'Test Course 101'")
        model.c.execute("DELETE FROM Ders_Ogretmen_Iliskisi WHERE ders_adi = 'Test Course 101'")
        model.conn.commit()

    try:
        test_db = "test_verification.db"
        if os.path.exists(test_db):
            os.remove(test_db)
            
        app = QApplication(sys.argv)
        model = ScheduleModel(db_path=test_db)
        # model._init_db() # Called in __init__
        
        # Capture errors
        def on_error(msg):
             print(f"   [ERROR SIGNAL CAUGHT]: {msg}")
        model.error_occurred.connect(on_error)
        model.course_added.connect(lambda msg: print(f"   [SUCCESS SIGNAL]: {msg}"))

        print("1. Cleaning up previous test data...")
        cleanup(model)
        
        print("2. Testing add_curriculum_course_as_template...")
        
        # Seed Data if missing
        model.c.execute("SELECT COUNT(*) FROM Bolumler")
        if model.c.fetchone()[0] == 0:
            print("   -> Seeding dummy department (Computers)")
            model.c.execute("INSERT INTO Fakulteler (fakulte_adi) VALUES ('Engineering')")
            fac_id = model.c.lastrowid
            model.c.execute("INSERT INTO Bolumler (bolum_num, bolum_adi, fakulte_num) VALUES (101, 'Computer Engineering', ?)", (fac_id,))
            model.conn.commit()
            
        model.c.execute("SELECT COUNT(*) FROM Ogretmenler")
        if model.c.fetchone()[0] == 0:
            print("   -> Seeding dummy teacher (John Doe)")
            model.c.execute("INSERT INTO Ogretmenler (ad, soyad, bolum_adi) VALUES ('John', 'Doe', 'Computer Engineering')")
            model.conn.commit()

        # Need a valid department ID. Let's get one.
        model.c.execute("SELECT bolum_num FROM Bolumler LIMIT 1")
        row = model.c.fetchone()
        dept_id = row[0]
        
        data = {
            'code': 'TST101',
            'name': 'Test Course 101',
            'dept_id': dept_id,
            'year': 1,
            't': 2, 'u': 0, 'l': 0, 'akts': 3
        }
        
        # This might fail if Ogrenci_Donemleri is empty for that dept/year, so let's check
        model.c.execute("SELECT * FROM Ogrenci_Donemleri WHERE bolum_num = ? AND sinif_duzeyi = ?", (dept_id, 1))
        if not model.c.fetchone():
             # Insert dummy period for test
             model.c.execute("INSERT INTO Ogrenci_Donemleri (bolum_num, sinif_duzeyi, donem_sinif_num) VALUES (?, ?, ?)", (dept_id, 1, 9999))
             model.conn.commit()

        success = model.add_curriculum_course_as_template(data)
        if success:
            print("   -> Success: Course added.")
        else:
            print("   -> Failed: Could not add course.")
            return

        print("3. Testing assign_teacher_to_course...")
        # Get a teacher
        model.c.execute("SELECT ogretmen_num FROM Ogretmenler LIMIT 1")
        t_row = model.c.fetchone()
        if t_row:
            t_id = t_row[0]
            success = model.assign_teacher_to_course(t_id, 'Test Course 101', 1)
            if success:
                print(f"   -> Success: Assigned teacher {t_id} to Test Course 101 (Instance 1)")
                
                # Verify persistence
                courses = model.get_courses_assigned_to_teacher(t_id)
                found = False
                for name, instance in courses:
                    if name == 'Test Course 101' and instance == 1:
                        found = True
                        break
                
                if found:
                    print("   -> Verification: Assignment found in DB.")
                else:
                    print("   -> Verification FAILED: Assignment not found in DB.")

        print("4. Cleanup...")
        cleanup(model)
        print("Done.")
        
    except Exception as e:
        print(f"CRASH: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_backend()
