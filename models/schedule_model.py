# -*- coding: utf-8 -*-
"""
Schedule Model - MVC Pattern
Handles all data operations and business logic
"""
import os
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from PyQt5.QtCore import QObject, pyqtSignal

simdiki_sene = datetime.now().year


class ScheduleModel(QObject):
    """
    Model class for schedule management
    Handles data operations and business logic
    """
    
    # Signals for view updates
    course_added = pyqtSignal(str)  # Emits course info when added
    course_removed = pyqtSignal(str)  # Emits course info when removed
    error_occurred = pyqtSignal(str)  # Emits error messages
    
    def __init__(self, db_path: str = None):
        super().__init__()
        
        # Initialize database path
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if db_path is None:
            db_path = os.path.join(script_dir, "okul_veritabani.db")
        
        # Initialize database connection
        self.conn = sqlite3.connect(db_path)
        self.c = self.conn.cursor()
        self.c.execute("PRAGMA foreign_keys = ON")
        self._create_tables()
        
        # Create simple tables if they don't exist
        self._create_simple_tables()
    
    def _create_tables(self):
        """Create all database tables"""
        db_create = [
            '''CREATE TABLE IF NOT EXISTS Fakulteler (
                fakulte_num INTEGER PRIMARY KEY AUTOINCREMENT,
                fakulte_adi TEXT NOT NULL
            )''',

            '''CREATE TABLE IF NOT EXISTS Bolumler (
                bolum_id INTEGER PRIMARY KEY,       --sadece veri tabani işlevleri için, resmiyette kullanilan bir numara değil
                bolum_num INTEGER NOT NULL,
                bolum_adi TEXT NOT NULL,
                fakulte_num INTEGER NOT NULL,
                UNIQUE (fakulte_num, bolum_num),
                FOREIGN KEY (fakulte_num) REFERENCES Fakulteler(fakulte_num)
            )''',

            '''CREATE TABLE IF NOT EXISTS Ogrenci_Donemleri (       --bunu dönemle alakali yap!!!!
                donem_sinif_num INTEGER PRIMARY KEY,      --mesela "210507"
                baslangic_yili INTEGER,                   --otomatize et, fnord
                bolum_num INTEGER NOT NULL,
                sinif_duzeyi INTEGER NOT NULL CHECK (sinif_duzeyi BETWEEN 0 AND 5), --0: Hazirlik, 1: 1. Sinif, 2: 2. Sinif, 3: 3. Sinif, 4: 4. Sinif, 5: Mezun
                UNIQUE (sinif_duzeyi, bolum_num),
                FOREIGN KEY (bolum_num) REFERENCES Bolumler(bolum_id)
            )''',

            '''CREATE TABLE IF NOT EXISTS Dersler (
                ders_kodu TEXT,
                ders_instance INTEGER NOT NULL,
                ders_adi TEXT NOT NULL,
                teori_odasi INTEGER,
                lab_odasi INTEGER,
                PRIMARY KEY (ders_instance, ders_adi),
                FOREIGN KEY (teori_odasi) REFERENCES Derslikler(derslik_num) ON DELETE SET NULL,
                FOREIGN KEY (lab_odasi) REFERENCES Derslikler(derslik_num) ON DELETE SET NULL
            )''',

            '''CREATE TABLE IF NOT EXISTS dersler (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ders TEXT NOT NULL,
                hoca TEXT NOT NULL,
                gun TEXT NOT NULL,
                saat TEXT NOT NULL,
                silindi BOOLEAN DEFAULT 0,
                silinme_tarihi DATETIME
            )''',

            '''CREATE TABLE IF NOT EXISTS Ders_Sinif_Iliskisi (
                ders_adi TEXT,
                ders_instance INTEGER,
                donem_sinif_num TEXT,
                PRIMARY KEY (ders_instance, donem_sinif_num, ders_adi),
                FOREIGN KEY (ders_instance, ders_adi) REFERENCES Dersler(ders_instance, ders_adi) ON DELETE CASCADE,
                FOREIGN KEY (donem_sinif_num) REFERENCES Ogrenci_Donemleri(donem_sinif_num)
            )''',

            '''CREATE TABLE IF NOT EXISTS Ogrenciler (
                ogrenci_num INTEGER PRIMARY KEY,
                ad TEXT NOT NULL,
                soyad TEXT NOT NULL,
                girme_senesi INTEGER NOT NULL,
                kacinci_donem INTEGER NOT NULL,     --aldigi dersler degil de burokratik islemler icin, askerlik vs.
                bolum_num INTEGER NOT NULL,
                fakulte_num INTEGER NOT NULL,
                mezun_durumu INTEGER DEFAULT 0,
                ikinci_bolum_num INTEGER,
                ikinci_bolum_turu TEXT CHECK(ikinci_bolum_turu IN ('Yandal', 'Anadal')),
                ogrenci_num2 INTEGER,
                girme_senesi2 INTEGER,
                kacinci_donem2 INTEGER,
                FOREIGN KEY (bolum_num) REFERENCES Bolumler(bolum_id),
                FOREIGN KEY (ikinci_bolum_num) REFERENCES Bolumler(bolum_id)
            )''',

            '''CREATE TABLE IF NOT EXISTS Verilen_Dersler (
                ogrenci_num INTEGER PRIMARY KEY,
                ders_listesi TEXT
            )''',

            '''CREATE TABLE IF NOT EXISTS Alinan_Dersler (
                ders_adi TEXT,
                ders_instance INTEGER,
                donem_sinif_num TEXT,
                PRIMARY KEY (ders_instance, donem_sinif_num, ders_adi),
                FOREIGN KEY (ders_instance, ders_adi) REFERENCES Dersler(ders_instance, ders_adi) ON DELETE CASCADE,
                FOREIGN KEY (donem_sinif_num) REFERENCES Ogrenci_Donemleri(donem_sinif_num)
            )''',

            '''CREATE TABLE IF NOT EXISTS Derslikler (
                derslik_num INTEGER PRIMARY KEY AUTOINCREMENT,
                derslik_adi TEXT NOT NULL,
                tip TEXT NOT NULL CHECK (tip IN ('lab', 'amfi')),
                kapasite INTEGER NOT NULL,
                ozellikler TEXT,
                silindi BOOLEAN DEFAULT 0,
                silinme_tarihi DATETIME
            )''',

            '''CREATE TABLE IF NOT EXISTS Ogretmenler (
                ogretmen_num INTEGER PRIMARY KEY AUTOINCREMENT,
                ad TEXT NOT NULL,
                soyad TEXT NOT NULL,
                unvan TEXT,
                bolum_adi TEXT NOT NULL
            )''',

            '''CREATE TABLE IF NOT EXISTS Ders_Ogretmen_Iliskisi (
                ders_adi TEXT,
                ders_instance INTEGER,
                donem_sinif_num TEXT,
                PRIMARY KEY (ders_instance, donem_sinif_num, ders_adi),
                FOREIGN KEY (ders_instance, ders_adi) REFERENCES Dersler(ders_instance, ders_adi) ON DELETE CASCADE,
                FOREIGN KEY (donem_sinif_num) REFERENCES Ogrenci_Donemleri(donem_sinif_num)
            )'''

        ]
        for sql in db_create:
            self.c.execute(sql)
        
        # Index'leri oluştur
        indexes = [
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_derslik_adi_active ON Derslikler(derslik_adi) WHERE silindi = 0",
            "CREATE INDEX IF NOT EXISTS idx_bolumler_fakulte ON Bolumler(fakulte_num)",
            "CREATE INDEX IF NOT EXISTS idx_Ogrenci_Donemleri_bolum ON Ogrenci_Donemleri(bolum_num)",
            "CREATE INDEX IF NOT EXISTS idx_ders_sinif_iliskisi_sinif ON Ders_Sinif_Iliskisi(donem_sinif_num)",
            "CREATE INDEX IF NOT EXISTS idx_dersler_adi ON Dersler(ders_adi)",
            "CREATE INDEX IF NOT EXISTS idx_dersler_instance ON Dersler(ders_instance)",
            "CREATE INDEX IF NOT EXISTS idx_ogrenciler_bolum ON Ogrenciler(bolum_num)",
            "CREATE INDEX IF NOT EXISTS idx_ogrenciler_fakulte ON Ogrenciler(fakulte_num)"
        ]
        
        for index_sql in indexes:
            self.c.execute(index_sql)
        
        self.conn.commit()
    
    def _create_simple_tables(self):
        """Create simple course table for backward compatibility"""
        try:
            # Mevcut tabloya silindi kolonu ekle (eğer yoksa)
            self.c.execute("ALTER TABLE dersler ADD COLUMN silindi BOOLEAN DEFAULT 0")
            self.conn.commit()
        except:
            pass  # Kolon zaten varsa hata vermez
        
        try:
            self.c.execute("ALTER TABLE dersler ADD COLUMN silinme_tarihi DATETIME")
            self.conn.commit()
        except:
            pass  # Kolon zaten varsa hata vermez
    
    def add_course(self, course_data: Dict[str, str]) -> bool:
        """
        Add a new course to the schedule
        
        Args:
            course_data: Dictionary containing course information
                       {'ders': str, 'hoca': str, 'gun': str, 'baslangic': str, 'bitis': str}
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Validate input data
            if not self._validate_course_data(course_data):
                return False
            
            # Check for time conflicts
            if self._check_time_conflict(course_data['gun'], course_data['baslangic'], course_data['bitis']):
                self.error_occurred.emit("Bu saat aralığında zaten bir ders var!")
                return False
            
            # Add to database directly
            success = self.basit_ders_ekle(
                course_data['ders'], 
                course_data['hoca'], 
                course_data['gun'], 
                course_data['baslangic'], 
                course_data['bitis']
            )
            
            if success:
                # Emit signal for successful addition
                saat = f"{course_data['baslangic']}-{course_data['bitis']}"
                course_info = f"{course_data['ders']} - {course_data['hoca']} - {course_data['gun']} {saat}"
                self.course_added.emit(course_info)
                return True
            else:
                self.error_occurred.emit("Ders eklenirken veritabanı hatası oluştu!")
                return False
            
        except Exception as e:
            self.error_occurred.emit(f"Ders eklenirken hata oluştu: {str(e)}")
            return False
    
    def remove_course(self, course_info: str) -> bool:
        """
        Remove a course from the schedule
        
        Args:
            course_info: Course information string
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Parse course information
            parts = course_info.split(" - ")
            if len(parts) != 3:
                raise ValueError("Geçersiz ders bilgisi formatı")
            
            ders, hoca, time_info = parts
            gun, saat = time_info.split(" ", 1)
            
            # Remove from database directly
            success = self.basit_ders_sil(ders, hoca, gun, saat)
            
            if success:
                # Emit signal for successful removal
                self.course_removed.emit(course_info)
                return True
            else:
                self.error_occurred.emit("Ders silinirken veritabanı hatası oluştu!")
                return False
            
        except Exception as e:
            self.error_occurred.emit(f"Ders silinirken hata oluştu: {str(e)}")
            return False
    
    def get_all_courses(self) -> List[str]:
        """
        Get all courses from database
        
        Returns:
            List[str]: List of course information strings
        """
        try:
            courses_data = self.basit_dersleri_getir()
            courses = []
            for ders, hoca, gun, saat in courses_data:
                course_info = f"{ders} - {hoca} - {gun} {saat}"
                courses.append(course_info)
            return courses
        except Exception as e:
            self.error_occurred.emit(f"Dersler yüklenirken hata oluştu: {str(e)}")
            return []
    
    def get_teachers(self) -> List[str]:
        """
        Get all unique teacher names
        
        Returns:
            List[str]: List of teacher names
        """
        try:
            return self.basit_hocalari_getir()
        except Exception as e:
            self.error_occurred.emit(f"Öğretmenler yüklenirken hata oluştu: {str(e)}")
            return []
    
    def _validate_course_data(self, course_data: Dict[str, str]) -> bool:
        """
        Validate course data before adding
        
        Args:
            course_data: Course data dictionary
        
        Returns:
            bool: True if valid, False otherwise
        """
        required_fields = ['ders', 'hoca', 'gun', 'baslangic', 'bitis']
        
        # Check required fields
        for field in required_fields:
            if field not in course_data or not course_data[field].strip():
                self.error_occurred.emit(f"{field} alanı boş olamaz!")
                return False
        
        # Check time validity
        try:
            start_time = datetime.strptime(course_data['baslangic'], "%H:%M").time()
            end_time = datetime.strptime(course_data['bitis'], "%H:%M").time()
            
            if start_time >= end_time:
                self.error_occurred.emit("Başlangıç saati bitiş saatinden önce olmalıdır!")
                return False
                
        except ValueError:
            self.error_occurred.emit("Geçersiz saat formatı! (HH:MM formatında olmalı)")
            return False
        
        return True
    
    def _check_time_conflict(self, gun: str, baslangic: str, bitis: str) -> bool:
        """
        Check for time conflicts on the same day
        
        Args:
            gun: Day of the week
            baslangic: Start time
            bitis: End time
        
        Returns:
            bool: True if conflict exists, False otherwise
        """
        try:
            return self.basit_zaman_cakismasi_kontrol(gun, baslangic, bitis)
        except Exception as e:
            self.error_occurred.emit(f"Zaman çakışması kontrolünde hata: {str(e)}")
            return True  # Return True to be safe
    
    # Advanced database operations using DbManager
    def add_faculty(self, faculty_name: str) -> Optional[int]:
        """
        Add a new faculty using DbManager
        
        Args:
            faculty_name: Name of the faculty
        
        Returns:
            Optional[int]: Faculty ID if successful, None otherwise
        """
        try:
            faculty_id = self.fakulte_ekle(faculty_name)
            return faculty_id
        except Exception as e:
            self.error_occurred.emit(f"Fakülte eklenirken hata oluştu: {str(e)}")
            return None
    
    def add_department(self, faculty_id: int, department_name: str) -> Optional[int]:
        """
        Add a new department using DbManager
        
        Args:
            faculty_id: Faculty ID
            department_name: Name of the department
        
        Returns:
            Optional[int]: Department ID if successful, None otherwise
        """
        try:
            department_id = self.bolum_ekle(faculty_id, department_name)
            return department_id
        except Exception as e:
            self.error_occurred.emit(f"Bölüm eklenirken hata oluştu: {str(e)}")
            return None
    
    def get_faculties(self) -> List[Tuple[int, str]]:
        """
        Get all faculties
        
        Returns:
            List[Tuple[int, str]]: List of (faculty_id, faculty_name) tuples
        """
        try:
            self.c.execute("SELECT fakulte_num, fakulte_adi FROM Fakulteler ORDER BY fakulte_adi")
            return self.c.fetchall()
        except Exception as e:
            self.error_occurred.emit(f"Fakülteler yüklenirken hata oluştu: {str(e)}")
            return []
    
    def close_connections(self):
        """Close database connections"""
        try:
            self.conn.close()
        except Exception as e:
            print(f"Veritabanı bağlantısı kapatılırken hata: {str(e)}")
    
    # Database management methods from DbManager
    def fakulte_numarasini_al(self, ogrenci_num2: int) -> int:
        numara_str = str(ogrenci_num2).zfill(10)  # 10 haneye tamamla, güvenlik için
        return int(numara_str[2:4])
    
    def bolum_numarasini_al(self, bolum_adi: str, fakulte_num: int) -> int:
        self.c.execute('''
            SELECT bolum_num 
            FROM Bolumler 
            WHERE bolum_adi = ? AND fakulte_num = ?
        ''', (bolum_adi, fakulte_num))
        
        sonuc = self.c.fetchone()
        
        if sonuc:
            return sonuc[0]
        else:
            raise ValueError(f"{bolum_adi} adında ve {fakulte_num} fakülte numarasında bir bölüm bulunamadı.")

    def _format_ogrenci_num(self, girme_senesi, fakulte_num, bolum_num, program_tipi, sira):
        """Öğrenci numarası formatını oluştur: YY0FBBPSSS"""
        year_part = str(girme_senesi)[-2:]  # YY
        faculty_part = f"{fakulte_num:02d}"  # FF
        dept_part = f"{bolum_num:02d}"       # BB
        program_part = str(program_tipi)     # P
        sequence_part = f"{sira:03d}"        # SSS
        return int(f"{year_part}0{faculty_part}{dept_part}{program_part}{sequence_part}")

    def _parse_ogrenci_num(self, ogrenci_num):
        """Öğrenci numarasını parse et"""
        num_str = str(ogrenci_num).zfill(10)
        return {
            'year': int(num_str[0:2]),
            'faculty': int(num_str[2:4]),
            'dept': int(num_str[4:6]),
            'program': int(num_str[6:7]),
            'sequence': int(num_str[7:10])
        }

    # Fakülte ekle
    def fakulte_ekle(self, fakulte_adi):
        self.c.execute("INSERT INTO Fakulteler (fakulte_adi) VALUES (?)", (fakulte_adi,))
        self.conn.commit()
        return self.c.lastrowid
    
    # Bölüm ekle (otomatik 4-digit global bolum_id ataması)
    def bolum_ekle(self, fakulte_identifier: int | str, bolum_adi: str, by_name: bool = False) -> int:
        """
        Bolum ekler.
        :param fakulte_identifier: Fakulte numarası (int) veya fakulte adı (str)
        :param bolum_adi: Eklenecek bölümün adı (str)
        :param by_name: True ise fakulte_identifier fakulte adı olarak değerlendirilir.
                        False ise fakulte numarası olarak değerlendirilir.
        :return: Yeni 4-digit global bolum_id (int)
        """
        with self.conn:
            if by_name:
                # Fakülte adından numarasını bul
                self.c.execute('SELECT fakulte_num FROM Fakulteler WHERE fakulte_adi = ?', (fakulte_identifier,))
                res = self.c.fetchone()
                if res is None:
                    raise ValueError(f"Fakulte adi '{fakulte_identifier}' bulunamadi.")
                fakulte_num = res[0]
            else:
                fakulte_num = fakulte_identifier

            # Fakülte içi bölüm numarasını hesapla
            self.c.execute('SELECT COALESCE(MAX(bolum_num), 0) + 1 FROM Bolumler WHERE fakulte_num = ?', (fakulte_num,))
            yeni_bolum_num = self.c.fetchone()[0]

            # 4-digit global bolum_id oluştur: FFBB (Fakülte 2-digit + Bölüm 2-digit)
            global_bolum_id = int(f"{fakulte_num:02d}{yeni_bolum_num:02d}")

            # Bölüm ekle
            self.c.execute('''
                INSERT INTO Bolumler (bolum_id, bolum_num, bolum_adi, fakulte_num)
                VALUES (?, ?, ?, ?)
            ''', (global_bolum_id, yeni_bolum_num, bolum_adi, fakulte_num))
            return global_bolum_id
    
    # Öğrenci Sinifı ekle (otomatik donem_sinif_num hesaplaması)
    def ogrenci_sinifi_ekle(self, bolum_id: int, sinif_duzeyi: int) -> int:
        with self.conn:
            self.c.execute('SELECT fakulte_num, bolum_num FROM Bolumler WHERE bolum_id = ?', (bolum_id,))
            result = self.c.fetchone()
            if not result:
                raise ValueError("Bölüm bulunamadı.")
            fakulte_num, bolum_num = result

            donem_sinif_num = int(f"{fakulte_num}{bolum_num}0{sinif_duzeyi}")

            self.c.execute('''
                INSERT INTO Ogrenci_Donemleri (donem_sinif_num, sinif_duzeyi, bolum_num) 
                VALUES (?, ?, ?)
            ''', (donem_sinif_num, sinif_duzeyi, bolum_id))
            return donem_sinif_num
    
    # Ders ekle (ders_instance otomatik atanır)
    def ders_ekle(self, ders_adi, ders_kodu=None, teori_odasi=None, lab_odasi=None):
        self.c.execute('SELECT ders_instance FROM Dersler WHERE ders_adi = ?', (ders_adi,))
        kullanilanlar = {row[0] for row in self.c.fetchall()}

        instance = 1
        while instance in kullanilanlar:
            instance += 1
        # Kullanılmayan en küçük pozitif sayıyı bulana kadar devam eder.

        self.c.execute('''
            INSERT INTO Dersler (ders_kodu, ders_adi, ders_instance, teori_odasi, lab_odasi)
            VALUES (?, ?, ?, ?, ?)
        ''', (ders_kodu, ders_adi, instance, teori_odasi, lab_odasi))
        self.conn.commit()
        return instance
    
    def ogrenci_ekle(self, ad, soyad, bolum_num, fakulte_num, 
                 girme_senesi=None, kacinci_donem=None):
        program_tipi = 0  # Normal öğrenci

        if girme_senesi is None:
            girme_senesi = simdiki_sene

        self.c.execute('''
            SELECT COUNT(*) FROM Ogrenciler
            WHERE girme_senesi = ? AND bolum_num = ? AND fakulte_num = ? AND ikinci_bolum_turu IS NULL
        ''', (girme_senesi, bolum_num, fakulte_num))
        sira = self.c.fetchone()[0] + 1

        ogrenci_num = self._format_ogrenci_num(girme_senesi, fakulte_num, bolum_num, program_tipi, sira)

        self.c.execute('''
            INSERT INTO Ogrenciler (
                ogrenci_num, ad, soyad, girme_senesi, kacinci_donem,
                bolum_num, fakulte_num
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            ogrenci_num, ad, soyad, girme_senesi, kacinci_donem,
            bolum_num, fakulte_num
        ))

        self.conn.commit()
        return ogrenci_num

    def ogrenci_ekle2(self, ogrenci_num, ikinci_bolumu, ikinci_bolum_turu,
                     girme_senesi2=None, kacinci_donem2=None,):

        # Program tipi belirleme (8: yandal, 9: ikinci anadal)
        if ikinci_bolum_turu.lower() == 'yandal':
            program_tipi = 8
        elif ikinci_bolum_turu.lower() == 'anadal':
            program_tipi = 9
        else:
            raise ValueError("Geçersiz ikinci bölüm türü: 'Yandal' veya 'Anadal' olmalı.")
        
        if girme_senesi2 is None:
            girme_senesi2 = simdiki_sene

        # İkinci bölüm farklı fakülteden olabilir, fakulte_num'u ikinci bölümden al
        self.c.execute('SELECT fakulte_num FROM Bolumler WHERE bolum_adi = ?', (ikinci_bolumu,))
        fakulte_result = self.c.fetchone()
        if not fakulte_result:
            raise ValueError(f"İkinci bölüm '{ikinci_bolumu}' bulunamadı.")
        fakulte_num2 = fakulte_result[0]
        
        bolum_num2 = self.bolum_numarasini_al(ikinci_bolumu, fakulte_num2)

        # Aynı yıl, fakülte, bölüm ve program tipinde kaç kişi kayıtlı?
        self.c.execute('''
            SELECT COUNT(*) FROM Ogrenciler
            WHERE girme_senesi2 = ?
              AND ikinci_bolum_num = ?
              AND ikinci_bolum_turu = ?
        ''', (girme_senesi2, bolum_num2, ikinci_bolum_turu))
        sira = self.c.fetchone()[0] + 1

        # Öğrenci numarası: YY0FBBPSSS (ikinci fakülte numarası kullanılır)
        ogrenci_num2 = self._format_ogrenci_num(girme_senesi2, fakulte_num2, bolum_num2, program_tipi, sira)

        self.c.execute('''
            UPDATE Ogrenciler
            SET ikinci_bolum_num = ?, ikinci_bolum_turu = ?, ogrenci_num2 = ?, girme_senesi2 = ?, kacinci_donem2 = ?
            WHERE ogrenci_num = ?
        ''', (bolum_num2, ikinci_bolum_turu, ogrenci_num2, girme_senesi2, kacinci_donem2, ogrenci_num))

        self.conn.commit()
        return ogrenci_num2
    
    def verilen_ders_ekle(self, ogrenci_num, yeni_dersler):
        # Mevcut ders_listesini al
        self.c.execute('SELECT ders_listesi FROM Verilen_Dersler WHERE ogrenci_num = ?', (ogrenci_num,))
        sonuc = self.c.fetchone()

        if sonuc is None:
            # Kayıt yoksa direkt ekle
            ders_listesi_str = '|'.join(yeni_dersler)
            self.c.execute('INSERT INTO Verilen_Dersler (ogrenci_num, ders_listesi) VALUES (?, ?)', (ogrenci_num, ders_listesi_str))
        else:
            mevcut_dersler = sonuc[0].split('|') if sonuc[0] else []
            # Yeni dersleri mevcut listeye ekle, tekrarı önle
            toplam_dersler = list(set(mevcut_dersler + yeni_dersler))
            ders_listesi_str = '|'.join(sorted(toplam_dersler))  # İstersen sıralayabilirsin
            # Güncelle
            self.c.execute('UPDATE Verilen_Dersler SET ders_listesi = ? WHERE ogrenci_num = ?', (ders_listesi_str, ogrenci_num))
        
        self.conn.commit()

    def verilen_dersleri_getir(self, ogrenci_num):
        self.c.execute('SELECT ders_listesi FROM Verilen_Dersler WHERE ogrenci_num = ?', (ogrenci_num,))
        row = self.c.fetchone()
        return row[0].split('|') if row and row[0] else []

    def alinan_ders_ekle(self, ders_adi, ders_instance, donem_sinif_num):
        self.c.execute('''
            INSERT OR IGNORE INTO Alinan_Dersler (ders_adi, ders_instance, donem_sinif_num)
            VALUES (?, ?, ?)
        ''', (ders_adi, ders_instance, donem_sinif_num))
        self.conn.commit()

    def alinan_dersleri_getir(self, donem_sinif_num):
        self.c.execute('SELECT ders_adi, ders_instance FROM Alinan_Dersler WHERE donem_sinif_num = ?', (donem_sinif_num,))
        return self.c.fetchall()
    
    def derslik_ekle(self, derslik_adi, tip, kapasite, ozellikler=None):
        """Derslik ekle"""
        self.c.execute('''
            INSERT INTO Derslikler (derslik_adi, tip, kapasite, ozellikler)
            VALUES (?, ?, ?, ?)
        ''', (derslik_adi, tip, kapasite, ozellikler))
        self.conn.commit()
        return self.c.lastrowid

    def derslik_sil(self, derslik_num):
        """Derslik soft delete - gerçekten silmez, sadece işaretler"""
        from datetime import datetime
        self.c.execute('''
            UPDATE Derslikler 
            SET silindi = 1, silinme_tarihi = ?
            WHERE derslik_num = ?
        ''', (datetime.now(), derslik_num))
        self.conn.commit()

    def aktif_derslikleri_getir(self):
        """Sadece aktif (silinmemiş) derslikleri getir"""
        self.c.execute('SELECT derslik_num, derslik_adi, tip, kapasite FROM Derslikler WHERE silindi = 0')
        return self.c.fetchall()

    def tum_derslikleri_getir(self):
        """Tüm derslikleri getir (silinmiş olanlar dahil)"""
        self.c.execute('SELECT derslik_num, derslik_adi, tip, kapasite, silindi, silinme_tarihi FROM Derslikler')
        return self.c.fetchall()

    # Basit ders programı yönetimi metodları
    def basit_ders_ekle(self, ders_adi, hoca_adi, gun, baslangic_saati, bitis_saati):
        """
        Basit ders programı için ders ekleme
        
        Args:
            ders_adi: Ders adı
            hoca_adi: Öğretmen adı
            gun: Gün (Pazartesi, Salı, vb.)
            baslangic_saati: Başlangıç saati (HH:MM)
            bitis_saati: Bitiş saati (HH:MM)
        
        Returns:
            bool: Başarılı ise True
        """
        try:
            saat = f"{baslangic_saati}-{bitis_saati}"
            self.c.execute("""
                INSERT INTO dersler (ders, hoca, gun, saat) 
                VALUES (?, ?, ?, ?)
            """, (ders_adi, hoca_adi, gun, saat))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Ders eklenirken hata: {e}")
            return False
    
    def basit_ders_sil(self, ders_adi, hoca_adi, gun, saat):
        """
        Basit ders programından ders silme
        
        Args:
            ders_adi: Ders adı
            hoca_adi: Öğretmen adı
            gun: Gün
            saat: Saat aralığı
        
        Returns:
            bool: Başarılı ise True
        """
        try:
            self.c.execute("""
                DELETE FROM dersler 
                WHERE ders=? AND hoca=? AND gun=? AND saat=?
            """, (ders_adi, hoca_adi, gun, saat))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Ders silinirken hata: {e}")
            return False
    
    def basit_dersleri_getir(self):
        """
        Tüm basit dersleri getir
        
        Returns:
            List: Ders bilgileri listesi
        """
        try:
            self.c.execute("SELECT ders, hoca, gun, saat FROM dersler")
            return self.c.fetchall()
        except Exception as e:
            print(f"Dersler getirilirken hata: {e}")
            return []
    
    def basit_hocalari_getir(self):
        """
        Tüm öğretmenleri getir
        
        Returns:
            List: Öğretmen adları listesi
        """
        try:
            self.c.execute("SELECT DISTINCT hoca FROM dersler WHERE hoca IS NOT NULL AND hoca != ''")
            return [row[0] for row in self.c.fetchall()]
        except Exception as e:
            print(f"Öğretmenler getirilirken hata: {e}")
            return []
    
    def basit_zaman_cakismasi_kontrol(self, gun, baslangic, bitis):
        """
        Aynı günde zaman çakışması kontrolü
        
        Args:
            gun: Gün
            baslangic: Başlangıç saati
            bitis: Bitiş saati
        
        Returns:
            bool: Çakışma varsa True
        """
        try:
            self.c.execute("SELECT saat FROM dersler WHERE gun = ?", (gun,))
            existing_times = self.c.fetchall()
            
            for (existing_time_str,) in existing_times:
                existing_start, existing_end = existing_time_str.split('-')
                
                # Zaman aralıkları çakışıyor mu kontrol et
                if (baslangic < existing_end and bitis > existing_start):
                    return True
            
            return False
        except Exception as e:
            print(f"Zaman çakışması kontrolünde hata: {e}")
            return True  # Güvenli tarafta kal
