import sqlite3

conn = sqlite3.connect('database/okul_veritabani.db')
c = conn.cursor()

c.execute("PRAGMA table_info(Ogretmen_Musaitlik);")
for col in c.fetchall():
    print(col)
