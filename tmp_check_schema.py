import sqlite3
import os

db_path = r"d:\Git_Projects\School-Planning\database\okul_veritabani.db"
conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='Ders_Ogretmen_Iliskisi'")
row = c.fetchone()
if row:
    print(row[0])
else:
    print("Table not found")
conn.close()
