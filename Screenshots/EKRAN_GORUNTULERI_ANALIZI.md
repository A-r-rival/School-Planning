# Proje Ekran Görüntüleri ve İşlevsel Analiz

Bu belge, "Otomatik Üniversite Ders Programı Oluşturma Sistemi"ne ait arayüz ekran görüntülerini ve bu arayüzlerin teknik işlevlerini sunmak ve değerlendirmek amacıyla hazırlanmıştır.

## 1. Arayüz Modülleri ve Teknik Değerlendirme

Sistem, **Model-View-Controller (MVC)** mimarisine uygun olarak 4 ana görsel modül üzerinden kullanıcı etkileşimi sağlar. Mevcut ekran görüntüleri aşağıdaki modüllere ait görsel kanıtlardır:

### 1.1. Ana Yönetim Ekranı (ScheduleView)
- **Amaç:** Kullanıcının ders havuzunu yönetmesi ve hızlı aksiyon alması.
- **Değerlendirme:** Sol tarafta geniş bir liste ve sağ tarafta detaylı "Filtreleme Paneli" (Fakülte, Bölüm, Sınıf) yer alır. Bu tasarım, kullanıcının binlerce ders arasından istediği veriye saniyeler içinde ulaşmasını sağlar. Kullanıcı deneyimi (UX) açısından en kritik ekrandır.

### 1.2. Haftalık Takvim Görünümü (CalendarView)
- **Amaç:** Oluşturulan programın görsel doğrulaması.
- **Değerlendirme:** 5 günlük ve 9 saatlik (08:00-17:00) bir matris yapısındadır. Derslerin çakışıp çakışmadığı, blok derslerin sürekliliği burada görselleştirilir. Seçmeli ders havuzlarının renk kodları ile ayrıştırılması (Lejant), karmaşık programların okunabilirliğini artırır.

### 1.3. Öğrenci Analiz Paneli (StudentView)
- **Amaç:** Öğrenci bazlı akademik takip.
- **Değerlendirme:** İki parçalı (Splitter) yapıdadır. Sol tarafta öğrenci listesi, sağ tarafta ise seçilen öğrencinin transkripti bulunur. Renkli durum göstergeleri (Geçti/Kaldı), akademik danışmanların öğrenci durumunu hızlıca analiz etmesine olanak tanır.

### 1.4. Kısıt ve Müsaitlik Yönetimi (TeacherAvailabilityView)
- **Amaç:** Öğretmenlerin özel zaman kısıtlarının sisteme girilmesi.
- **Değerlendirme:** Tab sekmeli (TabWidget) yapısı ile kullanıcıya iki farklı kısıt türü (Gün/Saat engelleme veya Gün sayısı kısıtlama) sunar. Bu esneklik, gerçek hayat senaryolarının (örn. "Hocam Salı günü gelmesin") sisteme doğru aktarılmasını sağlar.

---

## 2. Ekran Görüntüsü Galerisi

Aşağıda proje çalışırken alınan ekran görüntüleri listelenmiştir. Her bir görüntü, yukarıda açıklanan modüllerden bir veya birkaçının eyleme geçmiş halini temsil etmektedir.


### Görüntü 1: `Ekran görüntüsü 2026-01-17 003929.png`
**Tahmini İçerik:** Ana Ekran veya Liste Görünümü  
**Dosya Boyutu:** 53.2 KB

![Ekran Görüntüsü](Ekran%20g%C3%B6r%C3%BCnt%C3%BCs%C3%BC%202026-01-17%20003929.png)

> **Analiz:** Bu ekran görüntüsü, sistemin canlı veri ile çalışırkenki anlık durumunu belgeler. Arayüzün doluluk oranı ve veri sunumu, sistemin operasyonel kapasitesini gösterir.

---

### Görüntü 2: `Ekran görüntüsü 2026-01-17 004014.png`
**Tahmini İçerik:** Genel Arayüz Görünümü  
**Dosya Boyutu:** 29.0 KB

![Ekran Görüntüsü](Ekran%20g%C3%B6r%C3%BCnt%C3%BCs%C3%BC%202026-01-17%20004014.png)

> **Analiz:** Bu ekran görüntüsü, sistemin canlı veri ile çalışırkenki anlık durumunu belgeler. Arayüzün doluluk oranı ve veri sunumu, sistemin operasyonel kapasitesini gösterir.

---

### Görüntü 3: `Ekran görüntüsü 2026-01-17 004026.png`
**Tahmini İçerik:** Ana Ekran veya Liste Görünümü  
**Dosya Boyutu:** 47.9 KB

![Ekran Görüntüsü](Ekran%20g%C3%B6r%C3%BCnt%C3%BCs%C3%BC%202026-01-17%20004026.png)

> **Analiz:** Bu ekran görüntüsü, sistemin canlı veri ile çalışırkenki anlık durumunu belgeler. Arayüzün doluluk oranı ve veri sunumu, sistemin operasyonel kapasitesini gösterir.

---

### Görüntü 4: `Ekran görüntüsü 2026-01-17 004057.png`
**Tahmini İçerik:** Ana Ekran veya Liste Görünümü  
**Dosya Boyutu:** 61.4 KB

![Ekran Görüntüsü](Ekran%20g%C3%B6r%C3%BCnt%C3%BCs%C3%BC%202026-01-17%20004057.png)

> **Analiz:** Bu ekran görüntüsü, sistemin canlı veri ile çalışırkenki anlık durumunu belgeler. Arayüzün doluluk oranı ve veri sunumu, sistemin operasyonel kapasitesini gösterir.

---

### Görüntü 5: `Ekran görüntüsü 2026-01-17 004106.png`
**Tahmini İçerik:** Ana Ekran veya Liste Görünümü  
**Dosya Boyutu:** 45.0 KB

![Ekran Görüntüsü](Ekran%20g%C3%B6r%C3%BCnt%C3%BCs%C3%BC%202026-01-17%20004106.png)

> **Analiz:** Bu ekran görüntüsü, sistemin canlı veri ile çalışırkenki anlık durumunu belgeler. Arayüzün doluluk oranı ve veri sunumu, sistemin operasyonel kapasitesini gösterir.

---

### Görüntü 6: `Ekran görüntüsü 2026-01-17 004147.png`
**Tahmini İçerik:** Kapsamlı Veri Tablosu (Takvim veya Öğrenci Paneli)  
**Dosya Boyutu:** 107.9 KB

![Ekran Görüntüsü](Ekran%20g%C3%B6r%C3%BCnt%C3%BCs%C3%BC%202026-01-17%20004147.png)

> **Analiz:** Bu ekran görüntüsü, sistemin canlı veri ile çalışırkenki anlık durumunu belgeler. Arayüzün doluluk oranı ve veri sunumu, sistemin operasyonel kapasitesini gösterir.

---

### Görüntü 7: `Ekran görüntüsü 2026-01-17 004200.png`
**Tahmini İçerik:** Ana Ekran veya Liste Görünümü  
**Dosya Boyutu:** 51.7 KB

![Ekran Görüntüsü](Ekran%20g%C3%B6r%C3%BCnt%C3%BCs%C3%BC%202026-01-17%20004200.png)

> **Analiz:** Bu ekran görüntüsü, sistemin canlı veri ile çalışırkenki anlık durumunu belgeler. Arayüzün doluluk oranı ve veri sunumu, sistemin operasyonel kapasitesini gösterir.

---

### Görüntü 8: `Ekran görüntüsü 2026-01-17 004208.png`
**Tahmini İçerik:** Diyalog Penceresi / Pop-up (Kısıt Ekleme veya Ders Ekleme)  
**Dosya Boyutu:** 13.7 KB

![Ekran Görüntüsü](Ekran%20g%C3%B6r%C3%BCnt%C3%BCs%C3%BC%202026-01-17%20004208.png)

> **Analiz:** Bu ekran görüntüsü, sistemin canlı veri ile çalışırkenki anlık durumunu belgeler. Arayüzün doluluk oranı ve veri sunumu, sistemin operasyonel kapasitesini gösterir.

---

### Görüntü 9: `Ekran görüntüsü 2026-01-17 004214.png`
**Tahmini İçerik:** Diyalog Penceresi / Pop-up (Kısıt Ekleme veya Ders Ekleme)  
**Dosya Boyutu:** 15.5 KB

![Ekran Görüntüsü](Ekran%20g%C3%B6r%C3%BCnt%C3%BCs%C3%BC%202026-01-17%20004214.png)

> **Analiz:** Bu ekran görüntüsü, sistemin canlı veri ile çalışırkenki anlık durumunu belgeler. Arayüzün doluluk oranı ve veri sunumu, sistemin operasyonel kapasitesini gösterir.

---
