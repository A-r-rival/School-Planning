# -*- coding: utf-8 -*-
import sqlite3
from datetime import datetime

simdiki_sene = datetime.now().year

class DbManager:
    def __init__(self, db_path="okul_veritabani.db"):
        self.conn = sqlite3.connect(db_path)
        self.c = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        db_create = [
            '''CREATE TABLE IF NOT EXISTS Fakulteler (
                fakulte_num INTEGER PRIMARY KEY AUTOINCREMENT,
                fakulte_adi TEXT NOT NULL
            )''',

            '''CREATE TABLE IF NOT EXISTS Bolumler (
                bolum_num INTEGER NOT NULL DEFAULT 0,
                bolum_adi TEXT NOT NULL,
                fakulte_num INTEGER NOT NULL,
                PRIMARY KEY (fakulte_num, bolum_num),
                FOREIGN KEY (fakulte_num) REFERENCES Fakulteler(fakulte_num)
            )''',

            '''CREATE TABLE IF NOT EXISTS Siniflar (
                sinif_num INTEGER,
                sinif_duzeyi INTEGER NOT NULL CHECK (sinif_duzeyi BETWEEN 1 AND 4),
                bolum_num INTEGER NOT NULL,
                PRIMARY KEY (sinif_duzeyi, bolum_num),
                FOREIGN KEY (bolum_num) REFERENCES Bolumler(bolum_num)
            )''',

            '''CREATE TABLE IF NOT EXISTS Dersler (
                ders_kodu TEXT,
                ders_instance INTEGER NOT NULL DEFAULT 0,
                ders_adi TEXT NOT NULL,
                teori_odasi INTEGER,
                lab_odasi INTEGER,
                PRIMARY KEY (ders_adi, ders_instance),
                FOREIGN KEY (teori_odasi) REFERENCES Derslikler(derslik_num),
                FOREIGN KEY (lab_odasi) REFERENCES Derslikler(derslik_num)
            )''',

            '''CREATE TABLE IF NOT EXISTS Ders_Sinif_Iliskisi (
                ders_adi TEXT,
                ders_instance INTEGER,
                sinif_num TEXT,
                PRIMARY KEY (ders_instance, sinif_num, ders_adi),
                FOREIGN KEY (ders_instance, ders_adi) REFERENCES Dersler(ders_instance, ders_adi) ON DELETE CASCADE,
                FOREIGN KEY (sinif_num) REFERENCES Siniflar(sinif_num)
            )''',

            '''CREATE TABLE IF NOT EXISTS Ogrenciler (
                ogrenci_num INTEGER PRIMARY KEY,
                ad TEXT NOT NULL,
                soyad TEXT NOT NULL,
                girme_senesi INTEGER NOT NULL,
                kacinci_donem INTEGER NOT NULL,
                sinif_duzeyi INTEGER NOT NULL CHECK (sinif_duzeyi BETWEEN 0 AND 4)
                bolumu TEXT NOT NULL,
                mezun_durumu INTEGER DEFAULT 0, -- 0: Hazirlik, 1: Okuyor, 2: Mezun
                --Yandal/ÇAP
                ikinci_bolumu TEXT,
                ikinci_bolum_turu TEXT CHECK(ikinci_bolum_turu IN ('Yandal', 'Anadal')), --Null eklemeye gerek yok, true false da unknown verir o da geçerli kabul edilir
                ogrenci_num2 INTEGER
                girme_senesi2 INTEGER,
                kacinci_donem2 INTEGER,
                FOREIGN KEY (sinif_num) REFERENCES Siniflar(sinif_num)
            )''',

            '''CREATE TABLE IF NOT EXISTS Verilen_Dersler (
                ogrenci_num
                ders_listesi --burada dersleri string olarak yanyana koyup saklayacak
            )''',

            '''CREATE TABLE IF NOT EXISTS Alınan_Dersler (
                ders_adi TEXT,
                ders_instance INTEGER,
                sinif_num TEXT,
                PRIMARY KEY (ders_instance, sinif_num, ders_adi),
                FOREIGN KEY (ders_instance, ders_adi) REFERENCES Dersler(ders_instance, ders_adi) ON DELETE CASCADE,
                FOREIGN KEY (sinif_num) REFERENCES Siniflar(sinif_num)
            )''',

            '''CREATE TABLE IF NOT EXISTS Derslikler (
                derslik_num INTEGER PRIMARY KEY AUTOINCREMENT,
                derslik_adi TEXT NOT NULL UNIQUE,
                tip TEXT NOT NULL CHECK (tip IN ('lab', 'amfi')),
                kapasite INTEGER NOT NULL,
                ozellikler TEXT
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
                sinif_num TEXT,
                PRIMARY KEY (ders_instance, sinif_num, ders_adi),
                FOREIGN KEY (ders_instance, ders_adi) REFERENCES Dersler(ders_instance, ders_adi) ON DELETE CASCADE,
                FOREIGN KEY (sinif_num) REFERENCES Siniflar(sinif_num)
            )'''
        ]
        for sql in db_create:
            self.c.execute(sql)
        self.conn.commit()

    def fakulte_numarasini_al(ogrenci_num2: int) -> int:
        numara_str = str(ogrenci_num2).zfill(10)  # 10 haneye tamamla, güvenlik için
        return int(numara_str[2:4])
    
    def bolum_numarasini_al(bolum_adi: str, fakulte_num: int) -> int:
        conn = sqlite3.connect("okul_veritabani.db")
        c = conn.cursor()
        
        c.execute('''
            SELECT bolum_num 
            FROM Bolumler 
            WHERE bolum_adi = ? AND fakulte_num = ?
        ''', (bolum_adi, fakulte_num))
        
        sonuc = c.fetchone()
        conn.close()
        
        if sonuc:
            return sonuc[0]
        else:
            raise ValueError(f"{bolum_adi} adında ve {fakulte_num} fakülte numarasında bir bölüm bulunamadı.")


    # Fakülte ekle
    def fakulte_ekle(self, fakulte_adi):
        self.c.execute("INSERT INTO Fakulteler (fakulte_adi) VALUES (?)", (fakulte_adi,))
        self.conn.commit()
        return self.c.lastrowid
    

    # Bölüm ekle (otomatik bolum_num ataması)
    def bolum_ekle(self, fakulte_identifier, bolum_adi, by_name=False):
        """
        Bolum ekler.
        :param fakulte_identifier: Fakulte numarası (int) veya fakulte adı (str)
        :param bolum_adi: Eklenecek bölümün adı (str)
        :param by_name: True ise fakulte_identifier fakulte adı olarak değerlendirilir.
                        False ise fakulte numarası olarak değerlendirilir.
        :return: Yeni bölüm numarası (int)
        """
        if by_name:
            # Fakülte adından numarasını bul
            self.c.execute('SELECT fakulte_num FROM Fakulteler WHERE fakulte_adi = ?', (fakulte_identifier,))
            res = self.c.fetchone()
            if res is None:
                raise ValueError(f"Fakulte adi '{fakulte_identifier}' bulunamadi.")
            fakulte_num = res[0]
        else:
            fakulte_num = fakulte_identifier

        # Bölüm numarasını hesapla
        self.c.execute('SELECT COALESCE(MAX(bolum_num), 0) + 1 FROM Bolumler WHERE fakulte_num = ?', (fakulte_num,))
        yeni_bolum_num = self.c.fetchone()[0]

        # Bölüm ekle
        self.c.execute('''
            INSERT INTO Bolumler (bolum_num, bolum_adi, fakulte_num)
            VALUES (?, ?, ?)
        ''', (yeni_bolum_num, bolum_adi, fakulte_num))
        self.conn.commit()
        return yeni_bolum_num
    

    # Sınıf ekle (otomatik sinif_num hesaplaması)
    def sinif_ekle(self, bolum_num, sinif_duzeyi):
        self.c.execute('SELECT fakulte_num FROM Bolumler WHERE bolum_num = ?', (bolum_num,))
        result = self.c.fetchone()
        if not result:
            raise ValueError("Bölüm bulunamadı.")
        fakulte_num = result[0]

        sinif_num = int(f"{fakulte_num}{bolum_num}0{sinif_duzeyi}")

        self.c.execute('''
            INSERT INTO Siniflar (sinif_num, sinif_duzeyi, bolum_num) 
            VALUES (?, ?, ?)
        ''', (sinif_num, sinif_duzeyi, bolum_num))
        self.conn.commit()
        return sinif_num
    

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

        ogrenci_num = int(f"{str(girme_senesi)[-2:]}0{fakulte_num:02d}{bolum_num:02d}{program_tipi}{sira:03d}")

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
                     girme_senesi2=None, kacinci_donem=None,):

        # Program tipi belirleme (8: yandal, 9: ikinci anadal)
        if ikinci_bolum_turu.lower() == 'yandal':
            program_tipi = 8
        elif ikinci_bolum_turu.lower() == 'anadal':
            program_tipi = 9
        else:
            raise ValueError("Geçersiz ikinci bölüm türü: 'Yandal' veya 'Anadal' olmalı.")
        
        if girme_senesi2 is None:
            girme_senesi = simdiki_sene

        #Otomatik döenm atlama getir FNORD!

        fakulte_num = fakulte_numarasini_al(ogrenci_num)
        bolum_num2 = bolum_numarasini_al(ikinci_bolumu, fakulte_num)

        # Aynı yıl, fakülte, bölüm ve program tipinde kaç kişi kayıtlı?
        self.c.execute('''
            SELECT COUNT(*) FROM Ogrenciler
            WHERE girme_senesi2 = ?
              AND bolum_num2 = ?
              AND fakulte_num = ?
              AND (
                  (? = 8 AND ikinci_bolum_turu = 'Yandal') OR
                  (? = 9 AND ikinci_bolum_turu = 'Anadal')
              )
        ''', (girme_senesi, bolum_num, fakulte_num, program_tipi, program_tipi, program_tipi))
        sira = self.c.fetchone()[0] + 1

        # Öğrenci numarası: YY0FBBPSSS
        ogrenci_num2 = int(f"{str(girme_senesi)[-2:]}0{fakulte_num:02d}{bolum_num:02d}{program_tipi}{sira:03d}")

        self.c.execute('''
            UPDATE Ogrenciler
            SET ikinci_bolumu = ?, ikinci_bolum_turu = ?, ogrenci_num2 = ?, girme_senesi2 = ?, kacinci_donem2 = ?
            WHERE ogrenci_num = ?
        ''', (ikinci_bolumu, ikinci_bolum_turu, ogrenci_num2, girme_senesi2, kacinci_donem2, ogrenci_num))

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

    def alinan_ders_ekle(self, ders_adi, ders_instance, sinif_num):
        self.c.execute('''
            INSERT OR IGNORE INTO Alınan_Dersler (ders_adi, ders_instance, sinif_num)
            VALUES (?, ?, ?)
        ''', (ders_adi, ders_instance, sinif_num))
        self.conn.commit()

    def alinan_dersleri_getir(self, sinif_num):
        self.c.execute('SELECT ders_adi, ders_instance FROM Alınan_Dersler WHERE sinif_num = ?', (sinif_num,))
        return self.c.fetchall()
    

    def close(self):
        self.conn.close()


# Kullanım örneği
if __name__ == "__main__":
    db = DbManager()

    # Fakulte numarasına göre
    bolum_num1 = db.bolum_ekle(1, "Makine Mühendisliği")
    # Fakulte adına göre
    bolum_num2 = db.bolum_ekle("Mühendislik Fakültesi", "Elektrik Mühendisliği", by_name=True)

    bolum_num = db.bolum_ekle(fakulte_id, "Bilgisayar Mühendisliği")

    sinif_num = db.sinif_ekle(bolum_num, 3)

    ders_instance = db.ders_ekle("Matematik", ders_kodu="MAT101")

    print(f"Fakulte ID: {fakulte_id}")
    print(f"Bolum No: {bolum_num}")
    print(f"Sinif No: {sinif_num}")
    print(f"Ders Instance: {ders_instance}")

    db.close()
