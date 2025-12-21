
import sqlite3
import os
import random

# Database path
DB_PATH = os.path.join(os.getcwd(), 'okul_veritabani.db')


from collections import defaultdict

def optimize_room_usage():
    print(f"Connecting to database at: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 1. Calculate loads for ALL rooms to find the saturated one
    print("Calculating room loads...")
    c.execute("SELECT teori_odasi FROM Dersler WHERE teori_odasi IS NOT NULL")
    room_assignments = c.fetchall()
    
    print(f"Total assignments found: {len(room_assignments)}")
    
    room_load = defaultdict(int)
    for r in room_assignments:
        room_load[r[0]] += 1
        
    print(f"Room loads calculated: {len(room_load)} rooms active.")
    
    saturated_room_id = None
    for r_id, load in room_load.items():
        print(f"Checking Room ID {r_id}: {load} hours")
        if load >= 40:
            saturated_room_id = r_id
            print(f"Found Saturated Room ID: {r_id} with Load: {load}")
            break
            
    if not saturated_room_id:
        print("No room found with >= 40 hours load.")
        conn.close()
        return

    # 2. Get Room Name for context
    c.execute("SELECT derslik_adi FROM Derslikler WHERE derslik_num = ?", (saturated_room_id,))
    res = c.fetchone()
    r_name = res[0] if res else "Unknown"
    print(f"Target Room: {r_name} (ID: {saturated_room_id})")

    # 3. Find courses in this room
    c.execute("SELECT ders_adi, ders_instance FROM Dersler WHERE teori_odasi = ?", (saturated_room_id,))
    courses = c.fetchall()
    
    # 4. Evict courses
    target_load = 32
    num_to_remove = len(courses) - target_load
    
    if num_to_remove <= 0:
         print("Load is fine.")
         return
         
    print(f"Planning to evict {num_to_remove} courses to reach target load of {target_load}...")
    
    courses_to_evict = random.sample(courses, num_to_remove)
    
    print("\nEvicting the following courses (Setting Room to NULL):")
    for crs in courses_to_evict:
        name = crs[0]
        instance = crs[1]
        print(f"  - {name} ({instance})")
        
        c.execute('''
            UPDATE Dersler 
            SET teori_odasi = NULL 
            WHERE ders_adi = ? AND ders_instance = ? AND teori_odasi = ?
        ''', (name, instance, saturated_room_id))
        
    conn.commit()
    print(f"\nSuccessfully updated {len(courses_to_evict)} courses.")
    conn.close()

if __name__ == "__main__":
    optimize_room_usage()
