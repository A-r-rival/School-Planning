import sqlite3
import os

def inspect_db():
    db_path = r'd:\Git_Projects\School-Planning\database\okul_veritabani.db'
    if not os.path.exists(db_path):
        print(f"DB not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Find the department
    print("--- Departments containing 'Enerji' ---")
    try:
        cursor.execute("SELECT * FROM Bolumler WHERE bolum_adi LIKE '%Enerji%'")
        depts = cursor.fetchall()
        
        if not depts:
             print("No 'Enerji' department found using 'bolum_adi'. Trying 'name' column just in case schema differs.")
             # Fallback to verify schema
             cursor.execute("PRAGMA table_info(Bolumler)")
             cols = [c[1] for c in cursor.fetchall()]
             print(f"Bolumler columns: {cols}")
             return

        for d in depts:
            print(f"Dept: {d}")
            dept_id = d[0] # Assuming id is first
            
            # 2. List courses for this dept (Year 3 & 4)
            print(f"   --- Courses for Dept ID {dept_id} (Year 3 & 4) ---")
            
            # Check Ders_Sinif_Iliskisi schema
            # cursor.execute("PRAGMA table_info(Ders_Sinif_Iliskisi)")
            # print(f"Ders_Sinif_Iliskisi columns: {[c[1] for c in cursor.fetchall()]}")

            # Note: models/schedule_model.py uses 'bolum_num' in Ogrenci_Donemleri to link.
            # Query from model:
            # JOIN Ders_Sinif_Iliskisi dsi ... JOIN Ogrenci_Donemleri od ON dsi.donem_sinif_num = od.donem_sinif_num
            # WHERE od.bolum_num = ?
            
            query = """
            SELECT d.ders_kodu, d.ders_adi, od.sinif_duzeyi
            FROM Dersler d
            JOIN Ders_Sinif_Iliskisi dsi ON d.ders_adi = dsi.ders_adi AND d.ders_instance = dsi.ders_instance
            JOIN Ogrenci_Donemleri od ON dsi.donem_sinif_num = od.donem_sinif_num
            WHERE od.bolum_num = ? AND od.sinif_duzeyi IN (3, 4)
            ORDER BY od.sinif_duzeyi, d.ders_adi
            """
            cursor.execute(query, (dept_id,))
            courses = cursor.fetchall()
            
            for code, name, sinif in courses:
                print(f"      [Year {sinif}] {code} - {name}")
                
                # Check for pool/elective status
                # 3. Check Ders_Havuz_Iliskisi
                cursor.execute("SELECT * FROM Ders_Havuz_Iliskisi WHERE ders_adi = ?", (name,))
                pool_data = cursor.fetchall()
                if pool_data:
                    print(f"          -> IN POOL TABLE: {pool_data}")
                
                # Check name/code patterns
                is_elective_detected = False
                if "seçmeli" in name.lower() or "sdi" in (code or "").lower() or "gsd" in (code or "").lower():
                    is_elective_detected = True
                print(f"          -> Pattern Check: {is_elective_detected}")

    except Exception as e:
        print(f"Error: {e}")

    conn.close()

if __name__ == "__main__":
    inspect_db()
