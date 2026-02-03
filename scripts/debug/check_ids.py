import sqlite3
conn = sqlite3.connect('okul_veritabani.db')
conn.row_factory = sqlite3.Row

print("=== DEPARTMENTS IDs CHECK ===")
for r in conn.execute("SELECT bolum_id, bolum_num, bolum_adi FROM Bolumler"):
    print(dict(r))

print("\n=== DERS_HAVUZ_ILISKISI BOLUM_NUM CHECK ===")
# Check which bolum_nums are used in pools
pool_bolums = conn.execute("SELECT DISTINCT bolum_num FROM Ders_Havuz_Iliskisi").fetchall()
for pb in pool_bolums:
    print(f"Pool for bolum_num: {pb['bolum_num']}")

print("\n=== SEARCHING FOR ANALIZ I IN SINIF ILISKISI FOR COMP ENG ===")
comp_bolum = conn.execute("SELECT * FROM Bolumler WHERE bolum_adi LIKE '%Bilgisayar%'").fetchone()
if comp_bolum:
    b_id = comp_bolum['bolum_id']
    print(f"Bilgisayar PK (bolum_id): {b_id}, Local (bolum_num): {comp_bolum['bolum_num']}")
    
    rows = conn.execute("""
        SELECT dsi.*, od.bolum_num as od_bolum_num
        FROM Ders_Sinif_Iliskisi dsi
        JOIN Ogrenci_Donemleri od ON dsi.donem_sinif_num = od.donem_sinif_num
        WHERE od.bolum_num = ? AND dsi.ders_adi LIKE '%Analiz%'
    """, (b_id,)).fetchall()
    
    print(f"Analiz rows found: {len(rows)}")
    for r in rows:
        print(dict(r))

conn.close()
