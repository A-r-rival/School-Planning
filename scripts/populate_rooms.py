
import sqlite3
import os

def populate_rooms():
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database", "okul_veritabani.db")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    print("Clearing existing rooms...")
    c.execute("DELETE FROM Derslikler")
    
    rooms = []
    
    # Department Specific Labs (2 per department)
    # Total: 9 Depts * 2 = 18 Labs
    
    dept_labs = [
        # Mühendislik (01)
        ("Bilgisayar", 101),
        ("Elektrik_Elektronik", 102),
        ("Endüstri", 103),
        ("Makine", 104),
        ("Mekatronik", 105),
        ("İnşaat", 106),
        # Fen (02)
        ("Enerji", 201),
        ("Malzeme", 202),
        ("Moleküler", 203)
    ]
    
    lab_counter = 1
    for name, code in dept_labs:
        for i in range(1, 3): # 2 Labs each
            # Floor Logic: 
            # Labs 1-9 (First 5 depts) -> Floor 0
            # Labs 10-18 (Rest) -> Floor 1
            floor = 0 if lab_counter <= 10 else 1 
            
            room_name = f"{name} Lab-{i}"
            # Type: "Laboratuvar" is standard, but keeping specific name in type might be useful? 
            # Scheduler checks for "Lab" in name/type, so standard "Laboratuvar" is safe + name has "Lab".
            # User said "lab türü kur" (establish lab type). Let's start with "Laboratuvar" type but distinct names.
            
            rooms.append((room_name, "Laboratuvar", 300, floor))
            lab_counter += 1
        
    # 4 Amfis (Capacity 70) 
    # 1-2: Floor 0
    # 3-4: Floor 2
    for i in range(1, 5):
        floor = 0 if i <= 2 else 2
        rooms.append((f"Amfi-{i}", "Amfi", 444, floor))
        
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
            
        if i <= 32:
            rooms.append((f"Büyük Derslik-{i}", "Derslik", 150, floor))
        else:
            rooms.append((f"Küçük Derslik-{i-32}", "Derslik", 69, floor))

    print(f"Inserting {len(rooms)} rooms...")
    # Update query to include floor
    c.executemany("INSERT INTO Derslikler (derslik_adi, derslik_tipi, kapasite, floor) VALUES (?, ?, ?, ?)", rooms)
    
    conn.commit()
    conn.close()
    print("Room population complete.")

if __name__ == "__main__":
    populate_rooms()
