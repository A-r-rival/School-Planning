import sys
import os
import random
import sqlite3

# Add project root to path
sys.path.append(os.getcwd())

from models.schedule_model import ScheduleModel
from scripts.curriculum_data import DEPARTMENTS_DATA, COMMON_USD_POOL

GRADES = ["AA", "BA", "BB", "CB", "CC", "DC", "DD", "FD", "FF"]
PASSING_GRADES = ["AA", "BA", "BB", "CB", "CC", "DC", "DD"]

def get_courses_for_slot(code, department, faculty, required_ects, taken_codes=None):
    """
    Returns a list of courses (code, name, ects) from the pool.
    """
    dept_data = DEPARTMENTS_DATA.get(faculty, {}).get(department)
    if not dept_data:
        # Try finding department in other faculties if not found directly
        for f, data in DEPARTMENTS_DATA.items():
            if department in data:
                dept_data = data[department]
                break
    
    if not dept_data:
        return None

    pools = dept_data.get("pools", {})
    pool_courses = None
    
    # Check if code is a pool key
    if code in pools:
        pool_courses = pools[code]
    
    # Check generic USD
    elif "USD" in code or "ÜSD" in code:
        pool_courses = COMMON_USD_POOL
        
    if not pool_courses:
        return None

    # Filter taken
    available = list(pool_courses)
    if taken_codes:
        available = [c for c in available if c[0] not in taken_codes]
        
    selected = []
    current_ects = 0
    random.shuffle(available)
    
    while current_ects < required_ects and available:
        course = available.pop()
        selected.append(course)
        current_ects += course[2]
        
    return selected

def populate():
    print("Starting Student Population...")
    try:
        model = ScheduleModel()
    except Exception as e:
        print(f"Error connecting to DB: {e}")
        return

    # Clear existing data
    print("Clearing existing student data...")
    try:
        model.c.execute("DROP TABLE IF EXISTS Dersler")
        model.c.execute("DROP TABLE IF EXISTS Ogrenci_Notlari")
        model.c.execute("DROP TABLE IF EXISTS Verilen_Dersler")
        model.c.execute("DROP TABLE IF EXISTS Alinan_Dersler")
        model.c.execute("DROP TABLE IF EXISTS Ders_Sinif_Iliskisi")
        model.c.execute("DROP TABLE IF EXISTS Ogrenci_Donemleri")
        model.c.execute("DROP TABLE IF EXISTS Ogrenciler")
        model.c.execute("DROP TABLE IF EXISTS Bolumler")
        model.c.execute("DROP TABLE IF EXISTS Fakulteler")
        model.conn.commit()
        model._create_tables()
    except Exception as e:
        print(f"Error clearing/recreating data: {e}")

    # 1. Setup Faculties and Departments
    print("Setting up Faculties and Departments...")
    faculty_ids = {}
    dept_ids = {} # Name -> (id, num)
    
    dept_counter = 1
    
    for fac_name, fac_data in DEPARTMENTS_DATA.items():
        model.c.execute("INSERT OR IGNORE INTO Fakulteler (fakulte_adi) VALUES (?)", (fac_name,))
        model.conn.commit()
        model.c.execute("SELECT fakulte_num FROM Fakulteler WHERE fakulte_adi = ?", (fac_name,))
        fac_id = model.c.fetchone()[0]
        faculty_ids[fac_name] = fac_id
        
        # Departments are keys in DEPARTMENTS_DATA[fac_name]? 
        # Wait, structure is DEPARTMENTS_DATA = { "Faculty": { "curriculum": ..., "pools": ... } } ?
        # OR DEPARTMENTS_DATA = { "DeptName": { ... } } ?
        # Let's check curriculum_data.py structure again.
        # It is: DEPARTMENTS_DATA = { "Hukuk Fakültesi": { "curriculum": ... }, "ENERJİ...": ... }
        # Ah, looking at the file I generated:
        # "Hukuk Fakültesi": { "curriculum": ... } -> This is the Faculty Name acting as Department?
        # No, Hukuk Fakültesi usually has Hukuk Bölümü.
        # The parser used filename as key.
        # "Bilgisayar Müh": { ... }
        # So the keys in DEPARTMENTS_DATA are actually Department Names (mostly).
        # But "Hukuk Fakültesi" key implies the department is Hukuk.
        # I need to map these keys to Faculties.
        
        # Heuristic for Faculty mapping:
        # If "Müh" in name -> Mühendislik
        # If "Hukuk" -> Hukuk
        # If "İşletme", "İktisat", "Siyaset" -> İİBF
        # If "Kültür", "Sosyoloji" -> Kültür ve Sosyal
        # If "Moleküler", "Malzeme", "Enerji" -> Fen
        pass

    # Re-mapping logic because DEPARTMENTS_DATA keys are Dept Names (mostly)
    # But I need to insert them into Bolumler and link to Fakulteler.
    
    # Let's define the mapping explicitly based on known keys
    dept_to_faculty = {}
    for key in DEPARTMENTS_DATA.keys():
        if "Müh" in key or "Mühendisliği" in key:
            dept_to_faculty[key] = "Mühendislik Fakültesi"
        elif "Hukuk" in key:
            dept_to_faculty[key] = "Hukuk Fakültesi"
        elif key in ["İşletme", "İktisat", "Siyaset Bilimi ve Uluslararası İlişkiler"]:
            dept_to_faculty[key] = "İktisadi ve İdari Bilimler Fakültesi"
        elif key in ["Kültür ve İletişim Bölümü", "Sosyoloji"]:
            dept_to_faculty[key] = "Kültür ve Sosyal Bilimler Fakültesi"
        else:
            dept_to_faculty[key] = "Fen Fakültesi" # Fallback for Enerji, Malzeme, Moleküler

    # Insert Faculties
    unique_faculties = set(dept_to_faculty.values())
    for f in unique_faculties:
        model.c.execute("INSERT OR IGNORE INTO Fakulteler (fakulte_adi) VALUES (?)", (f,))
    model.conn.commit()
    
    # Get Faculty IDs
    fac_map = {}
    for f in unique_faculties:
        model.c.execute("SELECT fakulte_num FROM Fakulteler WHERE fakulte_adi = ?", (f,))
        fac_map[f] = model.c.fetchone()[0]

    # Insert Departments
    dept_info_map = {} # key -> (bolum_id, bolum_num, fac_id)
    
    for i, (dept_name, fac_name) in enumerate(dept_to_faculty.items(), 1):
        bolum_id = 100 + i
        bolum_num = 100 + i # Changed to 3 digits as requested
        fac_id = fac_map[fac_name]
        
        # Clean dept name for DB (remove "Öğretim Planı" if exists, though parser handled it)
        clean_name = dept_name
        
        model.c.execute("INSERT OR IGNORE INTO Bolumler (bolum_id, bolum_num, bolum_adi, fakulte_num) VALUES (?, ?, ?, ?)",
                       (bolum_id, bolum_num, clean_name, fac_id))
        dept_info_map[dept_name] = (bolum_id, bolum_num, fac_id)
    model.conn.commit()

    student_count = 0
    
    # 2. Generate Students
    for dept_name, dept_data in DEPARTMENTS_DATA.items():
        print(f"Processing {dept_name}...")
        bolum_id, bolum_num, fac_id = dept_info_map[dept_name]
        curriculum = dept_data["curriculum"]
        
        # Identify available departments for Double Major/Minor
        same_faculty_depts = [d for d, f in dept_to_faculty.items() if f == dept_to_faculty[dept_name] and d != dept_name]
        other_faculty_depts = [d for d, f in dept_to_faculty.items() if f != dept_to_faculty[dept_name]]
        
        for year in range(1, 5): # 1-4
            current_semester = year * 2 - 1
            entry_year = 2024 - year + 1
            
            donem_sinif_num = f"{entry_year}_{bolum_num}_{year}"
            model.c.execute("INSERT OR IGNORE INTO Ogrenci_Donemleri (donem_sinif_num, baslangic_yili, bolum_num, sinif_duzeyi) VALUES (?, ?, ?, ?)",
                           (donem_sinif_num, entry_year, bolum_id, year))
            
            # --- Regular Students (35) ---
            students_in_year = []
            for i in range(1, 36):
                s_num = int(f"{entry_year}{bolum_id}{i:03d}")
                students_in_year.append(s_num)
                create_student(model, s_num, dept_name, year, entry_year, current_semester, bolum_id, fac_id, curriculum, dept_to_faculty[dept_name], is_irregular=False)
                student_count += 1
                
            # --- Double Major (ÇAP) & Minor (Yandal) ---
            # Only for 3rd and 4th years
            if year >= 3:
                # Shuffle students to pick candidates
                candidates = list(students_in_year)
                random.shuffle(candidates)
                
                # Double Major (4-6 students)
                num_cap = random.randint(4, 6)
                for _ in range(num_cap):
                    if not candidates or not same_faculty_depts: break
                    s_num = candidates.pop()
                    target_dept = random.choice(same_faculty_depts)
                    t_id, t_num, _ = dept_info_map[target_dept]
                    
                    model.c.execute("UPDATE Ogrenciler SET ikinci_bolum_num = ?, ikinci_bolum_turu = 'Anadal' WHERE ogrenci_num = ?",
                                   (t_id, s_num))
                                   
                # Minor (4-6 students)
                num_yandal = random.randint(4, 6)
                for _ in range(num_yandal):
                    if not candidates or not other_faculty_depts: break
                    s_num = candidates.pop()
                    target_dept = random.choice(other_faculty_depts)
                    t_id, t_num, _ = dept_info_map[target_dept]
                    
                    model.c.execute("UPDATE Ogrenciler SET ikinci_bolum_num = ?, ikinci_bolum_turu = 'Yandal' WHERE ogrenci_num = ?",
                                   (t_id, s_num))

            # --- Irregular Students (25-30 total per major -> ~7 per year) ---
            num_irregular = random.randint(6, 8)
            for i in range(1, num_irregular + 1):
                # Irregular ID: use 500+ suffix to distinguish
                s_num = int(f"{entry_year}{bolum_id}{500+i:03d}")
                
                # Irregular Entry Year: 1-2 years earlier than class
                irr_entry_year = entry_year - random.randint(1, 2)
                
                create_student(model, s_num, dept_name, year, irr_entry_year, current_semester, bolum_id, fac_id, curriculum, dept_to_faculty[dept_name], is_irregular=True)
                student_count += 1

    model.conn.commit()
    print(f"✅ Successfully created {student_count} students.")
    model.conn.close()

def create_student(model, s_num, dept_name, year, entry_year, current_semester, bolum_id, fac_id, curriculum, faculty_name, is_irregular):
    # Name generation
    prefix = "Irr" if is_irregular else "Ogr"
    first_name = f"{prefix}_{dept_name[:3]}_{year}"
    last_name = f"No_{s_num % 1000}"
    
    model.c.execute('''
        INSERT OR REPLACE INTO Ogrenciler (ogrenci_num, ad, soyad, girme_senesi, kacinci_donem, bolum_num, fakulte_num)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (s_num, first_name, last_name, entry_year, current_semester, bolum_id, fac_id))
    
    taken_codes = set()
    passed_courses = []
    
    # Iterate through semesters up to current
    # For irregulars, logic is messy, but let's simulate:
    # They take courses from 1 to current_semester.
    # Some they pass, some they fail (if irregular), some they skip.
    
    # Determine max semester to process
    # For regular: current_semester
    # For irregular: current_semester (but they might be retaking old ones)
    
    # We iterate 1..current_semester
    for sem in range(1, current_semester + 1):
        sem_str = str(sem)
        if sem_str not in curriculum: continue
        
        courses = curriculum[sem_str]
        
        term_label = "Guz" if sem % 2 != 0 else "Bahar"
        # Calculate term year based on when they took it
        # Ideally: entry_year + (sem-1)//2
        term_year = entry_year + (sem - 1) // 2
        term_str = f"{term_year}-{term_label}"
        
        is_current_term = (sem == current_semester)
        
        for course_data in courses:
            # course_data is [code, name, ects]
            code, name, ects = course_data
            
            # Handle Pools
            real_courses = []
            pool_courses = get_courses_for_slot(code, dept_name, faculty_name, ects, taken_codes)
            
            if pool_courses:
                real_courses = pool_courses
            else:
                real_courses = [(code, name, ects)]
            
            for r_code, r_name, r_ects in real_courses:
                if r_code in taken_codes: continue
                
                # Decision: Pass, Fail, or Take Now?
                
                if is_current_term:
                    # Current Semester
                    # Regular: Take all
                    # Irregular: Take if not skipped/failed before? 
                    # Simpler: Just take it.
                    status = "Geçti" # Placeholder, will assign grade
                    grade = random.choice(GRADES)
                    
                    # Add to Dersler
                    model.c.execute("INSERT OR IGNORE INTO Dersler (ders_kodu, ders_instance, ders_adi, akts) VALUES (?, ?, ?, ?)", 
                                  (r_code, 1, r_name, r_ects))
                    
                    # Add to Ogrenci_Notlari
                    status = "Geçti" if grade != "FF" else "Kaldı"
                    model.c.execute("INSERT INTO Ogrenci_Notlari (ogrenci_num, ders_kodu, ders_adi, harf_notu, durum, donem) VALUES (?, ?, ?, ?, ?, ?)",
                                  (s_num, r_code, r_name, grade, status, f"2024-Guz")) # Always 2024-Guz for current view
                    
                    # Add to Class Relation
                    # Calculate the cohort that is currently taking this course
                    # The course is in semester 'sem' (e.g. 1, 3, 5, 7)
                    # The year level is (sem + 1) // 2 (e.g. 1, 2, 3, 4)
                    # The entry year for this cohort is 2024 - year_level + 1
                    course_year_level = (sem + 1) // 2
                    cohort_entry_year = 2024 - course_year_level + 1
                    donem_sinif_num = f"{cohort_entry_year}_{bolum_id}_{course_year_level}"
                    
                    model.c.execute("INSERT OR IGNORE INTO Ders_Sinif_Iliskisi (ders_adi, ders_instance, donem_sinif_num) VALUES (?, ?, ?)", 
                                  (r_name, 1, donem_sinif_num))
                    
                    taken_codes.add(r_code)
                    
                else:
                    # Past Semester
                    # Regular: Pass all
                    # Irregular: 10% Fail, 10% Skip (don't take yet)
                    
                    if is_irregular:
                        roll = random.random()
                        if roll < 0.10: # Fail
                            grade = "FF"
                            status = "Kaldı"
                            # Record failure
                            model.c.execute("INSERT OR IGNORE INTO Dersler (ders_kodu, ders_instance, ders_adi, akts) VALUES (?, ?, ?, ?)", 
                                          (r_code, 1, r_name, r_ects))
                            model.c.execute("INSERT INTO Ogrenci_Notlari (ogrenci_num, ders_kodu, ders_adi, harf_notu, durum, donem) VALUES (?, ?, ?, ?, ?, ?)",
                                          (s_num, r_code, r_name, grade, status, term_str))
                            # Don't add to taken_codes so they can retake? 
                            # Actually, if they failed, they "took" it. But for selection logic, maybe we want them to retake.
                            # For now, let's just record it.
                        elif roll < 0.20: # Skip (never took)
                            continue
                        else: # Pass
                            grade = "AA" # Simplified
                            status = "Geçti"
                            passed_courses.append(r_name)
                            taken_codes.add(r_code)
                            
                            model.c.execute("INSERT OR IGNORE INTO Dersler (ders_kodu, ders_instance, ders_adi, akts) VALUES (?, ?, ?, ?)", 
                                          (r_code, 1, r_name, r_ects))
                            model.c.execute("INSERT INTO Ogrenci_Notlari (ogrenci_num, ders_kodu, ders_adi, harf_notu, durum, donem) VALUES (?, ?, ?, ?, ?, ?)",
                                          (s_num, r_code, r_name, grade, status, term_str))
                    else:
                        # Regular - Pass
                        grade = "AA"
                        status = "Geçti"
                        passed_courses.append(r_name)
                        taken_codes.add(r_code)
                        
                        model.c.execute("INSERT OR IGNORE INTO Dersler (ders_kodu, ders_instance, ders_adi, akts) VALUES (?, ?, ?, ?)", 
                                      (r_code, 1, r_name, r_ects))
                        model.c.execute("INSERT INTO Ogrenci_Notlari (ogrenci_num, ders_kodu, ders_adi, harf_notu, durum, donem) VALUES (?, ?, ?, ?, ?, ?)",
                                      (s_num, r_code, r_name, grade, status, term_str))

    if passed_courses:
        passed_str = ", ".join(passed_courses)
        model.c.execute("INSERT OR REPLACE INTO Verilen_Dersler (ogrenci_num, ders_listesi) VALUES (?, ?)",
                       (s_num, passed_str))

if __name__ == "__main__":
    populate()
