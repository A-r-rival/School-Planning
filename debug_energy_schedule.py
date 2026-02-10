import sqlite3
import os

def check_schedule():
    db_path = r'd:\Git_Projects\School-Planning\database\okul_veritabani.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get Dept ID
    cursor.execute("SELECT bolum_id FROM Bolumler WHERE bolum_adi LIKE '%Enerji%'")
    dept_id = cursor.fetchone()[0]
    print(f"Dept ID: {dept_id}")

    # Check Schedule for Year 3, 4
    # Join with Ders_Sinif_Iliskisi -> Ogrenci_Donemleri to filter by dept/year
    query = """
    SELECT dp.gun, dp.baslangic, dp.ders_adi, od.sinif_duzeyi
    FROM Ders_Programi dp
    JOIN Ders_Sinif_Iliskisi dsi ON dp.ders_adi = dsi.ders_adi AND dp.ders_instance = dsi.ders_instance
    JOIN Ogrenci_Donemleri od ON dsi.donem_sinif_num = od.donem_sinif_num
    WHERE od.bolum_num = ? AND od.sinif_duzeyi IN (3, 4)
    ORDER BY od.sinif_duzeyi, dp.gun, dp.baslangic
    """
    cursor.execute(query, (dept_id,))
    rows = cursor.fetchall()

    print(f"--- Scheduled Courses for Enerji (Year 3, 4) ---")
    for r in rows:
        print(r)

    conn.close()

if __name__ == "__main__":
    check_schedule()
