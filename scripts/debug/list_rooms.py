import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True, errors='replace')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from models.schedule_model import ScheduleModel
m = ScheduleModel()

m.c.execute("SELECT derslik_num, derslik_adi, derslik_tipi, kapasite, floor FROM Derslikler WHERE silindi=0 ORDER BY derslik_adi")
rooms = m.c.fetchall()

with open("room_list.txt", "w", encoding="utf-8") as f:
    f.write(f"Total active rooms: {len(rooms)}\n\n")
    for r in rooms:
        f.write(f"ID={r[0]:3d}  Name={r[1]:20s}  Type={r[2]:10s}  Cap={r[3]:4d}  Floor={r[4]}\n")

print(f"Written {len(rooms)} rooms to room_list.txt")
