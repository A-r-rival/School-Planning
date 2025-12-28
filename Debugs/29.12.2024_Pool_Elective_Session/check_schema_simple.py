import sqlite3

conn = sqlite3.connect('okul_veritabani.db')
c = conn.cursor()

# Find schedule table
c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%program%'")
table = c.fetchone()

if table:
    table_name = table[0]
    print(f"=== {table_name} ===\n")
    
    # Get schema
    c.execute(f"PRAGMA table_info({table_name})")
    cols = c.fetchall()
    print("Columns:")
    for col in cols:
        print(f"  {col[1]} ({col[2]})")
    
    # Total count
    c.execute(f"SELECT COUNT(*) FROM {table_name}")
    print(f"\nTotal entries: {c.fetchone()[0]}")
    
    # Sample data
    c.execute(f"SELECT * FROM {table_name} LIMIT 3")
    print("\nSample data:")
    for row in c.fetchall():
        print(f"  {row}")
else:
    print("No program table found")

conn.close()
