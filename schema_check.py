# -*- coding: utf-8 -*-
import sqlite3

conn = sqlite3.connect('okul_veritabani.db')
cursor = conn.cursor()

# Just check the schema
cursor.execute("PRAGMA table_info(Ders_Havuz_Iliskisi)")
print("Ders_Havuz_Iliskisi Schema:")
for row in cursor.fetchall():
    print(row)

conn.close()
