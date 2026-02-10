import sqlite3
import os

def compare_schedules():
    db_path = r'd:\Git_Projects\School-Planning\database\okul_veritabani.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    def get_scheduled(dept_name_part):
        cursor.execute("SELECT bolum_id, bolum_adi FROM Bolumler WHERE bolum_adi LIKE ?", (f'%{dept_name_part}%',))
        res = cursor.fetchone()
        if not res: return [], "Not Found"
        dept_id, name = res
        
        query = """
        SELECT dp.ders_adi, od.sinif_duzeyi
        FROM Ders_Programi dp
        JOIN Ders_Sinif_Iliskisi dsi ON dp.ders_adi = dsi.ders_adi AND dp.ders_instance = dsi.ders_instance
        JOIN Ogrenci_Donemleri od ON dsi.donem_sinif_num = od.donem_sinif_num
        WHERE od.bolum_num = ? AND od.sinif_duzeyi IN (3, 4)
        """
        cursor.execute(query, (dept_id,))
        return cursor.fetchall(), name

    energy_courses, energy_name = get_scheduled("Enerji")
    comp_courses, comp_name = get_scheduled("Bilgisayar")

    print(f"--- {energy_name} (Year 3, 4) ---")
    print(f"Count: {len(energy_courses)}")
    for c in sorted(list(set(energy_courses))):
         print(f"  {c}")

    print(f"\n--- {comp_name} (Year 3, 4) ---")
    print(f"Count: {len(comp_courses)}")
    for c in sorted(list(set(comp_courses))):
         print(f"  {c}")

    conn.close()

if __name__ == "__main__":
    compare_schedules()
