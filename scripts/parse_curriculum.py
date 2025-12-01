import os
import re
import json

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
        if p.isdigit():
            return int(p)
    return 0

def clean_course_name(name):
    # Remove (Z), (S), (TR/DE) etc.
    name = re.sub(r'\s*\(.*?\)\s*$', '', name)
    return name.strip()

def parse_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    curriculum = {}
    pools = {}
    
    current_semester = 0
    in_pool_section = False
    current_pool_code = None
    
    # Regexes
    # Matches "1. YARIYIL", "I. YARIYIL", "1. DÖNEM", "I. DÖNEM"
    sem_term_regex = re.compile(r'([IVX]+|\d+)\.\s*(YARIYIL|DÖNEM|SEMESTER|SEMESTIR)', re.IGNORECASE)
    # Matches "1. YIL", "I. YIL"
    year_regex = re.compile(r'([IVX]+|\d+)\.\s*YIL', re.IGNORECASE)
    # Matches "1. GÜZ", "2. BAHAR"
    season_regex = re.compile(r'([IVX]+|\d+)\.\s*(GÜZ|BAHAR)', re.IGNORECASE)
    
    pool_header_regex = re.compile(r'SEÇMELİ DERS|SEÇMELİLER|MODÜLLERİ', re.IGNORECASE)
    # Matches pool code in header like "| HUKSD5 | ..."
    pool_code_regex = re.compile(r'\|\s*([A-ZİĞÜŞÖÇ0-9_]*SD[A-ZİĞÜŞÖÇ0-9_]*)\s*\|', re.IGNORECASE)

    romans = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7, 'VIII': 8}

    def to_int(val):
        if val.isdigit(): return int(val)
        return romans.get(val.upper(), 0)

    for line in lines:
        if not line.strip(): continue
        if line.startswith('='): continue
        if line.startswith('-'): continue
        if line.startswith('+'): continue
        
        # Check for Pool Section Start
        if pool_header_regex.search(line) and line.count('|') < 5:
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
            if "MODÜL" in line.upper() or "SEÇMELİ DERSLER" in line.upper() or "SEÇMELİLER" in line.upper() or "ZSD" in line.upper() or "HAVUZU" in line.upper():
                # Format 1: | CODE | DESCRIPTION |
                match1 = pool_code_regex.search(line)
                # Format 2: | DESCRIPTION (CODE) |
                match2 = re.search(r'\((ZSD[IVX]*|SD[IVX]*|ÜSD[IVX]*|HUKSD[0-9]*)\)', line)
                # Format 3: | ZSD I - ... |
                match3 = re.search(r'\|\s*(ZSD\s*[IVX]+)\s*-', line)
                # Format 4: | CODE SEÇMELİ ... | or | CODE HAVUZU ... |
                # Matches SDBIOII, SDMATI, ÜSD
                match4 = re.search(r'\|\s*([A-ZİĞÜŞÖÇ0-9_]{3,})\s+(?:SEÇMELİ|HAVUZU|DERSLER)', line, re.IGNORECASE)

                code = None
                if match1:
                    code = match1.group(1).strip()
                elif match2:
                    code = match2.group(1).strip()
                elif match3:
                    code = match3.group(1).strip()
                elif match4:
                    code = match4.group(1).strip()
                
                if code:
                    # Ignore if it looks like a course code (e.g. HUK151) unless it's clearly a pool header
                    # Pool codes often like HUKSD5, SDBIOI, ZSD, SD, ÜSD
                    current_pool_code = code
                    if current_pool_code not in pools:
                        pools[current_pool_code] = []
                continue

        # Semester Parsing
        # Priority: YARIYIL/DÖNEM > GÜZ/BAHAR > YIL
        if not in_pool_section:
            term_match = sem_term_regex.search(line)
            season_match = season_regex.search(line)
            year_match = year_regex.search(line)
            
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
                
            if re.match(r'^[A-ZİĞÜŞÖÇ]{2,}[0-9IVX]*$', p_clean):
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
            ects = extract_ects(parts)
            
            # Fix for 0 ECTS: check if last column is digit
            if ects == 0 and parts[-1].strip().isdigit():
                ects = int(parts[-1].strip())

            course_tuple = (code, name, ects)
            
            if in_pool_section and current_pool_code:
                # Avoid adding the pool header itself as a course
                if code != current_pool_code:
                    pools[current_pool_code].append(course_tuple)
            elif 1 <= current_semester <= 8:
                if current_semester not in curriculum:
                    curriculum[current_semester] = []
                if course_tuple not in curriculum[current_semester]:
                    curriculum[current_semester].append(course_tuple)

    return curriculum, pools

def main():
    departments_data = {}
    
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
                try:
                    curriculum, pools = parse_file(filepath)
                    departments_data[dept_name] = {
                        "curriculum": curriculum,
                        "pools": pools
                    }
                except Exception as e:
                    print(f"Error parsing {file}: {e}")

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

if __name__ == "__main__":
    main()
