-- Fakülteler tablosu
CREATE TABLE Fakulteler (
    fakulte_id INTEGER PRIMARY KEY AUTOINCREMENT,
    fakulte_adi TEXT NOT NULL
);

-- Bölümler tablosu (normal yapı)
CREATE TABLE Bolumler (
    bolum_id INTEGER,
    bolum_adi TEXT NOT NULL,
    fakulte_id INTEGER NOT NULL,
    PRIMARY KEY (fakulte_id, bolum_id),
    FOREIGN KEY (fakulte_id) REFERENCES Fakulteler(fakulte_id)
);
-- Bölüm ekleme trigger'ı
CREATE TRIGGER bolum_id_ayarla
BEFORE INSERT ON Bolumler
FOR EACH ROW
BEGIN
    SELECT COALESCE(MAX(bolum_id), 0) + 1 INTO NEW.bolum_id
    FROM Bolumler
    WHERE fakulte_id = NEW.fakulte_id;
END;

-- Sınıflar tablosu
CREATE TABLE Siniflar (
    sinif_id INTEGER,
    sinif_duzeyi INTEGER NOT NULL CHECK (sinif_duzeyi BETWEEN 1 AND 4),
    bolum_id INTEGER NOT NULL,
    PRIMARY KEY (sinif_duzeyi, bolum_id),
    FOREIGN KEY (bolum_id) REFERENCES Bolumler(bolum_id)
);
-- Sınıf ekleme trigger'ı
CREATE TRIGGER sinif_id_ayarla
BEFORE INSERT ON Siniflar
FOR EACH ROW
BEGIN
    SELECT 
        CAST(b.fakulte_id AS TEXT) || 
        CAST(NEW.bolum_id AS TEXT) || 
        '0' || 
        CAST(NEW.sinif_duzeyi AS TEXT)
    INTO NEW.sinif_id
    FROM Bolumler b
    WHERE b.bolum_id = NEW.bolum_id;
END;

-- Dersler tablosu
-- Dersler tablosu (manuel ID ve çoklu hoca desteği)
CREATE TABLE Dersler (
    ders_kodu TEXT PRIMARY KEY,  -- Örnek: MEC208-1, MEC208-2
    ders_adi TEXT NOT NULL,
    sinif_id INTEGER NOT NULL,
    FOREIGN KEY (sinif_id) REFERENCES Siniflar(sinif_id)
);

-- Bölüm bilgisi için görünüm (view) oluşturma
/*
CREATE VIEW DersDetay AS
SELECT 
    d.ders_kodu,
    d.ders_adi,
    d.sinif_id,
    s.sinif_duzeyi,
    s.bolum_id,
    b.bolum_adi,
    -- Ders kodundan bölüm kısaltmasını çıkar (MEC208-1 -> MEC)
    SUBSTR(d.ders_kodu, 1, INSTR(d.ders_kodu, '-') - 1) AS bolum_kisaltmasi
FROM Dersler d
JOIN Siniflar s ON d.sinif_id = s.sinif_id
JOIN Bolumler b ON s.bolum_id = b.bolum_id;
*/
--bolumu direkt çekecek sekilde yap !fnord

-- Öğrenciler tablosu
CREATE TABLE Ogrenciler (
    ogrenci_id INTEGER PRIMARY KEY AUTOINCREMENT,
    --girdiği sene son 2 digit sonra 0 sonra girdiği mühensliğin idsi sonra da ikinci anadal ile aldıysa 9, yandal olarak aldıysa 8, normal geldiyse 0 ekle sonra kaçıncı olarak girdiğini ekle k 2 digit olacak o.
    ad TEXT NOT NULL,
    soyad TEXT NOT NULL,
    girme_senesi INTEGER NOT NULL,
    kacinci_donem INTEGER NOT NULL, --dondurduysa farklı olabilir
    sinif_id INTEGER NOT NULL,
    mezun_durumu INTEGER DEFAULT 0, -- SQLite'ta boolean için 0/1
    --ALINAN DERSLER? FNORD
    FOREIGN KEY (sinif_id) REFERENCES Siniflar(sinif_id)
);

-- Tekrar alınan dersler tablosu
CREATE TABLE TekrarDersleri (
    tekrar_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ogrenci_id INTEGER NOT NULL,
    ders_id INTEGER NOT NULL,
    FOREIGN KEY (ogrenci_id) REFERENCES Ogrenciler(ogrenci_id),
    FOREIGN KEY (ders_id) REFERENCES Dersler(ders_id)
);

-- Çift anadal bilgileri tablosu
CREATE TABLE CiftAnadal (
    cift_anadal_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ogrenci_id INTEGER NOT NULL,
    hedef_bolum_id INTEGER NOT NULL,
    FOREIGN KEY (ogrenci_id) REFERENCES Ogrenciler(ogrenci_id),
    FOREIGN KEY (hedef_bolum_id) REFERENCES Bolumler(bolum_id)
);

-- Derslikler tablosu
CREATE TABLE Derslikler (
    derslik_id INTEGER PRIMARY KEY AUTOINCREMENT,
    derslik_adi TEXT NOT NULL,
    tip TEXT NOT NULL CHECK (tip IN ('lab', 'amfi')),
    kapasite INTEGER NOT NULL
);