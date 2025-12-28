import sqlite3

conn = sqlite3.connect('okul_veritabani.db')
c = conn.cursor()

# Check full schema with sample data
c.execute("PRAGMA table_info(Ders_Programi)")
print("=== Ders_Programi Schema ===")
for col in c.fetchall():
    print(f"  {col[1]} ({col[2]})")

print("\n=== Full Sample Data ===")
c.execute("SELECT * FROM Ders_Programi LIMIT 5")
for i, row in enumerate(c.fetchall(), 1):
    print(f"{i}. {row}")

# Count by seçmeli in name
c.execute("SELECT COUNT(*) FROM Ders_Programi WHERE LOWER(ders_adi) LIKE '%seçmeli%'")
print(f"\n'Seçmeli' in name: {c.fetchone()[0]} courses")

# Total
c.execute("SELECT COUNT(*) FROM Ders_Programi")
print(f"Total courses: {c.fetchone()[0]}")

conn.close()
