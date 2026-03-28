import sqlite3
conn = sqlite3.connect('database/school_schedule.db')
c = conn.cursor()
c.execute('SELECT ders_kodu, ders_adi FROM mufredat WHERE ders_adi LIKE "%Proj%"')
for r in c.fetchall():
    print(r)
