# Walkthrough: Dönem Sistemi ve Müfredat Görünümü Düzeltmeleri

**Tarih:** 15 Şubat 2026  
**Kapsam:** Dönem ayrımı, eksik ders verileri, zamanlayıcı filtresi, takvim görünümü

---

## 1. Dönem Anahtarlarının İyileştirilmesi

### Problem
`curriculum_data.py` dönem anahtarları basit integer (`1`, `2`, ...) formatındaydı, okunaklı değildi.

### Çözüm
Betimleyici format eklendi: `"1. Dönem / 1. Yıl Güz Dönemi"`, `"2. Dönem / 1. Yıl Bahar Dönemi"`, vb.

### Değişen Dosyalar

| Dosya | Değişiklik |
|---|---|
| `scripts/parse_curriculum.py` | `semester_key()` yardımcı fonksiyonu eklendi, betimleyici anahtarlar üretiliyor |
| `database/curriculum_data.py` | Yeni formatta yeniden üretildi |
| `scripts/populate_students.py` | String anahtarlardan dönem numarası parse ediliyor |
| `models/schedule_model.py` | `_build_semester_lookup` yeni anahtarları parse ediyor |

---

## 2. Bahar Dönemi Zorunlu Derslerinin Düzeltilmesi

### Problem
Müfredat görünümünde "Bahar" seçildiğinde hiçbir zorunlu (core) ders görünmüyordu. Birinci sınıf tamamen boştu.

### Kök Neden
`populate_students.py` satır 216:
```python
current_semester = year * 2 - 1  # Her zaman 1, 3, 5, 7 (Güz!)
```
`Ders_Sinif_Iliskisi` tablosuna kayıt sadece `is_current_term` bloğunda yapılıyordu. Güz dışındaki dönemler hiç kayıt almıyordu.

### Çözüm

```diff
- current_semester = year * 2 - 1
+ current_semester = year * 2  # Hem Güz hem Bahar dahil
```

Ayrıca geçmiş dönem bloklarına da (irregular fail/pass, regular pass) `Ders_Sinif_Iliskisi` ekleme kodu eklendi:

```python
# Geçmiş dönemler için de sınıf ilişkisi ekle
course_year_level = (sem + 1) // 2
cohort_entry_year = 2024 - course_year_level + 1
donem_sinif_num = f"{cohort_entry_year}_{bolum_id}_{course_year_level}"
model.c.execute("INSERT OR IGNORE INTO Ders_Sinif_Iliskisi ...")
```

### Değişen Dosya
- `scripts/populate_students.py` — 3 yerde `Ders_Sinif_Iliskisi` ekleme kodu + `current_semester` düzeltmesi

---

## 3. Müfredat Görünümü Index Düzeltmesi

### Problem
`curriculum_view.py` havuz checkbox kısmı eski tuple indekslerini kullanıyordu (`c[11]`, `c[12]`). Dönem sütununun eklenmesiyle indeksler kaydı.

### Çözüm
```diff
- if c[11] == 1 and c[12]:  # IsPool ve PoolCode
-     current_pool_codes.add(c[12])
+ if c[10] == 1 and c[11]:  # IsPool ve PoolCode
+     current_pool_codes.add(c[11])
```

### Değişen Dosya
- `views/curriculum_view.py` — Havuz checkbox indeksleri düzeltildi

---

## 4. Zamanlayıcı (Scheduler) Dönem Filtresi

### Problem
Zamanlayıcıdaki dönem filtresi tamamen devre dışıydı — 70 satır yorum ve sonunda `is_match = True` ile tüm dersler dahil ediliyordu. Güz ve Bahar dersleri beraber zamanlanmaya çalışılıyordu → solver FAILED.

### Çözüm
`semester_lookup` kullanılarak gerçek filtreleme eklendi:

```python
if semester_filter and semester_filter not in ("Hepsi", "Yaz"):
    lookup = getattr(self.db_model, 'semester_lookup', {})
    for c in self.courses:
        code = str(c.get('code', '')).strip()
        if code and code in lookup:
            sem_set = lookup[code]
            if semester_filter in sem_set:
                semester_courses.append(c)
            elif "Güz" in sem_set and "Bahar" in sem_set:
                semester_courses.append(c)
        else:
            semester_courses.append(c)
```

Buton ismi de güncellendi:
```diff
- "Şuanki Dönem için Otomatik Ders Programı Oluştur"
+ "Filtrede Seçili Dönem İçin Otomatik Ders Programı Oluştur"
```

### Değişen Dosyalar
- `controllers/scheduler.py` — 70 satır no-op → 20 satır gerçek filtre
- `views/schedule_view.py` — Buton ismi güncellendi

---

## 5. Takvim Havuz/Staj/Proje Gösterimi

### Problem
Takvim sağ üstte havuz, staj ve proje dersleri artık görünmüyordu. `calendar_view.py` eski integer anahtarı (`"2"`) ile `curriculum_data` sorgusu yapıyordu, ama anahtarlar artık betimleyici.

### Çözüm
```diff
- sem_courses = dept_data['curriculum'].get(str(semester_num), [])
+ sem_key = f"{semester_num}. Dönem / {sem_year}. Yıl {sem_season} Dönemi"
+ sem_courses = dept_data['curriculum'].get(sem_key, [])
```

### Değişen Dosya
- `views/calendar_view.py` — Dönem anahtarı yeni formata güncellendi

---

## 6. Modül Yeniden Adlandırma

```
models/services/seeder.py → models/services/faculty_and_department_id_seeder.py
```

İlgili import'lar güncellendi:
- `models/schedule_model.py`
- `scripts/populate_students.py`

---

## Doğrulama Sonuçları

| Test | Sonuç |
|---|---|
| Müfredat Görünümü — Bahar zorunlu dersler | ✅ Görünüyor |
| Müfredat Görünümü — 1. sınıf verileri | ✅ Görünüyor |
| Takvim — Havuz/Staj/Proje etiketleri | ✅ Görünüyor |
| Zamanlayıcı — Dönem filtresi | ✅ Aktif (eski no-op kaldırıldı) |
| DB — `Ders_Sinif_Iliskisi` kayıtları | ✅ Hem Güz hem Bahar mevcut |
