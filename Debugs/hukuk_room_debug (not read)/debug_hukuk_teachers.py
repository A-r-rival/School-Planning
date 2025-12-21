
import sqlite3
import os
from collections import defaultdict

DB_PATH = os.path.join(os.getcwd(), 'okul_veritabani.db')

def analyze_hukuk_teachers():
    print(f"Connecting to {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 1. Identify Hukuk-101 ID (Room 16 as confirmed previously)
    TARGET_ROOM_ID = 16 
    print(f"Analyzing Room ID: {TARGET_ROOM_ID}")
    
    # 2. Get all courses for this room
    c.execute("SELECT ders_adi, ders_instance, ogretmen_id FROM Ders_Programi WHERE 1=0") # Mock query structure
    # Real query from Dersler
    c.execute("SELECT ders_adi, ders_instance, teori_odasi FROM Dersler WHERE teori_odasi = ?", (TARGET_ROOM_ID,))
    room_courses = c.fetchall()
    
    # Get Teachers for these courses
    teacher_ids = set()
    for crs in room_courses:
        # Get teacher ID
        c.execute("SELECT ogretmen_id FROM Ders_Ogretmen_Iliskisi WHERE ders_adi=? AND ders_instance=?", (crs[0], crs[1]))
        t_rows = c.fetchall()
        for t in t_rows:
            teacher_ids.add(t[0])
            
    print(f"\nTeachers teaching in Room {TARGET_ROOM_ID}: {list(teacher_ids)}")
    
    # 3. Analyze each teacher
    for t_id in teacher_ids:
        # Get Teacher Name
        c.execute("SELECT ad, soyad FROM Ogretmenler WHERE ogretmen_num=?", (t_id,))
        t_name = c.fetchone()
        t_name = f"{t_name[0]} {t_name[1]}" if t_name else f"ID {t_id}"
        
        # Get TOTAL load for this teacher
        c.execute('''
            SELECT d.teori_odasi, count(*) 
            FROM Dersler d
            JOIN Ders_Ogretmen_Iliskisi doi ON d.ders_adi = doi.ders_adi AND d.ders_instance = doi.ders_instance
            WHERE doi.ogretmen_id = ?
            GROUP BY d.teori_odasi
        ''', (t_id,))
        load_rows = c.fetchall()
        
        total_load = sum([x[1] for x in load_rows]) # Assuming 1 hour per course instance roughly
        
        print(f"\nTeacher: {t_name} (ID: {t_id}) | Total Load: {total_load} hours")
        for room_id, count in load_rows:
            room_label = "Room " + str(room_id) if room_id else "ANY Room"
            print(f"  - {room_label}: {count} hours")
            
        if total_load > 30:
            print("  WARNING: High Load!")
            
    conn.close()

if __name__ == "__main__":
    analyze_hukuk_teachers()
    
# Only for printing if run interactively, though 'python' doesn't do this automatically.
# Let's just create a separate read command or rely on user downloading it.
# Actually I'll make a second script to read it cleanly.
