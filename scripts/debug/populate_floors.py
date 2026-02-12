"""
Distribute rooms across floors 0, 1, 2.

Distribution logic:
- Amfi (4): All on Floor 0 (ground floor, large halls, accessible)
- Lab (10): Split between Floor 0 (5) and Floor 1 (5)
- Derslik (64): ~21 per floor
  - Derslik 1-21 -> Floor 0 (21 rooms)
  - Derslik 22-43 -> Floor 1 (22 rooms) 
  - Derslik 44-64 -> Floor 2 (21 rooms)

Result:
  Floor 0: 4 Amfi + 21 Derslik + 5 Lab = 30 rooms
  Floor 1: 22 Derslik + 5 Lab = 27 rooms
  Floor 2: 21 Derslik = 21 rooms
"""
import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True, errors='replace')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from models.schedule_model import ScheduleModel
m = ScheduleModel()

# Get all active rooms
m.c.execute("SELECT derslik_num, derslik_adi, derslik_tipi FROM Derslikler WHERE silindi=0 ORDER BY derslik_adi")
rooms = m.c.fetchall()

updates = []

for r in rooms:
    r_id, r_name, r_type = r
    
    if r_type == 'Amfi':
        # Amfis span 2 floors: entrance at floor 0 or floor 2
        # Split Amfis: Amfi-1, Amfi-2 -> floor 0, Amfi-3, Amfi-4 -> floor 2
        num = int(r_name.split('-')[1])
        floor = 0 if num <= 2 else 2
    elif r_type == 'Laboratuvar':
        # Distribute labs across all floors: 3-4-3 distribution
        num = int(r_name.split('-')[1])
        if num <= 3:
            floor = 0  # Lab-1, Lab-2, Lab-3 on Floor 0
        elif num <= 7:
            floor = 1  # Lab-4, Lab-5, Lab-6, Lab-7 on Floor 1
        else:
            floor = 2  # Lab-8, Lab-9, Lab-10 on Floor 2
    elif r_type == 'Derslik':
        # Extract derslik number
        num = int(r_name.split('-')[1])
        if num <= 21:
            floor = 0
        elif num <= 43:
            floor = 1
        else:
            floor = 2
    else:
        floor = 0  # fallback
    
    updates.append((floor, r_id))

# Apply updates
m.c.executemany("UPDATE Derslikler SET floor = ? WHERE derslik_num = ?", updates)
m.conn.commit()

# Verify
m.c.execute("SELECT floor, COUNT(*) FROM Derslikler WHERE silindi=0 GROUP BY floor ORDER BY floor")
results = m.c.fetchall()
print("=== FLOOR DISTRIBUTION AFTER UPDATE ===")
total = 0
for f, cnt in results:
    print(f"  Floor {f}: {cnt} rooms")
    total += cnt
print(f"  Total: {total} rooms")

# Show a few examples per floor
for f in [0, 1, 2]:
    m.c.execute("SELECT derslik_adi, derslik_tipi FROM Derslikler WHERE silindi=0 AND floor=? ORDER BY derslik_adi LIMIT 5", (f,))
    examples = m.c.fetchall()
    print(f"\n  Floor {f} examples: {', '.join(r[0] + ' (' + r[1] + ')' for r in examples)}")

print("\nDone!")
