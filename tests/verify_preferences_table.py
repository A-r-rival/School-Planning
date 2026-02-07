import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database", "okul_veritabani.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print(f"Checking database at: {db_path}")

try:
    cursor.execute("PRAGMA table_info(Ogretmen_Ders_Tercihleri)")
    columns = cursor.fetchall()
    
    found_note = False
    found_instance = False
    
    print("Columns in Ogretmen_Ders_Tercihleri:")
    for col in columns:
        print(f" - {col[1]} ({col[2]})")
        if col[1] == 'ders_secim_notu':
            found_note = True
        if col[1] == 'ders_instance':
            found_instance = True
            
    if found_note and not found_instance:
        print("\nSUCCESS: 'ders_secim_notu' exists and 'ders_instance' is gone.")
    elif found_instance:
        print("\nFAIL: 'ders_instance' still exists!")
    else:
        print("\nFAIL: 'ders_secim_notu' not found!")
        
except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()
