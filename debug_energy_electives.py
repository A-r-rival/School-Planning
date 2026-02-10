import sqlite3

def inspect_db():
    conn = sqlite3.connect('d:/Git_Projects/School-Planning/school_planning.db')
    cursor = conn.cursor()

    # 1. List all tables
    print("--- Tables ---")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    for t in tables:
        print(t[0])

    # 2. Try to find the department with case-insensitive search or just listing all
    print("\n--- Departments containing 'Enerji' ---")
    try:
        cursor.execute("SELECT * FROM Bolumler WHERE name LIKE '%Enerji%'")
        depts = cursor.fetchall()
        for d in depts:
            print(d)
            dept_id = d[0]
            
            # 3. List courses for this dept
            print(f"   --- Courses for Dept ID {dept_id} (Year 3 & 4) ---")
            # Try to guess table names based on common conventions if previous failed, 
            # but let's assume standard names based on file inspection (Dersler, Ders_Sinif_Iliskisi)
            
            query = """
            SELECT d.code, d.name, d.is_elective, ds.sinif, ds.donem
            FROM Dersler d
            JOIN Ders_Sinif_Iliskisi ds ON d.id = ds.ders_id
            WHERE ds.bolum_id = ? AND ds.sinif IN (3, 4)
            """
            cursor.execute(query, (dept_id,))
            courses = cursor.fetchall()
            for c in courses:
                print(f"      {c}")

    except Exception as e:
        print(f"Error querying departments/courses: {e}")

    conn.close()

if __name__ == "__main__":
    inspect_db()
