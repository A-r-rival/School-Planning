import sqlite3
import os
import sys
import io

# Force UTF-8 for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def check_eng201():
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "database", "okul_veritabani.db")
    print(f"Checking DB at: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n--- Finding Name for Code ENG201 ---")
    cursor.execute("SELECT ders_adi, ders_instance FROM Dersler WHERE ders_kodu LIKE '%ENG201%'")
    rows = cursor.fetchall()
    
    course_instances = {}
    for r in rows:
        print(f"Found in Dersler: Name='{r[0]}', Instance={r[1]}")
        course_instances[r[0]] = r[1]
        
    for name, instance in course_instances.items():
        print(f"\n--- Checking assignments for '{name}' (Expected Instance: {instance}) ---")
        cursor.execute("SELECT ders_adi, ders_instance, donem_sinif_num FROM Ders_Sinif_Iliskisi WHERE ders_adi = ?", (name,))
        rels = cursor.fetchall()
        if not rels:
             print("  NO ROWS in Ders_Sinif_Iliskisi matching name!")
             
        for rel in rels:
            rl_name = rel[0]
            rl_inst = rel[1]
            ds_num = rel[2]
            
            match_status = "MATCH" if rl_inst == instance else "MISMATCH"
            print(f"  Row: Inst={rl_inst}, Group={ds_num} [{match_status}]")
            
            if match_status == "MISMATCH":
                print(f"    CRITICAL: Join fails for this group! {instance} != {rl_inst}")

            # Check details of this group
            cursor.execute("SELECT * FROM Ogrenci_Donemleri WHERE donem_sinif_num = ?", (ds_num,))
            group_info = cursor.fetchone()
            if group_info:
                # Group info: (donem_sinif_num, baslangic_yili, bolum_num, sinif_duzeyi)
                dept_id = group_info[2]
                class_year = group_info[3]
                
                cursor.execute("SELECT bolum_adi FROM Bolumler WHERE bolum_id = ?", (dept_id,))
                dept_row = cursor.fetchone()
                dept_name = dept_row[0] if dept_row else "UNKNOWN"
                
                print(f"     -> {dept_name} (Year {class_year})")
        else:
            print("  -> Group NOT FOUND in Ogrenci_Donemleri!")

if __name__ == "__main__":
    check_eng201()
