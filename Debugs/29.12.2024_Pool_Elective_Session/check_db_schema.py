import sqlite3

conn = sqlite3.connect('okul_veritabani.db')
c = conn.cursor()

# List all tables
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in c.fetchall()]

print("=== DATABASE SCHEMA ===")
print(f"Tables: {', '.join(tables)}\n")

# Check Dersler table for elective/pool info
if "Dersler" in tables:
    print("=== Dersler Table ===")
    c.execute("PRAGMA table_info(Dersler)")
    cols = c.fetchall()
    print("Columns:")
    for col in cols:
        print(f"  {col[1]} ({col[2]})")
    print()

# Check Ders_Sinif_Iliskisi for cross-department elective info
if "Ders_Sinif_Iliskisi" in tables:
    print("=== Ders_Sinif_Iliskisi Table ===")
    c.execute("PRAGMA table_info(Ders_Sinif_Iliskisi)")
    cols = c.fetchall()
    print("Columns:")
    for col in cols:
        print(f"  {col[1]} ({col[2]})")
    print()
    
    # Sample data
    c.execute("SELECT * FROM Ders_Sinif_Iliskisi LIMIT 5")
    print("Sample data:")
    for row in c.fetchall():
        print(f"  {row}")

# Check if there's pool/elective type info anywhere
for table in tables:
    c.execute(f"PRAGMA table_info({table})")
    cols = [col[1] for col in c.fetchall()]
    if any('pool' in col.lower() or 'elective' in col.lower() or 'seçmeli' in col.lower() for col in cols):
        print(f"\n=== {table} (has pool/elective column) ===")
        print(f"Columns: {', '.join(cols)}")

conn.close()
