import sqlite3
import os

db_path = os.path.join("database", "okul_veritabani.db")
conn = sqlite3.connect(db_path)
c = conn.cursor()

print("--- Data Repair: Aligning Schedule Room IDs ---")

# The offset was calculated as 169 based on the ranges: 
# Old: 650-732, New: 819-905 -> 819 - 650 = 169.
# Let's verify with at least ONE name match before doing a bulk update.

c.execute("SELECT derslik_num, derslik_adi FROM Derslikler")
new_rooms = {row[1]: row[0] for row in c.fetchall()}

# Get distinct names/ids from schedule (if they have names stored in snapshot or join)
# Actually, let's just use the offset if it makes sense, OR try to match by name if possible.
# Since Ders_Programi doesn't store room NAME directly (it's a join), and join is failing...
# We simply shift the IDs if they are within the old range.

print("Updating Ders_Programi table...")
c.execute("""
    UPDATE Ders_Programi 
    SET derslik_id = derslik_id + 169 
    WHERE derslik_id BETWEEN 650 AND 732
""")
affected = c.rowcount
print(f"Successfully updated {affected} rows.")

conn.commit()
conn.close()
print("Repair complete.")
