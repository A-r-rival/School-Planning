# Ortak Ders Grupları Oluşturma Özelliği (Tamamlandı)

Bu çalışma kapsamında, aynı T/U/L kredisine sahip ancak farklı isim veya şubelerde yer alan dersleri programlayıcıda (scheduler) tek bir fiziksel ders bloku olarak birleştirmeyi sağlayan "Ortak Ders Grupları" özelliği başarıyla uygulanmıştır.

## Değişiklik Özeti

### 1. Veritabanı (Database) Katmanı
- **Yeni Tablo:** `migration_010_common_course_groups.py` ile `Ortak_Ders_Gruplari` tablosu oluşturuldu. Bu tablo, birbiriyle gruplanan dersleri `grup_id` üzerinden birbirine bağlamak için tasarlandı.
- **Model Metotları:** `schedule_model.py` içerisine grupları çekmek, kaydetmek ve silmek için metotlar (örn. `get_similar_course_groups`, `save_common_course_group`) eklendi.
  - *Düzeltme:* Tek bir varyasyonu olan veya tek bir bölümde işlenen derslerin listede görünmesi, varyasyon sayısı (>1) filtresiyle engellendi.
  - *Düzeltme:* "Ders_Havuz_Iliskisi" (Seçmeli Havuz) tabloları da sorguya dahil edilerek, ortak derslerde bölüm isimlerinin doğru çekilmesi sağlandı.
- **Seeder Düzeltmesi:** `populate_students.py` içerisindeki ders oluşturma mantığı güncellenerek, derslerin bölümlere ("bolum_id") özel ayrı "ders_instance" numaraları alması sağlandı. Böylece otomatik birleşme sorunu çözüldü.

### 2. Arayüz (UI) Katmanı
- **Kısayol Butonu:** `curriculum_view.py` içerisindeki arama panelinin yanına "Ortak Dersleri Düzenle" butonu eklendi.
- **Yeni Ortak Ders Tab'ı:** `teacher_availability_view.py` içerisine 3. pencere olarak "Ortak Ders Grupları" menüsü eklendi.
  - **Arama Çubuğu:** Derse göre filtreleme eklendi.
  - **Gizleme Ayarı:** Sadece 1 versiyonu olan derslerin gizlenmesini sağlayan "Tekil Dersleri Gizle" seçeneği eklendi.
  - **Mevcut Grupları Listeleme & Silme:** Daha önce kaydedilmiş grupları alt bölümde görme ve silme yeteneği eklendi.

### 3. Zamanlayıcı (Scheduler) Entegrasyonu
- **Otomatik Birleşimin İptali:** `CourseMerger` yapısında *otomatik olarak uygulanan farklı bölümlerdeki aynı isimli dersleri birleştirme mantığı* bölüm spesifik (department unique key) hale getirilerek kaldırıldı.
- **Manuel Grup Birleşimi:** `CourseMerger.merge()` içindeki `key` mekanizması yenilendi. Kullanıcının oluşturduğu ortak gruptaki dersler, bölüm bağımsız biçimde aynı `KEY` (Ortak Grup No) ile eşleştirilip, saat atama işlemine tek bir blok gibi (`PhysicalCourse`) girmeye başladı.

## Doğrulama / Test (Verification)
- DB tablosunun başarıyla oluştuğu `migration.py` aracılığıyla test edildi.
- Arayüz elemanları ve Controller metotları (`schedule_controller.py`) birleştirildi.
- Ortak ders gruplarını silme ve ekleme işlemlerinin SQL tarafındaki Atomicity'si (Transaction) sağlandı.
- Veritabanı yeniden kurularak derslerin istemsizce birleşmesinin (Analiz 1 vb.) önüne geçildiği doğrulandı.

Uygulamanın yeni sürümünü sorunsuz bir şekilde kullanmaya başlayabilirsiniz.
