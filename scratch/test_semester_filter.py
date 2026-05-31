"""
Semester filter dry-run test.
Simulates what scheduler.py does after the fix.
"""
import sys, re, sqlite3
sys.path.insert(0, 'd:/Git_Projects/School-Planning')
sys.path.insert(0, 'd:/Git_Projects/School-Planning/database')
from database import curriculum_data

# ---- Build lookup as schedule_model._build_semester_lookup does ----
lookup_by_dept = {}
lookup = {}
data = curriculum_data.DEPARTMENTS_DATA
for dept, details in data.items():
    curr = details.get('curriculum', {})
    for sem_key, courses in curr.items():
        try:
            match = re.search(r'\d+', sem_key)
            if not match: continue
            sem_num = int(match.group())
            semester = 'Güz' if (sem_num % 2 != 0) else 'Bahar'
            if not isinstance(courses, list): continue
            for course in courses:
                if not isinstance(course, list) or len(course) < 2: continue
                code = str(course[0]).strip()
                name = str(course[1]).strip()
                if code:
                    lookup.setdefault(code, set()).add(semester)
                    lookup_by_dept.setdefault((dept, code), set()).add(semester)
                if name:
                    lookup.setdefault(name, set()).add(semester)
                    lookup_by_dept.setdefault((dept, name), set()).add(semester)
                # Expand pools
                pools = details.get('pools', {})
                if code in pools:
                    for pc in pools[code]:
                        if len(pc) >= 2:
                            pcode = str(pc[0]).strip()
                            pname = str(pc[1]).strip()
                            if pcode:
                                lookup.setdefault(pcode, set()).add(semester)
                                lookup_by_dept.setdefault((dept, pcode), set()).add(semester)
                            if pname:
                                lookup.setdefault(pname, set()).add(semester)
                                lookup_by_dept.setdefault((dept, pname), set()).add(semester)
        except Exception as e:
            print(f"  Warning: {e}")

print(f"Lookup entries: {len(lookup)}, by-dept: {len(lookup_by_dept)}")

# ---- Simulate semester filter on Enerji 1. sinif courses ----
conn = sqlite3.connect('d:/Git_Projects/School-Planning/database/okul_veritabani.db')
c = conn.cursor()

c.execute("""
    SELECT d.ders_adi, d.ders_kodu, d.teori_saati + d.uygulama_saati + d.lab_saati as saat
    FROM Dersler d 
    JOIN Ders_Sinif_Iliskisi dsi ON d.ders_adi = dsi.ders_adi AND d.ders_instance = dsi.ders_instance
    JOIN Ogrenci_Donemleri od ON dsi.donem_sinif_num = od.donem_sinif_num
    WHERE od.sinif_duzeyi = 1 
    AND od.bolum_num = (SELECT bolum_id FROM Bolumler WHERE bolum_adi = 'Enerji Bilimi ve Teknolojileri')
    AND d.teori_saati + d.uygulama_saati + d.lab_saati > 0
""")
enerji_1_courses = c.fetchall()
conn.close()

print(f"\n=== Enerji 1. Sınıf - Toplam DB'de: {len(enerji_1_courses)} ders ===")

dept = 'Enerji Bilimi ve Teknolojileri'

def simulate_filter(courses, semester_filter):
    passed = []
    excluded = []
    passthrough = []
    
    for name, code, saat in courses:
        code = str(code or '').strip()
        name_s = str(name or '').strip()
        
        # Check lookup
        sem_set = set()
        found = False
        if (dept, code) in lookup_by_dept:
            sem_set |= lookup_by_dept[(dept, code)]
            found = True
        elif (dept, name_s) in lookup_by_dept:
            sem_set |= lookup_by_dept[(dept, name_s)]
            found = True
        elif code and code in lookup:
            sem_set |= lookup[code]
            found = True
        elif name_s and name_s in lookup:
            sem_set |= lookup[name_s]
            found = True
        
        if not found:
            passthrough.append((name_s, code, saat, 'NOT_IN_LOOKUP'))
        elif semester_filter in sem_set or ('Güz' in sem_set and 'Bahar' in sem_set):
            passed.append((name_s, code, saat, sem_set))
        else:
            excluded.append((name_s, code, saat, sem_set))
    
    return passed, excluded, passthrough

for sem in ['Güz', 'Bahar']:
    passed, excluded, passthrough = simulate_filter(enerji_1_courses, sem)
    total_hours = sum(s for _,_,s,_ in passed) + sum(s for _,_,s,_ in passthrough)
    print(f"\n--- {sem} Filtresi ---")
    print(f"  Geçen (lookup match): {len(passed)} ders")
    print(f"  Geçen (lookup yok - passthrough): {len(passthrough)} ders")
    print(f"  Dışlanan: {len(excluded)} ders")
    print(f"  Toplam haftalık yük: {total_hours} saat (öncesi: {sum(s for _,_,s in enerji_1_courses)})")
    for n, code, s, ss in excluded:
        print(f"    EXCLUDED: [{code}] {n} ({ss})")
    for n, code, s, reason in passthrough:
        print(f"    PASSTHROUGH: [{code}] {n}")
