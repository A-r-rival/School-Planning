import sqlite3

def check_schema():
    conn = sqlite3.connect('okul_veritabani.db')
    c = conn.cursor()
    
    print("--- Ders_Programi Columns ---")
    c.execute("PRAGMA table_info(Ders_Programi)")
    for r in c.fetchall():
        print(f"CID: {r[0]} | Name: {r[1]} | Type: {r[2]}")
        
    print("\n--- Bolumler Columns ---")
    c.execute("PRAGMA table_info(Bolumler)")
    for r in c.fetchall():
        print(f"CID: {r[0]} | Name: {r[1]} | Type: {r[2]} | PK: {r[5]}")

if __name__ == "__main__":
    check_schema()
