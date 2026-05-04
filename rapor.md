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
