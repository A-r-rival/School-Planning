# -*- coding: utf-8 -*-
"""Verify fixed DB data for MBT323 and SDBIOI"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from models.schedule_model import ScheduleModel

def verify():
    print("--- Verifying Database Fix ---")
    m = ScheduleModel()
    
    # Check MBT323
    print("Checking MBT323...")
    m.c.execute("SELECT ders_kodu, ders_adi, teori_saati, uygulama_saati, lab_saati, akts, ders_instance FROM Dersler WHERE ders_kodu='MBT323'")
    rows = m.c.fetchall()
    if not rows:
        print("FAIL: MBT323 not found in DB!")
    else:
        for r in rows:
            print(f"  Found: {r}")
            # Expected: T=2, U=1, L=2
            if r[2]==2 and r[3]==1 and r[4]==2:
                print("  SUCCESS: MBT323 hours are correct (2+1+2).")
            else:
                print(f"  FAILURE: MBT323 hours mismatch! Got T={r[2]}, U={r[3]}, L={r[4]}")

    # Check SDBIOI
    print("\nChecking SDBIOI...")
    m.c.execute("SELECT ders_kodu, ders_adi, teori_saati, uygulama_saati, lab_saati, akts FROM Dersler WHERE ders_kodu='SDBIOI'")
    rows_sd = m.c.fetchall()
    if not rows_sd:
        print("FAIL: SDBIOI not found in DB!")  # Might happen if parsing logic skipped it?
    else:
         for r in rows_sd:
             print(f"  Found: {r}")
             # Expected: T=0, U=0, L=0, AKTS=18
             if r[2]==0 and r[3]==0 and r[4]==0 and r[5]==18:
                 print("  SUCCESS: SDBIOI is present as placeholder (0 hours, 18 AKTS).")
             else:
                 print(f"  NOTE: SDBIOI values: T={r[2]}, U={r[3]}, L={r[4]}, AKTS={r[5]}")

    # Check SDBIOI Pool Content
    print("\nChecking SDBIOI Pool Content (Ders_Havuz_Iliskisi)...")
    m.c.execute("SELECT ders_instance, ders_adi FROM Ders_Havuz_Iliskisi WHERE havuz_kodu='SDBIOI'")
    pool_rows = m.c.fetchall()
    if not pool_rows:
        print("  EMPTY: No courses linked to SDBIOI pool (Expected if source file lacks definition).")
    else:
        print(f"  FOUND {len(pool_rows)} courses in SDBIOI pool:")
        for pr in pool_rows:
            print(f"    {pr}")

    m.close_connections()

if __name__ == "__main__":
    verify()
