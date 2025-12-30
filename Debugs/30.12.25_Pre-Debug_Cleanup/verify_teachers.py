
import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'okul_veritabani.db')
conn = sqlite3.connect(db_path)
c = conn.cursor()

print("--- Teachers Summary ---")
c.execute("SELECT COUNT(*) FROM Ogretmenler")
print(f"Total Teachers: {c.fetchone()[0]}")

print("\n--- Unavailability Summary ---")
c.execute("SELECT COUNT(*) FROM Ogretmen_Musaitlik")
print(f"Total Constraints: {c.fetchone()[0]}")

print("\n--- Sample Teachers ---")
c.execute("SELECT * FROM Ogretmenler LIMIT 5")
for row in c.fetchall():
    print(row)

print("\n--- Sample Constraints ---")
c.execute("""
    SELECT o.ad, o.soyad, m.gun, m.baslangic, m.bitis 
    FROM Ogretmen_Musaitlik m 
    JOIN Ogretmenler o ON m.ogretmen_id = o.ogretmen_num 
    LIMIT 5
""")
for row in c.fetchall():
    print(f"{row[0]} {row[1]}: {row[2]} {row[3]}-{row[4]}")

conn.close()
