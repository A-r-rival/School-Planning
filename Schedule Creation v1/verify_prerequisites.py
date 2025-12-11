
import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'okul_veritabani.db')
conn = sqlite3.connect(db_path)
c = conn.cursor()

def check_table(table_name):
    try:
        c.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = c.fetchone()[0]
        print(f"[{table_name}]: {count} records")
        return count
    except Exception as e:
        print(f"[{table_name}]: ERROR - {e}")
        return 0

print("--- Data Prerequisites Check ---")

d_count = check_table("Dersler")
dsi_count = check_table("Ders_Sinif_Iliskisi")
o_count = check_table("Ogretmenler")
dl_count = check_table("Derslikler")
dp_count = check_table("Ders_Programi")

# Check if Ders without Ders_Sinif_Iliskisi exists
c.execute("""
    SELECT COUNT(*) FROM Dersler d
    LEFT JOIN Ders_Sinif_Iliskisi dsi ON d.ders_adi = dsi.ders_adi AND d.ders_instance = dsi.ders_instance
    WHERE dsi.donem_sinif_num IS NULL
""")
orphaned_courses = c.fetchone()[0]
print(f"Orphaned Courses (No Student Group): {orphaned_courses}")

# Check if we have rooms
if dl_count == 0:
    print("WARNING: No classrooms found! Scheduler will fail.")

# Check if we have teachers
if o_count == 0:
    print("WARNING: No teachers found! Scheduler might fail if teachers are required.")
    
# Check constraints
c.execute("SELECT COUNT(*) FROM Ogretmen_Musaitlik")
print(f"Teacher Unavailability Constrains: {c.fetchone()[0]}")

conn.close()
