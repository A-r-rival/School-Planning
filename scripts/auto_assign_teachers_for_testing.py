import sqlite3
import random
import os
import sys

def auto_assign_teachers():
    """
    Test amaçlı olarak veritabanındaki tüm derslere (Güz/Bahar fark etmeksizin)
    rastgele bir hoca ataması yapar. Program Güz/Bahar filtresini UI üzerinden
    kendisi yaptığı için hangi dönem olduğuna bu skriptte bakmaya gerek yoktur.
    """
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(script_dir, "database", "okul_veritabani.db")
    
    if not os.path.exists(db_path):
        print(f"HATA: Veritabanı bulunamadı -> {db_path}")
        sys.exit(1)
        
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # 1. Kayıtlı hocaları al
    c.execute("SELECT ogretmen_num FROM Ogretmenler")
    teachers = [r[0] for r in c.fetchall()]
    
    if not teachers:
        print("HATA: Veritabanında kayıtlı öğretmen bulunamadı. Lütfen önce 'Oto-Doldur' yapın.")
        sys.exit(1)
        
    # 2. Kayıtlı dersleri al
    c.execute("SELECT ders_adi, ders_instance FROM Dersler")
    courses = c.fetchall()
    
    if not courses:
        print("HATA: Veritabanında kayıtlı ders bulunamadı.")
        sys.exit(1)
        
    # Mevcut atamaları temizle (İsteğe bağlı, sıfırdan test etmek için)
    c.execute("DELETE FROM Ders_Ogretmen_Iliskisi")
    print("Eski öğretmen atamaları temizlendi.")
    
    # 3. Her derse rastgele bir hoca ata
    count = 0
    for course_name, instance in courses:
        teacher_id = random.choice(teachers)
        try:
            c.execute(
                "INSERT INTO Ders_Ogretmen_Iliskisi (ders_adi, ders_instance, ogretmen_id) VALUES (?, ?, ?)", 
                (course_name, instance, teacher_id)
            )
            count += 1
        except sqlite3.Error as e:
            pass # Eğer ignore etmezse (örn. unique constraint varsa) devam et.
            
    conn.commit()
    conn.close()
    
    print(f"BAŞARILI! Toplam {count} derse test amaçlı otomatik öğretmen ataması yapıldı.")
    print("Artık UI üzerinden Güz veya Bahar dönemini seçerek oluştur butonuna basabilirsiniz.")

if __name__ == "__main__":
    auto_assign_teachers()
