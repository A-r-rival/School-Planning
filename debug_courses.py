import sqlite3
import pandas as pd

def check_courses():
    conn = sqlite3.connect('okul_veritabani.db')
    cursor = conn.cursor()
    
    print("\n--- Searching for 'Seçmeli' or 'SD' or 'ZSD' in Dersler ---")
    query = """
    SELECT ders_kodu, ders_adi, ders_instance
    FROM Dersler 
    WHERE ders_adi LIKE '%Seçmeli%' 
       OR ders_kodu LIKE '%SD%' 
       OR ders_kodu LIKE '%ZSD%'
    ORDER BY ders_kodu
    LIMIT 50
    """
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        if not rows:
            print("No matching courses found.")
        for r in rows:
            print(r)
            
    except Exception as e:
        print(f"Error: {e}")
        
    print("\n--- Checking Scheduled Courses (Ders_Programi) ---")
    query = """
    SELECT dp.ders_adi, d.ders_kodu
    FROM Ders_Programi dp
    LEFT JOIN Dersler d ON dp.ders_adi = d.ders_adi AND dp.ders_instance = d.ders_instance
    WHERE dp.ders_adi LIKE '%Seçmeli%' OR d.ders_kodu LIKE '%SD%' LIMIT 20
    """
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        for r in rows:
            print(r)
    except Exception as e:
        print(f"Error: {e}")

    conn.close()

if __name__ == "__main__":
    check_courses()
