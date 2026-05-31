import sqlite3
import pprint

def test_query():
    conn = sqlite3.connect('database/okul_veritabani.db')
    c = conn.cursor()
    
    # We want to know for each department (Bolumler), what courses belong to it and under which "category" (1. Sınıf, ZSDII, etc.)
    # Category 1: Regular classes (Ders_Sinif_Iliskisi)
    query_regular = """
        SELECT b.bolum_adi, od.sinif_duzeyi || '. Sınıf' as category, d.ders_adi, d.ders_instance
        FROM Bolumler b
        JOIN Ogrenci_Donemleri od ON b.bolum_id = od.bolum_num
        JOIN Ders_Sinif_Iliskisi dsi ON od.donem_sinif_num = dsi.donem_sinif_num
        JOIN Dersler d ON dsi.ders_adi = d.ders_adi AND dsi.ders_instance = d.ders_instance
    """
    c.execute(query_regular)
    regular = c.fetchall()
    
    # Category 2: Pool courses (Ders_Havuz_Iliskisi)
    query_pool = """
        SELECT b.bolum_adi, dhi.havuz_kodu as category, d.ders_adi, d.ders_instance
        FROM Bolumler b
        JOIN Ders_Havuz_Iliskisi dhi ON b.bolum_id = dhi.bolum_id
        JOIN Dersler d ON dhi.ders_adi = d.ders_adi AND dhi.ders_instance = d.ders_instance
    """
    c.execute(query_pool)
    pools = c.fetchall()
    
    results = {}
    for r in regular + pools:
        dept, cat, c_name, c_inst = r
        if dept not in results:
            results[dept] = {}
        if cat not in results[dept]:
            results[dept][cat] = []
        results[dept][cat].append((c_name, c_inst))
        
    for dept, cats in list(results.items())[:2]:
        print(f"--- {dept} ---")
        for cat, courses in cats.items():
            print(f"  {cat}: {len(courses)} courses")
            
    conn.close()

if __name__ == '__main__':
    test_query()
