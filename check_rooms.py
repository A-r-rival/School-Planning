import sqlite3

def check_rooms():
    # Connect to the correct database
    import os
    db_path = os.path.join("database", "okul_veritabani.db")
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return
        
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    print("Checking 'Derslikler' table structure...")
    c.execute("PRAGMA table_info(Derslikler)")
    columns = c.fetchall()
    for col in columns:
        print(col)
        
    print("\nChecking Room Data (First 20):")
    try:
        c.execute("SELECT derslik_num, derslik_adi, derslik_tipi, kapasite, floor FROM Derslikler WHERE silindi = 0 LIMIT 20")
        rows = c.fetchall()
        for r in rows:
            print(r)
            
        print("\nChecking Floor Distribution:")
        c.execute("SELECT floor, COUNT(*) FROM Derslikler WHERE silindi=0 GROUP BY floor")
        dist = c.fetchall()
        for d in dist:
            print(f"Floor {d[0]}: {d[1]} rooms")
            
    except Exception as e:
        print(f"Error querying rooms: {e}")
        import traceback
        traceback.print_exc()
        
    conn.close()

if __name__ == "__main__":
    check_rooms()
