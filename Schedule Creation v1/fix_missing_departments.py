
import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'okul_veritabani.db')
conn = sqlite3.connect(db_path)
c = conn.cursor()

print("--- Fixing Missing Departments ---")

# 1. Get all faculties
c.execute("SELECT fakulte_num, fakulte_adi FROM Fakulteler")
faculties = c.fetchall()

fixed_count = 0

for f_id, f_name in faculties:
    # Check if has departments
    c.execute("SELECT COUNT(*) FROM Bolumler WHERE fakulte_num = ?", (f_id,))
    d_count = c.fetchone()[0]
    
    if d_count == 0:
        print(f"Faculty '{f_name}' (ID: {f_id}) has NO departments. Creating default...")
        
        # Determine new bolum_id/num
        # We can just pick something safe. Use 1000 + f_id * 10 
        new_id = 1000 + f_id * 10 + 1
        
        try:
            c.execute("""
                INSERT INTO Bolumler (bolum_id, bolum_num, bolum_adi, fakulte_num) 
                VALUES (?, ?, ?, ?)
            """, (new_id, new_id, f_name, f_id))
            print(f"Created Department '{f_name}' with ID {new_id}")
            fixed_count += 1
        except Exception as e:
            print(f"Error creating department: {e}")
            
conn.commit()
print(f"Fixed {fixed_count} faculties.")
conn.close()
