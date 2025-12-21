# 02. UI Çökmesi (Crash) ve Filtreleme Mantığı

## Sorun Tanımı
Kullanıcılar iki temel UI sorunu bildirdi:
1.  **Crash:** Takvim ekranında, Öğrenci Grubu -> Fakülte -> Bölüm seçimi yapıldığı anda uygulama çöküyordu. Hata mesajı terminalde veya `debug` loglarında görünüyordu.
2.  **Stale Filters (Bayat Filtreler):** Bir Fakülte seçilip Bölüm seçildikten sonra, kullanıcı Fakülteyi değiştirirse alttaki Bölüm ve Yıl kutucukları eski halinde kalıyordu. Bu durum tutarsız veri sorgularına ve kafa karışıklığına yol açıyordu.

## Teknik Analiz ve Çözüm

### 1. Crash Analizi: `ValueError`
Terminal çıktısındaki hata şuydu: `ValueError: invalid literal for int() with base 10: 'Seçiniz...'`.

**Senaryo:**
1.  Kullanıcı Bölümü seçtiğinde `currentIndexChanged` sinyali tetikleniyor.
2.  Controller (`schedule_controller.py`), `handle_calendar_filter` metodunu çağırıyor.
3.  Metot, ders programını çekmek için parametreleri topluyor: `dept_id` ve `year`.
4.  Kullanıcı henüz Yıl seçmediği için Yıl combobox'ının değeri varsayılan olan `"Seçiniz..."` stringi.
5.  Kod `int(data["year"])` satırında string'i sayıya çevirmeye çalışırken patlıyor.

**Çözüm:**
Controller katmanına bir "Sanity Check" (Mantık kontrolü) eklendi.

```python
# schedule_controller.py içindeki düzeltme
# 'year' değeri var mı VE sayıya çevrilebilir mi?
elif "year" in data and data["year"] and str(data["year"]).isdigit():
     raw_schedule = self.model.get_schedule_by_student_group(...)
```
Bu kontrol sayesinde, kullanıcı henüz geçerli bir yıl seçmemişse sistem sorgu atmayı reddediyor ve çökmeyi engelliyor.

### 2. Sinyal Yönetimi ve Filtre Sıfırlama
Fakülte değiştirildiğinde alt filtrelerin (Bölüm, Yıl) sıfırlanması gerekiyordu. Ancak PyQt5'te programatik olarak `.setCurrentIndex(0)` veya `.clear()` çağırmak da bir `currentIndexChanged` sinyali tetikler. Bu, istenmeyen sonsuz döngülere veya gereksiz sorgulara yol açabilir.

**Çözüm: `blockSignals` Kullanımı**
`views/calendar_view.py` içinde sinyaller geçici olarak bloklanarak temizlik işlemi yapıldı.

```python
def _on_filter_1_changed(self): # Fakülte değiştiğinde
    if view_type == "Öğrenci Grubu":
        # Alt widgetların sinyallerini sustur
        self.filter_widget_2.blockSignals(True)
        self.filter_widget_3.blockSignals(True)
        
        # İçeriği temizle ve varsayılanları yükle
        self.filter_widget_2.clear()
        self.filter_widget_3.clear()
        self.filter_widget_3.addItem("Seçiniz...", None)
        self.filter_widget_3.addItems([str(i) for i in range(1, 5)])
        
        # Sinyalleri tekrar aç
        self.filter_widget_2.blockSignals(False)
        self.filter_widget_3.blockSignals(False)
```

### 3. Görsel Düzenlemeler
Kullanıcı takvimde Haftasonlarını görmek istemediğini belirtti.
*   `views/calendar_view.py` içinde tablo oluşturulurken `days` listesinden "Cumartesi" ve "Pazar" çıkarıldı.
*   Tablo sütun sayısı 7'den 5'e düştü.
*   Veri doldurma mantığındaki (`day_map`) haritalama güncellendi. Eğer veritabanından hafta sonu dersi gelirse (ki scheduler artık üretmiyor) bu dersler sessizce yutulacak şekilde `if day not in day_map: continue` kontrolü zaten mevcuttu.
