import sqlite3

conn = sqlite3.connect('school_schedule.db')
c = conn.cursor()

# Find schedule table name
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in c.fetchall()]
print(f"Tables: {tables}\n")

# Find schedule/program table
schedule_table = None
for t in tables:
    if 'program' in t.lower() or 'schedule' in t.lower() or 'ders' in t.lower():
        schedule_table = t
        print(f"Found schedule table: {schedule_table}")
        
        # Show schema
        c.execute(f"PRAGMA table_info({schedule_table})")
        columns = c.fetchall()
        print(f"\nColumns in {schedule_table}:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        # Sample data
        c.execute(f"SELECT * FROM {schedule_table} LIMIT 3")
        print(f"\nSample data:")
        for row in c.fetchall():
            print(f"  {row}")
        
        break

# Check Dersler table for pool info
if "Dersler" in tables:
    print(f"\n=== Dersler Table ===")
    c.execute("PRAGMA table_info(Dersler)")
    columns = c.fetchall()
    print("Columns:")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
    
    # Check for elective courses
    c.execute("SELECT ders_kodu, ders_adi FROM Dersler WHERE ders_adi LIKE '%Seçmeli%' LIMIT 5")
    print("\nSample elective courses:")
    for row in c.fetchall():
        print(f"  [{row[0]}] {row[1]}")

conn.close()
