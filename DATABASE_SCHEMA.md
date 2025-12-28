**Database Schema - Course (Ders) Information**

## Main Tables:

### 1. Dersler (Course Master Table)
Location: `models/schedule_model.py`
Tutulan bilgiler:
- `ders_id` (INTEGER PRIMARY KEY)
- `ders_adi` (TEXT) - Ders ismi
- `ders_instance` (INTEGER) - Instance sayısı
- `bolum_num` (INTEGER) - Bölüm ID
- `sinif` (INTEGER) - Sınıf (1-4)
- `donem` (TEXT) - Dönem (Güz/Bahar)

### 2. Ders_Programi (Scheduled Courses)
Aktif ders programındaki dersler:
- `program_id` (INTEGER PRIMARY KEY)
- `ders_adi` (TEXT) - Ders ismi
- `ders_instance` (INTEGER)
- `ogretmen_id` (INTEGER)
- `gun` (TEXT) - Gün
- `slot_baslangic` (TEXT) - Başlangıç saati
- `slot_bitis` (TEXT) - Bitiş saati
- `oda` (TEXT) - Derslik

**NOT:** 
- ❌ `ders_kodu` column YOK (bu yüzden code-based filtering çalışmıyordu)
- ✅ Pool bilgisi curriculum_data.py'de var (kod tarafında)
- ✅ Cross-department elective ilişkisi için `Ders_Sinif_Iliskisi` tablosu olmalı

## Files:
- **Model**: `models/schedule_model.py`
- **Database**: `okul_veritabani.db`
- **Schema**: Check with `PRAGMA table_info(TableName)`
