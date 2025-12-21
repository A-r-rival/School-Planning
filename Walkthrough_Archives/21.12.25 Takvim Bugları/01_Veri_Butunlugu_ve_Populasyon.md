# 01. Veri Bütünlüğü ve Veri Popülasyonu Düzeltmeleri

## Sorun Tanımı
Kullanıcı, Takvim görünümünde fakülte seçtiğinde "Bölüm Yok" hatası alıyordu. Dropdown menüleri dolmuyordu veya bazı fakülteler mükerrer (duplicate) görünüyordu. Ayrıca veritabanındaki `Ders_Sinif_Iliskisi` tablosu olması gerekenden çok daha az kayıt içeriyordu (sadece 3 satır), bu da öğrenci programlarının boş gelmesine neden oluyordu.

## Teşhis Süreci

### Debugging - Adım 1
İlk olarak `populate_students.py` scripti ve oluşan veritabanı incelendi. `debug_data_linkage.py` adında özel bir script yazılarak şu sorgular çalıştırıldı:

```python
# Veritabanındaki toplam Fakülte sayısı
cursor.execute("SELECT COUNT(*) FROM Fakulteler")
# Veritabanındaki toplam Bölüm sayısı
cursor.execute("SELECT COUNT(*) FROM Bolumler")
# Fakülte başına düşen bölüm sayısı
cursor.execute("SELECT f.fakulte_adi, COUNT(b.bolum_id) FROM Fakulteler f LEFT JOIN Bolumler b ... GROUP BY f.fakulte_adi")
```

**Bulgular:**
1. "Hukuk Fakültesi" gibi kayıtların birden fazla ID ile veritabanında olduğu görüldü.
2. Birçok "Fakülte" isminin aslında Bölüm ismi olduğu fark edildi (Örn: "Bilgisayar Mühendisliği" adında bir Fakülte kaydı vardı ama içinde bölüm yoktu).

### Kök Neden Analizi
`scripts/populate_students.py` dosyasında, veritabanı ilk oluşturulurken `DEPARTMENTS_DATA` sözlüğünün anahtarları üzerinde dönen bir döngü olduğu tespit edildi:

```python
# ESKİ KOD (Hatalı Mantık)
for dept_name in DEPARTMENTS_DATA.keys():
    # Bölüm adını Fakülte gibi eklemeye çalışıyordu!
    self.db.add_faculty(dept_name) 
```

Bu döngü, her bölüm isminden bir fakülte yaratıyor, ancak `MAPPED_FACULTIES` mantığı daha sonra devreye girip *gerçek* fakülteleri de yaratınca kaos oluşuyordu.

Ayrıca `Ders_Sinif_Iliskisi` tablosunun boş kalmasının sebebi, scriptin sadece `is_current_term` (Şu anki dönem) olarak işaretlenen dersleri işlemesiydi. Veri setindeki dönem bilgileri ile scriptin "Current Term" varsayımı uyuşmadığı için çoğu ders atlanıyordu.

## Çözüm Uygulaması

### 1. Popülasyon Mantığının Temizlenmesi
Hatalı döngü kaldırılarak, fakülte ve bölüm yaratma süreci `MAPPED_FACULTIES` haritasına bağlandı. Artık sadece tanımlı, resmi fakülteler (Örn: "Mühendislik ve Doğa Bilimleri Fakültesi") yaratılıyor.

```python
# YENİ KOD (Düzeltilmiş)
# Sadece canonical (eşleştirilmiş) fakülteleri oluştur
canonical_faculties = set(MAPPED_FACULTIES.values())
for fac_name in canonical_faculties:
    self.schedule_model.add_faculty(fac_name)
```

### 2. İlişkisel Veri Düzeltmesi
`Ders_Sinif_Iliskisi` tablosunu dolduran döngüdeki kısıtlayıcı `if` kontrolleri esnetildi ve tüm döneme ait derslerin doğru sınıflarla (1. sınıf, 2. sınıf vb.) eşleşmesi sağlandı.

Bu değişiklikler sonrası veritabanı "Regenerate" (Sıfırdan oluşturma) işlemine tabi tutuldu.

**Sonuç:**
*   Fakülte sayısı normale döndü (Mükerrerlik bitti).
*   Her fakültenin altında doğru bölümler listelendi (Dropdown sorunu çözüldü).
*   `Ders_Sinif_Iliskisi` tablosu binlerce satır veri ile doldu, bu da "Boş Program" sorununu çözdü.
