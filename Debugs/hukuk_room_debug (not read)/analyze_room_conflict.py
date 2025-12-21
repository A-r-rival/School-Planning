
import sqlite3
import os
from collections import defaultdict

DB_PATH = os.path.join(os.getcwd(), 'okul_veritabani.db')
TARGET_ROOM_ID = 4 # Amfi-4

def analyze_room():
    print(f"Connecting to {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    print(f"\n--- Analyzing Room {TARGET_ROOM_ID} ---")
    
    # Get courses
    c.execute("SELECT d.ders_adi, d.ders_instance, d.teori_odasi, d.lab_odasi, doi.ogretmen_id FROM Dersler d LEFT JOIN Ders_Ogretmen_Iliskisi doi ON d.ders_adi = doi.ders_adi AND d.ders_instance = doi.ders_instance WHERE d.teori_odasi = ?", (TARGET_ROOM_ID,))
    courses = c.fetchall()
    
    print(f"Total Courses: {len(courses)} (Hours: {len(courses)})") # Assuming 1h/course
    
    analysis_data = {}
    teachers = defaultdict(int)
    for row in courses:
        t_id = row[4]
        teachers[t_id] += 1
        
    for t_id, load in teachers.items():
        # Get unavailability
        c.execute("SELECT gun, baslangic, bitis FROM Ogretmen_Musaitlik WHERE ogretmen_id = ?", (t_id,))
        unavail = c.fetchall()
        
        # Calculate Unavailability Duration (approx)
        blocked_hours = 0
        for day, start, end in unavail:
             h_start = int(start.split(':')[0])
             h_end = int(end.split(':')[0])
             blocked_hours += (h_end - h_start)
             
        t_name = f"Teacher {t_id}"
        if t_id:
             c.execute("SELECT ad, soyad FROM Ogretmenler WHERE ogretmen_num=?", (t_id,))
             res = c.fetchone()
             if res: t_name = f"{res[0]} {res[1]}"
             
        analysis_data[t_id] = {'load': load, 'blocked': blocked_hours, 'name': t_name}

    print("\n--- SUMMARY ---")
    print(f"Room Load: {len(courses)}/40")
    
    # Check Deadlocks
    deadlock = False
    for t_id, data in analysis_data.items():
        free_slots = 40 - data['blocked']
        needed = data['load']
        status = "OK"
        if needed > free_slots:
            status = "IMPOSSIBLE (Needed > Free)"
            deadlock = True
            
        if needed + data['blocked'] > 30: # Showing strict threshold
             print(f"Teacher {data['name']} (ID {t_id}): Need {needed}h, Blocked {data['blocked']}h. Free: {free_slots}h. Status: {status}")
             
    if deadlock:
        print("\nCONCLUSION: Room is mathematically impossible due to Teacher Unavailability.")
    else:
        print("\nCONCLUSION: Room SEEMS feasible based on Teacher Availability counts.")
             
    conn.close()

if __name__ == "__main__":
    analyze_room()
