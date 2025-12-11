
import sys
import os
import sqlite3

# Add project root to path
sys.path.append(os.getcwd())

try:
    from scripts.curriculum_data import DEPARTMENTS_DATA
    print("Successfully imported DEPARTMENTS_DATA")
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

dept_name = "Kültür ve İletişim Bölümü"
if dept_name in DEPARTMENTS_DATA:
    print(f"Found {dept_name}")
    curr = DEPARTMENTS_DATA[dept_name].get("curriculum", {})
    if "7" in curr:
        print("Semester 7 found:")
        courses = curr["7"]
        found = False
        for c in courses:
            print(f" - {c}")
            if c[0] == "KKW419":
                print("FOUND KKW419!")
                found = True
        if not found:
            print("KKW419 NOT FOUND in Semester 7")
    else:
        print("Semester 7 NOT FOUND")
else:
    print(f"{dept_name} NOT FOUND in DEPARTMENTS_DATA keys:")
    for k in DEPARTMENTS_DATA.keys():
        print(f" - {k}")

# Check DB
conn = sqlite3.connect('okul_veritabani.db')
c = conn.cursor()
c.execute("SELECT * FROM Dersler WHERE ders_kodu = 'KKW419'")
res = c.fetchall()
print(f"DB Query Result: {res}")
conn.close()
