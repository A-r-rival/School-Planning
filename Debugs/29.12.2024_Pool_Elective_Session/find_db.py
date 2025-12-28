import sqlite3
import os

# Find correct db file
db_files = []
for root, dirs, files in os.walk('.'):
    for f in files:
        if f.endswith('.db'):
            db_files.append(os.path.join(root, f))

print(f"Found {len(db_files)} .db files:")
for db in db_files:
    print(f"  {db}")
    size = os.path.getsize(db)
    print(f"    Size: {size:,} bytes")
    
    # Try to connect and check
    try:
        conn = sqlite3.connect(db)
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [t[0] for t in c.fetchall()]
        print(f"    Tables ({len(tables)}): {', '.join(tables[:5])}")
        
        # If has schedule data
        for table in tables:
            if 'program' in table.lower() or 'schedule' in table.lower():
                c.execute(f"SELECT COUNT(*) FROM {table}")
                count = c.fetchone()[0]
                print(f"      {table}: {count} entries")
        
        conn.close()
    except Exception as e:
        print(f"    Error: {e}")
    print()
