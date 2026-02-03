import sqlite3
import pandas as pd

DB_PATH = "okul_veritabani.db"

def check_assignments():
    conn = sqlite3.connect(DB_PATH)
    
    # 1. Fetch Assignments with joined details
    query = """
    SELECT 
        dp.ders_adi, 
        dp.ders_tipi as CourseType,
        d.derslik_adi as AssignedRoom, 
        d.derslik_tipi as RoomType,
        t.teori_odasi as FixedTheoryRoom,
        t.lab_odasi as FixedLabRoom
    FROM Ders_Programi dp
    JOIN Derslikler d ON dp.derslik_id = d.derslik_num
    LEFT JOIN Dersler t ON dp.ders_adi = t.ders_adi AND dp.ders_instance = t.ders_instance
    """
    
    try:
        df = pd.read_sql_query(query, conn)
        
        print("\n--- VIOLATION REPORT ---")
        violations = 0
        
        for idx, row in df.iterrows():
            c_type = (row['CourseType'] or "").lower()
            r_type = (row['RoomType'] or "").lower()
            
            is_lab_course = "lab" in c_type
            is_lab_room = "lab" in r_type or "laboratuvar" in r_type
            is_amfi_room = "amfi" in r_type
            
            violation = None
            
            # Rule 1: Lab Course must be in Lab Room
            if is_lab_course and not is_lab_room:
                 violation = "Lab Course in Non-Lab Room"
            
            # Rule 2: Lab Course must NOT be in Amfi
            if is_lab_course and is_amfi_room:
                 violation = "Lab Course in Amfi"
                 
            # Rule 3: Theory in Lab
            if not is_lab_course and is_lab_room:
                 violation = "Theory Course in Lab Room"
                 
            if violation:
                violations += 1
                print(f"FAIL: {row['ders_adi']} ({row['CourseType']}) -> {row['AssignedRoom']} ({row['RoomType']})")
                print(f"      Reason: {violation}")
                print(f"      Fixed Overrides - T: {row['FixedTheoryRoom']}, L: {row['FixedLabRoom']}")
                print("-" * 50)
            else:
                 # Success Case Dump (Limit to first 50 to avoid spam, or filter for specific rooms)
                 if "lab" in c_type or "derslik-1" in (row['AssignedRoom'] or "").lower():
                     print(f"OK:   {row['ders_adi']} ({row['CourseType']}) -> {row['AssignedRoom']} ({row['RoomType']})")
                
        if violations == 0:
            print("SUCCESS: No room type violations detected by script logic.")
        else:
            print(f"\nFound {violations} violations.")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_assignments()
