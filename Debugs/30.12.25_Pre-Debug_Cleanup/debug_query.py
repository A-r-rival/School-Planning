
import sys
import os
sys.path.append(os.getcwd())
from models.schedule_model import ScheduleModel

def test_query():
    print("Testing SQL Query...")
    model = ScheduleModel()
    
    query = '''
            SELECT 
                d.ders_adi, 
                d.ders_instance, 
                d.teori_odasi, 
                d.lab_odasi,
                d.teori_saati,
                d.uygulama_saati,
                d.lab_saati,
                d.akts,
                doi.ogretmen_id,
                dsi.donem_sinif_num
            FROM Dersler d
            LEFT JOIN Ders_Ogretmen_Iliskisi doi ON d.ders_adi = doi.ders_adi AND d.ders_instance = doi.ders_instance
            LEFT JOIN Ders_Sinif_Iliskisi dsi ON d.ders_adi = dsi.ders_adi AND d.ders_instance = dsi.ders_instance
        '''
    
    try:
        model.c.execute(query)
        rows = model.c.fetchall()
        print(f"Query executed successfully. Fetched {len(rows)} rows.")
        if rows:
            print(f"First row: {rows[0]}")
    except Exception as e:
        print(f"Query FAILED: {e}")

if __name__ == "__main__":
    test_query()
