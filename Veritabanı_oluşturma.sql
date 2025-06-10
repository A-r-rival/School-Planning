--FNORD: to be done RAF: rafa kalktı,şimdilik

-- Fakülteler tablosu
CREATE TABLE Fakulteler (
    fakulte_num INTEGER PRIMARY KEY AUTOINCREMENT,
    fakulte_adi TEXT NOT NULL
);


-- Bölümler tablosu (normal yapı)
CREATE TABLE Bolumler (
    bolum_num INTEGER NOT NULL DEFAULT 0,
    bolum_adi TEXT NOT NULL,
    fakulte_num INTEGER NOT NULL,
    PRIMARY KEY (fakulte_num, bolum_num),
    FOREIGN KEY (fakulte_num) REFERENCES Fakulteler(fakulte_num)
);
-- Bölüm ekleme trigger'ı
CREATE TRIGGER bolum_num_ayarla
BEFORE INSERT ON Bolumler
FOR EACH ROW
BEGIN
    SELECT COALESCE(MAX(bolum_num), 0) + 1 INTO NEW.bolum_num
    FROM Bolumler
    WHERE fakulte_num = NEW.fakulte_num;
END;
--FNORD: Sınıfları otomarik oluştursun

-- Sınıflar tablosu
CREATE TABLE Siniflar (
    sinif_num INTEGER,
    sinif_duzeyi INTEGER NOT NULL CHECK (sinif_duzeyi BETWEEN 1 AND 4),
    bolum_num INTEGER NOT NULL,
    PRIMARY KEY (sinif_duzeyi, bolum_num),
    FOREIGN KEY (bolum_num) REFERENCES Bolumler(bolum_num)
);
-- Sınıf ekleme trigger'ı
CREATE TRIGGER sinif_num_ayarla
BEFORE INSERT ON Siniflar
FOR EACH ROW
BEGIN
    SELECT 
        CAST(b.fakulte_num AS TEXT) || 
        CAST(NEW.bolum_num AS TEXT) || 
        '0' || 
        CAST(NEW.sinif_duzeyi AS TEXT)
    INTO NEW.sinif_num --- Mesela 5703
    FROM Bolumler b
    WHERE b.bolum_num = NEW.bolum_num;
END;


-- Dersler tablosu
CREATE TABLE Dersler (
    ders_kodu TEXT,
    ders_instance INTEGER NOT NULL DEFAULT '0',
    ders_adi TEXT NOT NULL,
    teori_odasi INTEGER,  -- amfi vs.
    lab_odasi INTEGER,    -- varsa lab
    PRIMARY KEY (ders_adi, ders_instance),
    FOREIGN KEY (teori_odasi) REFERENCES Derslikler(derslik_num),
    FOREIGN KEY (lab_odasi) REFERENCES Derslikler(derslik_num)
);
-- Ders instance otomatik ayarlama trigger'ı
CREATE TRIGGER ders_instance_ayarla
BEFORE INSERT ON Dersler
FOR EACH ROW
WHEN NEW.ders_instance IS NULL OR NEW.ders_instance <= 0 ---?
---Belki direkt des_instance'i belirleme imkanını kaldr?
BEGIN
    -- Aynı ders adına sahip derslerin en küçük kullanılmayan instance'ını bul
    UPDATE Dersler SET ders_instance = (
        WITH RECURSIVE instance_sayilari(n) AS (
            -- 1'den başlayarak sayıları oluştur
            SELECT 1
            UNION ALL
            SELECT n + 1 FROM instance_sayilari 
            WHERE n < (
                SELECT COALESCE(MAX(ders_instance), 0) + 1 
                FROM Dersler 
                WHERE ders_adi = NEW.ders_adi
            )
        ),
        kullanilan_instancelar AS (
            SELECT ders_instance FROM Dersler 
            WHERE ders_adi = NEW.ders_adi
        )
        SELECT MIN(n) 
        FROM instance_sayilari 
        WHERE n NOT IN (SELECT ders_instance FROM kullanilan_instancelar)
    )
    WHERE rowid = NEW.rowid;
END;

/*

-- Test için örnek veriler ve kullanım
-- Önce bazı dersler ekleyelim
INSERT INTO Dersler (ders_adi, ders_instance, sinif_num) VALUES 
('Matematik', 1, '1101'),
('Matematik', 2, '1102'),
('Matematik', 4, '1103'),  -- 3'ü atlayarak
('Fizik', 1, '1101');

-- Şimdi yeni matematik dersi ekleyelim (instance belirtmeden)
INSERT INTO Dersler (ders_adi, sinif_num) VALUES ('Matematik', '1104');
-- Bu ders otomatik olarak ders_instance = 3 alacak

-- Başka bir matematik dersi daha
INSERT INTO Dersler (ders_adi, sinif_num) VALUES ('Matematik', '1105');
-- Bu ders otomatik olarak ders_instance = 5 alacak

-- Sonuçları kontrol et
SELECT ders_adi, ders_instance, sinif_num FROM Dersler ORDER BY ders_adi, ders_instance;
*/

--RAF Ders-Sınıf ilişki tablosu (Many-to-Many)
CREATE TABLE Ders_Sinif_Iliskisi (
    ders_adi TEXT,
    ders_instance INTEGER,
    sinif_num TEXT,
    PRIMARY KEY (ders_instance, sinif_num, ders_adi),
    FOREIGN KEY (ders_instance, ders_adi) REFERENCES Dersler(ders_instance, ders_adi) ON DELETE CASCADE,
    FOREIGN KEY (sinif_num) REFERENCES Siniflar(sinif_num)
);

--RAF: Bölüm bilgisi için görünüm (view) oluşturma
/*
CREATE VIEW DersDetay AS
SELECT 
    d.ders_kodu,
    d.ders_adi,
    d.sinif_num,
    s.sinif_duzeyi,
    s.bolum_num,
    b.bolum_adi,
    -- Ders kodundan bölüm kısaltmasını çıkar (MEC208-1 -> MEC)
    SUBSTR(d.ders_kodu, 1, INSTR(d.ders_kodu, '-') - 1) AS bolum_kisaltmasi
FROM Dersler d
JOIN Siniflar s ON d.sinif_num = s.sinif_num
JOIN Bolumler b ON s.bolum_num = b.bolum_num;
*/
--bolumu direkt çekecek sekilde yap !fnord

-- Öğrenciler tablosu
CREATE TABLE Ogrenciler (
    ogrenci_num INTEGER PRIMARY KEY AUTOINCREMENT,
    --girdiği sene son 2 digit sonra 0 sonra girdiği mühensliğin numsi sonra da ikinci anadal ile aldıysa 9, yandal olarak aldıysa 8, normal geldiyse 0 ekle sonra kaçıncı olarak girdiğini ekle k 2 digit olacak o.
    ad TEXT NOT NULL,
    soyad TEXT NOT NULL,
    girme_senesi INTEGER NOT NULL,
    kacinci_donem INTEGER NOT NULL, --dondurduysa farklı olabilir
    --ikinci dal kaçıncı donem
    sinif_num INTEGER NOT NULL,
    mezun_durumu INTEGER DEFAULT 0, -- SQLite'ta boolean için 0/1
    --ALINAN DERSLER? FNORD
    FOREIGN KEY (sinif_num) REFERENCES Siniflar(sinif_num)
);
CREATE TABLE Ders_Sinif_Iliskisi (
    ders_adi TEXT,
    ders_instance INTEGER,
    sinif_num TEXT,
    PRIMARY KEY (ders_instance, sinif_num, ders_adi),
    FOREIGN KEY (ders_instance, ders_adi) REFERENCES Dersler(ders_instance, ders_adi) ON DELETE CASCADE,
    FOREIGN KEY (sinif_num) REFERENCES Siniflar(sinif_num)
);

-- Derslikler tablosu
CREATE TABLE Derslikler (
    derslik_num INTEGER PRIMARY KEY AUTOINCREMENT,
    derslik_adi TEXT NOT NULL UNIQUE,
    tip TEXT NOT NULL CHECK (tip IN ('lab', 'amfi')),
    kapasite INTEGER NOT NULL
);

-- Öğretmenler tablosu
CREATE TABLE Ogretmenler (
    ogretmen_num INTEGER PRIMARY KEY AUTOINCREMENT,
    ad TEXT NOT NULL,
    soyad TEXT NOT NULL,
    bolum_adi TEXT NOT NULL,
    FOREIGN KEY (sinif_num) REFERENCES Siniflar(sinif_num)
    FOREIGN KEY (bolum_adi) REFERENCES Bolumler(bolum_adi)
);

CREATE TABLE Ders_Ogretmen_Iliskisi (
    ders_adi TEXT,
    ders_instance INTEGER,
    sinif_num TEXT,
    PRIMARY KEY (ders_instance, sinif_num, ders_adi),
    FOREIGN KEY (ders_instance, ders_adi) REFERENCES Dersler(ders_instance, ders_adi) ON DELETE CASCADE,
    FOREIGN KEY (sinif_num) REFERENCES Siniflar(sinif_num)
);


--FNORD & RAF
-- Tekrar alınan dersler tablosu?????????
/*
CREATE TABLE TekrarDersleri (
    tekrar_num INTEGER PRIMARY KEY AUTOINCREMENT,
    ogrenci_num INTEGER NOT NULL,
    ders_num INTEGER NOT NULL,
    FOREIGN KEY (ogrenci_num) REFERENCES Ogrenciler(ogrenci_num),
    FOREIGN KEY (ders_num) REFERENCES Dersler(ders_num)
);

-- Çift anadal bilgileri tablosu
CREATE TABLE CiftAnadal (
    cift_anadal_num INTEGER PRIMARY KEY AUTOINCREMENT,
    ogrenci_num INTEGER NOT NULL,
    hedef_bolum_num INTEGER NOT NULL,
    FOREIGN KEY (ogrenci_num) REFERENCES Ogrenciler(ogrenci_num),
    FOREIGN KEY (hedef_bolum_num) REFERENCES Bolumler(bolum_num)
);
*/