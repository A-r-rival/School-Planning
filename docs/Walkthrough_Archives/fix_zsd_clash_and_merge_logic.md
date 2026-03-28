# ZSD (Havuz Dersleri) Çakışma ve "Ortak Ders Grupları" Çözümü Walkthrough

**Tarih:** 29.03.2026
**Konu:** Seçmeli derslerin (ZSD vb. havuz dersleri) otomatik programlayıcıda yaratttığı çakışmaların ve UI (Arayüz) üzerindeki üst üste binme (overlap) hatalarının çözümü.

## Sorun Neydi?
Kullanıcı, Mekatronik Mühendisliği gibi bölümlerin programında, zorunlu (Core) bir ders olan *Kontrol Mühendisliğinin Temelleri* ile ZSD havuzundan seçilen *Endüstriyel Robotik II* veya *Isı Transferi* gibi derslerin UI üzerinde aynı saatte üst üste bindiğini (çakıştığını) fark etti.

Bunun yanı sıra, çözüm sürecinde daha önce geliştirilen **"Ortak Ders Grupları"** (farklı bölümlerdeki aynı isimli zorunlu dersleri manüel olarak birleştirme) özelliğinin yanlışlıkla bozulduğu ve sistemin her şeyi otomatik birleştirdiği tespit edildi.

### Kök Neden (Root Cause)
1. **Veri Hazırlama Hatası (CourseMerger):** CP-SAT çözücü, kısıtlamaları (constraints) uygulamadan önce her fiziksel dersi (`PhysicalCourse`) tekilleştirir. Ancak `CourseMerger` sınıfı, dersleri gruplarken anahtar (key) içerisine `department` (bölüm) bilgisini de dahil ediyordu.
2. **Kopya Ders Oluşumu:** "Isı Transferi" Makine Mühendisliği'nde zorunlu (`department="Makine Müh"`), Mekatronik Mühendisliği'nde ise ZSD havuz dersiydi (`department="Mekatronik Müh"`). Veritabanından gelen bu iki satır, farklı departmanlara sahip oldukları için **iki ayrı, bağımsız ders** olarak çözücüye gönderildi.
3. **Çözücünün Yanılgısı:** Çözücü iki farklı "Isı Transferi" gördü ancak ikisinin de hocası aynıydı. Hoca çakışmasını engellemek için mecbur kalarak bu "ikiz" dersleri farklı saatlere (örn: biri 08:30, diğeri 10:30) yerleştirdi.
4. **Arayüz (UI) Hatası:** `calendar_schedule_builder.py` takvimi çizerken `Ders_Programi` tablosunda "Isı Transferi" ismini gördüğü *herhangi bir* saati alıp Mekatronik'in takvimine yapıştırdı. Böylece çözücünün aslında Makine için 10:30'a atadığı saat, Mekatronik'in ekranında 10:30'daki zorunlu dersin (Kontrol Müh.) tam üstüne yapıştı.

## Çözüm ve Uygulanan Adımlar

1. **`scheduler_services.py` - SQL Havuz Sorgusunun Düzeltilmesi (Fix 1 & 2):**
   - Havuz dersleri çekilirken kullanılan `JOIN` kısıtlaması esnetildi: `(od.sinif_duzeyi = dhi.sinif_duzeyi OR dhi.sinif_duzeyi = 0)`
   - `UNION ALL` sorgusundaki sütun eşitsizliği `NULL AS pool_dhi_year` eklenerek düzeltildi.
   - Aşırı kısıtlamayı engellemek için Python seviyesinde "Havuz - Yıl" eşleştirmesi (`curriculum_data.py` üzerinden) dinamik filtre olarak eklendi.

2. **`CourseMerger._validate_contexts()` Çarpışma Çözümü (Fix 4):**
   - Aynı anda hem CORE hem ELECTIVE rolü üstlenen problemli veritabanı girdilerinde sistemin çökmesini engellemek için `CourseRole.CORE` rolüne öncelik verildi.

3. **`CourseMerger.merge()` - Ortak Ders Grupları ve Havuz Derslerinin Uyumlu Hale Getirilmesi (Fix 5 - Kritik Çözüm):**
   - `RawCourseRow` sınıfına `host_department` özelliği eklendi.
   - ZSD (Havuz) dersleri veritabanından okunurken, `Ders_Sinif_Iliskisi` üzerinden **bu dersi asıl açan bölüm (Host Department)** tespit edildi.
   - `CourseMerger` içindeki birleştirme (merge) işleminde şu zekice ayrım yapıldı:
     - **Zorunlu (Core) Dersler:** Birleşme anahtarında (key) kendi `department` bilgilerini tutmaya devam ettiler. Böylece Bilgisayar Müh. "Matematik 1" ile Makine Müh. "Matematik 1" otomatik BİRLEŞMEDİ. (Kullanıcının manüel **Ortak Ders Grupları** sekmesi özelliği korundu).
     - **Havuz (ZSD) Dersleri:** Birleşme anahtarında kendi (misafir oldukları) bölümlerini değil, `host_department` (asıl sahip bölüm) bilgisini kullandılar. Böylece sisteme "kopya" ders olarak girmek yerine, gidip **ana bölümün dersine sorunsuz şekilde eklendiler**.

## Sonuç
* Havuz dersleri (`is_from_pool=1`) artık çözücüye gönderilirken bağımsız değişkenler yaratmıyor, direkt ev sahibi (Host) dersin kimliğine (ID) `group_id` olarak ekleniyor.
* Çözücü, Havuz dersini tek bir fiziksel olay olarak görüp, hem asıl bölümün hem de seçen bölümün aynı saatteki çekirdek (Core) dersleriyle **matematiksel olarak kesin bir şekilde çakışmamasını** garanti altına alıyor.
* Arayüz (UI) mantıksız üst üste binmeler üretmeyi bıraktı.
* Tüm bu işlemler yapılırken kullanıcının geçmişte istediği manüel "Ortak Ders Grupları" müdahale özelliği tamamen sağlam bırakıldı.
