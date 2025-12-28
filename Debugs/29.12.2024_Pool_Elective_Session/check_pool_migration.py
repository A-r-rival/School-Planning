# Quick check: How many pool relationships were created?
import sqlite3

conn = sqlite3.connect('okul_veritabani.db')
c = conn.cursor()

# Count total
c.execute("SELECT COUNT(*) FROM Ders_Havuz_Iliskisi")
total = c.fetchone()[0]
print(f"Total pool relationships: {total}")

# Count by pool
c.execute("""
    SELECT havuz_kodu, COUNT(*) 
    FROM Ders_Havuz_Iliskisi 
    GROUP BY havuz_kodu 
    ORDER BY COUNT(*) DESC
""")

print("\nBy pool type:")
for pool, count in c.fetchall():
    print(f"  {pool}: {count} courses")

# Sample cross-department courses
c.execute("""
    SELECT ders_adi, COUNT(DISTINCT bolum_num) as dept_count, GROUP_CONCAT(DISTINCT havuz_kodu) as pools
    FROM Ders_Havuz_Iliskisi
    GROUP BY ders_adi
    HAVING dept_count > 1
    LIMIT 5
""")

print("\nSample cross-department electives:")
for name, dept_count, pools in c.fetchall():
    print(f"  {name}: {dept_count} depts, pools: {pools}")

conn.close()
