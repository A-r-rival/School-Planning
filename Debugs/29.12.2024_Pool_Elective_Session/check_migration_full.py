import sqlite3

conn = sqlite3.connect('okul_veritabani.db')
c = conn.cursor()

# Count total relationships
c.execute("SELECT COUNT(*) FROM Ders_Havuz_Iliskisi")
total = c.fetchone()[0]

# Count by pool type
c.execute("""
    SELECT havuz_kodu, COUNT(*) 
    FROM Ders_Havuz_Iliskisi 
    GROUP BY havuz_kodu 
    ORDER BY COUNT(*) DESC
""")
pool_counts = c.fetchall()

# Sample data
c.execute("""
    SELECT D.ders_adi, B.bolum_adi, D.havuz_kodu
    FROM Ders_Havuz_Iliskisi D
    JOIN Bolumler B ON D.bolum_num = B.bolum_num
    LIMIT 10
""")
samples = c.fetchall()

# Cross-department courses
c.execute("""
    SELECT ders_adi, COUNT(DISTINCT bolum_num) as dept_count
    FROM Ders_Havuz_Iliskisi
    GROUP BY ders_adi
    HAVING dept_count > 1
    ORDER BY dept_count DESC
    LIMIT 5
""")
cross_dept = c.fetchall()

print("=" * 60)
print("MIGRATION RESULTS")
print("=" * 60)
print(f"\n✅ Total Pool Relationships: {total}")

print(f"\n📊 By Pool Type:")
for pool, count in pool_counts:
    print(f"   {pool}: {count} courses")

print(f"\n📋 Sample Data:")
for ders, bolum, pool in samples:
    print(f"   {ders[:30]:30} | {bolum[:20]:20} | {pool}")

print(f"\n🔄 Cross-Department Courses (same course, multiple depts):")
for ders, count in cross_dept:
    print(f"   {ders[:40]:40} appears in {count} departments")

conn.close()
