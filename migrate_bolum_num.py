import sqlite3

def run_migration():
    conn = sqlite3.connect('okul_veritabani.db')
    c = conn.cursor()
    
    try:
        print("Starting migration...")
        
        # 1. Bolumler: bolum_num -> bolum_resmi_num
        print("Renaming Bolumler.bolum_num to bolum_resmi_num...")
        c.execute("ALTER TABLE Bolumler RENAME COLUMN bolum_num TO bolum_resmi_num")
        
        # 2. Ders_Havuz_Iliskisi: bolum_num -> bolum_resmi_num
        print("Renaming Ders_Havuz_Iliskisi.bolum_num to bolum_resmi_num...")
        c.execute("ALTER TABLE Ders_Havuz_Iliskisi RENAME COLUMN bolum_num TO bolum_resmi_num")
        
        # 3. Ogrenci_Donemleri: bolum_num -> bolum_id
        print("Renaming Ogrenci_Donemleri.bolum_num to bolum_id...")
        c.execute("ALTER TABLE Ogrenci_Donemleri RENAME COLUMN bolum_num TO bolum_id")
        
        # 4. Ogrenciler: bolum_num -> bolum_id
        print("Renaming Ogrenciler.bolum_num to bolum_id...")
        c.execute("ALTER TABLE Ogrenciler RENAME COLUMN bolum_num TO bolum_id")
        
        conn.commit()
        print("Migration successful!")
    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
        print("Note: If the columns were already renamed, this might fail.")
    finally:
        conn.close()

if __name__ == "__main__":
    run_migration()
