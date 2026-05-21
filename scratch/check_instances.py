import os
import sys

sys.path.append(os.getcwd())

from models.schedule_model import ScheduleModel

model = ScheduleModel()
model.c.execute("SELECT ders_instance, donem_sinif_num FROM Ders_Sinif_Iliskisi WHERE ders_adi LIKE '%Endüstriyel Robotik 1%'")
for row in model.c.fetchall():
    print("Class Rel:", row)

model.c.execute("SELECT ders_instance, bolum_id FROM Ders_Havuz_Iliskisi WHERE ders_adi LIKE '%Endüstriyel Robotik 1%'")
for row in model.c.fetchall():
    print("Pool Rel:", row)
