
import sqlite3
import os

def populate_rooms():
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "okul_veritabani.db")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    print("Clearing existing rooms...")
    c.execute("DELETE FROM Derslikler")
    
    rooms = []
    
    # 10 Labs (Capacity 40)
    for i in range(1, 11):
        rooms.append((f"Lab-{i}", "Laboratuvar", 40))
        
    # 4 Amfis (Capacity 70)
    for i in range(1, 5):
        rooms.append((f"Amfi-{i}", "Amfi", 70))
        
    # 64 Classrooms (Capacity 40) - 8 blocks of 8? Or just numbered 1-64.
    # User said "8*8 derslik". Let's name them meaningfully if possible, e.g. Block A-H.
    # Or just Derslik-1 to Derslik-64. Let's stick to simple numbering for now.
    for i in range(1, 65):
        rooms.append((f"Derslik-{i}", "Derslik", 40))

    print(f"Inserting {len(rooms)} rooms...")
    c.executemany("INSERT INTO Derslikler (derslik_adi, derslik_tipi, kapasite) VALUES (?, ?, ?)", rooms)
    
    conn.commit()
    conn.close()
    print("Room population complete.")

if __name__ == "__main__":
    populate_rooms()
