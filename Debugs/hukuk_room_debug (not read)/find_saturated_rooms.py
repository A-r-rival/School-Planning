
import sqlite3
import os
from collections import defaultdict

# Database path
DB_PATH = os.path.join(os.getcwd(), 'okul_veritabani.db')

def list_room_loads():
    print(f"Connecting to database at: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Get room names
    c.execute("SELECT derslik_num, derslik_adi FROM Derslikler")
    rooms = {r[0]: r[1] for r in c.fetchall()}
    
    # Get assignments
    c.execute("SELECT teori_odasi FROM Dersler WHERE teori_odasi IS NOT NULL")
    room_assignments = c.fetchall()
    
    room_load = defaultdict(int)
    for r in room_assignments:
        room_load[r[0]] += 1
        
    print("\n--- Room Load Report ---")
    sorted_rooms = sorted(room_load.items(), key=lambda x: x[1], reverse=True)
    
    for r_id, load in sorted_rooms:
        r_name = rooms.get(r_id, f"ID {r_id}")
        status = "OK"
        if load >= 40: status = "CRITICAL (100% Full)"
        elif load >= 35: status = "WARNING (High Load)"
        
        if load >= 30:
            print(f"Room: {r_name:30} | Load: {load:2} | {status}")
        
    conn.close()

if __name__ == "__main__":
    list_room_loads()
