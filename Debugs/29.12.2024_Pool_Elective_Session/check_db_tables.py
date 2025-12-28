import sqlite3

conn = sqlite3.connect('school_schedule.db')
c = conn.cursor()

# List all tables
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = c.fetchall()

print("=== TABLES IN DATABASE ===")
for table in tables:
    print(f"  - {table[0]}")

# Find schedule table
schedule_table = None
for table in tables:
    if 'program' in table[0].lower() or 'schedule' in table[0].lower():
        schedule_table = table[0]
        break

if schedule_table:
    print(f"\n=== SCHEDULE TABLE: {schedule_table} ===")
    c.execute(f"SELECT COUNT(*) FROM {schedule_table}")
    total = c.fetchone()[0]
    print(f"Total entries: {total}")
    
    # Sample data
    c.execute(f"SELECT * FROM {schedule_table} LIMIT 5")
    print("\nSample entries:")
    for row in c.fetchall():
        print(f" {row}")

conn.close()
