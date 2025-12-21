import sys
import os
import sqlite3

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.schedule_model import ScheduleModel

def debug_sql_relationships():
    print("--- SQL Relationship Debug ---")
    model = ScheduleModel()
    
    # Check if Ders_Sinif_Iliskisi has any data
    model.c.execute("SELECT COUNT(*) FROM Ders_Sinif_Iliskisi")
    count_dsi = model.c.fetchone()[0]
    print(f"Total rows in Ders_Sinif_Iliskisi: {count_dsi}")
    
    # Check if Ogrenci_Donemleri has any data
    model.c.execute("SELECT COUNT(*) FROM Ogrenci_Donemleri")
    count_od = model.c.fetchone()[0]
    print(f"Total rows in Ogrenci_Donemleri: {count_od}")
    
    # Check if we can join them manually
    print("\nAttempting Join...")
    query = '''
    SELECT dsi.ders_adi, od.bolum_num, od.sinif_duzeyi 
    FROM Ders_Sinif_Iliskisi dsi
    JOIN Ogrenci_Donemleri od ON dsi.donem_sinif_num = od.donem_sinif_num
    LIMIT 5
    '''
    model.c.execute(query)
    rows = model.c.fetchall()
    print(f"Join Result (Limit 5): {len(rows)}")
    for r in rows:
        print(f"  - {r}")

    if not rows and count_dsi > 0 and count_od > 0:
        print("!! Join failed. Mismatch in 'donem_sinif_num' keys?")
        # Inspect keys
        model.c.execute("SELECT donem_sinif_num FROM Ders_Sinif_Iliskisi LIMIT 3")
        print(f"Keys in DSI: {model.c.fetchall()}")
        model.c.execute("SELECT donem_sinif_num FROM Ogrenci_Donemleri LIMIT 3")
        print(f"Keys in OD: {model.c.fetchall()}")

if __name__ == "__main__":
    debug_sql_relationships()
