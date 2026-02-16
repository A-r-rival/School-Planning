# Walkthrough: ScheduleModel Cleanup (16.02.2026)

## Changes Summary

[schedule_model.py](file:///D:/Git_Projects/School-Planning/models/schedule_model.py) went from **1689 → 1641 lines** (~50 lines net removed, +39 lines of section headers added).

---

## 1. Dead/Duplicate Methods Removed

### `get_all_teacher_course_preferences` — 2 copies, both deleted
- **L366 version:** 5-tuple `(ders_adi, preference_note, preference_type, hoca, ogretmen_num)` — İngilizce kolon adları
- **L891 version:** 4-tuple `(ders_adi, ders_secim_notu, tercih_tipi, hoca)` — Türkçe kolon adları
- **Neden silindi?** `grep` ile tüm proje tarandı, hiçbir view/controller/service bu metodu çağırmıyordu. İkisi de dead code.

### `get_all_courses_assigned_to_teachers` — duplicate deleted
- **L323 (TUTULAN):** 4-tuple `(ders_adi, ders_instance, hoca, ogretmen_id)` — `teacher_availability_view.py:386` bunu kullanıyor
- **L908 (SİLİNEN):** 3-tuple `(ders_adi, ders_instance, hoca)` — `ogretmen_id` eksik
- **Neden?** Python'da aynı isimli iki method tanımlanırsa sonuncusu geçerli olur. Yani uygulama yanlış (3-tuple) versiyonu kullanıyordu, ama crash etmemişti çünkü `ogretmen_id` opsiyonel kullanılıyordu.

### Teacher Preferences Feature — tamamen kaldırıldı
`add_teacher_course_preference`, `remove_teacher_course_preference`, `get_teacher_course_preferences` — 3 method silindi. WANTED/BLOCKED sistemi hiç UI'a bağlanmamıştı, scheduler da kullanmıyordu. Kaldırılan feature.

- `delete_curriculum_course` içindeki `Ogretmen_Ders_Tercihleri` temizleme satırı da silindi
- `tests/verify_preferences_table.py` test dosyası silindi
- Migration 003 ve DB tablosu tutuldu (migration silmek version tracking'i bozar)

---

## 2. Section Headers Eklendi (13 bölüm)

Dosyada navigasyonu kolaylaştırmak için `═══` çizgili section header'ları eklendi:

```
INIT & CONNECTION
SCHEDULE CRUD
CALENDAR QUERIES (used by CalendarScheduleBuilder)
TEACHER-COURSE ASSIGNMENT
CURRICULUM MANAGEMENT
TEACHER & CLASSROOM LOOKUPS
FACULTY & DEPARTMENT
STUDENT & STUDENT-NUMBER HELPERS
CLASSROOM CRUD
TEACHER AVAILABILITY & UNAVAILABILITY
STUDENT QUERIES & GRADES
MASTER VIEW & SNAPSHOTS
```

---

## 3. File Cleanup (Aynı Oturumda)

| Kategori | Dosyalar | Aksiyon |
|---|---|---|
| Debug `.txt` dosyaları (7) | `debug_infeasibility_report.txt`, `room_preference_debug.txt`, `unschedulable_courses.txt`, `missing_data_report.txt`, `output_debugging.txt`, `verify_output.txt`, `faculty_department_codes.txt` | Silindi |
| Orphan `.db` dosyaları (3) | `school_data.db`, `school_planning.db`, `school_schedule.db` | Silindi |
| Debug scripts (16) | `scripts/debug/` klasörü komple | Silindi |
| Root docs (2) | `Project_Documentation.html`, `README_MVC.md` | Korundu |
| Empty dir | `logs/` | `.gitkeep` eklendi |

---

## Q&A: Bu Oturumda Sorulan Sorular

### L189: Niye `LEFT JOIN`? Niye düz `JOIN` konmuş olabilirler?

**Düz JOIN:** İlk geliştirici "her ders `Dersler` tablosunda olmalı" varsayımıyla yazmış. Normal akışta doğru — ders önce müfredata, sonra programa eklenir.

**Sorun:** "Bu Dönemlik Ekle" (ad-hoc) ile eklenen dersler `Ders_Programi`'ye doğrudan yazılıyor, `Dersler`'de karşılıkları yok. Düz JOIN bu dersleri sessizce düşürüyordu.

**LEFT JOIN çözümü:** `Ders_Programi` her zaman master tablo. `Dersler`'de karşılığı yoksa `ders_kodu` NULL döner, `COALESCE` ile `'CUSTOM'` gösterilir.

### `GROUP_CONCAT(COALESCE(...))` vs düz `COALESCE(...)` farkı ne?

İkisi de aynı mantık: ad-hoc derslerde `ders_kodu` NULL ise `'CUSTOM'` yaz.

- **Classroom query:** `GROUP BY` var → aynı slot'ta birden fazla instance olabilir → `GROUP_CONCAT` ile birleştirilir
- **Student group query:** `GROUP BY` yok → her satır tek ders → düz `COALESCE` yeterli

### `get_all_courses_as_string` export için tutulmayacak mıydı?

Hayır. Export için tutulan fonksiyonlar `export_schedule()` ve `import_schedule()` — bunlar FUTURE olarak hâlâ duruyor. `get_all_courses_as_string` eski string-based formatter'dı, tek çağıranı (`get_statistics`) zaten audit'te silinmişti.

### `_validate_course_data` niye silindi?

Silindi değil, taşındı. Validation artık:
1. **`CourseInput`** entity — type-safe dataclass, yanlış tip veremezsin
2. **`ScheduleService.add_course()`** — iş kuralları burada

Eski `_validate_course_data()` raw dict üzerinde elle kontrol yapıyordu, hiçbir yerden çağrılmıyordu.

---

## Verification

- `ScheduleModel()` instantiation ✅
- Tüm view tab'ları (Schedule, Calendar, Curriculum, Teacher) çalışıyor ✅
- Git commit: `4c33c34` (ad-hoc fix + cleanup)
