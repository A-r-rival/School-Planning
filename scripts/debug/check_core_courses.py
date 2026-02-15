"""Quick debug: check core course data."""
import sys, os
sys.path.append(os.getcwd())
import sqlite3
conn = sqlite3.connect('database/okul_veritabani.db')

# Check Ders_Sinif for MAT courses 
rows = conn.execute("SELECT dsi.ders_adi, dsi.donem_sinif_num FROM Ders_Sinif_Iliskisi dsi WHERE dsi.ders_adi LIKE '%Analiz%' LIMIT 5").fetchall()
print("Analiz in Ders_Sinif:", rows)

# Year distribution in get_all_curriculum_details
from models.schedule_model import ScheduleModel
m = ScheduleModel()
all_data = m.get_all_curriculum_details()
years = {}
for row in all_data:
    y = row[9]
    years[y] = years.get(y, 0) + 1
print("Year dist:", dict(sorted(years.items())))

is_pool_dist = {}
for row in all_data:
    p = row[10]
    is_pool_dist[p] = is_pool_dist.get(p, 0) + 1
print("IsPool dist:", is_pool_dist)

# Year 1 sample
y1 = [r for r in all_data if r[9] == 1]
print(f"Year 1 count: {len(y1)}")
for r in y1[:3]:
    print(f"  {r[0]} | {r[1]} | pool={r[10]}")

m.close_connections()
conn.close()
