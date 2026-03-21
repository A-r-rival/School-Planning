import sqlite3
import re
import sys
import os

db_path = "d:/Git_Projects/School-Planning/database/okul_veritabani.db"
conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute("SELECT COUNT(*) FROM Ders_Havuz_Iliskisi WHERE sinif_duzeyi = 0")
count = c.fetchone()[0]
print(f"[DB Patch] Found {count} pool courses with missing sinif_duzeyi. Patching...")

if count > 0:
    sys.path.insert(0, "d:/Git_Projects/School-Planning")
    from database import curriculum_data
    data = getattr(curriculum_data, 'DEPARTMENTS_DATA', {})
    
    # Map (bolum_adi, havuz_kodu) -> sinif_duzeyi
    pool_map = {}
    for dept_name, details in data.items():
        curr = details.get('curriculum', {})
        for sem_key, courses in curr.items():
            year_match = re.search(r'(\d+)\.\s*Y[ıi]l', sem_key)
            if not year_match: continue
            sinif_duzeyi = int(year_match.group(1))
            
            if isinstance(courses, list):
                for course in courses:
                    if isinstance(course, list) and len(course) >= 2:
                        pool_map[(dept_name, course[0])] = sinif_duzeyi

    # Get bolum_id dictionary
    c.execute("SELECT bolum_id, bolum_adi FROM Bolumler")
    bolum_dict = {row[1]: row[0] for row in c.fetchall()}

    # Now update
    updated_count = 0
    for key, sinif in pool_map.items():
        dept_name, pool_code = key
        if dept_name in bolum_dict:
            bolum_id = bolum_dict[dept_name]
            c.execute('''
                UPDATE Ders_Havuz_Iliskisi 
                SET sinif_duzeyi = ? 
                WHERE bolum_id = ? AND havuz_kodu = ? AND sinif_duzeyi = 0
            ''', (sinif, bolum_id, pool_code))
            if c.rowcount > 0:
                updated_count += c.rowcount
    
    conn.commit()
    print(f"[DB Patch] Successfully updated {updated_count} rows in Ders_Havuz_Iliskisi.")
else:
    print("[DB Patch] Nothing to patch.")

# Re-test the UNION query output for Computer Engineering, Year 3
c.execute("SELECT bolum_id FROM Bolumler WHERE bolum_adi LIKE '%Bilgisayar%'")
row = c.fetchone()
bolum_id = row[0] if row else 1
sinif = 3

query = '''
SELECT dp.gun, dp.baslangic, dp.bitis, dp.ders_adi,
       (SELECT ad || ' ' || soyad FROM Ogretmenler WHERE ogretmen_num = dp.ogretmen_id) as hoca,
       (SELECT derslik_adi FROM Derslikler WHERE derslik_num = dp.derslik_id) as oda,
       COALESCE(d.ders_kodu, 'CUSTOM') as ders_kodu, dp.ders_tipi
FROM Ders_Programi dp
LEFT JOIN Dersler d ON dp.ders_adi = d.ders_adi AND dp.ders_instance = d.ders_instance
JOIN Ders_Havuz_Iliskisi dhi ON dp.ders_adi = dhi.ders_adi AND dp.ders_instance = dhi.ders_instance
JOIN Ogrenci_Donemleri od ON od.bolum_num = dhi.bolum_id AND od.sinif_duzeyi = dhi.sinif_duzeyi
WHERE od.bolum_num = ? AND od.sinif_duzeyi = ?
'''
c.execute(query, (bolum_id, sinif))
results = c.fetchall()
print(f"\nTotal POOL rows inside live schedule (Ders_Programi) for Dept {bolum_id}, Year {sinif}: {len(results)}")
for r in results:
    print(f"[POOL RECORD FOUND IN LIVE SCHEDULE] {r[6]} - {r[3]}")
    
# Debug: check the actual existing havuz entries
c.execute("SELECT kacinci_donem FROM Ogrenciler LIMIT 1")
print(f"Sample Student Semester (kacinci_donem): {c.fetchone()[0]}")
