import sqlite3

def query_schedule(dept, grade, term):
    conn = sqlite3.connect('database/okul_veritabani.db')
    c = conn.cursor()
    
    # Check what courses are in Ders_Sinif_Iliskisi for this dept/grade/term
    print(f"--- Ders_Sinif_Iliskisi for {dept} Year {grade} {term} ---")
    c.execute('''
        SELECT dsi.ders_adi, dsi.ders_instance 
        FROM Ders_Sinif_Iliskisi dsi
        JOIN Ogrenci_Donemleri od ON dsi.donem_sinif_num = od.donem_sinif_num
        JOIN Bolumler b ON od.bolum_num = b.bolum_id
        WHERE b.bolum_adi LIKE ? AND od.sinif_duzeyi = ? AND od.semester_season = ?
    ''', (f'%{dept}%', grade, term))
    courses = c.fetchall()
    for row in courses:
        print(f"  {row[0]} (Inst {row[1]})")
        
    print(f"\n--- SCHEDULED COURSES (Ders_Programi) ---")
    # For each of these courses, check if they are in Ders_Programi
    for row in courses:
        c.execute('''
            SELECT ders_adi, ders_instance, gun, baslangic, bitis
            FROM Ders_Programi
            WHERE ders_adi = ? AND ders_instance = ?
        ''', (row[0], row[1]))
        scheds = c.fetchall()
        for s in scheds:
            print(f"  SCHEDULED: {s[0]} ({s[1]}) -> {s[2]} {s[3]}-{s[4]}")
            
    # Also check electives from Havuz
    print(f"\n--- POOL ELECTIVES SCHEDULED ---")
    c.execute('''
        SELECT p.ders_adi, p.ders_instance, h.havuz_kodu, p.gun, p.baslangic, p.bitis
        FROM Ders_Programi p
        JOIN Ders_Havuz_Iliskisi h ON p.ders_adi = h.ders_adi AND p.ders_instance = h.ders_instance
        JOIN Bolumler b ON h.bolum_id = b.bolum_id
        WHERE b.bolum_adi LIKE ? AND (h.sinif_duzeyi = ? OR h.sinif_duzeyi = 0)
    ''', (f'%{dept}%', grade))
    pool_scheds = c.fetchall()
    for s in pool_scheds:
        print(f"  POOL SCHEDULED: {s[2]} -> {s[0]} ({s[1]}) -> {s[3]} {s[4]}-{s[5]}")

    conn.close()

if __name__ == '__main__':
    query_schedule('Bilgisayar Müh', 4, 'Bahar')
