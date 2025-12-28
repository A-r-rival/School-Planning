import sqlite3

conn = sqlite3.connect('okul_veritabani.db')
c = conn.cursor()

# Sample actual course names
c.execute("""
    SELECT DISTINCT ders_adi 
    FROM Dersler 
    WHERE LOWER(ders_adi) NOT LIKE '%seçmeli%'
       AND LOWER(ders_adi) NOT LIKE '%havuz%'
       AND LOWER(ders_adi) NOT LIKE '%staj%'
       AND LOWER(ders_adi) NOT LIKE '%proje%'
    ORDER BY RANDOM()
    LIMIT 20
""")

print("Sample CORE courses in Dersler:")
for row in c.fetchall():
    print(f"  - {row[0]}")

conn.close()
