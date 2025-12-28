# Populate Ders_Havuz_Iliskisi from curriculum_data.py
import sys
import sqlite3
sys.path.insert(0, r'd:\Git_Projects\School-Planning')

from scripts.curriculum_data import DEPARTMENTS_DATA

conn = sqlite3.connect('okul_veritabani.db')
c = conn.cursor()

# Clear existing data
c.execute("DELETE FROM Ders_Havuz_Iliskisi")
print("Cleared existing pool relationships")

# Get department IDs
c.execute("SELECT bolum_num, bolum_adi FROM Bolumler")
dept_map = {name: num for num, name in c.fetchall()}

inserted = 0
skipped = 0

for dept_name, dept_data in DEPARTMENTS_DATA.items():
    if dept_name not in dept_map:
        print(f"SKIP: Department '{dept_name}' not in database")
        continue
    
    bolum_num = dept_map[dept_name]
    pool_codes = dept_data.get('pool_codes', {})
    
    for havuz_kodu, courses in pool_codes.items():
        for course_name in courses:
            # Find course in Dersler table
            c.execute("""
                SELECT ders_instance 
                FROM Dersler 
                WHERE ders_adi = ? 
                LIMIT 1
            """, (course_name,))
            
            result = c.fetchone()
            if result:
                ders_instance = result[0]
                
                try:
                    c.execute("""
                        INSERT INTO Ders_Havuz_Iliskisi 
                        (ders_instance, ders_adi, bolum_num, havuz_kodu)
                        VALUES (?, ?, ?, ?)
                    """, (ders_instance, course_name, bolum_num, havuz_kodu))
                    inserted += 1
                except sqlite3.IntegrityError:
                    # Duplicate - already exists
                    skipped += 1
            else:
                # Course not in Dersler table
                skipped += 1

conn.commit()
print(f"\n✅ Migration Complete!")
print(f"   Inserted: {inserted} pool relationships")
print(f"   Skipped: {skipped} (duplicates or missing courses)")

# Show sample data
c.execute("""
    SELECT D.ders_adi, B.bolum_adi, D.havuz_kodu
    FROM Ders_Havuz_Iliskisi D
    JOIN Bolumler B ON D.bolum_num = B.bolum_num
    LIMIT 10
""")

print("\nSample pool relationships:")
for row in c.fetchall():
    print(f"  {row[0]} | {row[1]} | {row[2]}")

conn.close()
