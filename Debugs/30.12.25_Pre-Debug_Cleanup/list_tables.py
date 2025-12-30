import sqlite3
import sys

try:
    conn = sqlite3.connect('school_schedule.db')
    cursor = conn.cursor()
    
    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print("Tables in database:")
    for table in tables:
        print(f"  - {table[0]}")
    
    conn.close()
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
