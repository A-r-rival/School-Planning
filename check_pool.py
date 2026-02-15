# -*- coding: utf-8 -*-
"""Debug SDBIOI pool and MBT323 details"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from models.schedule_model import ScheduleModel

def debug_check():
    m = ScheduleModel()
    
    # 1. MBT323
    print("--- MBT323 Details ---")
    m.c.execute("SELECT * FROM Dersler WHERE ders_kodu = 'MBT323'")
    row = m.c.fetchone()
    if row:
        print(f"  Name: {row[2]}, Hours: T={row[3]}, U={row[4]}, L={row[5]}, AKTS={row[6]}")
    else:
        print("  Not found!")

    # 2. SDBIOI vs SDBIOII Pools
    print("\n--- SDBIOI Pool Content ---")
    m.c.execute("SELECT ders_kodu, ders_adi FROM Ders_Havuz_Iliskisi WHERE havuz_kodu = 'SDBIOI'")
    rows = m.c.fetchall()
    if not rows:
        print("  EMPTY! No courses in SDBIOI.")
    else:
        for r in rows:
            print(f"  {r[0]} | {r[1]}")

    print("\n--- SDBIOII Pool Content ---")
    m.c.execute("SELECT ders_kodu, ders_adi FROM Ders_Havuz_Iliskisi WHERE havuz_kodu = 'SDBIOII'")
    rows = m.c.fetchall()
    for r in rows:
        print(f"  {r[0]} | {r[1]}")

    # 3. SDBIOI Container Course
    print("\n--- SDBIOI Container Course ---")
    m.c.execute("SELECT * FROM Dersler WHERE ders_kodu = 'SDBIOI'")
    row = m.c.fetchone()
    if row:
        print(f"  Name: {row[2]}, Hours: T={row[3]}, U={row[4]}, L={row[5]}, AKTS={row[6]}")
    else:
        print("  Not found!")

    m.close_connections()

if __name__ == "__main__":
    debug_check()
