import sqlite3

conn = sqlite3.connect('database/okul_veritabani.db')
c = conn.cursor()

c.execute("PRAGMA table_info(Dersler);")
print("Dersler cols:", c.fetchall())

c.execute("PRAGMA table_info(Ders_Sinif_Iliskisi);")
print("DSI cols:", c.fetchall())

c.execute("PRAGMA table_info(Ogrenci_Donemleri);")
print("OD cols:", c.fetchall())
