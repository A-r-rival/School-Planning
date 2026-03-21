import sqlite3
import os

db_path = os.path.join("d:\\Git_Projects\\School-Planning\\database", "okul_veritabani.db")
conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute("SELECT donem FROM Ders_Havuzu WHERE ders_kodu='MAT108'")
print(c.fetchall())
conn.close()
