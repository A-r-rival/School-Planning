import sqlite3

db_path = "d:/Git_Projects/School-Planning/database/okul_veritabani.db"
conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute("SELECT bolum_id FROM Bolumler WHERE bolum_adi LIKE '%Bilgisayar%'")
row = c.fetchone()
bolum_id = row[0] if row else 1

c.execute("SELECT ders_adi, ders_instance FROM Ders_Havuz_Iliskisi")
pool_courses = c.fetchall()
pool_names = set(p[0] for p in pool_courses)

c.execute("SELECT DISTINCT ders_adi, ders_instance FROM Ders_Programi")
scheduled_courses = c.fetchall()
scheduled_names = set(s[0] for s in scheduled_courses)

print(f"Total defined pool courses in DB: {len(pool_courses)}")
print(f"Total unique courses currently scheduled in DB: {len(scheduled_names)}")

matched_names = pool_names.intersection(scheduled_names)
print(f"Number of exact name matches between Ders_Programi and Ders_Havuz_Iliskisi: {len(matched_names)}")

if len(matched_names) > 0:
    for name in list(matched_names)[:5]:
        print(f"MATCH: '{name}'")
else:
    print("NO MATCHES AT ALL. Checking for loose matches...")
    for s_name in scheduled_names:
        if "Seçmeli" in s_name or "ZSD" in s_name or "ÜSD" in s_name:
            print(f"Scheduled elective (no exact match): '{s_name}'")

# Check if Ders_Programi is entirely devoid of pool courses
pool_like = [s for s in scheduled_names if "ZSD" in s[0] or "ÜSD" in s[0] or "Seçmeli" in s[0] or "GSD" in s[0]]
print(f"Total pool-like courses currently scheduled (based on name parsing): {len(pool_like)}")
if pool_like:
    print(f"Sample pool-like scheduled: {pool_like[:5]}")
