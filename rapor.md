# Salı Günündeki Sıkışmaların Matematiksel Nedeni (Paradoks)

Salı günkü o anlamsız sıkışmaların (bunching) tek bir nedeni var: **"Merdiven yapmasın, küçülürse önceki koordinatlarının içinde kalsın"** kuralının yarattığı matematiksel paradoks!

Senin istediğin kuralı sisteme tam olarak entegre ettim. Sistem artık blokların kayarak merdiven yapmasını yasaklıyor. Bir blok daralacaksa, **eski sınırlarının içinde kalmak zorunda**. 

Ancak bu kural, Salı günü gibi yoğun günlerde (2 dersten 7 derse çıkılan saatlerde) geometrik bir faciaya yol açıyor. Nedenini şu örnekle görselleştirelim:

### 1. Adım: Saat 11:30 (Sadece 2 Ders Var)
Ekran 2 ders tarafından %50 / %50 paylaşılır. İkisi de kocaman bloklardır.
`[ MAT106 %50 Alan ]` `[ VWL473 %50 Alan ]`

### 2. Adım: Saat 12:00 (5 Yeni Ders Daha Geliyor, Toplam 7 Ders)
Her dersin adil payı artık %14 olmalıdır. 
MAT106 ve VWL473'ün %14'e daralması gerekir.
Ama kuralın diyor ki: **"Daralacaklarsa eski koordinatlarının dışına çıkamazlar (kayamazlar)."**

MAT106 sol kenarda olduğu için %14'e daralır:
`[MAT14] [...... 36% BOŞLUK ......]`

VWL473 sağ tarafta (eski koordinatlarında) kalmak zorundadır, sola kayamaz (kayarsa merdiven olur):
`[MAT14] [...... 36% BOŞLUK ......] [VWL14] [...... 36% BOŞLUK ......]`

### 3. Adım: Yeni Gelen 5 Ders Nereye Gidecek?
Elimizde iki adet %36'lık kopuk boşluk var. Yeni gelen 5 dersi bu boşluklara yerleştirmek zorundayız. Çözücü bu dersleri bölüp parçalayamayacağı için mecburen bir boşluğa 1 dersi koyup, diğer daracık boşluğa kalan 4 dersi **üst üste sıkıştırmak (sliver/bunching)** zorunda kalıyor!

İşte Salı günkü o incecik iğrenç şeritlerin (sıkışmaların) sebebi tam olarak budur.

---

### Çözüm Seçenekleri (Karar Senin)

Bu iki durum aynı evrende aynı anda var olamaz. Birini seçmeliyiz:

1. **Seçenek A (Sıkışmalar Bitsin, Merdiven Serbest Olsun):**
   * Eğer "Merdiven" (blokların sağa sola kayması) yasağını kaldırırsam, Saat 12:00'da MAT106 ve VWL473 hemen sola doğru kayar.
   * `[MAT14] [VWL14] [YENİ14] [YENİ14] [YENİ14] [YENİ14] [YENİ14]`
   * Tüm ekran ip gibi, kusursuz ve eşit bir grid (ızgara) olur. Sıkışma biter. Ama VWL473 sola kaydığı için bir "Merdiven" çizmiş olur.

2. **Seçenek B (Merdiven Yasak Kalsın, Sıkışmalara Göz Yum):**
   * Şu anki sistem. Bloklar asla kaymaz, düzgün dururlar. Ama yeni dersler o küçük boşluklara sığmak için atomlarına kadar sıkışırlar.

**Hangisini tercih edersin? Merdiven yasağını (Staircase Penalty) kaldırıp ekranı kusursuz bir ızgaraya mı dönüştürelim?**

# Piksel Hassasiyetli ve Bilgi Odaklı Yeni Yerleşim Motoru (ARŞİV)

> [!NOTE]
> Bu sistem şu anda aktif değildir ve `archive/cp_solver_pixel_aware/` dizinine kaldırılmıştır. Mevcut takvim yerleşimi "midpoint" (orta nokta) mantığına geri dönmüştür, ancak metin render kalitesi (sabit puntolar ve word-wrap) korunmuştur.

Son güncellemelerle birlikte, takvim yerleşim motorunu tamamen "bilgi kazancı" (information gain) odaklı ve piksel hassasiyetli bir yapıya dönüştürmüştük. 

### Yapılan Temel Değişiklikler:

1. **Piksel Tabanlı Dinamik Ödüllendirme:** 
   - Soyut genişlik puanlaması yerine, `QFontMetrics` kullanarak ders adı, kodu, hoca ve oda bilgilerinin gerçek piksel ihtiyaçlarını hesaplıyoruz.
   - Solver, bir bloğu en uzun kelimesi sığana kadar (min_thresh) genişletmeye %50 puan verir; tam metin sığana kadar (max_thresh) ise lineer olarak puan kazandırmaya devam eder.

2. **Hiyerarşik Bilgi Önceliği:**
   - Puanlama sistemi şu önceliğe göre çalışır: **Ders Kodu (3000) > Ders Adı (700) > Öğretmen (300) > Oda (100)**.
   - Bu sayede en kritik bilgi her zaman en çok alanı kaplamaya çalışır.

3. **Göreceli Adalet Sınırı (Relative Fairness):**
   - Bir slot içindeki en geniş ve en dar blok arasındaki oran **3.0 kat** ile sınırlandırıldı. 
   - Bu, solver'ın puan toplamak için bir dersi devasa yapıp diğerini 30 piksele hapsetmesini (starvation) engeller.

4. **Dinamik Pencere Boyutlandırma (Responsive):**
   - Pencere boyutu değiştiğinde 400ms beklemeli (debounced) bir timer ile solver tekrar tetiklenir. Ekran büyüdükçe veya küçüldükçe ders blokları kendilerini en çok bilgiyi sığdıracak şekilde yeniden optimize eder.

5. **Metin Kırpma Mantığının Kaldırılması:**
   - Eski sistemdeki "sığmıyorsa gizle" veya "sadece kod göster" gibi katı kurallar kaldırıldı. Artık blok ne kadar genişse, metin o alan içinde doğal bir şekilde kelime kaydırma (word-wrap) yaparak sığmaya çalışır.

6. **Çoklu Çekirdek Performansı:**
   - CP-SAT solver parametreleri optimize edilerek 8 çekirdekli paralel arama aktif edildi. Çözüm süresi karmaşık günlerde bile 50ms altına düşürüldü.

### Teknik Commit Mesajı:
`feat(layout): implement pixel-aware CP-SAT block sizing and continuous info-gain rewards`
- Piksel bazlı ödüllendirme sistemi eklendi.
- Pencere yeniden boyutlandırma desteği getirildi.
- Bilgi hiyerarşisi (Kod > Ad > Hoca > Oda) tanımlandı.
- 3.0x adalet sınırı ile blok sönümlenmesi engellendi.
- Çoklu çekirdek desteği ile performans iyileştirildi.
