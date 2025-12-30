# Check what's actually in the database NOW
import sqlite3

conn = sqlite3.connect('okul_veritabani.db')
c = conn.cursor()

print("DERSLER TABLE - Makine courses:")
c.execute("""
    SELECT ders_kodu, ders_adi, ders_instance
    FROM Dersler
    WHERE ders_adi LIKE '%Makine Öğrenmesi%'
    AND ders_adi NOT LIKE '%Biyomedikal%'
    AND ders_adi NOT LIKE '%Machine Learning%'
    ORDER BY ders_kodu
""")
print(f"Found {c.rowcount} entries:")
for row in c.fetchall():
    print(f"  [{row[0]}] {row[1]} (instance={row[2]})")

print("\nDERS_PROGRAMI - Schedule entries:")
c.execute("""
    SELECT dp.program_id, d.ders_kodu, dp.ders_adi, dp.gun, dp.baslangic, dp.bitis
    FROM Ders_Programi dp
    JOIN Dersler d ON dp.ders_adi = d.ders_adi AND dp.ders_instance = d.ders_instance
    WHERE dp.ders_adi LIKE '%Makine Öğrenmesi%'
    AND dp.ders_adi NOT LIKE '%Biyomedikal%'
    AND dp.ders_adi NOT LIKE '%Machine Learning%'
    ORDER BY d.ders_kodu
""")
for row in c.fetchall():
    print(f"  program_id={row[0]}: [{row[1]}] {row[2]} - {row[3]} {row[4]}-{row[5]}")

conn.close()
