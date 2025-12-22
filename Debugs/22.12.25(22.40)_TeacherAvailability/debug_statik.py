import sqlite3

try:
    conn = sqlite3.connect('okul_veritabani.db')
    c = conn.cursor()
    
    # Check Statik course details
    print("Checking 'Statik' courses:")
    c.execute("SELECT ders_adi, ders_kodu, teori_saati, uygulama_saati, lab_saati FROM Dersler WHERE ders_adi LIKE '%Statik%'")
    rows = c.fetchall()
    
    if not rows:
        print("No 'Statik' course found.")
    else:
        print(f"{'Ders Adı':<40} | {'Kod':<10} | {'T':<3} | {'U':<3} | {'L':<3}")
        print("-" * 75)
        for r in rows:
            print(f"{r[0]:<40} | {r[1]:<10} | {r[2]:<3} | {r[3]:<3} | {r[4]:<3}")
    
    print("\nChecking 'Statik' usage in Scheduler (Simulated):")
    # Simulate logic from scheduler.py
    for r in rows:
        u_hours = r[3]
        if u_hours > 0:
            print(f"Course: {r[0]} has {u_hours} hours of Practice (U).")
            # Logic check:
            # If U=2, scheduler creates ONE block of duration 2 -> Must be consecutive
            # If somehow split, then not consecutive.
            
    conn.close()

except Exception as e:
    print(f"Error: {e}")
