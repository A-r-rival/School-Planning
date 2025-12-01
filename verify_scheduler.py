import os
import sys
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from models.schedule_model import ScheduleModel
from controllers.scheduler import ORToolsScheduler

def test_scheduler():
    print("Testing Scheduler Integration...")
    
    # Use a test database
    test_db = "test_scheduler.db"
    if os.path.exists(test_db):
        os.remove(test_db)
        
    model = ScheduleModel(test_db)
    
    # 1. Setup Data
    print("Setting up test data...")
    
    # Add Faculty & Dept
    fac_id = model.add_faculty("Engineering")
    dept_id = model.add_department(fac_id, "Computer Science")
    
    # Add Teacher
    model.c.execute("INSERT INTO Ogretmenler (ad, soyad, bolum_adi) VALUES (?, ?, ?)", ("John", "Doe", "CS"))
    teacher_id = model.c.lastrowid
    
    # Add Room
    model.derslik_ekle("Room 101", "amfi", 50)
    
    # Add Course (Manual insert to link teacher/dept)
    # Course 1: CS101 (Teacher: John Doe)
    model.c.execute("INSERT INTO Dersler (ders_kodu, ders_adi, ders_instance, teori_odasi) VALUES (?, ?, ?, ?)", 
                    ("CS101", "Intro to CS", 1, None))
    
    # Link Teacher
    model.c.execute("INSERT INTO Ders_Ogretmen_Iliskisi (ders_adi, ders_instance, ogretmen_id) VALUES (?, ?, ?)",
                    ("Intro to CS", 1, teacher_id))
                    
    model.conn.commit()
    
    # 2. Add Unavailability
    # John Doe is unavailable Monday 09:00-12:00
    print("Adding unavailability: Monday 09:00-12:00")
    model.add_teacher_unavailability(teacher_id, "Pazartesi", "09:00", "12:00")
    
    # 3. Run Scheduler
    print("Running Scheduler...")
    scheduler = ORToolsScheduler(model)
    success = scheduler.solve()
    
    if not success:
        print("Scheduler failed to find a solution!")
        return
        
    # 4. Verify Result
    print("Verifying result...")
    model.c.execute("SELECT gun, baslangic, bitis FROM Ders_Programi WHERE ders_adi = 'Intro to CS'")
    row = model.c.fetchone()
    
    if row:
        day, start, end = row
        print(f"Scheduled: {day} {start}-{end}")
        
        # Check conflict
        if day == "Pazartesi" and start < "12:00" and end > "09:00":
            print("FAIL: Course scheduled during unavailability!")
        else:
            print("PASS: Course scheduled correctly.")
    else:
        print("FAIL: Course not scheduled!")
        
    model.close_connections()
    
    # Clean up
    if os.path.exists(test_db):
        try:
            os.remove(test_db)
        except:
            pass

if __name__ == "__main__":
    test_scheduler()
