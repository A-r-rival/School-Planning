import sys
import os
import random
import sqlite3

# Add project root to path
sys.path.append(os.getcwd())

from models.schedule_model import ScheduleModel

# Curriculum Data (Simplified/Representative based on provided links)
CURRICULUM = {
    "Bilgisayar Mühendisliği": {
        1: ["Matematik I", "Fizik I", "Bilgisayar Mühendisliğine Giriş", "Programlama I", "Türk Dili I", "Atatürk İlkeleri I"],
        2: ["Matematik II", "Fizik II", "Programlama II", "Lineer Cebir", "Türk Dili II", "Atatürk İlkeleri II"], # Spring
        3: ["Veri Yapıları", "Nesneye Yönelik Programlama", "Diferansiyel Denklemler", "Sayısal Analiz", "Elektrik Devreleri"],
        4: ["Algoritmalar", "Veritabanı Sistemleri", "İşletim Sistemleri", "Olasılık ve İstatistik"], # Spring
        5: ["Yazılım Mühendisliği", "Bilgisayar Ağları", "Biçimsel Diller ve Otomatlar", "Mikroişlemciler"],
        6: ["Yapay Zeka", "Bilgisayar Mimarisi", "Web Programlama", "Sistem Programlama"], # Spring
        7: ["Bitirme Projesi I", "Veri Madenciliği", "Görüntü İşleme", "Ağ Güvenliği"],
        8: ["Bitirme Projesi II", "Dağıtık Sistemler", "Mobil Programlama", "İş Sağlığı ve Güvenliği"] # Spring
    },
    "Elektrik-Elektronik Mühendisliği": {
        1: ["Matematik I", "Fizik I", "Kimya", "Elektrik-Elektronik Müh. Giriş", "Türk Dili I"],
        2: ["Matematik II", "Fizik II", "Bilgisayar Programlama", "Teknik Resim", "Türk Dili II"],
        3: ["Devre Analizi I", "Diferansiyel Denklemler", "Mantık Devreleri", "Malzeme Bilimi"],
        4: ["Devre Analizi II", "Elektromanyetik Alanlar", "Elektronik I", "Sinyaller ve Sistemler"],
        5: ["Elektronik II", "Elektrik Makineleri I", "Kontrol Sistemleri I", "Haberleşme Teorisi I"],
        6: ["Mikroişlemciler", "Elektrik Makineleri II", "Kontrol Sistemleri II", "Haberleşme Teorisi II"],
        7: ["Bitirme Tasarım Projesi I", "Güç Elektroniği", "Dijital Sinyal İşleme", "Mikrodalga Tekniği"],
        8: ["Bitirme Tasarım Projesi II", "Yüksek Gerilim Tekniği", "Antenler", "Gömülü Sistemler"]
    },
    "Endüstri Mühendisliği": {
        1: ["Matematik I", "Fizik I", "Endüstri Mühendisliğine Giriş", "Ekonomi I", "Türk Dili I"],
        2: ["Matematik II", "Fizik II", "Ekonomi II", "Bilgisayar Programlama", "Türk Dili II"],
        3: ["İstatistik I", "Lineer Cebir", "Malzeme Bilimi", "Genel Muhasebe"],
        4: ["İstatistik II", "Yöneylem Araştırması I", "Maliyet Muhasebesi", "Üretim Yöntemleri"],
        5: ["Yöneylem Araştırması II", "Üretim Planlama ve Kontrol I", "Ergonomi", "Simülasyon"],
        6: ["Kalite Kontrol", "Üretim Planlama ve Kontrol II", "Tesis Planlama", "Yönetim Bilişim Sistemleri"],
        7: ["Bitirme Projesi I", "Tedarik Zinciri Yönetimi", "Proje Yönetimi", "Karar Analizi"],
        8: ["Bitirme Projesi II", "Girişimcilik", "Stratejik Yönetim", "İnsan Kaynakları Yönetimi"]
    },
    # Using generic placeholders for others to ensure we have data for all faculties if needed
    "İnşaat Mühendisliği": {
        1: ["Matematik I", "Fizik I", "Kimya", "Teknik Resim", "İnşaat Müh. Giriş"],
        3: ["Statik", "Mukavemet I", "Malzeme Bilimi", "Jeoloji"],
        5: ["Yapı Statiği I", "Zemin Mekaniği I", "Akışkanlar Mekaniği", "Ulaştırma I"],
        7: ["Betonarme I", "Çelik Yapılar", "Su Kaynakları", "Temel İnşaatı"]
    },
    "Makine Mühendisliği": {
        1: ["Matematik I", "Fizik I", "Kimya", "Teknik Resim", "Makine Müh. Giriş"],
        3: ["Statik", "Dinamik", "Termodinamik I", "Malzeme I"],
        5: ["Akışkanlar Mekaniği I", "Makine Elemanları I", "Isı Transferi", "İmalat Yöntemleri I"],
        7: ["Makine Tasarımı I", "Otomatik Kontrol", "Motorlar", "Enerji Dönüşüm Sistemleri"]
    },
    "Mekatronik Mühendisliği": {
        1: ["Matematik I", "Fizik I", "Bilgisayar Programlama", "Mekatronik Müh. Giriş"],
        3: ["Statik", "Dinamik", "Elektrik Devreleri", "Sayısal Elektronik"],
        5: ["Mikroişlemciler", "Sinyaller ve Sistemler", "Makine Elemanları", "Sensörler ve Eyleyiciler"],
        7: ["Robotik", "Otomatik Kontrol", "Gömülü Sistemler", "Mekatronik Tasarım I"]
    }
}

def populate():
    print("Starting Student Population...")
    model = ScheduleModel()
    
    # Ensure Faculties and Departments exist
    faculties = ["Mühendislik Fakültesi"]
    for f in faculties:
        model.c.execute("INSERT OR IGNORE INTO Fakulteler (fakulte_adi) VALUES (?)", (f,))
    model.conn.commit()
    
    model.c.execute("SELECT fakulte_num FROM Fakulteler WHERE fakulte_adi = 'Mühendislik Fakültesi'")
    eng_faculty_id = model.c.fetchone()[0]
    
    departments = list(CURRICULUM.keys())
    dept_ids = {}
    
    for i, dept in enumerate(departments, 1):
        # Using arbitrary IDs for bolum_id (100+i) and bolum_num (1000+i)
        bolum_id = 100 + i
        bolum_num = 1000 + i
        model.c.execute("INSERT OR IGNORE INTO Bolumler (bolum_id, bolum_num, bolum_adi, fakulte_num) VALUES (?, ?, ?, ?)",
                       (bolum_id, bolum_num, dept, eng_faculty_id))
        dept_ids[dept] = (bolum_id, bolum_num)
    model.conn.commit()

    # Generate Students
    student_count = 0
    
    for dept_name, (bolum_id, bolum_num) in dept_ids.items():
        print(f"Processing {dept_name}...")
        curriculum = CURRICULUM.get(dept_name, {})
        
        for year in range(1, 5): # 1st to 4th year
            # Populate Ogrenci_Donemleri for this class
            # sinif_duzeyi: 1, 2, 3, 4
            # donem_sinif_num: e.g., "2023_BM_1"
            donem_sinif_num = f"{2024-year}_{bolum_num}_{year}"
            model.c.execute('''
                INSERT OR IGNORE INTO Ogrenci_Donemleri (donem_sinif_num, baslangic_yili, bolum_num, sinif_duzeyi)
                VALUES (?, ?, ?, ?)
            ''', (donem_sinif_num, 2024-year, bolum_id, year))
            
            # Create 20 students
            for i in range(1, 21):
                student_num = int(f"{2024-year}{bolum_id}{i:03d}") # e.g. 2023101001
                first_name = f"Ogrenci_{dept_name[:3]}_{year}"
                last_name = f"No_{i}"
                
                model.c.execute('''
                    INSERT OR REPLACE INTO Ogrenciler (ogrenci_num, ad, soyad, girme_senesi, kacinci_donem, bolum_num, fakulte_num)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (student_num, first_name, last_name, 2024-year, year*2-1, bolum_id, eng_faculty_id))
                
                # 1. Past Courses (Passed)
                passed_courses_list = []
                
                # Iterate through previous semesters (Odd and Even)
                # For a student in Year N (e.g., 3), they passed years 1 to N-1.
                # Semesters: 1, 2, 3, 4... (Year 1: 1-2, Year 2: 3-4)
                for past_year in range(1, year):
                    # Fall (Odd)
                    if past_year * 2 - 1 in curriculum:
                        for course in curriculum[past_year * 2 - 1]:
                            passed_courses_list.append(course)
                            # Add to Ogrenci_Notlari
                            model.c.execute('''
                                INSERT INTO Ogrenci_Notlari (ogrenci_num, ders_kodu, ders_adi, harf_notu, durum, donem)
                                VALUES (?, ?, ?, ?, ?, ?)
                            ''', (student_num, f"CODE_{past_year}1", course, "AA", "Geçti", f"{2024-year+past_year}-Guz"))
                    
                    # Spring (Even)
                    if past_year * 2 in curriculum:
                        for course in curriculum[past_year * 2]:
                            passed_courses_list.append(course)
                            # Add to Ogrenci_Notlari
                            model.c.execute('''
                                INSERT INTO Ogrenci_Notlari (ogrenci_num, ders_kodu, ders_adi, harf_notu, durum, donem)
                                VALUES (?, ?, ?, ?, ?, ?)
                            ''', (student_num, f"CODE_{past_year}2", course, "BA", "Geçti", f"{2024-year+past_year}-Bahar"))

                # Update Verilen_Dersler (Simple String)
                if passed_courses_list:
                    passed_str = ", ".join(passed_courses_list)
                    model.c.execute("INSERT OR REPLACE INTO Verilen_Dersler (ogrenci_num, ders_listesi) VALUES (?, ?)",
                                   (student_num, passed_str))
                
                # 2. Current Courses (Enrolled)
                # Enroll in current Fall semester courses (Year * 2 - 1)
                current_semester = year * 2 - 1
                if current_semester in curriculum:
                    for course in curriculum[current_semester]:
                        # Ensure Course exists in Dersler
                        model.c.execute("INSERT OR IGNORE INTO Dersler (ders_kodu, ders_instance, ders_adi) VALUES (?, ?, ?)",
                                       (f"CODE_{current_semester}", 1, course))
                        
                        # Link Class to Course (Ders_Sinif_Iliskisi)
                        # This effectively enrolls the whole class
                        model.c.execute('''
                            INSERT OR IGNORE INTO Ders_Sinif_Iliskisi (ders_adi, ders_instance, donem_sinif_num)
                            VALUES (?, ?, ?)
                        ''', (course, 1, donem_sinif_num))
                        
                        # Also add to Alinan_Dersler for individual tracking if needed (optional based on schema, but good for completeness)
                        model.c.execute('''
                            INSERT OR IGNORE INTO Alinan_Dersler (ders_adi, ders_instance, donem_sinif_num)
                            VALUES (?, ?, ?)
                        ''', (course, 1, donem_sinif_num))

                student_count += 1
                
    model.conn.commit()
    print(f"✅ Successfully created {student_count} students across {len(departments)} departments.")
    model.conn.close()

if __name__ == "__main__":
    populate()
