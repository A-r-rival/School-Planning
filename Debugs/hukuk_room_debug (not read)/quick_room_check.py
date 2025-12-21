# Quick diagnostic to find the saturation issue
import sqlite3

conn = sqlite3.connect('okul_veritabani.db')
c = conn.cursor()

# Get room saturation
c.execute('''
    SELECT ders_adi, ders_instance, teori_odasi, lab_odasi
    FROM Dersler
    WHERE teori_odasi IS NOT NULL OR lab_odasi IS NOT NULL
''')
courses = c.fetchall()

room_counts = {}
for ders_adi, instance, teori, lab in courses:
    room = teori if teori else lab
    if room:
        room_counts[room] = room_counts.get(room, 0) + 1

print("\n=== ROOM SATURATION ANALYSIS ===\n")
print(f"Total courses with fixed rooms: {len(courses)}")
print(f"\nTop saturated rooms:")

# Sort by count
sorted_rooms = sorted(room_counts.items(), key=lambda x: x[1], reverse=True)

for room_id, count in sorted_rooms[:15]:  # Top 15
    # Get room name
    c.execute('SELECT derslik_adi FROM Derslikler WHERE derslik_num = ?', (room_id,))
    result = c.fetchone()
    room_name = result[0] if result else f"Room #{room_id}"
    
    saturation_pct = (count / 40) * 100  # 40 slots per week
    status = "❌ CRITICAL" if saturation_pct > 75 else ("⚠️ HIGH" if saturation_pct > 50 else "✓ OK")
    print(f"  {room_name}: {count} courses ({saturation_pct:.1f}%) {status}")

conn.close()
