# -*- coding: utf-8 -*-
"""
Initial database schema migration.
Creates all tables and indexes for base functionality.
"""
import sqlite3


def create_initial_schema(conn: sqlite3.Connection) -> None:
    """
    Create complete initial database schema.
    
    Tables created:
    - Fakulteler (Faculties)
    - Bolumler (Departments)
    - Ogrenci_Donemleri (Student semesters/periods)
    - Dersler (Courses)
    - Ders_Sinif_Iliskisi (Course-Class relationships)
    - Ders_Havuz_Iliskisi (Course-Pool relationships)
    - Ogrenciler (Students)
    - Verilen_Dersler (Given courses)
    - Alinan_Dersler (Taken courses)
    - Derslikler (Classrooms)
    - Ogretmenler (Teachers)
    - Ders_Ogretmen_Iliskisi (Course-Teacher relationships)
    - Ders_Programi (Schedule)
    - Ogrenci_Notlari (Student grades)
    - Ogretmen_Musaitlik (Teacher unavailability)
    
    Args:
        conn: Database connection
    """
    tables = [
        '''CREATE TABLE IF NOT EXISTS Fakulteler (
            fakulte_num INTEGER PRIMARY KEY AUTOINCREMENT,
            fakulte_adi TEXT NOT NULL
        )''',

        '''CREATE TABLE IF NOT EXISTS Bolumler (
            bolum_id INTEGER PRIMARY KEY,
            bolum_num INTEGER NOT NULL,
            bolum_adi TEXT NOT NULL,
            fakulte_num INTEGER NOT NULL,
            UNIQUE (fakulte_num, bolum_num),
            FOREIGN KEY (fakulte_num) REFERENCES Fakulteler(fakulte_num)
        )''',

        '''CREATE TABLE IF NOT EXISTS Ogrenci_Donemleri (
            donem_sinif_num TEXT PRIMARY KEY,
            baslangic_yili INTEGER,
            bolum_num INTEGER NOT NULL,
            sinif_duzeyi INTEGER NOT NULL CHECK (sinif_duzeyi BETWEEN 0 AND 5),
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
            kacinci_donem INTEGER NOT NULL,
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
            derslik_tipi TEXT NOT NULL,
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

    # Create tables
    with conn:
        for statement in tables:
            conn.execute(statement)
        
        # Create indexes
        for index_sql in indexes:
            conn.execute(index_sql)
