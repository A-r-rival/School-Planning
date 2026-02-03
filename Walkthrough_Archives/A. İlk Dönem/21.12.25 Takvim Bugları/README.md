# 21.12.2025 Tarihli Hata Giderme ve Geliştirme Paketi

Bu klasör, projenin Takvim (Calendar) ve Programlayıcı (Scheduler) modüllerinde yapılan kapsamlı hata giderme ve geliştirme çalışmalarını içerir. Konular teknik derinliklerine göre ayrı dosyalara bölünmüştür.

## İçindekiler

### [01. Veri Bütünlüğü ve Popülasyon Düzeltmeleri](./01_Veri_Butunlugu_ve_Populasyon.md)
*   Drop-down menülerinin boş gelme sorunu.
*   Fakülte isimlerinin mükerrer oluşması.
*   `Ders_Sinif_Iliskisi` tablosunun boş kalması ve `populate_students.py` refaktörü.

### [02. UI Çökmesi ve Filtreleme](./02_UI_Crash_ve_Filtreler.md)
*   Bölüm seçimi sırasındaki `ValueError` (Crash) ve çözümü.
*   Filtreler arası sinyal yönetimi (`blockSignals`).
*   Takvim grid'inden hafta sonlarının çıkarılması.

### [03. Scheduler Kısıtlamaları ve Laboratuvarlar](./03_Scheduler_Constraints_ve_Lablar.md)
*   Hatalı oda atamaları (Örn: Hukuk derslerinin Laboratuvara atanması).
*   Veritabanından Fakülte bilgisinin çekilip kısıtlama (Constraint) olarak kullanılması.
*   Laboratuvar kullanımının sadece Fen/Mühendislik fakültelerine kısıtlanması mantığı.

---
**Özet:** Bu güncelleme ile sistemin kararlılığı artırılmış, veri tutarlılığı sağlanmış ve programlama algoritması kullanıcı isteklerine (Fakülte bazlı oda kısıtlamaları) uygun hale getirilmiştir.
