# Database and Class Architecture Documentation

Bu doküman, sistemdeki derslerin ve veritabanı tablolarının nasıl yapılandığını, hangi sınıfların ne amaçla kullanıldığını ve birbirleriyle olan ilişkilerini açıklamaktadır. Sistem değiştikçe bu doküman güncellenmelidir.

## 1. Veritabanı Tabloları (Database Schema)

### Çekirdek Tablolar

- **`Fakulteler`**: `fakulte_num` (PK, auto-increment), `fakulte_adi`.
- **`Bolumler`**: `bolum_id` (PK), `bolum_num`, `bolum_adi`, `fakulte_num` (FK). UNIQUE(`fakulte_num`, `bolum_num`).
- **`Ogrenci_Donemleri`**: `donem_sinif_num` (PK, TEXT), `baslangic_yili`, `bolum_num` (FK), `sinif_duzeyi` (0–5). Bir bölümün belirli sınıfındaki öğrenci grubunu temsil eder. Tüm atamalar ve çakışma kontrolleri bu gruplara göre yapılır.
  - **Not**: `baslangic_yili` var çünkü bu da arşivlenmeye uygun olacak bir class olacak.

### Ders Tabloları

- **`Dersler`**: Sisteme eklenmiş ham ders bilgisini tutar.
  - PK: **(`ders_instance`, `ders_adi`)**
  - Sütunlar: `ders_kodu` (TEXT), `ders_instance` (INTEGER), `ders_adi` (TEXT), `teori_odasi` (FK → Derslikler), `lab_odasi` (FK → Derslikler), `akts`, `teori_saati`, `uygulama_saati`, `lab_saati`.
  - **Not**: Her fiziksel satır yalnızca TEK bir `ders_kodu` tutar. `ders_id` gibi bir sütun yoktur.
  - **Not_2**: `ders_instance` müfredatı değişmiş ama ismi hala kullanılan dersleri arşivlemek amacıyla kullanılıyor bu class içinde.
- **`Ders_Sinif_Iliskisi`**: Hangi `Dersler` satırının hangi `Ogrenci_Donemleri` grubuna zorunlu (Core) olarak atandığını tutar. PK: (`ders_instance`, `donem_sinif_num`, `ders_adi`).
  - **FNORD**: İsmini değiştirsek mi class'ın? Gerçi zaten ders odaları Derslik olarak geçiyor.
- **`Ders_Havuz_Iliskisi`**: Hangi dersin hangi bölümün hangi seçmeli havuzuna (Elective Pool) dahil edildiğini tutar. `iliski_id` (PK, auto-increment), `ders_instance`, `ders_adi`, `bolum_id`, `havuz_kodu`.
- **`Ders_Ogretmen_Iliskisi`**: Hangi dersin hangi hocalar tarafından verildiğini eşleştirir. PK: (`ders_instance`, `ders_adi`, `ogretmen_id`).

### Fiziksel Kaynaklar

- **`Derslikler`**: `derslik_num` (PK, auto-increment), `derslik_adi`, `derslik_tipi`, `kapasite`, `ozellikler`, `silindi` (BOOLEAN, default 0), `silinme_tarihi` (DATETIME). Soft-delete destekler.
- **`Ogretmenler`**: `ogretmen_num` (PK, auto-increment), `ad`, `soyad`, `unvan`, `bolum_adi`.

### Program ve Zamanlama

- **`Ders_Programi`**: Ders programı çıktısını tutan tablo. `program_id` (PK), `ders_adi`, `ders_instance`, `ogretmen_id`, `gun`, `baslangic`, `bitis`.
- **`schedule_snapshots`**: Geçmiş ders programlarını saklamak için. `id` (PK), `name`, `created_at`, `semester`, `data` (JSON).

### Öğrenci Tabloları

- **`Ogrenciler`**: `ogrenci_num` (PK), `ad`, `soyad`, `girme_senesi`, `kacinci_donem`, `bolum_num` (FK), `fakulte_num` (FK), `mezun_durumu`, `ikinci_bolum_num`, `ikinci_bolum_turu` ('Yandal'|'Anadal'), `ogrenci_num2`, `girme_senesi2`, `kacinci_donem2`.
- **`Verilen_Dersler`**: `ogrenci_num` (PK), `ders_listesi` (TEXT).
- **`Alinan_Dersler`**: Öğrencinin aldığı dersleri tutar. PK: (`ders_instance`, `donem_sinif_num`, `ders_adi`).
- **`Ogrenci_Notlari`**: `id` (PK, auto-increment), `ogrenci_num`, `ders_kodu`, `ders_adi`, `harf_notu`, `durum`, `donem`, `onceki_not_id`.

### Hoca Tercihleri ve Müsaitlik

- **`Ogretmen_Musaitlik`**: `id` (PK, auto-increment), `ogretmen_id` (FK), `gun`, `baslangic`, `bitis`. Hocaların müsait olmadığı zaman dilimlerini tutar.
- **`Ogretmen_Ders_Tercihleri`**: `id` (PK, auto-increment), `ogretmen_id` (FK), `ders_adi`, `ders_secim_notu`, `tercih_tipi` ('WANTED'|'BLOCKED'). Hocaların hangi dersleri vermek istediği veya reddettiği.

---

## 2. Programatik Sınıflar (Course Classes)

`controllers/scheduler_services.py` içinde tanımlanan ve OR-Tools programlayıcısına veriyi hazırlarken kullanılan veri yapıları:

### A. RawCourseRow
**Amaç:** Veritabanından yapılan dev SQL `JOIN` sorgusunun getirdiği her bir ham satırı tutar.
- İçerik: O derse ait tek bir bağlantı (Örn: "Analiz 1 - Bilgisayar Mühendisliği 1. Sınıf Core bağlantısı").
- Aynı ders hem Bilgisayar hem Yazılım'a eklenmişse, veri tabanından 2 ayrı `RawCourseRow` gelir.

### B. ProgramCourseContext
**Amaç:** Bir dersin spesifik bir bölüm ve sınıftaki **rolünü** tutar (frozen dataclass).
- İçerik: `(department, year, role: CORE|ELECTIVE, pool_code)`

### C. PhysicalCourse
**Amaç:** Zaman çizelgesine **fiziksel olarak yerleştirilecek** tekil blokları oluşturur. `CourseMerger` tarafından üretilir.
- Alanlar: `name`, `teacher_ids` (FrozenSet), `t`, `u`, `l`, `akts`, `code`, `fixed_t_room`, `fixed_l_room`, `faculties` (Set), `group_ids` (Set), `contexts` (Set[ProgramCourseContext]), `instance`.
- **Merge Key:** `(name, teacher_ids, t, u, l, instance)` — yani aynı isim, aynı hocalar, aynı saat dağılımları **ve** aynı instance numarası olan satırlar birleştirilir.
- **OR-Tools Tarafından Görünen:** Algoritma bu `PhysicalCourse` birimini programlar. Saati belirlenince, içindeki tüm `group_ids` o saatte meşgul ilan edilir.

---

## 3. Senaryolar ve Durum İzahları

### "CourseMerger ne zaman dersleri birleştirir?"

**Bu durum şu zaman olur:**
Aynı isme (`ders_adi` = "Atatürk İlkeleri"), aynı instance'a (`ders_instance` = 1), **aynı hocalara ve aynı saat yapısına (T, U, L)** sahip ders, birden fazla bölüme/sınıfa (Ogrenci_Donemleri) atandığında:

1. `CourseRepository` veritabanından N adet `RawCourseRow` çeker.
2. `CourseMerger` merge key'e bakar: `(name, teacher_ids, t, u, l, instance)` aynı mı?
3. Aynılarını birleştirip `group_ids`'leri ve `contexts`'leri toplayarak TEK bir `PhysicalCourse` üretir.
4. Programlayıcı bu dersi tek saatte programlar ve tüm gruplardaki öğrencileri o saatte meşgul ilan eder.

**Bu neden her senaryoya uymaz?**
- `Dersler` tablosunda her satır yalnızca TEK bir `ders_kodu` ve TEK bir `akts` tutar.
- Farklı bölümlerin aynı dersi farklı kodlarla (BİL101 vs YAZ101) vermesi gerekiyorsa, iki ayrı DB satırı (farklı instance) oluşturmak **zorunludur**.
- Bu durumda merge key eşleşmez ve `CourseMerger` bunları **iki bağımsız ders** sayar.

**Yeni "Ortak Dersler" tablosu ihtiyacı buradan doğar:** Farklı isimlere, farklı ders kodlarına ve farklı instance numaralarına sahip dersleri "Fiziksel olarak beraber işlensinler" diye birbirine bağlamak için.
