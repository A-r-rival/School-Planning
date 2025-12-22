import sqlite3

try:
    conn = sqlite3.connect('okul_veritabani.db')
    c = conn.cursor()
    
    # 1. Check table existence
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Ogretmen_Musaitlik'")
    table = c.fetchone()
    
    if not table:
        print("TABLE 'Ogretmen_Musaitlik' DOES NOT EXIST!")
    else:
        print("Table 'Ogretmen_Musaitlik' exists.")
        
        # 2. Check data count
        c.execute("SELECT count(*) FROM Ogretmen_Musaitlik")
        count = c.fetchone()[0]
        print(f"Total rows in Ogretmen_Musaitlik: {count}")
        
        # 3. Show sample data
        if count > 0:
            print("\nSample Data:")
            c.execute("SELECT * FROM Ogretmen_Musaitlik LIMIT 5")
            for row in c.fetchall():
                print(row)
        else:
            print("\nTable is empty. No constraints have been added.")

    conn.close()

except Exception as e:
    print(f"Error: {e}")
