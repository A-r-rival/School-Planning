import os
import sys

sys.path.append(os.getcwd())

from models.schedule_model import ScheduleModel

model = ScheduleModel()
model.c.execute("SELECT d.ders_instance, dsi.donem_sinif_num, b.bolum_adi FROM Dersler d LEFT JOIN Ders_Sinif_Iliskisi dsi ON d.ders_adi = dsi.ders_adi AND d.ders_instance = dsi.ders_instance LEFT JOIN Ogrenci_Donemleri od ON dsi.donem_sinif_num = od.donem_sinif_num LEFT JOIN Bolumler b ON od.bolum_num = b.bolum_id WHERE d.ders_adi LIKE '%Yazılım Mühendisliği Projesi%'")
print("Class Relations:")
for r in model.c.fetchall():
    print(r)

model.c.execute("SELECT d.ders_instance, dhi.havuz_kodu, b.bolum_adi FROM Dersler d LEFT JOIN Ders_Havuz_Iliskisi dhi ON d.ders_adi = dhi.ders_adi AND d.ders_instance = dhi.ders_instance LEFT JOIN Bolumler b ON dhi.bolum_id = b.bolum_id WHERE d.ders_adi LIKE '%Yazılım Mühendisliği Projesi%'")
print("\nPool Relations:")
for r in model.c.fetchall():
    print(r)
