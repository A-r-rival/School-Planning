import sqlite3
conn = sqlite3.connect('okul_veritabani.db')
conn.row_factory = sqlite3.Row

print("=== CHECKING IF ACTUAL POOL COURSES ARE IN DERSLER ===")
# Get some actual courses from havuz relation
pool_courses = conn.execute("SELECT ders_adi, ders_instance FROM Ders_Havuz_Iliskisi LIMIT 20").fetchall()

for pc in pool_courses:
    name, inst = pc['ders_adi'], pc['ders_instance']
    d_row = conn.execute("SELECT * FROM Dersler WHERE ders_adi = ? AND ders_instance = ?", (name, inst)).fetchone()
    if d_row:
        print(f"FOUND: {name} (Inst {inst}) in Dersler")
    else:
        print(f"MISSING: {name} (Inst {inst}) NOT in Dersler")

conn.close()
