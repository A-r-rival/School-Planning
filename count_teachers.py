
import sqlite3
import os

db_path = os.path.join(os.getcwd(), "database", "okul_veritabani.db")
conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute("SELECT count(*) FROM Ogretmenler")
print(f"Total teachers: {c.fetchone()[0]}")
c.execute("SELECT ogretmen_num, ad || ' ' || soyad FROM Ogretmenler ORDER BY ad")
teachers = c.fetchall()
print(f"Last 5 teachers:")
for t in teachers[-5:]:
    print(t)
