import sqlite3

def check_db():
    try:
        conn = sqlite3.connect('database/school_schedule.db')
        c = conn.cursor()
        c.execute("""
            SELECT dhi.ders_adi, b.bolum_adi, dhi.sinif_duzeyi, dhi.havuz_kodu 
            FROM Ders_Havuz_Iliskisi dhi
            LEFT JOIN Bolumler b ON dhi.bolum_id = b.bolum_id
            WHERE dhi.ders_adi LIKE '%Öğrenme%' OR dhi.ders_adi LIKE '%Akışkanlar%'
        """)
        rows = c.fetchall()
        
        with open('zsd_db_dump.txt', 'w', encoding='utf-8') as f:
            for r in rows:
                f.write(str(r) + '\n')
                
        # Also check what fetch_course_rows would return
        c.execute("""
            SELECT d.ders_adi, od.sinif_duzeyi, b.bolum_adi
            FROM Dersler d
            JOIN Ders_Havuz_Iliskisi dhi ON d.ders_instance = dhi.ders_instance AND d.ders_adi = dhi.ders_adi
            JOIN Bolumler b ON dhi.bolum_id = b.bolum_id
            JOIN Ogrenci_Donemleri od ON od.bolum_num = b.bolum_id AND od.sinif_duzeyi = dhi.sinif_duzeyi
            WHERE d.ders_adi LIKE '%Öğrenme%' OR d.ders_adi LIKE '%Akışkanlar%'
        """)
        f_rows = c.fetchall()
        with open('zsd_db_dump.txt', 'a', encoding='utf-8') as f:
            f.write('\nFETCHED ROWS:\n')
            for r in f_rows:
                f.write(str(r) + '\n')
    except Exception as e:
        with open('zsd_db_dump.txt', 'w', encoding='utf-8') as f:
            f.write(str(e))

if __name__ == '__main__':
    check_db()
