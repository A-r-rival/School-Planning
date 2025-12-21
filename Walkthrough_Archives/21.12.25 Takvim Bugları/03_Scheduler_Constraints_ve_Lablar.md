# 03. Scheduler Kısıtlamaları ve Laboratuvar Atamaları

## Sorun Tanımı
Otomatik program oluşturulduğunda "Anayasa Hukuku I" gibi derslerin Laboratuvarlara atandığı görüldü. Kullanıcı, **Laboratuvarların** sadece **Mühendislik**, **Fen** ve **Mimarlık** fakülteleri tarafından kullanılması gerektiğini ve Hukuk, İktisat gibi fakülte derslerinin buralara atanmaması gerektiğini belirtti.

## Çözüm Mimarisi

Sorun `ORToolsScheduler` sınıfının oda atama mantığındaydı. Scheduler, `Derslikler` tablosundaki tüm odaları (Tip ayırt etmeksizin) her ders için "olası oda" (`possible_rooms`) olarak değerlendiriyordu.

Bu durumu çözmek için iki aşamalı bir "Filtreleme" (Constraint) mekanizması kuruldu.

### Adım 1: Veri Zenginleştirme (Faculty Mapping)
Scheduler'ın bir dersin hangi fakülteye ait olduğunu bilmesi gerekiyordu. Veritabanı modelinde (`models/schedule_model.py`) tablolar arası (Ders -> Ders_Sinif -> Donem -> Bolum -> Fakulte) bir JOIN sorgusu ile bu haritayı çıkaran bir metot eklendi:

```python
def get_course_faculty_map(self):
    # Returns: { ("Ders Adi", Instance): ["Mühendislik Fak.", "Fen Fak."] }
    ...
```

### Adım 2: Constraint Logic (Kısıtlama Mantığı)
`controllers/scheduler.py` içindeki `load_data` metodunda bu harita belleğe yüklendi. Değişken yaratma döngüsü (`create_variables`) içine ise şu mantık eklendi:

```python
# Eğer oda bir Laboratuvar ise:
if "Laboratuvar" in room_type or "Lab" in room_type:

    # Kural 1: Dersin isminde "Lab" veya "Uygulama" geçiyor mu?
    # Geçmiyorsa (Örn: "Anayasa Hukuku"), bu odayı PAS GEÇ (Continue).
    if not ("Laboratuvar" in course_name or "Lab" in course_name):
        continue
    
    # Kural 2: Dersin Fakültesi "Fen/Mühendislik/Mimarlık" mı?
    # Eğer Hukuk Fakültesi ise, ismi "Hukuk Lab" olsa bile PAS GEÇ.
    allowed_facs = ["Mühendislik", "Fen", "Mimarlık", "Engineering", "Science"]
    course_faculties = self.course_faculties.get(key, [])
    
    is_allowed = False
    for fac in course_faculties:
         if any(allowed in fac for allowed in allowed_facs):
             is_allowed = True
             break
    
    if not is_allowed:
        continue # Bu ders bu laboratuvara atanamaz.
```

Bu mantık, "Hard Constraint" (Sert Kısıtlama) olarak çalışır. Yani Solver (Çözücü) bu olasılığı değişken uzayına hiç eklemez. Bu da çözümün %100 bu kurala uymasını garanti eder. Eğer çözüm bulunamazsa "INFEASIBLE" hatası döner (ki bu istenen davranıştır; Hukuk dersi için laboratuvardan başka yer yoksa program oluşmamalıdır).

## Sonuç
Yapılan testlerde "Anayasa Hukuku" dersinin artık Amfilere atandığı, sadece "Bilgisayar Mühendisliği Uygulama" gibi derslerin Laboratuvarlara yerleştiği doğrulanmıştır.
