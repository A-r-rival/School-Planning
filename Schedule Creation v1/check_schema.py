
import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'okul_veritabani.db')
conn = sqlite3.connect(db_path)
c = conn.cursor()

print("Checking Ders_Ogretmen_Iliskisi schema...")
try:
    c.execute("PRAGMA table_info(Ders_Ogretmen_Iliskisi)")
    columns = c.fetchall()
    print("Columns found:")
    col_names = [col[1] for col in columns]
    for col in columns:
        print(col)
        
    if 'ogretmen_id' not in col_names:
        print("Column 'ogretmen_id' NOT FOUND!")
        print("Dropping table to force recreation...")
        c.execute("DROP TABLE Ders_Ogretmen_Iliskisi")
        conn.commit()
        print("Table dropped.")
    else:
        print("Schema looks correct.")
        
except Exception as e:
    print(f"Error: {e}")

conn.close()
