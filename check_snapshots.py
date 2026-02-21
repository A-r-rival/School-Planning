import sqlite3
import os

db_path = os.path.join("database", "okul_veritabani.db")
conn = sqlite3.connect(db_path)
c = conn.cursor()

print("--- Snapshots Table Inspection ---")
c.execute("SELECT id, name, created_at FROM Snapshots")
snapshots = c.fetchall()
for s in snapshots:
    print(s)

print("\n--- Snapshot Data Inspection (if any) ---")
for s in snapshots:
    c.execute("SELECT COUNT(*) FROM Snapshot_Data WHERE snapshot_id = ? AND (derslik_id BETWEEN 650 AND 732)", (s[0],))
    count = c.fetchone()[0]
    print(f"Snapshot '{s[1]}' (ID: {s[0]}) has {count} rows with old room IDs.")

conn.close()
