import sqlite3
conn = sqlite3.connect('okul_veritabani.db')
conn.row_factory = sqlite3.Row

print("=== BOLUMLER ===")
for row in conn.execute("SELECT * FROM Bolumler"):
    print(dict(row))

print("=== DERS_SINIF_ILISKISI (Subset) ===")
for row in conn.execute("SELECT * FROM Ders_Sinif_Iliskisi LIMIT 50"):
    print(dict(row))

print("\n=== DERSLERE BAGLI HAVUZLAR (Sample) ===")
query = """
    SELECT d.ders_adi, dhi.havuz_kodu, b.bolum_adi
    FROM Ders_Havuz_Iliskisi dhi
    JOIN Bolumler b ON dhi.bolum_num = b.bolum_id
    JOIN Dersler d ON dhi.ders_adi = d.ders_adi AND dhi.ders_instance = d.ders_instance
    LIMIT 20
"""
for row in conn.execute(query):
    print(dict(row))

conn.close()
