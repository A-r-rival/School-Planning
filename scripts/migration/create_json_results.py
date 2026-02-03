# -*- coding: utf-8 -*-
import sqlite3
import json

conn = sqlite3.connect('okul_veritabani.db')
c = conn.cursor()

results = {}

# Pool relationships
c.execute("""
    SELECT ders_adi, ders_instance, havuz_kodu
    FROM Ders_Havuz_Iliskisi
    WHERE ders_adi LIKE '%Makine%'
    ORDER BY ders_adi, havuz_kodu
""")
results['pool_relationships'] = [{'ders': row[0], 'instance': row[1], 'havuz': row[2]} for row in c.fetchall()]

# Schedule entries
c.execute("""
    SELECT program_id, ders_adi, ders_instance, gun, baslangic, bitis, ders_tipi
    FROM Ders_Programi
    WHERE ders_adi LIKE '%Makine%'
    ORDER BY gun, baslangic, ders_instance
""")
results['schedule_entries'] = [{'id': row[0], 'ders': row[1], 'instance': row[2], 'gun': row[3], 'start': row[4], 'end': row[5], 'tip': row[6]} for row in c.fetchall()]

# Course codes
c.execute("""
    SELECT ders_kodu, ders_adi, ders_instance
    FROM Dersler
    WHERE ders_adi LIKE '%Makine%'
    ORDER BY ders_kodu, ders_instance
""")
results['course_codes'] = [{'kod': row[0], 'ders': row[1], 'instance': row[2]} for row in c.fetchall()]

conn.close()

with open('results.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("JSON written")
print(f"Pool relationships: {len(results['pool_relationships'])}")
print(f"Schedule entries: {len(results['schedule_entries'])}")
print(f"Course codes: {len(results['course_codes'])}")
