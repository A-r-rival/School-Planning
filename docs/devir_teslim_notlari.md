# Devir Teslim & Geliştirici Durum Notları
Bu belge, bir sonraki `conversation` (geliştirme oturumu) için mevcut bağlamı, denenen yolları, elde edilen analizleri ve bir sonraki adımda çözülmesi muhtemel düğümleri korumak amacıyla hazırlanmıştır.

---

## 1. Çözmemiz Gerekenler ve Sonraki Adımlar
En son oturumda **"Takvim üzerinde havuz/seçmeli derslerinin (ZSD, ÜSD vb.) görünmemesi ve işaretli onay kutularının (CheckBox) çalışmaması"** sorununun kökenine inilmiştir. Kod bazındaki 4 devasa blokaj çözülmüştür. Ancak kullanıcı, denemelerinde uygulamanın eski sürümü RAM'de açıkken (hot-reload olmaksızın) sonuç alamadığı için mesai burada bırakılmıştır.

**Bir Sonraki Oturumda İlk Yapılacaklar:**
1. Uygulamanın **tamamen kapatılıp baştan çalıştırılması**. `ScheduleModel.__init__` bloğundaki `_patch_pool_sinif_duzeyi` oto-yamasının devreye girerek veritabanındaki `"0"` sınıf seviyesindeki havuz derslerini yamaması bekleniyor.
2. Arayüzden **"Programı Oluştur"** tuşuna yeniden basılması. Çünkü Python tabanlı olan JSON `pool_codes` filtre hatası (dersi tamamen silen sızıntı), ancak Scheduler baştan çalıştırıldığında eski etkisini yitirecektir.
3. Bunlar yapıldıktan sonra "Öğrenci Grubu" sekmesinde 3. Sınıf Bilgisayar M. seçildiğinde, "ÜSD / ZSD" gibi ders kutularının grid (ızgara) üzerine düşüp düşmediği ve onay kutusu kaldırıldığında grid üzerinden kaybolup kaybolmadığı son kez gözle teyit edilmeli.
4. **Ek Bir Teori (Ders Instance'ı Patlaması):**
   Eğer üstteki testler başarıyla yapılsa dahi havuz dersleri SQLAlchemy/SQLite tabanlı `UNION ALL` da kesintiye uğruyorsa, `Ders_Programi` tablosundaki `ders_instance` (2, 3 vb.) değerlerinin, `Ders_Havuz_Iliskisi` tablosundaki `ders_instance=1` (sabit) değerleri ile JOIN koşulunda çatışıp çatışmadığı `diagnose.py` betiği ile yeniden sınanmalıdır. Gerekirse SQL JOIN içerisinde `d.ders_instance = dp.ders_instance` gibi daraltmalar gevşetilmelidir.

---

## 2. Neleri Denedik ve Hangi Duvarlara Çarptık?

Aşağıdaki liste, aynı hataları ikinci kez araştırmamak adına bugüne kadar "Denediğimiz ve Yanlış/Yetersiz Çıkan" yöntemleri içerir:

*   **INFEASIBLE Duvarı ve Sınıf Filtresi (Denedik - Yarım Başarı):**
    *   **Ne Oldu?** Havuz dersleri her sınıfa 4 kez kopyalanıp kapasite patlaması yaratıyordu.
    *   **Ne Denedik?** `scheduler_services.py` içine `od.sinif_duzeyi = dhi.sinif_duzeyi` şartını koştuk. Kapasite patlaması bitti (Başarı). Ancak takvimdeki seçmeli dersler tamamen yok oldu.
    *   **Neden Yok Oldu?** Eski veritabanı yamasında (`migration_012`) yeni havuz derslerinin yılı "0" (sıfır) olarak kalmıştı. SQL sınıf seviyesi eşleştiremeyince dersleri listeden siliyordu. *(Çözüm: Başlangıç Oto-Yaması eklendi).*
*   **Arayüzdeki "Seçmeli" Algılama Hatası (Denedik - Hatalıydı):**
    *   **Ne Oldu?** Arayüz `is_elective` bayrağı için sadece ismin içerisinde "seçmeli" (string lookup) arıyordu ("Fotoğrafçılık" veya "ZSD" yazdığı için arayüz bunları "Zorunlu Ders" zannedip filter-bypass ediyordu).
    *   **Ne Denedik?** Frontend kodunu baştan yazıp Regex / Ön Ek (`ZSD`, `ÜSD` vb.) okuyacak şekilde `9-Tuple` taşıma katmanına geçtik.
*   **Python Scheduler'ının Derinliklerinde Sessiz Veri Kaybı (CurriculumResolver):**
    *   **Ne Denedik?** Çekilen SQL verilerinin neden OR-Tools'a gitmediğini bulmak için `diagnose.py` yazdık. Python'un `resolve_context()` fonksiyonunda json içindeki `pool_codes` listesine baktığını ama `curriculum_data.py` json'unda böyle bir key bulunmadığı için yüzlerce dersi "geçersiz" sayıp sessizce (`None` dönerek) iptal ettiğini yakaladık.
    *   **Nasıl Çözüldü?** Json okuma mantığı terk edilip saf SQLite verisindeki `is_from_pool=1` bayrağına sonsuz itimat edildi.
*   **SQL Okuma Körlüğü (UNION ALL Eksikliği):**
    *   **Ne Oldu?** İşlem bittiğinde `Ders_Programi` programlanıp arayüze dönerken havuz dersleri tekrar görünmüyordu.
    *   **Ne Denedik?** Sorgularda sadece zorunlu dersler tablosu (`Ders_Sinif_Iliskisi`) kullanıldığını fark ettik, oraya özel bir `UNION ALL` fırlatarak Havuz derslerini (`Ders_Havuz_Iliskisi` üzerinden) aynı sütun dizilimiyle okumayı araya kaynattık.

## 3. Mimari Durum Özeti (Statüko)
Şu anda kod tabanı;
1. SQLite: Dinamik yamalı ve doğru yıllara sahip.
2. Python Zamanlayıcı (Backend): Doğrudan veritabanı boolean tiplerine güvenen, veriyi çöpe atmayan bir durumda.
3. OR-Tools (Solver): Kombinasyon kopyalamayan (İnfeasible'a düşmeyen) optimize haldedir.
4. PyQt Arayüzü: `(day, start, end, ... pool_codes)` dizilimi şeklinde güncel modern 9-Tuple dinleme şablonuna ayarlıdır.

"Uygulamanın yeniden başlatılarak Programın Sıfırdan Üretilmesi" eylemi ile yukarıdaki altyapının ilk gerçek dünyadaki ateşlemesi (ignition) beklenmektedir. Yeni oturumda bu noktadan bayrak devralınmalıdır.
