import sqlite3
import re
from database import curriculum_data

conn = sqlite3.connect('database/okul_veritabani.db')
c = conn.cursor()

data = getattr(curriculum_data, 'DEPARTMENTS_DATA', {})

print("=== ZSD yılları (curriculum_data'dan) ===")
for dept_name, details in sorted(data.items()):
    curr = details.get('curriculum', {})
    zsd_years = []
    for sem_key, courses in curr.items():
        year_match = re.search(r'(\d+)\.\s*Y[ıi]l', sem_key)
        if not year_match: continue
        year = int(year_match.group(1))
        for course in courses:
            if isinstance(course, list) and len(course) >= 2 and course[0] == 'ZSD':
                zsd_years.append(year)
    if zsd_years:
        print(f"  {dept_name}: ZSD yılları = {sorted(zsd_years)}")

print("\n=== DB'deki ZSD sinif_duzeyi değerleri ===")
c.execute("""
    SELECT B.Bolum_adi, DHI.havuz_kodu, DHI.sinif_duzeyi, COUNT(*) as count
    FROM Ders_Havuz_Iliskisi DHI
    JOIN Bolumler B ON DHI.bolum_id = B.bolum_id
    WHERE DHI.havuz_kodu = 'ZSD'
    GROUP BY B.Bolum_adi, DHI.sinif_duzeyi
    ORDER BY B.Bolum_adi
""")
for r in c.fetchall():
    print(f"  {r[0]}: sinif_duzeyi={r[2]} ({r[3]} ders)")

conn.close()
