import re
import os

def parse_line(line):
    parts = [p.strip() for p in line.split('|')]
    if parts and parts[0] == '': parts.pop(0)
    if parts and parts[-1] == '': parts.pop()
    return parts

def extract_ects(parts):
    for p in reversed(parts):
        clean_p = p.replace('*', '').strip()
        if clean_p.isdigit():
            return int(clean_p)
    return 0

def clean_course_name(name):
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
    
    pool_header_regex = re.compile(r'SEÇMELİ DERS|SEÇMELİLER|MODÜLLERİ', re.IGNORECASE)
    pool_code_regex = re.compile(r'\s*([A-ZİĞÜŞÖÇ0-9_]*SD[A-ZİĞÜŞÖÇ0-9_]*)\s*([IVX]+|\d+)\s*', re.IGNORECASE)

    for line_num, line in enumerate(lines):
        if not line.strip(): continue
        if line.startswith('='): continue
        if line.startswith('-'): continue
        if line.startswith('+'): continue
        
        if (pool_header_regex.search(line) or pool_code_regex.search(line)) and line.count('|') < 5:
            in_pool_section = True
            print(f"Line {line_num+1}: Entered pool section")
        
        if in_pool_section:
            if "MODÜL" in line.upper() or "SEÇMELİ DERSLER" in line.upper() or "SEÇMELİLER" in line.upper() or "SD" in line.upper() or "HAVUZU" in line.upper():
                match1 = pool_code_regex.search(line)
                match2 = re.search(r'\((ZSD[IVX]*|SD[IVX]*|ÜSD[IVX]*|HUKSD[0-9]*)\)', line)
                match3 = re.search(r'\|\s*(ZSD\s*.*?)\s*-', line)
                match4 = re.search(r'\|\s*([A-ZİĞÜŞÖÇ0-9_]{3,})\s+(?:SEÇMELİ|HAVUZU|DERSLER)', line, re.IGNORECASE)

                code = None
                if match1:
                    print(f"Line {line_num+1}: Match1 groups: {match1.groups()}")
                    code = match1.group(1).strip()
                    # If group 2 exists (numeral), append it
                    if match1.lastindex >= 2:
                         suffix = match1.group(2).strip()
                         print(f"Line {line_num+1}: Suffix found: {suffix}")
                elif match2:
                    code = match2.group(1).strip()
                    print(f"Line {line_num+1}: Match2 found code: {code}")
                elif match3:
                    code = match3.group(1).strip()
                    print(f"Line {line_num+1}: Match3 found code: {code}")
                elif match4:
                    code = match4.group(1).strip()
                    print(f"Line {line_num+1}: Match4 found code: {code}")
                
                if code:
                    current_pool_code = code
                    if current_pool_code not in pools:
                        pools[current_pool_code] = []
                        print(f"Line {line_num+1}: Created pool {current_pool_code}")
                continue

        parts = parse_line(line)
        if not parts: continue

        code_idx = -1
        for i, p in enumerate(parts):
            p_clean = p.split(' - ')[0].strip()
            if p_clean in ["KOD", "KODU", "TOPLAM", "AKTS", "DERSİN", "T", "U", "L"]:
                continue
                
            if re.match(r'^[A-ZİĞÜŞÖÇ]{2,}\s*[0-9IVX]*$', p_clean):
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
            
            if ects == 0 and parts[-1].strip().isdigit():
                ects = int(parts[-1].strip())

            course_tuple = (code, name, ects)
            
            if in_pool_section and current_pool_code:
                if code != current_pool_code:
                    pools[current_pool_code].append(course_tuple)
                    print(f"Line {line_num+1}: Added {code} to pool {current_pool_code}")

    return pools

filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Curriculum", "Fen Fakültesi", "Malzeme Bilimi ve Teknolojileri Öğretim Planı.txt")
pools = parse_file(filepath)
print("Final Pools Keys:", pools.keys())
for k, v in pools.items():
    print(f"Pool {k}: {len(v)} items")
