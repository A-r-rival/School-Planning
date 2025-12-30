import sqlite3

def check_dersler():
    conn = sqlite3.connect('okul_veritabani.db')
    c = conn.cursor()
    
    print("--- Dersler Table Columns ---")
    c.execute("PRAGMA table_info(Dersler)")
    for r in c.fetchall():
        print(f"Name: {r[1]} | Type: {r[2]}")

if __name__ == "__main__":
    check_dersler()
