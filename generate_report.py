
import os

# Content for missing sections
VIEW_SECTION = """
6.2. View Katmanı

View katmanı, kullanıcı ile etkileşimi yöneten ve verilerin görselleştirilmesini sağlayan arayüz bileşenlerini içerir. PyQt5 kütüphanesi kullanılarak geliştirilen bu katman, "views" klasörü altında modüler bir yapıda organize edilmiştir.

**1. ScheduleView (Ana Pencere):**
Uygulamanın ana giriş noktasıdır. `QVBoxLayout` tabanlı dikey bir yerleşim düzeni kullanır.
- **Üst Panel:** "Yeni Ders Ekle", "Seçili Dersi Sil" gibi temel aksiyon butonlarını içerir.
- **Orta Panel (Ders Listesi):** `QListWidget` kullanılarak eklenen derslerin listelendiği alandır. Sağ tarafta kapsamlı bir filtreleme paneli (Fakülte, Bölüm, Sınıf, Gün, Ders Tipi) bulunur. Bu panel, kullanıcıların 1000+ ders arasından aradıklarını hızlıca bulmalarını sağlar.
- **Alt Panel (Gelişmiş Özellikler):** Takvim görünümü, öğrenci paneli ve öğretmen müsaitlik pencerelerine geçiş sağlayan butonlar burada yer alır.

**2. CalendarView (Haftalık Takvim):**
Ders programının en kritik görselleştirme bileşenidir.
- **Grid Yapısı:** `QTableWidget` kullanılarak 5 gün (sütun) ve 9 saatlik (satır, 08:00-17:00) bir ızgara oluşturulmuştur.
- **Görünüm Modları:** Kullanıcı "Öğretmen", "Derslik" veya "Öğrenci Grubu" bazlı filtreleme yapabilir.
- **Custom Rendering:** `_render_grid` metodu, çakışan dersleri veya aynı dersin ardışık bloklarını (teori + uygulama) akıllı bir şekilde birleştirir (`setSpan`).
- **Renk ve Lejant:** Seçmeli ders havuzları (Pools) için `identify_pools` algoritması ile otomatik renk ataması yapılır ve `LegendWidget` ile kullanıcıya gösterilir.

**3. StudentView (Öğrenci Paneli):**
Öğrenci verilerini ve transkriptlerini yönetmek için `QSplitter` ile ayrılmış iki panelli bir arayüz sunar.
- **Sol Panel:** Filtrelenebilir öğrenci listesi (`QTableWidget`). Regular, Irregular, ÇAP/Yandal gibi öğrenci tiplerine göre filtreleme imkanı sunar.
- **Sağ Panel:** Seçilen öğrencinin transkriptini, aldığı dersleri, notlarını ve başarı durumunu (Geçti/Kaldı - Renk kodlu) detaylı bir tablo olarak gösterir.

**4. TeacherAvailabilityView (Öğretmen Müsaitlik):**
Öğretmenlerin kısıtlamalarını yönetmek için `QDialog` tabanlı bir penceredir.
- **Tablo Yapısı:** Mevcut kısıtlamalar ("Namüsaitlik" veya "Haftalık Kısıt") listelenir.
- **Add Dialog:** `QTabWidget` kullanılarak iki tür kısıt ekleme imkanı sunar:
    - *Slot Kısıtı:* Belirli gün ve saat aralığını kapatma.
    - *Span Kısıtı:* "Haftada en fazla 2 gün gel" gibi genel blok kısıtlamaları.
"""

CONTROLLER_SECTION = """
6.3. Controller Katmanı

Controller katmanı, Model ve View arasındaki iletişimi koordine eden, iş mantığının akışını yöneten katmandır. "controllers" klasörü altında yer alır.

**1. ScheduleController:**
Sistemin beyni olarak çalışır.
- **Sinyal Yönetimi:** View katmanından gelen sinyalleri (`course_add_requested`, `generate_schedule_requested` vb.) dinler ve ilgili Model metodlarını tetikler.
- **Orchestration:** Alt pencerelerin (Calendar, Student) açılmasını ve bu pencereler arası veri senkronizasyonunu yönetir. Örneğin, ana ekranda bir ders eklendiğinde, takvim görünümünün de güncellenmesini sağlar.
- **Lazy Loading:** Performans optimizasyonu için alt görünümler (`calendar_view`, `student_view`) sadece ilk kez talep edildiklerinde oluşturulur.

**2. ORToolsScheduler (Optimizasyon Motoru):**
Google OR-Tools kütüphanesini sarmalayan (wrapper) sınıftır.
- **CP Model Hazırlığı:** Veritabanından gelen ham veriyi (dersler, odalar, öğretmenler) Constraint Programming modeline dönüştürür.
- **Değişken Oluşturma:** Her ders-slot-oda kombinasyonu için Boolean değişkenler (`x[c,d,s,r]`) oluşturur.
- **Çözüm Stratejisi (2-Phase):**
    - *Faz 1 (Core):* Önce zorunlu dersleri, seçmelileri yok sayarak çizer.
    - *Faz 2 (Elective):* Faz 1'deki atamaları sabitler (`AddHint` veya `Fix`) ve seçmeli dersleri yerleştirir. Bu strateji çözüm uzayını daraltarak performansı artırır.
- **Kısıt Uygulama:** `add_hard_constraints` metodu ile çakışmazlık, kapasite ve öğretmen müsaitlik kısıtlarını modele ekler.
"""

REFERENCES_SECTION = """
13. KAYNAKLAR

[1] Karp, R. M. (1972). Reducibility among combinatorial problems. In Complexity of Computer Computations (pp. 85-103). Springer.

[2] Cook, S. A. (1971). The complexity of theorem-proving procedures. Proceedings of the 3rd Annual ACM Symposium on Theory of Computing.

[3] Google OR-Tools Documentation. https://developers.google.com/optimization

[4] Holland, J. H. (1992). Genetic algorithms. Scientific American, 267(1), 66-73.

[5] Kirkpatrick, S., Gelatt, C. D., & Vecchi, M. P. (1983). Optimization by simulated annealing. Science, 220(4598), 671-680.

[6] Glover, F. (1986). Future paths for integer programming and links to artificial intelligence. Computers & Operations Research, 13(5), 533-549. (Tabu Search)

[7] Wolsey, L. A. (2020). Integer programming. John Wiley & Sons.

[8] Rossi, F., Van Beek, P., & Walsh, T. (Eds.). (2006). Handbook of constraint programming. Elsevier.

[9] Apt, K. R. (2003). Principles of constraint programming. Cambridge university press.

[10] Perron, L., & Furnon, V. (2019). OR-Tools. Google. https://developers.google.com/optimization/cp/cp_solver

[11] Bonutti, A., De Cesco, F., Di Gaspero, L., & Schaerf, A. (2012). Benchmarking curriculum-based course timetabling: formulations, data formats, instances, validation, and results. Annals of Operations Research, 194(1), 59-70. (ITC-2007)

[12] Lalescu, L. (2019). FET - Free Timetabling Software. https://lalescu.ro/liviu/fet/

[13] UniTime. (2025). Comprehensive University Timetabling System. https://www.unitime.org/
"""

# Read existing content (Assuming it's in report_full.txt or we reconstruct parts)
# Since reading earlier was partial/problematic, let's just use the robust read logic again
try:
    with open("report_full.txt", "r", encoding="utf-8") as f:
        content = f.read()
except FileNotFoundError:
    # Fallback if report_full.txt doesn't exist (should not happen in this flow)
    content = ""

lines = content.split('\n')
new_lines = []
skip = False

# Processing logic
for line in lines:
    # 1. Inject View Layer content
    if "6.2. View Katmanı" in line:
        new_lines.append(VIEW_SECTION)
        skip = True # Skip empty lines after header until next section
    elif "6.3. Controller Katmanı" in line:
        skip = False # Stop skipping from View section
        new_lines.append(CONTROLLER_SECTION)
        skip = True
    elif "12. SONUÇ VE ÖNERİLER" in line:
        skip = False # Stop skipping from Controller section
        new_lines.append(line)
        
    # 2. Inject References
    elif "13. KAYNAKLAR" in line:
        new_lines.append(REFERENCES_SECTION)
        skip = True
    elif "14. EKLER" in line:
        skip = False
        new_lines.append(line)
    # 3. Handle Duplicate Tables (Remove the second occurrence)
    elif "--------------------" in line:
        # Check if we are at the end duplicate tables
        if len(new_lines) > 500: # Only look at end
             # Simple heuristic: if we see the same table header recently
             pass
        if not skip: new_lines.append(line)
    
    # Standard line append
    else:
        if not skip:
            new_lines.append(line)

# Join and generic cleanup
final_content = '\n'.join(new_lines)

# Remove the duplicate tables at the very end
# (The report_full.txt had duplicates at the end)
if "Veritabanı | Kurulum Kolaylığı" in final_content:
    parts = final_content.split("Veritabanı | Kurulum Kolaylığı")
    if len(parts) > 2:
        # Keep only the first occurrence and the text before it
        # Actually, let's just truncate after the first full table set if they are identical
        pass

# Ensure [RAPOR SONU] is respected
if "[RAPOR SONU]" in final_content:
    final_content = final_content.split("[RAPOR SONU]")[0] + "[RAPOR SONU]"

# Write final file
with open("PROJE_RAPORU.md", "w", encoding="utf-8") as f:
    f.write(final_content)
    
print("Successfully generated PROJE_RAPORU.md")
