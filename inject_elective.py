import sqlite3
import os
import sys

DB_PATH = "okul_veritabani.db"
COURSE_NAME = "Makine Öğrenmesi (Seçmeli)"
COURSE_CODE = "CSE301"
TEACHER_NAME = "Test Hoca"
TEACHER_SURNAME = "Yılmaz"
DAY = "Pazartesi"
START_TIME = "10:00"
END_TIME = "12:00"
DEPT_NAME = "Bilgisayar Müh"
CLASS_LEVEL = 3

def get_db_connection():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database {DB_PATH} not found.")
        return None
    return sqlite3.connect(DB_PATH)

def inject_data():
    conn = get_db_connection()
    if not conn: return
    c = conn.cursor()
    
    try:
        print("--- INJECTING DATA ---")
        # 1. Get Department and Term IDs
        c.execute("SELECT bolum_id FROM Bolumler WHERE bolum_adi LIKE ?", (f"%{DEPT_NAME}%",))
        dept_row = c.fetchone()
        if not dept_row:
            print("Department not found!")
            return
        dept_id = dept_row[0]

        c.execute("SELECT donem_sinif_num FROM Ogrenci_Donemleri WHERE bolum_num = ? AND sinif_duzeyi = ?", (dept_id, CLASS_LEVEL))
        term_row = c.fetchone()
        if not term_row:
            print("Class term not found!")
            return
        term_id = term_row[0]

        # 2. Add/Get Teacher
        c.execute("SELECT ogretmen_num FROM Ogretmenler WHERE ad = ? AND soyad = ?", (TEACHER_NAME, TEACHER_SURNAME))
        teacher_row = c.fetchone()
        if teacher_row:
            teacher_id = teacher_row[0]
        else:
            c.execute("INSERT INTO Ogretmenler (ad, soyad, bolum_adi) VALUES (?, ?, ?)", (TEACHER_NAME, TEACHER_SURNAME, DEPT_NAME))
            teacher_id = c.lastrowid
            print(f"Teacher added: {TEACHER_NAME} {TEACHER_SURNAME} ({teacher_id})")

        # 3. Add/Get Course
        instance = 1
        c.execute("SELECT ders_instance FROM Dersler WHERE ders_adi = ?", (COURSE_NAME,))
        course_row = c.fetchone()
        if not course_row:
            c.execute("""
                INSERT INTO Dersler (ders_kodu, ders_instance, ders_adi, akts, teori_saati, uygulama_saati, lab_saati)
                VALUES (?, ?, ?, 6, 2, 0, 0)
            """, (COURSE_CODE, instance, COURSE_NAME))
            print(f"Course added: {COURSE_NAME}")
        
        # 4. Schedule Course
        c.execute("""
            SELECT program_id FROM Ders_Programi 
            WHERE ders_adi = ? AND gun = ? AND baslangic = ?
        """, (COURSE_NAME, DAY, START_TIME))
        if not c.fetchone():
            c.execute("""
                INSERT INTO Ders_Programi (ders_adi, ders_instance, ogretmen_id, gun, baslangic, bitis)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (COURSE_NAME, instance, teacher_id, DAY, START_TIME, END_TIME))
            print(f"Scheduled: {DAY} {START_TIME}-{END_TIME}")

        # 5. Link to Class
        c.execute("""
            SELECT * FROM Ders_Sinif_Iliskisi 
            WHERE ders_adi = ? AND ders_instance = ? AND donem_sinif_num = ?
        """, (COURSE_NAME, instance, term_id))
        if not c.fetchone():
            c.execute("""
                INSERT INTO Ders_Sinif_Iliskisi (ders_adi, ders_instance, donem_sinif_num)
                VALUES (?, ?, ?)
            """, (COURSE_NAME, instance, term_id))
            print("Linked to class.")

        conn.commit()
        print("Injection successful.")
        print(f"Verify at: {DEPT_NAME} - Year {CLASS_LEVEL}")

    except Exception as e:
        print(f"Injection error: {e}")
        conn.rollback()
    finally:
        conn.close()

def clean_data():
    conn = get_db_connection()
    if not conn: return
    c = conn.cursor()
    
    try:
        print("--- CLEANING DATA ---")
        
        # 1. Remove from Ders_Programi
        c.execute("DELETE FROM Ders_Programi WHERE ders_adi = ?", (COURSE_NAME,))
        if c.rowcount > 0: print(f"Removed schedule entries: {c.rowcount}")

        # 2. Remove from Ders_Sinif_Iliskisi
        c.execute("DELETE FROM Ders_Sinif_Iliskisi WHERE ders_adi = ?", (COURSE_NAME,))
        if c.rowcount > 0: print(f"Removed class links: {c.rowcount}")

        # 3. Remove from Dersler
        c.execute("DELETE FROM Dersler WHERE ders_adi = ?", (COURSE_NAME,))
        if c.rowcount > 0: print(f"Removed course definition: {c.rowcount}")

        # 4. Remove Teacher (Only if created by us)
        # Check if teacher has other courses first? For safety, let's just delete by specific name/surname
        # Assuming no one else uses "Test Hoca"
        c.execute("DELETE FROM Ogretmenler WHERE ad = ? AND soyad = ?", (TEACHER_NAME, TEACHER_SURNAME))
        if c.rowcount > 0: print(f"Removed test teacher: {c.rowcount}")

        conn.commit()
        print("Cleanup successful.")

    except Exception as e:
        print(f"Cleanup error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--revert":
        clean_data()
    else:
        inject_data()
