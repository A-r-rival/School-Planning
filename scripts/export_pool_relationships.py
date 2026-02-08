import sqlite3

import os
db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'database', 'okul_veritabani.db')
conn = sqlite3.connect(db_path)
c = conn.cursor()

output_file = 'pool_course_relationships.txt'

# Get all pool relationships with department info
c.execute("""
    SELECT B.bolum_adi, D.havuz_kodu, D.ders_adi
    FROM Ders_Havuz_Iliskisi D
    JOIN Bolumler B ON D.bolum_id = B.bolum_id
    ORDER BY B.bolum_adi, D.havuz_kodu, D.ders_adi
""")

relationships = c.fetchall()

# Write to file
with open(output_file, 'w', encoding='utf-8') as f:
    f.write("=" * 80 + "\n")
    f.write("HAVUZ - DERS İLİŞKİLERİ\n")
    f.write("=" * 80 + "\n\n")
    
    # Count totals
    c.execute("SELECT COUNT(*) FROM Ders_Havuz_Iliskisi")
    total = c.fetchone()[0]
    
    c.execute("SELECT COUNT(DISTINCT bolum_id) FROM Ders_Havuz_Iliskisi")
    dept_count = c.fetchone()[0]
    
    c.execute("SELECT COUNT(DISTINCT havuz_kodu) FROM Ders_Havuz_Iliskisi")
    pool_count = c.fetchone()[0]
    
    f.write(f"Toplam: {total} ilişki\n")
    f.write(f"Bölüm Sayısı: {dept_count}\n")
    f.write(f"Havuz Sayısı: {pool_count}\n\n")
    f.write("=" * 80 + "\n\n")
    
    # Group by department
    current_dept = None
    current_pool = None
    
    for dept_name, pool_code, course_name in relationships:
        # New department
        if dept_name != current_dept:
            current_dept = dept_name
            current_pool = None
            f.write(f"\n{'=' * 80}\n")
            f.write(f"{dept_name}\n")
            f.write(f"{'=' * 80}\n")
        
        # New pool within department
        if pool_code != current_pool:
            current_pool = pool_code
            # Count courses in this pool for this dept
            c.execute("""
                SELECT COUNT(*) 
                FROM Ders_Havuz_Iliskisi D
                JOIN Bolumler B ON D.bolum_id = B.bolum_id
                WHERE B.bolum_adi = ? AND D.havuz_kodu = ?
            """, (dept_name, pool_code))
            pool_course_count = c.fetchone()[0]
            
            f.write(f"\n  [{pool_code}] - {pool_course_count} ders\n")
            f.write(f"  {'-' * 76}\n")
        
        # Write course
        f.write(f"    • {course_name}\n")

conn.close()

print(f"✅ Pool-ders ilişkileri yazıldı: {output_file}")
print(f"   Toplam {total} ilişki, {dept_count} bölüm, {pool_count} havuz")
