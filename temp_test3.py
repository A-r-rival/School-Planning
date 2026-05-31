import sqlite3
conn = sqlite3.connect('database/okul_veritabani.db')
c = conn.cursor()
c.execute("SELECT ders_adi, teori_saati, uygulama_saati, lab_saati FROM Dersler WHERE ders_adi LIKE '%Türkçe 2%' OR ders_adi LIKE '%Özdevinirler%'")
for r in c.fetchall():
    print(r)
conn.close()
