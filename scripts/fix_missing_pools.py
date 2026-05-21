import sqlite3
import sys
import os

sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "database"))

from database import curriculum_data
from models.schedule_model import ScheduleModel
import re

def fix_pools():
    print("Fixing missing pool relationships in Ders_Havuz_Iliskisi...")
    model = ScheduleModel()
    
    # Preload bolum_ids
    model.c.execute("SELECT bolum_id, bolum_adi FROM Bolumler")
    bolum_map = {row[1]: row[0] for row in model.c.fetchall()}
    
    pool_count = 0
    for dept_name, dept_data in curriculum_data.DEPARTMENTS_DATA.items():
        bolum_id = None
        for k, v in bolum_map.items():
            if k.strip() == dept_name.strip():
                bolum_id = v
                break
                
        if not bolum_id:
            continue
            
        pools = dept_data.get("pools", {})
        pool_codes_def = dept_data.get("pool_codes", {})
        curriculum = dept_data.get("curriculum", {})
        
        pool_year_map = {}
        for semester_key, semester_courses in curriculum.items():
            year_match = re.search(r'(\d+)\.\s*Y[ıi]l', semester_key)
            if not year_match:
                continue
            sinif_duzeyi = int(year_match.group(1))
            
            if isinstance(semester_courses, list):
                for course_entry in semester_courses:
                    if isinstance(course_entry, list) and len(course_entry) >= 2:
                        course_code = course_entry[0]
                        if course_code in pool_codes_def or course_code in pools:
                            if course_code not in pool_year_map:
                                pool_year_map[course_code] = set()
                            pool_year_map[course_code].add(sinif_duzeyi)

        for pool_code, courses in pools.items():
            sinif_duzeyleri = pool_year_map.get(pool_code, {0})
            for course_data in courses:
                if len(course_data) >= 2:
                    code = course_data[0]
                    name = course_data[1]
                    
                    # Find instance by code first, fallback to name
                    model.c.execute("SELECT ders_instance, ders_adi FROM Dersler WHERE ders_kodu = ?", (code,))
                    rows = model.c.fetchall()
                    if not rows:
                        model.c.execute("SELECT ders_instance, ders_adi FROM Dersler WHERE ders_adi = ?", (name,))
                        rows = model.c.fetchall()
                        
                    if rows:
                        for row in rows:
                            instance = row[0]
                            db_name = row[1]
                            # If a pool spans multiple years, use 0 (wildcard) to avoid UNIQUE constraint violation
                            final_s_duzeyi = list(sinif_duzeyleri)[0] if len(sinif_duzeyleri) == 1 else 0
                            
                            try:
                                model.c.execute("""
                                    INSERT OR IGNORE INTO Ders_Havuz_Iliskisi (ders_instance, ders_adi, bolum_id, havuz_kodu, sinif_duzeyi)
                                    VALUES (?, ?, ?, ?, ?)
                                """, (instance, db_name, bolum_id, pool_code, final_s_duzeyi))
                                if model.c.rowcount > 0:
                                    pool_count += 1
                                elif len(sinif_duzeyleri) > 1:
                                    # Update existing to 0 if it was already inserted with a specific year
                                    model.c.execute("""
                                        UPDATE Ders_Havuz_Iliskisi SET sinif_duzeyi = 0
                                        WHERE ders_instance = ? AND ders_adi = ? AND bolum_id = ? AND havuz_kodu = ?
                                    """, (instance, db_name, bolum_id, pool_code))
                            except sqlite3.Error as e:
                                    pass
    
    model.conn.commit()
    print(f"✅ Added {pool_count} missing pool relationships.")
    model.conn.close()

if __name__ == "__main__":
    fix_pools()
