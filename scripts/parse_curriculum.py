import os
import re
import json

#Elektrikte SDP SDT filan SD altında birleşmiş???
#mekatronikte projelerin döneme göre ayrı pool yapmamış hepsi birlikte semesterda (o kadar sıkıntı değil)

#SDUx için diğer havuzlardan seçmeyi yaz.
# 2 adet ders
# 2x kullanımları
#kodları şu ana kadar küçük harfle görmedim ama onun için if de koy
#iktisat seçmelilerini kontrol et manuel olarak düzeltildi

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


    pool_code = re.compile(r'([A-ZİĞÜŞÖÇ0-9_]*SD[A-ZİĞÜŞÖÇ0-9_]*)\s*([IVX0-9]+[a-zA-Z]?)?', re.IGNORECASE)

def check_semester_akts(curriculum, dept_name):
    """Check if each semester has exactly 30 AKTS and return discrepancies."""
    akts_issues = []
    
    for semester in range(1, 9):  # Check semesters 1-8
        if semester in curriculum:
            total_akts = sum(course[2] for course in curriculum[semester])
            if total_akts == 31 and dept_name == "Hukuk Fakültesi" and semester == 8:
                continue
            if total_akts == 28 and dept_name == "İnşaat Müh" and semester == 8:
                continue
            elif total_akts != 30:
                akts_issues.append(f"Dönem {semester}: {total_akts} AKTS")
    
    return akts_issues

# Dynamic column extraction helper
def detect_columns(header_line):
    # Standardize header line
    header = [h.strip().upper() for h in header_line.split('|') if h.strip()]
    mapping = {}
    
    # Map 'T', 'U', 'L', 'AKTS' to their indices in the split parts
    for idx, col in enumerate(header):
        if col == 'T': mapping['T'] = idx
        elif col == 'U': mapping['U'] = idx
        elif col == 'L': mapping['L'] = idx
        elif col == 'AKTS': mapping['AKTS'] = idx
    
    return mapping

def extract_course_details(parts, col_mapping):
    # Extracts T, U, L, AKTS based on mapping
    # Defaults to 0 if column missing or parsing fails
    
    def get_val(key):
        if key in col_mapping and col_mapping[key] < len(parts):
            val = parts[col_mapping[key]].strip()
            # Remove * or other markers
            val = val.replace('*', '')
            if val.isdigit():
                return int(val)
        return 0

    t = get_val('T')
    u = get_val('U')
    l = get_val('L')
    
    # AKTS might be detected via column or fallback
    ects = get_val('AKTS')
    
    # Fallback for AKTS if not found in mapping or 0 (some files might strictly follow old logic if header missing)
    if ects == 0:
         # Try logic from old extract_ects: look at last few columns
        for p in reversed(parts):
            clean_p = p.replace('*', '').strip()
            if clean_p.isdigit():
                ects = int(clean_p)
                break
                
    return t, u, l, ects

def parse_file(filepath, log_file=None):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    curriculum = {}
    pools = {}
    
    current_semester = 0
    in_pool_section = False
    current_pool_codes = []
    
    # Dynamic Column Mapping
    col_mapping = {} 
    # Default fallback mapping if no header found (standard engineering format)
    # This is risky, better to rely on finding a header.
    # But usually T, U, L, AKTS are at the end.
    
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
        
        # Check for Header Line
        # Matches lines containing | KOD | ... | AKTS |
        if "| KOD" in line.upper() and "| AKTS" in line.upper():
            col_mapping = detect_columns(line)
            # print(f"DEBUG: Found columns for {filepath}: {col_mapping}")
            continue

        # Check for Pool Section Start
        if not in_pool_section:
            # Only enter pool section if we see clear indicators
            if (Regexes.pool_header.search(line) and line.count('|') < 3) or \
               (re.search(r'\[.*SD.*\]', line, re.IGNORECASE)):  # Bracketed pool code like [SDP]
                in_pool_section = True
                # Don't continue, might be a header line that also contains pool code
        
        # Check for Pool Code Header
        if in_pool_section:
            if Regexes.pool_header.search(line) and line.count('|') < 6:
                found_codes = []

                matches1 = Regexes.pool_code.findall(line)
                if matches1:
                    for m in matches1:
                        c = m[0].strip()
                        if m[1]:
                            c = f"{c} {m[1].strip()}"
                        c = c.strip()
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
                        if log_file: log_file.write(msg + "\n")
                    elif match3:
                        found_codes.append(match3.group(1).strip())
                        match3_count += 1
                        msg = f"[!] UYARI: match3 kullanildi - Satir: {line.strip()}"
                        if log_file: log_file.write(msg + "\n")
                    elif match4:
                        found_codes.append(match4.group(1).strip())
                        match4_count += 1
                        msg = f"[!] UYARI: match4 kullanildi - Satir: {line.strip()}"
                        if log_file: log_file.write(msg + "\n")

                if found_codes:
                    current_pool_codes = found_codes
                    for c in current_pool_codes:
                        if c not in pools:
                            pools[c] = []
                    # Only skip course processing if this is clearly just a header line (few pipes)
                    # If it's a full course table row (8+ pipes), we should still process it as a course
                    if line.count('|') < 6:
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
            if p_clean in ["KOD", "KODU", "TOPLAM", "AKTS", "DERSİN", "T", "U", "L", "DİL", "D/E", "E", "D"]:
                continue
                
            if re.match(r'^[A-ZİĞÜŞÖÇ]{2,}\s*[0-9IVXa-z]*$', p_clean):
                code_idx = i
                break

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
            
            # Use dynamic extraction if mapping exists, otherwise try best guess (though mapping usually exists if header was found)
            if col_mapping:
                t, u, l, ects = extract_course_details(parts, col_mapping)
            else:
                # Fallback: assume last column is AKTS, others 0? 
                # Or try to guess like before. 
                # Let's use the old approach for ECTS and default T/U/L to 0
                ects = extract_ects(parts) # This function still exists in the file (I kept it but not using it inside this block)
                # Wait, I am replacing the block that contained extract_ects definition? NO.
                # extract_ects defined at line 25 IS outside my replace block? 
                # My replace block covers 17-258. So `extract_ects` IS being removed/replaced.
                # I should re-define it or merge logic. 
                # I defined `extract_course_details` inside, but let's handle the case where `col_mapping` is empty.
                # In standard eng files, T, U, L, AKTS are usually -4, -3, -2, -1 if no extra columns.
                # But safer to just set T=0, U=0, L=0 if we don't know columns.
                t, u, l = 0, 0, 0
                
                # Re-implement simple ECTS extraction here since I removed the helper
                found_ects = 0
                for p in reversed(parts):
                    clean_p = p.replace('*', '').strip()
                    if clean_p.isdigit():
                        found_ects = int(clean_p)
                        break
                ects = found_ects
            
            # Fix for 0 ECTS: check if last column is digit
            if ects == 0 and parts[-1].strip().isdigit():
                ects = int(parts[-1].strip())

            # UPDATED: Tuple now includes T, U, L
            course_tuple = (code, name, ects, t, u, l)
            
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
                
                # Check for duplicates (accounting for new tuple size)
                # Since tuple is larger, simple containment check works if identical
                # But if existing entries have different T/U/L (unlikely), it won't match.
                
                if is_placeholder:
                     curriculum[current_semester].append(course_tuple)
                else:
                    # Check if code+name matches
                    exists = False
                    for existing in curriculum[current_semester]:
                        if existing[0] == code and existing[1] == name:
                            exists = True
                            break
                    if not exists:
                        curriculum[current_semester].append(course_tuple)

    return curriculum, pools, (match2_count, match3_count, match4_count)


def main():
    departments_data = {}
    
    # Total counters across all departments
    total_match2 = 0
    total_match3 = 0
    total_match4 = 0
    
    # Open log file for writing match warnings
    log_filepath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output_debugging.txt")
    
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
                        
                        # Check AKTS for each semester
                        akts_issues = check_semester_akts(curriculum, dept_name)
                        
                        # Write match type and AKTS info
                        match_info = ""
                        if match2_count > 0:
                            match_info += f"match2: {match2_count} kere, "
                        if match3_count > 0:
                            match_info += f"match3: {match3_count} kere, "
                        if match4_count > 0:
                            match_info += f"match4: {match4_count} kere, "
                        
                        if match_info:
                            match_info = match_info.rstrip(", ")
                        else:
                            match_info = "match1 ile tamamlandi"
                        
                        if akts_issues:
                            akts_info = " | AKTS HATASI: " + ", ".join(akts_issues)
                        else:
                            akts_info = " | Tum donemler 30 AKTS"
                        
                        log_file.write(f"Match Type: {match_info}{akts_info}\n")
                        
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

# region sdfsdfsdf


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

# endregion

if __name__ == "__main__":
    main()
