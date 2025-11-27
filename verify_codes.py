import sqlite3
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from models.schedule_model import ScheduleModel

def verify():
    print("Verifying Course Codes...")
    model = ScheduleModel()
    
    # Check for specific codes
    codes_to_check = ["ETE101", "PHY101", "ETE201", "SDII"]
    
    for code in codes_to_check:
        model.c.execute("SELECT count(*) FROM Ogrenci_Notlari WHERE ders_kodu = ?", (code,))
        count = model.c.fetchone()[0]
        print(f"Code {code}: Found {count} entries")
        
    # Sample some rows
    print("\nSample Rows:")
    model.c.execute("SELECT ogrenci_num, ders_kodu, ders_adi FROM Ogrenci_Notlari LIMIT 5")
    rows = model.c.fetchall()
    for row in rows:
        print(row)

if __name__ == "__main__":
    verify()
