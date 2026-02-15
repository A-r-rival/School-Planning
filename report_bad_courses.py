# -*- coding: utf-8 -*-
"""Report courses with NULL or 0 hours (unschedulable) writing to file"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from models.schedule_model import ScheduleModel

def report_unschedulable():
    m = ScheduleModel()
    out = ["--- Courses with invalid hours (NULL or 0) ---"]
    
    # Check NULL or 0 T+U+L
    m.c.execute("""
        SELECT ders_kodu, ders_adi, teori_saati, uygulama_saati, lab_saati 
        FROM Dersler 
        WHERE (teori_saati IS NULL AND uygulama_saati IS NULL AND lab_saati IS NULL)
           OR (COALESCE(teori_saati,0) + COALESCE(uygulama_saati,0) + COALESCE(lab_saati,0) = 0)
        ORDER BY ders_kodu
    """)
    rows = m.c.fetchall()
    
    if not rows:
        out.append("No invalid courses found.")
    else:
        out.append(f"Found {len(rows)} unschedulable courses:")
        for r in rows:
            t = r[2] if r[2] is not None else "NULL"
            u = r[3] if r[3] is not None else "NULL"
            l = r[4] if r[4] is not None else "NULL"
            out.append(f"  [{r[0]}] {r[1]}: T={t}, U={u}, L={l}")
            
    m.close_connections()
    with open("unschedulable_courses.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print("Output written to unschedulable_courses.txt")

if __name__ == "__main__":
    report_unschedulable()
