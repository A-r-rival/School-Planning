
import sqlite3
import os

def populate_rooms():
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database", "okul_veritabani.db")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    print("Clearing existing rooms...")
    c.execute("DELETE FROM Derslikler")
    
    rooms = []
    
    # 15 Labs (Capacity 40) - 5 per floor
    # 1-5: Floor 0
    # 6-10: Floor 1
    # 11-15: Floor 2
    for i in range(1, 16):
        floor = 0
        if 6 <= i <= 10:
            floor = 1
        elif i > 10:
            floor = 2
        rooms.append((f"Lab-{i}", "Laboratuvar", 40, floor))
        
    # 4 Amfis (Capacity 70) 
    # 1-2: Floor 0
    # 3-4: Floor 2
    for i in range(1, 5):
        floor = 0 if i <= 2 else 2
        rooms.append((f"Amfi-{i}", "Amfi", 70, floor))
        
    # 64 Classrooms (Capacity 40)
    # Distribution:
    # 1-20: Floor 0 (Giriş)
    # 21-40: Floor 1 (1. Kat)
    # 41-64: Floor 2 (2. Kat)
    for i in range(1, 65):
        floor = 0
        if 21 <= i <= 40:
            floor = 1
        elif i > 40:
            floor = 2
            
        rooms.append((f"Derslik-{i}", "Derslik", 40, floor))

    print(f"Inserting {len(rooms)} rooms...")
    # Update query to include floor
    c.executemany("INSERT INTO Derslikler (derslik_adi, derslik_tipi, kapasite, floor) VALUES (?, ?, ?, ?)", rooms)
    
    conn.commit()
    conn.close()
    print("Room population complete.")

if __name__ == "__main__":
    populate_rooms()
