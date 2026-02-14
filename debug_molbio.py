# -*- coding: utf-8 -*-
"""
Debug script for Molecular Biology department/courses using ScheduleModel, writing to file.
"""
import sys, os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.schedule_model import ScheduleModel

def debug_molbio():
    out = []
    out.append("--- Initializing ScheduleModel ---")
    m = ScheduleModel()
    
    try:
        out.append("--- Finding Department 'Moleküler Biyoloji' ---")
        m.c.execute("SELECT bolum_id, bolum_adi, bolum_num, fakulte_num FROM Bolumler WHERE bolum_adi LIKE '%Moleküler%' OR bolum_adi LIKE '%Biyoloji%'")
        depts = m.c.fetchall()
        
        dept_ids = []
        for d in depts:
            out.append(f"  ID: {d[0]}, Name: {d[1]}, Num: {d[2]}, FacultyNum: {d[3]}")
            dept_ids.append(d[0]) # bolum_id
            
        if not depts:
            out.append("  No matching department found.")
            return

        out.append("\n--- Finding Courses for these Departments ---")
        
        for dept_id in dept_ids:
            # Need to re-fetch dept name or store differently
            for d in depts:
                if d[0] == dept_id:
                    dept_name = d[1]
                    dept_num = d[2]
                    break
            
            out.append(f"\nCourses for {dept_name} (ID: {dept_id}, Num: {dept_num}):")
            
            # Use query for courses linked to this department
            m.c.execute("""
                SELECT d.ders_kodu, d.ders_adi, od.sinif_duzeyi, d.ders_instance
                FROM Dersler d
                JOIN Ders_Sinif_Iliskisi dsi ON d.ders_adi = dsi.ders_adi AND d.ders_instance = dsi.ders_instance
                JOIN Ogrenci_Donemleri od ON dsi.donem_sinif_num = od.donem_sinif_num
                WHERE od.bolum_num = ?
                ORDER BY od.sinif_duzeyi, d.ders_adi
            """, (dept_id,))
            courses = m.c.fetchall()
            
            course_list = []
            if not courses:
                out.append("  No curriculum courses found.")
            else:
                for c in courses:
                    out.append(f"  [{c[0]}] {c[1]} (Year {c[2]}, Inst {c[3]})")
                    course_list.append((c[1], c[3]))

                # Also check pool courses linked via Ders_Havuz_Iliskisi
                m.c.execute("""
                    SELECT d.ders_kodu, d.ders_adi, dhi.havuz_kodu, d.ders_instance   
                    FROM Dersler d
                    JOIN Ders_Havuz_Iliskisi dhi ON d.ders_adi = dhi.ders_adi AND d.ders_instance = dhi.ders_instance
                    WHERE dhi.bolum_id = ?
                """, (dept_num,)) # Note: bolum_num vs bolum_id confusion in schema usage, checking both might be safer but stick to bolum_num as ID usually
                # Wait, schema uses bolum_num or bolum_id? Checking migration:
                # usually bolum_id is the PK. Let's check bolum_id.
                pool_courses = m.c.fetchall()
                if pool_courses:
                    out.append("  -- Pool Courses --")
                    for p in pool_courses:
                        out.append(f"  [{p[0]}] {p[1]} (Pool {p[2]}, Inst {p[3]})")
                        course_list.append((p[1], p[3]))

                # Now check schedule for these
                out.append(f"\n  -- Scheduled Classes for {dept_name} --")
                
                if not course_list:
                    out.append("  No courses to check schedule for.")
                    continue

                # Prepare placeholders
                # We need to query by name AND instance strictly? Or just name?
                # Usually name + instance matters.
                # But let's check by name for now, easy match.
                unique_names = list(set([c[0] for c in course_list]))
                placeholders = ','.join(['?'] * len(unique_names))
                
                query_sched = f"""
                SELECT dp.gun, dp.baslangic, dp.bitis, dp.ders_adi, 
                       (SELECT ad || ' ' || soyad FROM Ogretmenler WHERE ogretmen_num = dp.ogretmen_id),
                       (SELECT derslik_adi FROM Derslikler WHERE derslik_num = dp.derslik_id),
                       dp.ders_instance
                FROM Ders_Programi dp
                WHERE dp.ders_adi IN ({placeholders})
                ORDER BY dp.ders_adi, dp.gun, dp.baslangic
                """
                m.c.execute(query_sched, unique_names)
                sched = m.c.fetchall()
                
                if not sched:
                    out.append("  No schedule entries found.")
                else:
                    for s in sched:
                        out.append(f"  {s[3]}: {s[0]} {s[1]}-{s[2]} | {s[4]} | {s[5]} (Inst {s[6]})")

    except Exception as e:
        out.append(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
         m.close_connections()

    with open("debug_molbio_output.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print("Done. Output written to debug_molbio_output.txt")

if __name__ == "__main__":
    debug_molbio()
