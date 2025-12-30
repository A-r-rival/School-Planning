import sqlite3

def check_9am_conflict():
    conn = sqlite3.connect('okul_veritabani.db')
    c = conn.cursor()
    
    print("Checking 09:00 schedule for Room ID 3...")
    
    query = """
        SELECT dp.gun, dp.ders_adi, o.ad, o.soyad
        FROM Ders_Programi dp
        JOIN Dersler d ON dp.ders_adi = d.ders_adi AND dp.ders_instance = d.ders_instance
        JOIN Ogretmenler o ON dp.ogretmen_id = o.ogretmen_num
        WHERE (d.teori_odasi = 3 OR d.lab_odasi = 3) 
        AND dp.baslangic = '09:00'
    """
    
    c.execute(query)
    rows = c.fetchall()
    
    if not rows:
        print("No conflicts found at 09:00.")
    else:
        for r in rows:
            print(f"Conflict: {r[0]} - {r[1]} ({r[2]} {r[3]})")

if __name__ == "__main__":
    check_9am_conflict()
