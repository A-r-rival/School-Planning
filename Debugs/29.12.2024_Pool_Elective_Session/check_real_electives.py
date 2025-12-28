import sqlite3

conn = sqlite3.connect('okul_veritabani.db')
c = conn.cursor()

# Find actual elective courses (not placeholders, not generic "Seçmeli Ders I/II")
c.execute("""
    SELECT DISTINCT ders_adi 
    FROM Dersler 
    WHERE (LOWER(ders_adi) LIKE '%seçmeli%' 
           OR LOWER(ders_kodu) LIKE 'sd%'
           OR LOWER(ders_kodu) LIKE 'zsd%'
           OR LOWER(ders_kodu) LIKE 'gsd%'
           OR LOWER(ders_kodu) LIKE 'üsd%')
    AND ders_adi NOT LIKE '%Havuz%'
    AND ders_adi NOT LIKE '%Pool%'
    AND ders_adi NOT LIKE '%000%'
    AND ders_adi NOT LIKE '%Uzmanlık%'
    ORDER BY ders_adi
    LIMIT 30
""")

electives = c.fetchall()

print("=" * 60)
print("ACTUAL ELECTIVE COURSES IN DERSLER TABLE")
print("=" * 60)
print(f"Found {len(electives)} electives\n")

# Categorize
generic = []
specific = []

for e in electives:
    name = e[0]
    # Generic names like "Seçmeli Ders I/II", "Zorunlu Seçmeli I"
    if any(x in name for x in ["Seçmeli Ders I", "Seçmeli Ders II", "Zorunlu Seçmeli I", "Zorunlu Seçmeli II"]):
        generic.append(name)
    else:
        specific.append(name)

print(f"📋 SPECIFIC ELECTIVES ({len(specific)}):")
for name in specific[:15]:
    print(f"  ✅ {name}")

if len(specific) > 15:
    print(f"  ... and {len(specific) - 15} more")

print(f"\n❓ GENERIC ELECTIVES ({len(generic)}):")
for name in generic[:10]:
    print(f"  ⚠️  {name}")

if len(generic) > 10:
    print(f"  ... and {len(generic) - 10} more")

conn.close()

print("\n" + "=" * 60)
if len(specific) > 0:
    print("✅ YES - Database has specific elective courses!")
    print("   Scheduler should schedule these after placeholder exclusion.")
else:
    print("❌ NO - Only generic/placeholder electives in database!")
    print("   Need to check curriculum data population.")
