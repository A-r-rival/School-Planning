# -*- coding: utf-8 -*-
"""
Schedule Model - MVC Pattern
Handles all data operations and business logic
"""
import os
import sqlite3
import re
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
                teori_saati INTEGER DEFAULT 0,
                uygulama_saati INTEGER DEFAULT 0,
                lab_saati INTEGER DEFAULT 0,
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

            '''CREATE TABLE IF NOT EXISTS Ders_Havuz_Iliskisi (
                iliski_id INTEGER PRIMARY KEY AUTOINCREMENT,
                ders_instance INTEGER NOT NULL,
                ders_adi TEXT NOT NULL,
                bolum_num INTEGER NOT NULL,
                havuz_kodu TEXT NOT NULL,
                FOREIGN KEY (ders_instance, ders_adi) REFERENCES Dersler(ders_instance, ders_adi) ON DELETE CASCADE,
                FOREIGN KEY (bolum_num) REFERENCES Bolumler(bolum_num) ON DELETE CASCADE,
                UNIQUE(ders_instance, ders_adi, bolum_num, havuz_kodu)
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
                derslik_tipi TEXT NOT NULL, -- Added for room types (Lab, Amfi, etc.)
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
                ogretmen_id INTEGER,
                PRIMARY KEY (ders_instance, ders_adi, ogretmen_id),
                FOREIGN KEY (ders_instance, ders_adi) REFERENCES Dersler(ders_instance, ders_adi) ON DELETE CASCADE,
                FOREIGN KEY (ogretmen_id) REFERENCES Ogretmenler(ogretmen_num)
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
            )''',

            '''CREATE TABLE IF NOT EXISTS Ogretmen_Musaitlik (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ogretmen_id INTEGER NOT NULL,
                gun TEXT NOT NULL,
                baslangic TEXT NOT NULL,
                bitis TEXT NOT NULL,
                FOREIGN KEY (ogretmen_id) REFERENCES Ogretmenler(ogretmen_num) ON DELETE CASCADE
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
            self.c.execute("SELECT ders_instance, ders_kodu FROM Dersler WHERE ders_adi = ?", (ders_adi,))
            course_rows = self.c.fetchall()
            
            if not course_rows:
                # Create new course entry
                # Default code is generated or placeholder
                default_code = "CODE"
                instance = self.ders_ekle(ders_adi, ders_kodu=default_code, teori_odasi=None, lab_odasi=None)
                current_code = default_code
            else:
                # Use the first instance found
                instance = course_rows[0][0]
                current_code = course_rows[0][1] if course_rows[0][1] else "CODE"

            # 3. Add to Ders_Programi
            self.c.execute('''
                INSERT INTO Ders_Programi (ders_adi, ders_instance, ogretmen_id, gun, baslangic, bitis)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (ders_adi, instance, ogretmen_id, gun, baslangic, bitis))
            
            self.conn.commit()
            
            # Fetch connected classes for display
            self.c.execute('''
                SELECT GROUP_CONCAT(DISTINCT b.bolum_adi || ' ' || od.sinif_duzeyi || '. Sınıf')
                FROM Ders_Sinif_Iliskisi dsi
                JOIN Ogrenci_Donemleri od ON dsi.donem_sinif_num = od.donem_sinif_num
                JOIN Bolumler b ON od.bolum_num = b.bolum_id
                WHERE dsi.ders_instance = ? AND dsi.ders_adi = ?
            ''', (instance, ders_adi))
            class_row = self.c.fetchone()
            classes_str = f" [{class_row[0]}]" if class_row and class_row[0] else ""

            # Emit signal
            saat = f"{baslangic}-{bitis}"
            # Format: [Code] Name - Teacher (Day Time) [Classes]
            course_info = f"[{current_code}] {ders_adi} - {hoca_adi} ({gun} {saat}){classes_str}"
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
            # Parse info: "[Code] Name - Teacher (Day Start-End) [Classes]"
            
            # 1. Try regex for new format (flexible end)
            import re
            match = re.search(r"\[(.*?)\] (.*?) - (.*?) \((.*?) (\d{2}:\d{2})-(\d{2}:\d{2})\)", course_info)
            
            if match:
                code, ders_adi, hoca_adi, gun, baslangic, bitis = match.groups()
            else:
                # 2. Try legacy split (fallback)
                parts = course_info.split(" - ")
                if len(parts) >= 3:
                    ders_adi = parts[0]
                    hoca_adi = parts[1]
                    # Handle "Pazartesi 09:00-09:50" or "[Code] Name ..." parts if split failed differently
                    if "]" in ders_adi: # clean [Code] suffix if existing in split
                         ders_adi = ders_adi.split("] ")[-1]
                         
                    # Handle "Pazartesi 09:00-09:50" or "(Pazartesi 09:00-09:50)"
                    time_part_full = parts[2]
                    # basic cleanup for time part
                    if "(" in time_part_full:
                         time_part_full = time_part_full.split("(")[1].split(")")[0]
                    
                    gun_parts = time_part_full.split(' ')
                    if len(gun_parts) >= 2:
                        gun = gun_parts[0]
                        saat_araligi = gun_parts[1]
                        baslangic = saat_araligi.split('-')[0]
                    else:
                        raise ValueError("Saat formatı hatası")
                else:
                    raise ValueError("Format hatası")
            
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
                SELECT dp.ders_adi, o.ad || ' ' || o.soyad, dp.gun, dp.baslangic, dp.bitis, d.ders_kodu,
                       GROUP_CONCAT(DISTINCT b.bolum_adi || ' ' || od.sinif_duzeyi || '. Sınıf')
                FROM Ders_Programi dp
                JOIN Ogretmenler o ON dp.ogretmen_id = o.ogretmen_num
                JOIN Dersler d ON dp.ders_adi = d.ders_adi AND dp.ders_instance = d.ders_instance
                LEFT JOIN Ders_Sinif_Iliskisi dsi ON d.ders_adi = dsi.ders_adi AND d.ders_instance = dsi.ders_instance
                LEFT JOIN Ogrenci_Donemleri od ON dsi.donem_sinif_num = od.donem_sinif_num
                LEFT JOIN Bolumler b ON od.bolum_num = b.bolum_id
                GROUP BY dp.program_id, dp.ders_adi, o.ad, o.soyad, dp.gun, dp.baslangic, dp.bitis, d.ders_kodu
            '''
            self.c.execute(query)
            rows = self.c.fetchall()
            
            courses = []
            for ders, hoca, gun, baslangic, bitis, kodu, siniflar in rows:
                saat = f"{baslangic}-{bitis}"
                # Format match: [Code] Name - Teacher (Day Time) [Classes]
                display_code = kodu if kodu else "CODE"
                classes_str = f" [{siniflar}]" if siniflar else ""
                course_info = f"[{display_code}] {ders} - {hoca} ({gun} {saat}){classes_str}"
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
                       (SELECT derslik_adi FROM Derslikler WHERE derslik_num = dp.derslik_id) as oda,
                       d.ders_kodu, dp.ders_tipi
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
                       (SELECT ad || ' ' || soyad FROM Ogretmenler WHERE ogretmen_num = dp.ogretmen_id) as hoca,
                       GROUP_CONCAT(DISTINCT d.ders_kodu), dp.ders_tipi
                FROM Ders_Programi dp
                JOIN Dersler d ON dp.ders_adi = d.ders_adi AND dp.ders_instance = d.ders_instance
                WHERE d.teori_odasi = ? OR d.lab_odasi = ?
                GROUP BY dp.gun, dp.baslangic, dp.bitis, dp.ders_adi, dp.ogretmen_id, dp.ders_tipi
            '''
#SQL kuralı: GROUP BY kullanırken, SELECT'teki aggregate olmayan (örn: SUM, COUNT, GROUP_CONCAT gibi fonksiyon kullanmayan) tüm sütunlar GROUP BY'da da olmalı
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
                       (SELECT derslik_adi FROM Derslikler WHERE derslik_num = dp.derslik_id) as oda,
                       d.ders_kodu, dp.ders_tipi
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
        """Get all classrooms with their IDs sorted naturally"""
        try:
            self.c.execute("SELECT derslik_num, derslik_adi FROM Derslikler WHERE silindi = 0")
            rows = self.c.fetchall()
            
            # Natural sort helper - sorts "Derslik 2" before "Derslik 10"
            def natural_keys(classroom_tuple):
                classroom_name = classroom_tuple[1]  # Get name from (id, name) tuple
                parts = re.split(r'(\d+)', classroom_name)  # Split into text and numbers
                
                # Convert number strings to integers, keep text as lowercase
                converted_parts = []
                for part in parts:
                    if part.isdigit():
                        converted_parts.append(int(part))  # "10" -> 10
                    else:
                        converted_parts.append(part.lower())  # "Derslik " -> "derslik "
                
                return converted_parts
                
            return sorted(rows, key=natural_keys)
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

    def get_courses_by_faculty(self, faculty_id: int, year: str = None, day: str = None) -> List[str]:
        """Fetch all scheduled courses for a faculty from Ders_Programi"""
        try:
            # Query Ders_Programi to get scheduled items with Teacher and Time
            query = """
                SELECT dp.ders_adi, GROUP_CONCAT(DISTINCT d.ders_kodu), 
                       (o.ad || ' ' || o.soyad) as hoca, dp.gun, dp.baslangic, dp.bitis,
                       GROUP_CONCAT(DISTINCT b.bolum_adi || ' ' || od.sinif_duzeyi || '. Sınıf') as siniflar
                FROM Ders_Programi dp
                JOIN Dersler d ON dp.ders_adi = d.ders_adi AND dp.ders_instance = d.ders_instance
                JOIN Ders_Sinif_Iliskisi dsi ON d.ders_instance = dsi.ders_instance AND d.ders_adi = dsi.ders_adi
                JOIN Ogrenci_Donemleri od ON dsi.donem_sinif_num = od.donem_sinif_num
                JOIN Bolumler b ON od.bolum_num = b.bolum_id
                LEFT JOIN Ogretmenler o ON dp.ogretmen_id = o.ogretmen_num
                WHERE b.fakulte_num = ?
            """
            params = [faculty_id]
            
            if year and str(year).isdigit():
                query += " AND od.sinif_duzeyi = ?"
                params.append(int(year))
                
            if day:
                query += " AND dp.gun = ?"
                params.append(day)
                
            # Group by schedule slot to merge codes if same course is shared
            query += " GROUP BY dp.gun, dp.baslangic, dp.bitis, dp.ders_adi, o.ad, o.soyad ORDER BY dp.ders_adi, dp.baslangic"
                
            self.c.execute(query, params)
            rows = self.c.fetchall()
            
            # Format: [CODE] Name - Teacher (Day Time) [Classes]
            result = []
            for r in rows:
                ders_adi = r[0]
                codes = r[1]
                hoca = r[2] if r[2] else "Belirsiz"
                gun = r[3]
                saat = f"{r[4]}-{r[5]}"
                siniflar = r[6]
                classes_str = f" [{siniflar}]" if siniflar else ""
                result.append(f"[{codes}] {ders_adi} - {hoca} ({gun} {saat}){classes_str}")
            return result
        except Exception as e:
            print(f"Error fetching faculty courses: {e}")
            return []

    def get_courses_by_department(self, dept_id: int, year: str = None, day: str = None) -> List[str]:
        """Fetch scheduled courses for a specific department from Ders_Programi"""
        try:
            query = """
                SELECT dp.ders_adi, GROUP_CONCAT(DISTINCT d.ders_kodu),
                       (o.ad || ' ' || o.soyad) as hoca, dp.gun, dp.baslangic, dp.bitis,
                       GROUP_CONCAT(DISTINCT b.bolum_adi || ' ' || od.sinif_duzeyi || '. Sınıf') as siniflar
                FROM Ders_Programi dp
                JOIN Dersler d ON dp.ders_adi = d.ders_adi AND dp.ders_instance = d.ders_instance
                JOIN Ders_Sinif_Iliskisi dsi ON d.ders_instance = dsi.ders_instance AND d.ders_adi = dsi.ders_adi
                JOIN Ogrenci_Donemleri od ON dsi.donem_sinif_num = od.donem_sinif_num
                JOIN Bolumler b ON od.bolum_num = b.bolum_id
                LEFT JOIN Ogretmenler o ON dp.ogretmen_id = o.ogretmen_num
                WHERE od.bolum_num = ?
            """
            params = [dept_id]
            
            if year and str(year).isdigit():
                query += " AND od.sinif_duzeyi = ?"
                params.append(int(year))
                
            if day:
                query += " AND dp.gun = ?"
                params.append(day)

            query += " GROUP BY dp.gun, dp.baslangic, dp.bitis, dp.ders_adi, o.ad, o.soyad ORDER BY dp.ders_adi, dp.baslangic"

            self.c.execute(query, params)
            rows = self.c.fetchall()
            
            result = []
            for r in rows:
                ders_adi = r[0]
                codes = r[1]
                hoca = r[2] if r[2] else "Belirsiz"
                gun = r[3]
                saat = f"{r[4]}-{r[5]}"
                siniflar = r[6]
                classes_str = f" [{siniflar}]" if siniflar else ""
                result.append(f"[{codes}] {ders_adi} - {hoca} ({gun} {saat}){classes_str}")
            return result
        except Exception as e:
            print(f"Error fetching dept courses: {e}")
            return []
            
    def get_schedule_for_faculty_common(self, faculty_id: int, year: int) -> List[Tuple]:
        """Get schedule for Common Courses of a faculty."""
        try:
            # We group by the schedule slot (day, time, course, teacher) to avoid duplicates
            q2 = """
                SELECT dp.gun, dp.baslangic, dp.bitis, dp.ders_adi, 
                       (o.ad || ' ' || o.soyad), d.teori_odasi, GROUP_CONCAT(DISTINCT d.ders_kodu)
                FROM Ders_Programi dp
                JOIN Dersler d ON dp.ders_adi = d.ders_adi AND dp.ders_instance = d.ders_instance
                LEFT JOIN Ogretmenler o ON dp.ogretmen_id = o.ogretmen_num
                JOIN Ders_Sinif_Iliskisi dsi ON dsi.ders_instance = d.ders_instance AND dsi.ders_adi = d.ders_adi
                JOIN Ogrenci_Donemleri od ON dsi.donem_sinif_num = od.donem_sinif_num
                JOIN Bolumler b ON od.bolum_num = b.bolum_id
                WHERE b.fakulte_num = ? AND od.sinif_duzeyi = ?
                GROUP BY dp.gun, dp.baslangic, dp.bitis, dp.ders_adi, o.ad, o.soyad, d.teori_odasi
            """
            self.c.execute(q2, (faculty_id, year))
            rows = self.c.fetchall()
            result = []
            for r in rows:
                gun, start, end, ders, hoca, room_id, codes = r
                room_name = "Belirsiz"
                if room_id:
                    self.c.execute("SELECT derslik_adi FROM Derslikler WHERE derslik_num=?", (room_id,))
                    rr = self.c.fetchone()
                    if rr: room_name = rr[0]
                result.append((gun, start, end, ders, hoca, room_name, codes))
            return result
        except Exception as e:
            print(f"Error fetching common schedule: {e}")
            return []
    
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
        self.conn.commit()
        return self.c.lastrowid

    def get_course_faculty_map(self) -> Dict[Tuple[str, int], List[str]]:
        """
        Get mapping of (course_name, instance) -> List[Faculty Names]
        Used for restricting Labs to Science/Engineering faculties.
        """
        try:
            query = '''
                SELECT DISTINCT d.ders_adi, d.ders_instance, f.fakulte_adi
                FROM Dersler d
                JOIN Ders_Sinif_Iliskisi dsi ON d.ders_adi = dsi.ders_adi AND d.ders_instance = dsi.ders_instance
                JOIN Ogrenci_Donemleri od ON dsi.donem_sinif_num = od.donem_sinif_num
                JOIN Bolumler b ON od.bolum_num = b.bolum_id
                JOIN Fakulteler f ON b.fakulte_num = f.fakulte_num
            '''
            self.c.execute(query)
            rows = self.c.fetchall()
            
            mapping = {}
            for ders, instance, fakulte in rows:
                key = (ders, instance)
                if key not in mapping:
                    mapping[key] = []
                mapping[key].append(fakulte)
            return mapping
        except Exception as e:
            print(f"Error fetching course faculty map: {e}")
            return {}
    
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
    def ders_ekle(self, ders_adi, ders_kodu=None, teori_odasi=None, lab_odasi=None, teori_saati=0, uygulama_saati=0, lab_saati=0):
        self.c.execute('SELECT ders_instance FROM Dersler WHERE ders_adi = ?', (ders_adi,))
        kullanilanlar = {row[0] for row in self.c.fetchall()}

        instance = 1
        while instance in kullanilanlar:
            instance += 1
        # Kullanılmayan en küçük pozitif sayıyı bulana kadar devam eder.

        self.c.execute('''
            INSERT INTO Dersler (ders_kodu, ders_adi, ders_instance, teori_odasi, lab_odasi, teori_saati, uygulama_saati, lab_saati)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (ders_kodu, ders_adi, instance, teori_odasi, lab_odasi, teori_saati, uygulama_saati, lab_saati))
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
        self.c.execute('SELECT derslik_num, derslik_adi, derslik_tipi, kapasite FROM Derslikler WHERE silindi = 0')
        return self.c.fetchall()

    def tum_derslikleri_getir(self):
        """Tüm derslikleri getir (silinmiş olanlar dahil)"""
        self.c.execute('SELECT derslik_num, derslik_adi, tip, kapasite, silindi, silinme_tarihi FROM Derslikler')
        return self.c.fetchall()

    def add_teacher_unavailability(self, teacher_id: int, day: str, start_time: str, end_time: str) -> bool:
        """
        Add a time slot where the teacher is NOT available.
        """
        try:
            # Check for existing overlap for this teacher
            self.c.execute('''
                SELECT id FROM Ogretmen_Musaitlik 
                WHERE ogretmen_id = ? AND gun = ? 
                AND (
                    (baslangic <= ? AND bitis >= ?) OR
                    (baslangic <= ? AND bitis >= ?) OR
                    (baslangic >= ? AND bitis <= ?)
                )
            ''', (teacher_id, day, start_time, start_time, end_time, end_time, start_time, end_time))
            
            if self.c.fetchone():
                return False # Already marked as unavailable

            self.c.execute('''
                INSERT INTO Ogretmen_Musaitlik (ogretmen_id, gun, baslangic, bitis)
                VALUES (?, ?, ?, ?)
            ''', (teacher_id, day, start_time, end_time))
            self.conn.commit()
            return True
        except Exception as e:
            self.error_occurred.emit(f"Müsaitlik eklenirken hata: {str(e)}")
            return False

    def get_teacher_unavailability(self, teacher_id: int) -> List[tuple]:
        """Get all unavailable slots for a teacher"""
        try:
            self.c.execute('''
                SELECT gun, baslangic, bitis, id 
                FROM Ogretmen_Musaitlik 
                WHERE ogretmen_id = ? 
                ORDER BY 
                    CASE gun 
                        WHEN 'Pazartesi' THEN 1 
                        WHEN 'Salı' THEN 2 
                        WHEN 'Çarşamba' THEN 3 
                        WHEN 'Perşembe' THEN 4 
                        WHEN 'Cuma' THEN 5 
                        WHEN 'Cumartesi' THEN 6 
                        WHEN 'Pazar' THEN 7 
                    END, baslangic
            ''', (teacher_id,))
            return self.c.fetchall()
        except Exception as e:
            print(f"Error fetching unavailability: {e}")
            return []

    def remove_teacher_unavailability(self, unavailability_id: int) -> bool:
        """Remove an unavailability slot"""
        try:
            self.c.execute("DELETE FROM Ogretmen_Musaitlik WHERE id = ?", (unavailability_id,))
            self.conn.commit()
            return True
        except Exception as e:
            self.error_occurred.emit(f"Müsaitlik silinirken hata: {str(e)}")
            return False



    def get_student_grades(self, student_id: int, show_history: bool = False) -> List[tuple]:
        """
        Get student grades.
        If show_history is False, returns only the latest attempt for each course.
        """
        try:
            if show_history:
                query = '''
                    SELECT t1.*, (SELECT akts FROM Dersler WHERE ders_kodu = t1.ders_kodu LIMIT 1) as akts 
                    FROM Ogrenci_Notlari t1 
                    WHERE t1.ogrenci_num = ? 
                    ORDER BY t1.donem DESC
                '''
                self.c.execute(query, (student_id,))
            else:
                # Filter out grades that are referenced as 'previous' by another grade
                query = '''
                    SELECT t1.*, (SELECT akts FROM Dersler WHERE ders_kodu = t1.ders_kodu LIMIT 1) as akts
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
        filters: {
            'fakulte_id': int, 
            'bolum_id': int, 
            'sinif': int, 
            'search': str,
            'show_regular': bool,
            'show_irregular': bool,
            'show_cap_yandal': bool
        }
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
                    target_year = filters['sinif']
                    min_sem = (target_year * 2) - 1
                    max_sem = target_year * 2
                    query += " AND o.kacinci_donem BETWEEN ? AND ?"
                    params.extend([min_sem, max_sem])
                
                if filters.get('search'):
                    search_term = f"%{filters['search']}%"
                    query += " AND (o.ad LIKE ? OR o.soyad LIKE ? OR CAST(o.ogrenci_num AS TEXT) LIKE ?)"
                    params.extend([search_term, search_term, search_term])

                # Student Type Filters
                # Default to showing all if keys are missing (backward compatibility)
                show_regular = filters.get('show_regular', True)
                show_irregular = filters.get('show_irregular', True)
                show_cap_yandal = filters.get('show_cap_yandal', True)

                # If all are true, no need to filter (optimization)
                if not (show_regular and show_irregular and show_cap_yandal):
                    type_conditions = []
                    
                    # Regular: No second major AND expected semester
                    # Expected semester = (Current Year - Entry Year) * 2 + 1 (For Fall)
                    # We use the global simdiki_sene variable. 
                    # NOTE: Database seems to be in Fall 2024 state, but system year is 2025.
                    # Adjusting by -1 to match database state.
                    effective_year = simdiki_sene - 1
                    
                    if show_regular:
                        type_conditions.append(f"(o.ikinci_bolum_turu IS NULL AND o.kacinci_donem = ({effective_year} - o.girme_senesi) * 2 + 1)")
                    
                    # Irregular: No second major AND NOT expected semester
                    if show_irregular:
                        type_conditions.append(f"(o.ikinci_bolum_turu IS NULL AND o.kacinci_donem != ({effective_year} - o.girme_senesi) * 2 + 1)")
                    
                    # ÇAP/Yandal: Has second major
                    if show_cap_yandal:
                        type_conditions.append("(o.ikinci_bolum_turu IS NOT NULL)")
                    
                    if type_conditions:
                        query += " AND (" + " OR ".join(type_conditions) + ")"
                    else:
                        # If all are false, show nothing
                        query += " AND 0"

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
