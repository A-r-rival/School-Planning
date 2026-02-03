import sqlite3
conn = sqlite3.connect('okul_veritabani.db')
conn.row_factory = sqlite3.Row

with open('results.txt', 'w', encoding='utf-8') as f:
    f.write("=== SEARCHING FOR 'Seçmeli' IN DERSLER ===\n")
    rows = conn.execute("SELECT * FROM Dersler WHERE ders_adi LIKE '%Seçmeli%'").fetchall()
    for r in rows:
        f.write(str(dict(r)) + "\n")

    f.write("\n=== SAMPLE DERS_SINIF_ILISKISI ===\n")
    rows = conn.execute("SELECT * FROM Ders_Sinif_Iliskisi LIMIT 100").fetchall()
    for r in rows:
        f.write(str(dict(r)) + "\n")

conn.close()
