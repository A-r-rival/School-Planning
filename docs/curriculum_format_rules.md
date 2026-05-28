# Müfredat (.txt) ASCII Yazım Standartları ve Kuralları

Bu belge, tüm bölümler ve fakülteler için müfredat dosyalarının (`.txt` uzantılı) standart bir formatta nasıl yazılması gerektiğini belirler. Bu kurallara uyulması, müfredatın ayrıştırıcı (`parse_curriculum.py`) tarafından hatasız ve tutarlı bir şekilde veritabanına aktarılmasını sağlar.

## 1. Ders İsimlendirme ve Rakam Kullanımı
* **Roma Rakamları:** Birbirini takip eden, seri veya seviye belirten tüm derslerde (I, II, III vb.) kesinlikle **Roma rakamları** kullanılmalıdır. Arap rakamları (1, 2, 3) kullanılmamalıdır.
    * ✅ **Doğru:** `Analiz I`, `Fizik II`, `İleri İngilizce III`
    * ❌ **Yanlış:** `Analiz 1`, `Fizik 2`, `İleri İngilizce 3`
* **Tek Dil Kuralı (Türkçe) ve Klasör Hiyerarşisi:** Sütun boşluklarına sığmadığı için aynı satırda 3 dil birden (`TR / EN / DE`) kullanılması **iptal edilmiştir**. Temel müfredat dosyaları sadece **Türkçe** olarak yazılacaktır.
    * ✅ **Doğru:** `Analiz II` veya `Bilgisayar Bilimine Giriş`
    * ❌ **Yanlış:** `Analiz II / Analysis II / Analysis II`
* **Çeviri Klasörleri:** Yabancı dildeki müfredatlar, kök müfredat dizini altındaki `EN/` ve `DE/` klasörlerinde, aynı dosya ve klasör hiyerarşisi korunarak tutulacaktır. (Örn: `Curriculum/EN/Mühendislik Fakültesi/...`)
* **Temizlik ve Meta Etiket Konumu:** Ders isimlerinin sonunda gereksiz boşluklar veya bölüm içi özel parantez notasyonları (örn. `(Z)`, `(S)`) bulunmamalıdır. Eğer eklenecekse **Meta Etiketler (`{...}`) daima en sonda ve o dosyanın dilinde veya evrensel (Türkçe kural formatında)** yer almalıdır.
    * ✅ **Doğru:** `Analiz II {TIP:KISITLI}` (Türkçe dosyada) veya `Analysis II {TIP:KISITLI}` (İngilizce dosyada)
    * ❌ **Yanlış:** `Analiz II {TIP:KISITLI} (Z)`

## 2. Havuz Dersleri, Çoklu Seçim Mantığı ve Süper Havuzlar
Aynı havuzdan birden fazla seçmeli ders alınması gereken durumlarda (Örn: Bir dönemde iki tane Teknik Seçmeli alınacaksa ve her biri 6 AKTS ise), bu dersler alt alta ayrı satırlar halinde **yazılmamalıdır**. Bunun yerine **tek satırda birleştirilerek** yazılmalıdır.
  ```text
  | SD  | Teknik Seçmeli Ders {SECIM:2} | - | D/E | 3 | 0 | 0 | 6 |
  ```
  *(Bu ifade parser tarafından: "Öğrenci bu havuzdan her biri 6 AKTS olan 2 ders seçecektir, toplam 12 AKTS" şeklinde okunup `Havuzlar` tablosundaki `zorunlu_secim_sayisi = 2` alanına yazılacaktır.)*

* **Süper Havuzlar (Havuz İçinde Havuz):** Eğer bir havuz, diğer alt havuzları kapsayan bir "Süper Havuz" ise (Örn: SDIII havuzu, SDIa ve SDIb havuzlarındaki tüm dersleri içeriyorsa), asıl tabloda süper havuza ait tek bir havuz banner'ı açılmalı ve altına alt havuzlar liste olarak eklenmelidir.
    * Alt havuzlar listelenirken `DİL | T | U | L | AKTS` sütunları **birleştirilerek** ilgili alt havuzun kodu buraya yazılmalıdır. Sütun çizgilerinin (`|`) hizası bozulmamalıdır.
    * ✅ **Örnek Doğru Kullanım:**
```text
+--------+------------------------------------------------------------+--------+----------------------------+
| KOD    | DERS ADI                                                   | ÖN KOS | DİL | T | U | L | AKTS |
+--------+------------------------------------------------------------+--------+----------------------------+
| HAVUZ  | UYGULAMALI BİLGİSAYAR MÜHENDİSLİĞİ HAVUZU                  | -      | SDIa, SDIIa                |
| HAVUZ  | BİLGİSAYAR DONANIMI HAVUZU                                 | -      | SDIb, SDIIb                |
+--------+------------------------------------------------------------+--------+----------------------------+
```

## 3. Ön Koşullar (Prerequisites) ve Uzun Açıklamalar
* Derslerin ön koşulları "ÖN KOS" sütununda belirtilir. Eğer ön koşul standart bir ders koduysa (Örn: `MAT101`) doğrudan sütuna yazılır.
* **Uzun Ön Koşullar:** Eğer ön koşul, sütuna sığmayacak kadar uzunsa (örn: "Kredinin %70'ini tamamlamış olmak" vb.) ön koşul sütununa yıldız (`*`, `**`, `***`) konur.
* **Yıldız Açıklamaları:** Bu yıldızların açıklaması, ilgili dönemin veya havuz tablosunun altındaki `----------------------------------------------------------------------------------------------------` ayırıcı çizgisinden **hemen sonra** yapılmalıdır.
* Ayrıca, sayfanın en sonunda da bu tip tüm özel açıklamaları barındıran genel bir "Açıklamalar / Notlar" bölümü bulunmalıdır.
Tüm satırlar dikey çizgi `|` (pipe) karakteri ile ayrılmalıdır. En temel ve standart sütun dizilimi şu şekilde olmalıdır:

`| Ders Kodu | Ders Adı {Etiketler} | Önkoşul | T | U | L | AKTS |`

* **Ders Kodu:** Birleşik ve büyük harf (Örn: `MAT108`). Havuz dersleri için standartlaştırılmış havuz kodları (`SD`, `ZSD`, `ÜSD` vb.).
* **Ders Adı:** Standart isimlendirme (Roma rakamları ile).
* **Önkoşul:** Önkoşul yoksa `-` işareti konulmalıdır. Boş bırakılmamalıdır.
* **T, U, L, AKTS:** Teori, Uygulama, Laboratuvar saatleri ve AKTS değerleri sayısal olmalıdır.

## 4. Metadata Etiketleri (Flags)
Ders adının sonuna süslü parantez `{}` içinde eklenen etiketler, parser'a özel mantıksal talimatlar verir:

* `{TIP:KISITLI}`: Bu havuz tüm okuldaki derslere değil, sadece belirli 3-4 derse kısıtlanmış bir havuzdur.
* `{SECIM:X}`: Bu havuz grubundan o dönem X adet ders seçilmelidir.
* `{ORTAK_KOD:X}`: Üniversite genelindeki ortak bir havuzu (Örn: `{ORTAK_KOD:USD}`) işaret eder.
* `{UST_HAVUZ:X_Y_Z}`: Bu havuz, kendi içerisinde başka alt havuzları barındıran kapsayıcı (parent) bir üst havuzdur. Alt havuzların kodları veya isimleri etiket içine virgülle veya tire ile yazılarak belirtilebilir (Örn: `{UST_HAVUZ:SD1,SD2}`).

**Örnek Bir Dönem Tablosu (ASCII Formatında):**
```text
II. YARIYIL (BAHAR)
| Ders Kodu | Ders Adı                                | Önkoşul | T | U | L | AKTS |
|-----------|-----------------------------------------|---------|---|---|---|------|
| MAT108    | Analiz II                               | MAT103  | 3 | 2 | 0 | 6    |
| FIZ102    | Fizik II                                | FIZ101  | 3 | 0 | 2 | 5    |
| ZSD       | Kısıtlı Zorunlu Seçmeli {TIP:KISITLI}   | -       | 3 | 0 | 0 | 5    |
| SD        | Teknik Seçmeli Ders {SECIM:2}           | -       | 3 | 0 | 0 | 6    |
```
## 5. Seçmeli Ders Havuzu Başlıkları (Banner)
Müfredat listelerinin en altında yer alan ve seçmeli derslerin içeriklerini detaylandıran havuz tablolarının başlıklarında (banner), **havuz kodu mutlaka köşeli parantez `[...]` içinde ve ismin en başında** belirtilmelidir. Bu, ayrıştırıcının o tablonun tam olarak hangi havuz koduna ait olduğunu hatasız bulmasını sağlar.

* ✅ **Doğru:** `[SDII] Seçmeli Ders Alanı II (2. Dönem)`
* ✅ **Doğru (Geniş Havuz):** `[SDV, SDVI, SDVII, SDVIII] Seçmeli Ders Alanları (Genel Havuz)`
* ❌ **Yanlış:** `Seçmeli Ders Alanı II - SDII` veya `SDM - Matematik Havuzu` (Kod köşeli parantez içinde ve en başta değil)

**Kapsayıcı Üst Havuzların (Super-Pools) Sıralaması:**
Eğer bir havuz (Örn: Makine Mühendisliğindeki `SDUx`), kendi altında `A`, `B`, `C` gibi uzmanlık alt havuzlarını tamamen kapsayacak şekilde tasarlandıysa, bu ana/kapsayıcı üst havuz, dosyanın en altındaki "SEÇMELİ DERS HAVUZLARI" listesinin **en başında (ilk sırada)** tanımlanmalıdır. Alt havuzlar ise bu ana havuzun altında listelenmelidir.

Müfredat tabloları standart `+--------+------------------+...` ASCII çerçeveleriyle çizilmeli ve dönemler `X. DÖNEM` başlıklarıyla birbirinden net bir şekilde ayrılmalıdır.

## 6. Dönem Başlıkları ve Toplam Satırları
* **Dönem Başlıkları:** Dönem başlıklarında "ZORUNLU" gibi gereksiz ifadeler bulunmamalıdır. Bunun yerine, tam olarak öğrencinin bulunduğu sınıf, yarıyıl ve dönemin (Güz/Bahar) belirtildiği `X. DÖNEM (Y. SINIF / Z. YARIYIL (GÜZ/BAHAR))` formatı kullanılmalıdır. 
    * ✅ **Doğru:** `5. DÖNEM (3. SINIF / 1. YARIYIL (GÜZ))` veya `6. DÖNEM (3. SINIF / 2. YARIYIL (BAHAR))`
    * ❌ **Yanlış:** `1. DÖNEM (ZORUNLU)` veya sadece `5. DÖNEM`
* **TOPLAM Satırları:** Tabloların altındaki "TOPLAM" satırında yer alan "Ders Adı" sütununa T, U, L toplamları **yazılmamalıdır**. Bunun yerine bu sütun boş bırakılabilir veya döneme ait **özel notlar** (Örn: "Seçmeli ders alınmasına gerek yoktur" vb.) yazmak için kullanılabilir.

## 6. Bölüm Önekleri (Department Prefixes) ve Veritabanı Güvenliği
Veritabanı bütünlüğünü (database integrity) sağlamak ve farklı bölümlerin aynı isimli havuzlarının (Örn: Makine Mühendisliğindeki `SDII` ile Elektrik-Elektronik Mühendisliğindeki `SDII`) birbirine karışmasını engellemek için, havuz kodları arka planda "BölümKodu_HavuzKodu" (Örn: `MEC_SDP I`, `ETE_SDII`) şeklinde nominal birleştirilmiş olarak veya `bolum_id` ile izole edilerek tutulacaktır. 

Ancak **kullanıcı arayüzünde (UI) ve bu `.txt` müfredat dosyalarında** bölüm kodunu (MEC_, ETE_ vb.) havuz isimlerinin başına yazmaya **gerek yoktur**. Müfredat `.txt` dosyaları sade kalmalıdır (Sadece `[SDP I]` yazılması yeterlidir). Arka plandaki ayrıştırıcı (parser) ve veritabanı kurgusu bu birleştirmeyi güvenlik ağı (safety net) olarak kendisi yapacaktır.
