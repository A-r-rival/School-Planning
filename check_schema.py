# -*- coding: utf-8 -*-
import sqlite3

conn = sqlite3.connect('okul_veritabani.db')
cursor = conn.cursor()

print("DERS_PROGRAMI SCHEMA:")
cursor.execute("PRAGMA table_info(Ders_Programi)")
for row in cursor.fetchall():
    print(row)

conn.close()
