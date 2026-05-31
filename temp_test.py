import sqlite3
conn = sqlite3.connect('database/okul_veritabani.db')
c = conn.cursor()
c.execute("SELECT d.ders_adi, dsi.donem_sinif_num, od.bolum_num, od.sinif_duzeyi FROM Ders_Sinif_Iliskisi dsi JOIN Dersler d ON dsi.ders_instance = d.ders_instance AND dsi.ders_adi = d.ders_adi JOIN Ogrenci_Donemleri od ON dsi.donem_sinif_num = od.donem_sinif_num WHERE d.ders_adi LIKE '%Türkçe 2%' OR d.ders_adi LIKE '%Özdevinirler%'")
for r in c.fetchall():
    print(r)
conn.close()
