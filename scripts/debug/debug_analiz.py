import sqlite3
conn = sqlite3.connect('okul_veritabani.db')
conn.row_factory = sqlite3.Row

print("=== CHECKING ANALIZ FOR COMP ENG (Year 1) ===")
# Comp Eng Dept ID is usually 105 or similar, let's find it
bolum = conn.execute("SELECT * FROM Bolumler WHERE bolum_adi LIKE '%Bilgisayar%'").fetchone()
if bolum:
    b_id = bolum['bolum_id']
    print(f"Bilgisayar Müh ID: {b_id}")
    
    # Get semester/period for Year 1
    donem = conn.execute("SELECT * FROM Ogrenci_Donemleri WHERE bolum_num = ? AND sinif_duzeyi = 1", (b_id,)).fetchone()
    if donem:
        d_id = donem['donem_sinif_num']
        print(f"Year 1 Period ID: {d_id}")
        
        # Check courses for this period
        print(f"\nCourses for {d_id}:")
        courses = conn.execute("SELECT * FROM Ders_Sinif_Iliskisi WHERE donem_sinif_num = ?", (d_id,)).fetchall()
        for c in courses:
            print(dict(c))
            
        # specifically look for Analiz
        analiz = conn.execute("SELECT * FROM Ders_Sinif_Iliskisi WHERE donem_sinif_num = ? AND ders_adi LIKE '%Analiz%'", (d_id,)).fetchall()
        print(f"\nAnaliz entries for CompEng Year 1: {len(analiz)}")
        for a in analiz:
            print(dict(a))

print("\n=== COMPARING WITH ANOTHER DEPT (e.g. Endüstri) ===")
ebolum = conn.execute("SELECT * FROM Bolumler WHERE bolum_adi LIKE '%Endüstri%'").fetchone()
if ebolum:
    eb_id = ebolum['bolum_id']
    edonem = conn.execute("SELECT * FROM Ogrenci_Donemleri WHERE bolum_num = ? AND sinif_duzeyi = 1", (eb_id,)).fetchone()
    if edonem:
        ed_id = edonem['donem_sinif_num']
        print(f"Endüstri Müh Year 1 Period ID: {ed_id}")
        eanaliz = conn.execute("SELECT * FROM Ders_Sinif_Iliskisi WHERE donem_sinif_num = ? AND ders_adi LIKE '%Analiz%'", (ed_id,)).fetchall()
        for a in eanaliz:
            print(dict(a))

conn.close()
