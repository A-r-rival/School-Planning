import os
import re
import json
#Elektrikte havuzların başında kod yok
#bilgisayarda SDUa/b filan ayrılıyor o bozuyor
#makinede SDUx olarak girmişler semesterda
#mekatronikte projeleri pool yapmamış semesterda
#iktisatta 30'a tamlamıyor

CURRICULUM_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Curriculum")
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "curriculum_data.py")

def parse_line(line):
    # Remove leading/trailing whitespace and split by '|'
    parts = [p.strip() for p in line.split('|')]
    # Remove empty strings from start/end if they exist due to leading/trailing '|'
    if parts and parts[0] == '': parts.pop(0)
    if parts and parts[-1] == '': parts.pop()
    return parts

def extract_ects(parts):
    # Try to find ECTS in the last few columns
    # It's usually a small integer
    for p in reversed(parts):
        # Remove asterisks or other common markers
        clean_p = p.replace('*', '').strip()
        if clean_p.isdigit():
            return int(clean_p)
    return 0

def clean_course_name(name):
    # Remove (Z), (S), (TR/DE) etc.
    name = re.sub(r'\s*\(.*?\)\s*$', '', name)
    return name.strip()

class Regexes:
    # Matches "1. YARIYIL", "I. YARIYIL", "1. DÖNEM", "I. DÖNEM"
    semester_term = re.compile(r'([IVX]+|\d+)\.\s*(YARIYIL|DÖNEM|SEMESTER|SEMESTIR)', re.IGNORECASE)
    # Matches "1. YIL", "I. YIL"
    year = re.compile(r'([IVX]+|\d+)\.\s*YIL', re.IGNORECASE)
    # Matches "1. GÜZ", "2. BAHAR"
    season = re.compile(r'([IVX]+|\d+)\.\s*(GÜZ|BAHAR)', re.IGNORECASE)
    
    pool_header = re.compile(r'SEÇMELİ DERS|SEÇMELİLER|MODÜL|SD|HAVUZU', re.IGNORECASE)

    pool_code = re.compile(r'([A-ZİĞÜŞÖÇ0-9_]*SD[A-ZİĞÜŞÖÇ0-9_]*?)\s*([IVX0-9]*)', re.IGNORECASE)

def parse_file(filepath, log_file=None):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    curriculum = {}
    pools = {}
    
    current_semester = 0
    in_pool_section = False
    current_pool_codes = []
    
    # Counters for tracking fallback match usage
    match2_count = 0
    match3_count = 0
    match4_count = 0

    romans = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10}

    def to_int(val):
        if val.isdigit(): return int(val)
        return romans.get(val.upper(), 0)

    for line in lines:
        if not line.strip(): continue
        if line.startswith('='): continue
        if line.startswith('-'): continue
        if line.startswith('+'): continue
        
        # Check for Pool Section Start
        if Regexes.pool_header.search(line) and line.count('|') < 5:
            in_pool_section = True
            # Don't continue, might be a header line that also contains pool code
        
        # Check for Pool Code Header
        if in_pool_section:
            # Look for "| CODE | DESCRIPTION |" pattern
            # But ensure it's not a course line (which also has pipes)
            # Pool headers usually don't have ECTS or have "Seçmeli Modül" text
            # Also handle "| ZSD I - 12 AKTS |" format
            
            # Course lines have many pipes (e.g. | CODE | NAME | T | U | L | AKTS | ... |)
            # Pool headers usually have 2 or 3 pipes.
            if Regexes.pool_header.search(line) and line.count('|') < 6:
                found_codes = []

                # Format 1: | CODE | DESCRIPTION | or | CODE1/CODE2 |
                # Use findall for the main regex to capture multiple codes like SOZSDII/SOZSDIV
                matches1 = Regexes.pool_code.findall(line)
                if matches1:
                    for m in matches1:
                        c = m[0].strip()
                        if m[1]:
                            c = f"{c} {m[1].strip()}"
                        c = c.strip()
                        # Only add if it's a valid code (minimum 2 characters)
                        if len(c) >= 2:
                             found_codes.append(c)



                # If no matches from main regex, try others (usually single code)
                if not found_codes:
                    # match1 = re.compile(r'([A-ZİĞÜŞÖÇ0-9_]*SD[A-ZİĞÜŞÖÇ0-9_]*?)\s*([IVX0-9]*)', re.IGNORECASE)
                    
                    # Format 2: | DESCRIPTION (CODE) |
                    match2 = re.search(r'\((ZSD[IVX]*|SD[IVX]*|ÜSD[IVX]*|HUKSD[0-9]*)\)', line)
                    # Format 3: | ZSD I - ... |
                    match3 = re.search(r'\|\s*(ZSD\s*.*?)\s*-', line)
                    # Format 4: | CODE SEÇMELİ ... | or | CODE HAVUZU ... |
                    match4 = re.search(r'\|\s*([A-ZİĞÜŞÖÇ0-9_]{3,})\s+(?:SEÇMELİ|HAVUZU|DERSLER)', line, re.IGNORECASE)

                    if match2:
                        found_codes.append(match2.group(1).strip())
                        match2_count += 1
                        msg = f"[!] UYARI: match2 kullanildi - Satir: {line.strip()}"
                        print(msg)
                        if log_file:
                            log_file.write(msg + "\n")
                    elif match3:
                        found_codes.append(match3.group(1).strip())
                        match3_count += 1
                        msg = f"[!] UYARI: match3 kullanildi - Satir: {line.strip()}"
                        print(msg)
                        if log_file:
                            log_file.write(msg + "\n")
                    elif match4:
                        found_codes.append(match4.group(1).strip())
                        match4_count += 1
                        msg = f"[!] UYARI: match4 kullanildi - Satir: {line.strip()}"
                        print(msg)
                        if log_file:
                            log_file.write(msg + "\n")


                
                        # (r'([A-ZİĞÜŞÖÇ0-9_]*SD[A-ZİĞÜŞÖÇ0-9_]*?)\s*([IVX0-9]*)', re.IGNORECASE)


                if found_codes:
                    current_pool_codes = found_codes
                    for c in current_pool_codes:
                        if c not in pools:
                            pools[c] = []
                continue

        # Semester Parsing
        # Priority: YARIYIL/DÖNEM > GÜZ/BAHAR > YIL
        if not in_pool_section:
            term_match = Regexes.semester_term.search(line)
            season_match = Regexes.season.search(line)
            year_match = Regexes.year.search(line)
            
            if term_match:
                val = to_int(term_match.group(1))
                if val > 0: current_semester = val
            elif season_match:
                val = to_int(season_match.group(1))
                if val > 0: current_semester = val
            elif year_match:
                y_val = to_int(year_match.group(1))
                if y_val > 0:
                    # Check context for semester
                    if "III. YARIYIL" in line.upper() or "3. YARIYIL" in line.upper(): current_semester = 3
                    elif "IV. YARIYIL" in line.upper() or "4. YARIYIL" in line.upper(): current_semester = 4
                    elif "I. YARIYIL" in line.upper() or "1. YARIYIL" in line.upper(): current_semester = y_val * 2 - 1
                    elif "II. YARIYIL" in line.upper() or "2. YARIYIL" in line.upper(): current_semester = y_val * 2
                    elif "GÜZ" in line.upper(): current_semester = y_val * 2 - 1
                    elif "BAHAR" in line.upper(): current_semester = y_val * 2
                    pass

        parts = parse_line(line)
        if not parts: continue

        # Course Extraction
        code_idx = -1
        for i, p in enumerate(parts):
            p_clean = p.split(' - ')[0].strip()
            # Regex for course code: 
            # 1. Standard: 2+ letters + 3+ digits (e.g. MAT103)
            # 2. Placeholders: ZSD, SD, ÜSD followed by optional Roman numerals or digits (e.g. ZSDII, SDI, ÜSD1)
            # Exclude common headers
            if p_clean in ["KOD", "KODU", "TOPLAM", "AKTS", "DERSİN", "T", "U", "L"]:
                continue
                
            if re.match(r'^[A-ZİĞÜŞÖÇ]{2,}\s*[0-9IVX]*$', p_clean):
                code_idx = i
                break
        #fnord isim ve kod karıştırabilir?

        if code_idx != -1:
            raw_code = parts[code_idx]
            if ' - ' in raw_code:
                code = raw_code.split(' - ')[0].strip()
                name = raw_code.split(' - ')[1].strip()
            else:
                code = raw_code
                if len(parts) > code_idx + 1:
                    name = parts[code_idx+1]
                else:
                    name = "Unknown"
            
            name = clean_course_name(name)
            ects = extract_ects(parts)
            
            # Fix for 0 ECTS: check if last column is digit
            if ects == 0 and parts[-1].strip().isdigit():
                ects = int(parts[-1].strip())

            course_tuple = (code, name, ects)
            
            if in_pool_section and current_pool_codes:
                # Avoid adding the pool header itself as a course
                if code not in current_pool_codes:
                    for pool_code in current_pool_codes:
                        pools[pool_code].append(course_tuple)
            elif 1 <= current_semester <= 8:
                if current_semester not in curriculum:
                    curriculum[current_semester] = []
                
                # Allow duplicates for placeholder courses (ZSD, SD, ÜSD, etc.)
                is_placeholder = "SD" in code
                
                if is_placeholder or course_tuple not in curriculum[current_semester]:
                    curriculum[current_semester].append(course_tuple)

    return curriculum, pools, (match2_count, match3_count, match4_count)

def main():
    departments_data = {}
    
    # Total counters across all departments
    total_match2 = 0
    total_match3 = 0
    total_match4 = 0
    
    # Open log file for writing match warnings
    log_filepath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output_match_type.txt")
    
    with open(log_filepath, 'w', encoding='utf-8') as log_file:
        log_file.write("="*60 + "\n")
        log_file.write("MATCH PATTERN KULLANIM DETAYLARI\n")
        log_file.write("="*60 + "\n\n")
        
        # Walk through Curriculum directory
        for root, dirs, files in os.walk(CURRICULUM_DIR):
            for file in files:
                if file.endswith(".txt"):
                    # Determine Department Name
                    # If file is "X Öğretim Planı.txt", Dept is X.
                    dept_name = file.replace(" Öğretim Planı.txt", "").strip()
                    
                    # If file is just "Öğretim Planı.txt" (unlikely based on list), use parent dir?
                    # Based on file list, they are named properly.
                    
                    filepath = os.path.join(root, file)
                    print(f"Parsing {dept_name}...")
                    log_file.write(f"\n--- {dept_name} ---\n")
                    try:
                        curriculum, pools, (match2_count, match3_count, match4_count) = parse_file(filepath, log_file)
                        departments_data[dept_name] = {
                            "curriculum": curriculum,
                            "pools": pools
                        }
                        
                        # Accumulate counters
                        total_match2 += match2_count
                        total_match3 += match3_count
                        total_match4 += match4_count
                        
                    except Exception as e:
                        print(f"Error parsing {file}: {e}")

        # Write summary to log file
        log_file.write("\n" + "="*60 + "\n")
        log_file.write("OZET ISTATISTIKLER\n")
        log_file.write("="*60 + "\n\n")
        
        if total_match2 > 0 or total_match3 > 0 or total_match4 > 0:
            log_file.write("[!] Ana regex (match1) yerine alternatif patternler kullanildi:\n\n")
            if total_match2 > 0:
                log_file.write(f"   • match2 (Format: | DESCRIPTION (CODE) |) : {total_match2} kere\n")
            if total_match3 > 0:
                log_file.write(f"   • match3 (Format: | ZSD I - ... |)        : {total_match3} kere\n")
            if total_match4 > 0:
                log_file.write(f"   • match4 (Format: | CODE SECMELI ... |)   : {total_match4} kere\n")
            log_file.write(f"\n   TOPLAM: {total_match2 + total_match3 + total_match4} alternatif pattern kullanimi\n")
        else:
            log_file.write("[OK] Tum pool kodlari ana regex (match1) ile basariyla yakalandi!\n")
        
        log_file.write("="*60 + "\n")


    # Write to curriculum_data.py
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("# Auto-generated curriculum data\n\n")
        
        # Add Common USD Pool
        f.write("# ==========================================\n")
        f.write("# COMMON POOLS\n")
        f.write("# ==========================================\n")
        f.write("COMMON_USD_POOL = [\n")
        f.write('    ("ELC101", "Fotoğrafçılık", 3),\n')
        f.write('    ("ELC102", "Sinema Tarihi", 3),\n')
        f.write('    ("ELC103", "İletişim Becerileri", 3),\n')
        f.write('    ("ELC104", "Yaratıcı Yazarlık", 3),\n')
        f.write('    ("ELC105", "Bilim Tarihi", 3),\n')
        f.write('    ("ELC106", "Müzik Kültürü", 3),\n')
        f.write('    ("ELC107", "İşaret Dili", 3),\n')
        f.write('    ("ELC108", "Gönüllülük Çalışmaları", 3),\n')
        f.write('    ("ELC109", "Girişimcilik", 3),\n')
        f.write('    ("ELC110", "Kariyer Planlama", 3)\n')
        f.write("]\n\n")
        
        f.write("DEPARTMENTS_DATA = ")
        f.write(json.dumps(departments_data, ensure_ascii=False, indent=4))
        f.write("\n")
    
    print(f"Successfully generated {OUTPUT_FILE}")
    
    # Display match pattern usage statistics
    print("\n" + "="*60)
    print("MATCH PATTERN KULLANIM ISTATISTIKLERI")
    print("="*60)
    
    if total_match2 > 0 or total_match3 > 0 or total_match4 > 0:
        print("\n[!] Ana regex (match1) yerine alternatif patternler kullanildi:\n")
        if total_match2 > 0:
            print(f"   • match2 (Format: | DESCRIPTION (CODE) |) : {total_match2} kere")
        if total_match3 > 0:
            print(f"   • match3 (Format: | ZSD I - ... |)        : {total_match3} kere")
        if total_match4 > 0:
            print(f"   • match4 (Format: | CODE SECMELI ... |)   : {total_match4} kere")
        print(f"\n   TOPLAM: {total_match2 + total_match3 + total_match4} alternatif pattern kullanimi")
    else:
        print("\n[OK] Tum pool kodlari ana regex (match1) ile basariyla yakalandi!")
    
    print("="*60 + "\n")
    print(f"Detayli uyari mesajlari: {log_filepath}\n")




if __name__ == "__main__":
    main()
