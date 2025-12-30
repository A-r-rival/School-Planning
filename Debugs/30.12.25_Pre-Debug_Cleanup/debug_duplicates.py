import sqlite3
import sys

def check_duplicates():
    conn = sqlite3.connect('okul_veritabani.db')
    c = conn.cursor()
    
    with open('duplicates_output.txt', 'w', encoding='utf-8') as f:
        f.write("--- Searching for Machine Learning ---\n")
        query = """
            SELECT dp.program_id, dp.ders_adi, dp.gun, dp.baslangic, dp.bitis, dp.ders_tipi, d.ders_kodu, d.ders_instance
            FROM Ders_Programi dp
            LEFT JOIN Dersler d ON dp.ders_adi = d.ders_adi AND dp.ders_instance = d.ders_instance
            WHERE dp.ders_adi LIKE '%Machine%' OR dp.ders_adi LIKE '%Makine Öğrenmesi%'
        """
        c.execute(query)
        rows = c.fetchall()
        
        if not rows:
            f.write("No matches found.\n")
            
        for r in rows:
            f.write(f"ID: {r[0]} | Name: {r[1]} | Day: {r[2]} | Time: {r[3]}-{r[4]} | Type: {r[5]} | Code: {r[6]} | Inst: {r[7]}\n")

if __name__ == "__main__":
    check_duplicates()
