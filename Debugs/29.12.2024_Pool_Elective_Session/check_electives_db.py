import sqlite3

conn = sqlite3.connect('okul_veritabani.db')
c = conn.cursor()

# Find schedule table
c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%program%'")
table = c.fetchone()

if table:
    table_name = table[0]
    print(f"Schedule table: {table_name}\n")
    
    # Total courses
    c.execute(f"SELECT COUNT(*) FROM {table_name}")
    total = c.fetchone()[0]
    print(f"Total courses: {total}")
    
    # Electives (check multiple patterns)
    c.execute(f"""
        SELECT COUNT(*) FROM {table_name} 
        WHERE LOWER(ders_adi) LIKE '%seçmeli%' 
           OR LOWER(ders_kodu) LIKE 'sdi%' 
           OR LOWER(ders_kodu) LIKE 'gsd%'
           OR LOWER(ders_kodu) LIKE 'zsd%'
    """)
    elective_count = c.fetchone()[0]
    print(f"Elective courses: {elective_count}")
    
    if elective_count > 0:
        # Sample electives
        c.execute(f"""
            SELECT ders_kodu, ders_adi, gun, slot_baslangic 
            FROM {table_name} 
            WHERE LOWER(ders_adi) LIKE '%seçmeli%' 
               OR LOWER(ders_kodu) LIKE 'sdi%'
            LIMIT 5
        """)
        print("\nSample electives:")
        for row in c.fetchall():
            print(f"  [{row[0]}] {row[1]} - {row[2]} {row[3]}")
    else:
        print("\n❌ NO ELECTIVES IN DATABASE!")
        # Check schema
        c.execute(f"PRAGMA table_info({table_name})")
        print("\nTable schema:")
        for col in c.fetchall():
            print(f"  {col[1]} ({col[2]})")
else:
    print("❌ No schedule table found!")

conn.close()
