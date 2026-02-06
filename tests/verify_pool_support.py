import sys
import os
from PyQt5.QtWidgets import QApplication

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.schedule_model import ScheduleModel

def verify_pool():
    test_db = "test_verification.db"
    
    # Clean previous run
    if os.path.exists(test_db):
        os.remove(test_db)
        
    app = QApplication(sys.argv)
    model = ScheduleModel(db_path=test_db)
    
    print("1. Seeding Data...")
    # Seed Data
    model.c.execute("INSERT INTO Fakulteler (fakulte_adi) VALUES ('Engineering')")
    fac_id = model.c.lastrowid
    model.c.execute("INSERT INTO Bolumler (bolum_num, bolum_adi, fakulte_num) VALUES (101, 'Computer Engineering', ?)", (fac_id,))
    model.conn.commit()
    
    print("2. Testing Add Pool Course...")
    data = {
        'code': 'POOL101',
        'name': 'Introduction to Pool',
        'dept_id': 101,
        'year': 0, # Ignored for pool
        't': 2, 'u': 0, 'l': 0, 'akts': 2,
        'is_pool': True,
        'pool_code': 'TEST_POOL'
    }
    
    success = model.add_curriculum_course_as_template(data)
    
    if success:
        print("   [SUCCESS] Pool course added via model.")
    else:
        print("   [FAIL] Model returned False.")
        return

    print("3. Verifying DB Insertion...")
    model.c.execute("SELECT * FROM Ders_Havuz_Iliskisi WHERE havuz_kodu = 'TEST_POOL'")
    row = model.c.fetchone()
    if row:
        print(f"   [PASS] Found in Ders_Havuz_Iliskisi: {row}")
    else:
        print("   [FAIL] Not found in Ders_Havuz_Iliskisi table!")
        
    model.c.execute("SELECT * FROM Dersler WHERE ders_kodu = 'POOL101'")
    if model.c.fetchone():
        print("   [PASS] Found in Dersler table.")
        
    print("Done.")

if __name__ == "__main__":
    verify_pool()
