import sqlite3
import os

db_path = os.path.join("database", "okul_veritabani.db")
conn = sqlite3.connect(db_path)
c = conn.cursor()

# Try to find a match between a course that looks like a lab and its assigned room ID
c.execute("""
    SELECT dp.ders_adi, dp.derslik_id
    FROM Ders_Programi dp
    WHERE dp.ders_adi LIKE '%Lab%'
    LIMIT 10
""")
lab_courses = c.fetchall()
print("--- Lab Courses in Schedule ---")
for name, rid in lab_courses:
    print(f"Course: {name}, Assigned Room ID: {rid}")

print("\n--- Potential Matching Rooms (with offset 169) ---")
for name, rid in lab_courses:
    target_id = rid + 169
    c.execute("SELECT derslik_adi, derslik_tipi FROM Derslikler WHERE derslik_num = ?", (target_id,))
    res = c.fetchone()
    if res:
        print(f"Room ID {rid} + 169 = {target_id} -> {res}")
    else:
        print(f"Room ID {rid} + 169 = {target_id} -> NOT FOUND")

conn.close()
