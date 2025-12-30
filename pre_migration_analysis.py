# -*- coding: utf-8 -*-
"""
Pre-migration analysis: Understand exactly what needs to be consolidated
"""
import sqlite3
import json

conn = sqlite3.connect('okul_veritabani.db')
c = conn.cursor()

results = {}

# 1. All Makine course entries in Dersler
c.execute("""
    SELECT ders_kodu, ders_adi, ders_instance, teori_odasi, lab_odasi, akts, 
           teori_saati, uygulama_saati, lab_saati
    FROM Dersler
    WHERE ders_adi LIKE '%Makine%'
    ORDER BY ders_kodu, ders_instance
""")
results['dersler_entries'] = []
for row in c.fetchall():
    results['dersler_entries'].append({
        'ders_kodu': row[0],
        'ders_adi': row[1],
        'ders_instance': row[2],
        'teori_odasi': row[3],
        'lab_odasi': row[4],
        'akts': row[5],
        'teori_saati': row[6],
        'uygulama_saati': row[7],
        'lab_saati': row[8]
    })

# 2. Schedule entries
c.execute("""
    SELECT dp.program_id, d.ders_kodu, d.ders_adi, d.ders_instance, 
           dp.gun, dp.baslangic, dp.bitis, dp.ogretmen_id, dp.derslik_id, dp.ders_tipi
    FROM Ders_Programi dp
    JOIN Dersler d ON dp.ders_adi = d.ders_adi AND dp.ders_instance = d.ders_instance
    WHERE d.ders_adi LIKE '%Makine%'
""")
results['schedule_entries'] = []
for row in c.fetchall():
    results['schedule_entries'].append({
        'program_id': row[0],
        'ders_kodu': row[1],
        'ders_adi': row[2],
        'ders_instance': row[3],
        'gun': row[4],
        'baslangic': row[5],
        'bitis': row[6],
        'ogretmen_id': row[7],
        'derslik_id': row[8],
        'ders_tipi': row[9]
    })

# 3. Pool relationships
c.execute("""
    SELECT dhi.iliski_id, dhi.ders_adi, dhi.ders_instance, dhi.bolum_num, dhi.havuz_kodu
    FROM Ders_Havuz_Iliskisi dhi
    WHERE dhi.ders_adi LIKE '%Makine%'
    ORDER BY dhi.havuz_kodu
""")
results['pool_relationships'] = []
for row in c.fetchall():
    results['pool_relationships'].append({
        'iliski_id': row[0],
        'ders_adi': row[1],
        'ders_instance': row[2],
        'bolum_num': row[3],
        'havuz_kodu': row[4]
    })

# 4. Class relationships
c.execute("""
    SELECT dsi.ders_adi, dsi.ders_instance, dsi.donem_sinif_num
    FROM Ders_Sinif_Iliskisi dsi
    WHERE dsi.ders_adi LIKE '%Makine%'
""")
results['class_relationships'] = []
for row in c.fetchall():
    results['class_relationships'].append({
        'ders_adi': row[0],
        'ders_instance': row[1],
        'donem_sinif_num': row[2]
    })

conn.close()

# Save to JSON
with open('pre_migration_analysis.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

# Print summary
print("PRE-MIGRATION ANALYSIS")
print("=" * 80)
print(f"Dersler entries: {len(results['dersler_entries'])}")
for entry in results['dersler_entries']:
    print(f"  [{entry['ders_kodu']}] {entry['ders_adi']} (instance={entry['ders_instance']})")
    
print(f"\nSchedule entries: {len(results['schedule_entries'])}")
for entry in results['schedule_entries']:
    print(f"  [{entry['ders_kodu']}] instance={entry['ders_instance']}, {entry['gun']} {entry['baslangic']}-{entry['bitis']}")

print(f"\nPool relationships: {len(results['pool_relationships'])}")
for entry in results['pool_relationships']:
    print(f"  {entry['havuz_kodu']} -> instance={entry['ders_instance']}")

print(f"\nClass relationships: {len(results['class_relationships'])}")
for entry in results['class_relationships']:
    print(f"  instance={entry['ders_instance']} -> {entry['donem_sinif_num']}")

print("\n" + "=" * 80)
print("Analysis saved to: pre_migration_analysis.json")
