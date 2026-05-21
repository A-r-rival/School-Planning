import os
import sys

sys.path.append(os.getcwd())

from models.schedule_model import ScheduleModel

model = ScheduleModel()

print("\n--- Endüstriyel Robotik entries in Ders_Ogretmen_Iliskisi ---")
model.c.execute("SELECT doi.ders_adi, o.ad, o.soyad FROM Ders_Ogretmen_Iliskisi doi JOIN Ogretmenler o ON doi.ogretmen_id = o.ogretmen_num WHERE doi.ders_adi LIKE '%Endüstriyel Robotik%'")
for row in model.c.fetchall():
    print(row)
    
print("\n--- Fabrika Yönetimine Giriş entries in Ders_Ogretmen_Iliskisi ---")
model.c.execute("SELECT doi.ders_adi, o.ad, o.soyad FROM Ders_Ogretmen_Iliskisi doi JOIN Ogretmenler o ON doi.ogretmen_id = o.ogretmen_num WHERE doi.ders_adi LIKE '%Fabrika Yönetimine Giriş%'")
for row in model.c.fetchall():
    print(row)

print("\n--- Endüstriyel Robotik in Ders_Programi ---")
model.c.execute("SELECT dp.ders_adi, dp.ders_instance, dp.gun, dp.saat, dp.bitis_saati, dp.derslik_id FROM Ders_Programi dp WHERE dp.ders_adi LIKE '%Endüstriyel Robotik%'")
for row in model.c.fetchall():
    print(row)

print("\n--- Fabrika Yönetimine Giriş in Ders_Programi ---")
model.c.execute("SELECT dp.ders_adi, dp.ders_instance, dp.gun, dp.saat, dp.bitis_saati, dp.derslik_id FROM Ders_Programi dp WHERE dp.ders_adi LIKE '%Fabrika Yönetimine Giriş%'")
for row in model.c.fetchall():
    print(row)
