import sqlite3

conn = sqlite3.connect('okul_veritabani.db')
c = conn.cursor()

# Find all "placeholder" pool courses
c.execute("""
    SELECT DISTINCT ders_adi 
    FROM Ders_Programi 
    WHERE ders_adi LIKE '%Havuz%' 
       OR ders_adi LIKE '%Pool%'
       OR ders_adi LIKE '%Uzmanlık%'
    ORDER BY ders_adi
""")

placeholders = c.fetchall()

print("=" * 60)
print("PLACEHOLDER POOL COURSES IN SCHEDULE")
print("=" * 60)
print(f"Total: {len(placeholders)}\n")

for p in placeholders:
    # Count how many times each appears
    c.execute("SELECT COUNT(*) FROM Ders_Programi WHERE ders_adi = ?", (p[0],))
    count = c.fetchone()[0]
    print(f"{count:3}x  {p[0]}")

# Check Dersler table for actual electives
print("\n" + "=" * 60)
print("ACTUAL ELECTIVE COURSES IN DERSLER TABLE")
print("=" * 60)

c.execute("""
    SELECT ders_adi 
    FROM Dersler 
    WHERE LOWER(ders_adi) LIKE '%seçmeli%'
       AND ders_adi NOT LIKE '%Havuz%'
       AND ders_adi NOT LIKE '%Pool%'
    LIMIT 10
""")

actual_electives = c.fetchall()
print(f"Sample actual electives ({len(actual_electives)} shown):\n")
for e in actual_electives:
    print(f"  - {e[0]}")

conn.close()
