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
        # self._create_simple_tables() # Removed legacy call
    
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
                donem_sinif_num TEXT PRIMARY KEY,      --mesela "210507"
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
                akts INTEGER,
                PRIMARY KEY (ders_instance, ders_adi),
                FOREIGN KEY (teori_odasi) REFERENCES Derslikler(derslik_num) ON DELETE SET NULL,
                FOREIGN KEY (lab_odasi) REFERENCES Derslikler(derslik_num) ON DELETE SET NULL
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
            )''',

            '''CREATE TABLE IF NOT EXISTS Ders_Programi (
                program_id INTEGER PRIMARY KEY AUTOINCREMENT,
                ders_adi TEXT,
                ders_instance INTEGER,
                ogretmen_id INTEGER,
                gun TEXT NOT NULL,
                baslangic TEXT NOT NULL,
                bitis TEXT NOT NULL,
                FOREIGN KEY (ders_instance, ders_adi) REFERENCES Dersler(ders_instance, ders_adi),
                FOREIGN KEY (ogretmen_id) REFERENCES Ogretmenler(ogretmen_num)
            )''',

            '''CREATE TABLE IF NOT EXISTS Ogrenci_Notlari (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ogrenci_num INTEGER NOT NULL,
                ders_kodu TEXT,
                ders_adi TEXT NOT NULL,
                harf_notu TEXT,
                durum TEXT,
                donem TEXT,
                onceki_not_id INTEGER,
                FOREIGN KEY (ogrenci_num) REFERENCES Ogrenciler(ogrenci_num),
                FOREIGN KEY (onceki_not_id) REFERENCES Ogrenci_Notlari(id)
            )'''
        ]

        for sql in db_create:
            self.c.execute(sql)

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

            ders_adi = course_data['ders']
            hoca_adi = course_data['hoca']
            gun = course_data['gun']
            baslangic = course_data['baslangic']
            bitis = course_data['bitis']

            # 1. Ensure Teacher exists
            self.c.execute("SELECT ogretmen_num FROM Ogretmenler WHERE ad || ' ' || soyad = ?", (hoca_adi,))
            teacher_row = self.c.fetchone()
            if not teacher_row:
                # Simple name splitting for ad/soyad
                parts = hoca_adi.split(' ')
                ad = parts[0]
                soyad = ' '.join(parts[1:]) if len(parts) > 1 else ''
                self.c.execute("INSERT INTO Ogretmenler (ad, soyad, bolum_adi) VALUES (?, ?, ?)", (ad, soyad, "Genel"))
                ogretmen_id = self.c.lastrowid
            else:
                ogretmen_id = teacher_row[0]

            # 2. Ensure Course exists
            self.c.execute("SELECT ders_instance FROM Dersler WHERE ders_adi = ?", (ders_adi,))
            course_rows = self.c.fetchall()
            
            if not course_rows:
                # Create new course entry
                instance = self.ders_ekle(ders_adi, ders_kodu="CODE", teori_odasi=None, lab_odasi=None)
            else:
                # Use the first instance found
                instance = course_rows[0][0]

            # 3. Add to Ders_Programi
            self.c.execute('''
                INSERT INTO Ders_Programi (ders_adi, ders_instance, ogretmen_id, gun, baslangic, bitis)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (ders_adi, instance, ogretmen_id, gun, baslangic, bitis))
            
            self.conn.commit()
            
            # Emit signal
            saat = f"{baslangic}-{bitis}"
            course_info = f"{ders_adi} - {hoca_adi} - {gun} {saat}"
            self.course_added.emit(course_info)
            return True
            
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
            # Parse info: "Matematik - Ahmet Hoca - Pazartesi 09:00-09:50"
            parts = course_info.split(" - ")
            if len(parts) != 3:
                raise ValueError("Format hatası")
            
            ders_adi = parts[0]
            hoca_adi = parts[1]
            time_part = parts[2] # "Pazartesi 09:00-09:50"
            
            gun = time_part.split(' ')[0]
            saat_araligi = time_part.split(' ')[1]
            baslangic = saat_araligi.split('-')[0]
            
            # Find IDs to delete specific entry
            query = '''
                SELECT dp.program_id
                FROM Ders_Programi dp
                JOIN Ogretmenler o ON dp.ogretmen_id = o.ogretmen_num
                WHERE dp.ders_adi = ? 
                AND (o.ad || ' ' || o.soyad) = ?
                AND dp.gun = ?
                AND dp.baslangic = ?
            '''
            self.c.execute(query, (ders_adi, hoca_adi, gun, baslangic))
            row = self.c.fetchone()
            
            if row:
                program_id = row[0]
                self.c.execute("DELETE FROM Ders_Programi WHERE program_id = ?", (program_id,))
                self.conn.commit()
                self.course_removed.emit(course_info)
                return True
            else:
                self.error_occurred.emit("Silinecek ders bulunamadı!")
                return False
                
        except Exception as e:
            self.error_occurred.emit(f"Ders silinirken hata: {str(e)}")
            return False
    
    def get_all_courses(self) -> List[str]:
        """
        Get all courses from database
        
        Returns:
            List[str]: List of course information strings
        """
        try:
            query = '''
                SELECT dp.ders_adi, o.ad || ' ' || o.soyad, dp.gun, dp.baslangic, dp.bitis
                FROM Ders_Programi dp
                JOIN Ogretmenler o ON dp.ogretmen_id = o.ogretmen_num
            '''
            self.c.execute(query)
            rows = self.c.fetchall()
            
            courses = []
            for ders, hoca, gun, baslangic, bitis in rows:
                saat = f"{baslangic}-{bitis}"
                course_info = f"{ders} - {hoca} - {gun} {saat}"
                courses.append(course_info)
            return courses
        except Exception as e:
            self.error_occurred.emit(f"Dersler yüklenirken hata: {str(e)}")
            return []
    
    def get_teachers(self) -> List[str]:
        """
        Get all unique teacher names
        
        Returns:
            List[str]: List of teacher names
        """
        try:
            self.c.execute("SELECT ad || ' ' || soyad FROM Ogretmenler")
            return [row[0] for row in self.c.fetchall()]
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
            self.c.execute("SELECT baslangic, bitis FROM Ders_Programi WHERE gun = ?", (gun,))
            existing_times = self.c.fetchall()
            
            for exist_start, exist_end in existing_times:
                if (baslangic < exist_end and bitis > exist_start):
                    return True
            return False
        except Exception as e:
            print(f"Conflict check error: {e}")
            return True

    def get_schedule_by_teacher(self, teacher_id: int) -> List[tuple]:
        """Get schedule for a specific teacher"""
        try:
            query = '''
                SELECT dp.gun, dp.baslangic, dp.bitis, dp.ders_adi, 
                       (SELECT derslik_adi FROM Derslikler WHERE derslik_num = d.teori_odasi) as oda
                FROM Ders_Programi dp
                JOIN Dersler d ON dp.ders_adi = d.ders_adi AND dp.ders_instance = d.ders_instance
                WHERE dp.ogretmen_id = ?
            '''
            self.c.execute(query, (teacher_id,))
            return self.c.fetchall()
        except Exception as e:
            print(f"Error fetching teacher schedule: {e}")
            return []

    def get_schedule_by_classroom(self, classroom_id: int) -> List[tuple]:
        """Get schedule for a specific classroom"""
        try:
            query = '''
                SELECT dp.gun, dp.baslangic, dp.bitis, dp.ders_adi,
                       (SELECT ad || ' ' || soyad FROM Ogretmenler WHERE ogretmen_num = dp.ogretmen_id) as hoca
                FROM Ders_Programi dp
                JOIN Dersler d ON dp.ders_adi = d.ders_adi AND dp.ders_instance = d.ders_instance
                WHERE d.teori_odasi = ? OR d.lab_odasi = ?
            '''
            self.c.execute(query, (classroom_id, classroom_id))
            return self.c.fetchall()
        except Exception as e:
            print(f"Error fetching classroom schedule: {e}")
            return []

    def get_schedule_by_student_group(self, bolum_id: int, sinif_duzeyi: int) -> List[tuple]:
        """Get schedule for a specific student group (Department + Year)"""
        try:
            query = '''
                SELECT dp.gun, dp.baslangic, dp.bitis, dp.ders_adi,
                       (SELECT ad || ' ' || soyad FROM Ogretmenler WHERE ogretmen_num = dp.ogretmen_id) as hoca,
                       (SELECT derslik_adi FROM Derslikler WHERE derslik_num = d.teori_odasi) as oda
                FROM Ders_Programi dp
                JOIN Dersler d ON dp.ders_adi = d.ders_adi AND dp.ders_instance = d.ders_instance
                JOIN Ders_Sinif_Iliskisi dsi ON d.ders_adi = dsi.ders_adi AND d.ders_instance = dsi.ders_instance
                JOIN Ogrenci_Donemleri od ON dsi.donem_sinif_num = od.donem_sinif_num
                WHERE od.bolum_num = ? AND od.sinif_duzeyi = ?
            '''
            self.c.execute(query, (bolum_id, sinif_duzeyi))
            return self.c.fetchall()
        except Exception as e:
            print(f"Error fetching student schedule: {e}")
            return []

    def get_all_teachers_with_ids(self) -> List[Tuple[int, str]]:
        """Get all teachers with their IDs"""
        try:
            self.c.execute("SELECT ogretmen_num, ad || ' ' || soyad FROM Ogretmenler ORDER BY ad")
            return self.c.fetchall()
        except Exception as e:
            print(f"Error fetching teachers: {e}")
            return []
            
    def get_all_classrooms_with_ids(self) -> List[Tuple[int, str]]:
        """Get all classrooms with their IDs"""
        try:
            self.c.execute("SELECT derslik_num, derslik_adi FROM Derslikler WHERE silindi = 0 ORDER BY derslik_adi")
            return self.c.fetchall()
        except Exception as e:
            print(f"Error fetching classrooms: {e}")
            return []

    def get_departments_by_faculty(self, faculty_id: int) -> List[Tuple[int, str]]:
        """Get departments for a faculty"""
        try:
            self.c.execute("SELECT bolum_id, bolum_adi FROM Bolumler WHERE fakulte_num = ? ORDER BY bolum_adi", (faculty_id,))
            return self.c.fetchall()
        except Exception as e:
            print(f"Error fetching departments: {e}")
            return []  # Return True to be safe
    
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



    def get_student_grades(self, student_id: int, show_history: bool = False) -> List[tuple]:
        """
        Get student grades.
        If show_history is False, returns only the latest attempt for each course.
        """
        try:
            if show_history:
                query = "SELECT * FROM Ogrenci_Notlari WHERE ogrenci_num = ? ORDER BY donem DESC"
                self.c.execute(query, (student_id,))
            else:
                # Filter out grades that are referenced as 'previous' by another grade
                query = '''
                    SELECT t1.*
                    FROM Ogrenci_Notlari t1
                    LEFT JOIN Ogrenci_Notlari t2 ON t1.id = t2.onceki_not_id
                    WHERE t1.ogrenci_num = ? AND t2.id IS NULL
                    ORDER BY t1.donem DESC
                '''
                self.c.execute(query, (student_id,))
            return self.c.fetchall()
        except Exception as e:
            print(f"Error fetching grades: {e}")
            return []

    def get_students(self, filters: Dict[str, any] = None) -> List[tuple]:
        """
        Get students based on filters.
        filters: {'fakulte_id': int, 'bolum_id': int, 'sinif': int, 'search': str}
        Returns: List of (ogrenci_num, ad, soyad, bolum_adi, sinif)
        """
        try:
            query = '''
                SELECT o.ogrenci_num, o.ad, o.soyad, b.bolum_adi, o.kacinci_donem
                FROM Ogrenciler o
                JOIN Bolumler b ON o.bolum_num = b.bolum_id
                WHERE 1=1
            '''
            params = []

            if filters:
                if filters.get('fakulte_id'):
                    query += " AND o.fakulte_num = ?"
                    params.append(filters['fakulte_id'])
                
                if filters.get('bolum_id'):
                    query += " AND o.bolum_num = ?"
                    params.append(filters['bolum_id'])
                
                if filters.get('sinif'):
                    # kacinci_donem is semester count (1-8). Year = (kacinci_donem + 1) // 2
                    # So Year 1: 1,2; Year 2: 3,4; etc.
                    target_year = filters['sinif']
                    min_sem = (target_year * 2) - 1
                    max_sem = target_year * 2
                    query += " AND o.kacinci_donem BETWEEN ? AND ?"
                    params.extend([min_sem, max_sem])
                
                if filters.get('search'):
                    search_term = f"%{filters['search']}%"
                    query += " AND (o.ad LIKE ? OR o.soyad LIKE ? OR CAST(o.ogrenci_num AS TEXT) LIKE ?)"
                    params.extend([search_term, search_term, search_term])

            query += " ORDER BY o.ad, o.soyad"
            
            self.c.execute(query, params)
            return self.c.fetchall()
        except Exception as e:
            print(f"Error fetching students: {e}")
            return []

    def get_all_faculties(self) -> List[tuple]:
        """Get all faculties (id, name)"""
        try:
            self.c.execute("SELECT fakulte_num, fakulte_adi FROM Fakulteler")
            return self.c.fetchall()
        except Exception as e:
            print(f"Error fetching faculties: {e}")
            return []

    def get_all_departments(self) -> List[tuple]:
        """Get all departments (id, name)"""
        try:
            self.c.execute("SELECT bolum_id, bolum_adi FROM Bolumler")
            return self.c.fetchall()
        except Exception as e:
            print(f"Error fetching departments: {e}")
            return []
