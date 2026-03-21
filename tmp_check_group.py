import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from models.schedule_model import ScheduleModel

def check_group():
    db = ScheduleModel()
    
    # First find the group ID
    db.c.execute("""
        SELECT od.bolum_num, od.sinif_duzeyi, od.donem_sinif_num, b.bolum_adi
        FROM Ogrenci_Donemleri od
        JOIN Bolumler b ON od.bolum_num = b.bolum_id
        WHERE b.bolum_adi LIKE '%Mekatronik%' AND od.sinif_duzeyi = 1
    """)
    group = db.c.fetchone()
    if not group:
         print("Group not found")
         return
         
    bolum_num, sinif, group_id, bolum_adi = group
    print(f"Group: {bolum_adi} Year {sinif} (ID: {group_id})")
    
    # Now get all courses for this group
    db.c.execute("""
        SELECT d.ders_adi, d.teori_saati, d.uygulama_saati, d.lab_saati, d.ders_instance
        FROM Dersler d
        JOIN Ders_Sinif_Iliskisi dsi ON d.ders_instance = dsi.ders_instance AND d.ders_adi = dsi.ders_adi
        WHERE dsi.donem_sinif_num = ?
    """, (group_id,))
    
    courses = db.c.fetchall()
    total_slots = 0
    t_sum, u_sum, l_sum = 0, 0, 0
    print("\nCourses in DB for this group:")
    for row in courses:
        dur = (row[1] + row[2] + row[3]) * 2
        total_slots += dur
        t_sum += row[1]
        u_sum += row[2]
        l_sum += row[3]
        print(f"  - {row[0]} (Inst {row[4]}): T={row[1]}, U={row[2]}, L={row[3]} => {dur} slots")
        
    print(f"\nTotal DB Hours: T={t_sum}, U={u_sum}, L={l_sum} => {total_slots} slots")

if __name__ == "__main__":
    check_group()
