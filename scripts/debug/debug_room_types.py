import sqlite3
import os

DB_PATH = "okul_veritabani.db"

def inspect_rooms():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    print(f"--- Room Type Inspection ---")
    try:
        # Check column names first to be sure
        cursor = c.execute('select * from Derslikler')
        names = [description[0] for description in cursor.description]
        print(f"Columns: {names}")
        
        # Verify if 'derslik_tipi' or 'tip' is the correct column (Model uses 'derslik_tipi' in aktif_derslikleri_getir)
        c.execute("SELECT derslik_num, derslik_adi, derslik_tipi FROM Derslikler WHERE silindi = 0 ORDER BY derslik_num")
        rows = c.fetchall()
        
        print(f"{'ID':<5} | {'Name':<20} | {'Type String':<20} | {'Is Lab?':<10} | {'Is Amfi?':<10}")
        print("-" * 80)
        
        for r in rows:
            r_id, name, type_str = r
            t_lower = (type_str or "").lower()
            is_lab = "laboratuvar" in t_lower or "lab" in t_lower
            is_amfi = "amfi" in t_lower
            
            print(f"{r_id:<5} | {name:<20} | {str(type_str):<20} | {str(is_lab):<10} | {str(is_amfi):<10}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    inspect_rooms()
