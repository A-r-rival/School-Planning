import sqlite3
import os

def check_data():
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "database", "okul_veritabani.db")
    print(f"Checking DB at: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Check Teachers
    print("\n--- Teachers (Ogretmenler) ---")
    try:
        cursor.execute("SELECT count(*) FROM Ogretmenler")
        count = cursor.fetchone()[0]
        print(f"Total Teachers: {count}")
        
        cursor.execute("SELECT ogretmen_num, ad || ' ' || soyad FROM Ogretmenler ORDER BY ad || ' ' || soyad LIMIT 5")
        rows = cursor.fetchall()
        print("First 5 teachers (Concatenated):")
        for r in rows:
            print(r)
            
        cursor.execute("SELECT ogretmen_num, ad, soyad FROM Ogretmenler LIMIT 1")
        print("Raw columns (1 row):", cursor.fetchone())
        
    except Exception as e:
        print(f"Error querying teachers: {e}")

    # 2. Check Classrooms
    print("\n--- Classrooms (Derslikler) ---")
    try:
        cursor.execute("SELECT count(*) FROM Derslikler")
        count = cursor.fetchone()[0]
        print(f"Total Classrooms: {count}")
        
        cursor.execute("SELECT derslik_num, derslik_adi FROM Derslikler ORDER BY derslik_adi LIMIT 5")
        rows = cursor.fetchall()
        print("First 5 classrooms:")
        for r in rows:
            print(r)
            
    except Exception as e:
        print(f"Error querying classrooms: {e}")
        
    conn.close()

if __name__ == "__main__":
    check_data()
