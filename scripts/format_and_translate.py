import os
import re

INPUT_DIR = r"d:\Git_Projects\School-Planning\database\Curriculum"
OUTPUT_DIR = r"d:\Git_Projects\School-Planning\database\Curriculum_Reformatted"

# Common Turkish words to detect TR part if no header is present
TR_KEYWORDS = ['Giriş', 'Mühendislik', 'Uygulamalı', 'Seçmeli', 'Proje', 'Temelleri', 'Sistemleri', 'Tasarım', 'Alan', 'Hukuk', 'Fizik', 'Kimya', 'Biyoloji', 'Matematik', 'Analiz', 'Makine']

PATH_TRANSLATIONS = {
    "Fen Fakültesi": {"EN": "Faculty of Science", "DE": "Naturwissenschaftliche Fakultät"},
    "Mühendislik Fakültesi": {"EN": "Faculty of Engineering", "DE": "Ingenieurfakultät"},
    "Enerji Bilimi ve Teknolojileri Öğretim Planı.txt": {"EN": "Energy Science and Technologies Curriculum.txt", "DE": "Energiewissenschaft und -technologien Lehrplan.txt"},
    "Malzeme Bilimi ve Teknolojileri Öğretim Planı.txt": {"EN": "Materials Science and Technologies Curriculum.txt", "DE": "Materialwissenschaft und -technologien Lehrplan.txt"},
    "Moleküler Biyoteknoloji Öğretim Planı.txt": {"EN": "Molecular Biotechnology Curriculum.txt", "DE": "Molekulare Biotechnologie Lehrplan.txt"},
    "Bilgisayar Müh Öğretim Planı.txt": {"EN": "Computer Eng Curriculum.txt", "DE": "Informatik Ing Lehrplan.txt"},
    "Elektrik-Elektronik Müh Öğretim Planı.txt": {"EN": "Electrical-Electronics Eng Curriculum.txt", "DE": "Elektro-Elektronik Ing Lehrplan.txt"},
    "Endüstri Müh Öğretim Planı.txt": {"EN": "Industrial Eng Curriculum.txt", "DE": "Wirtschaftsingenieurwesen Lehrplan.txt"},
    "İnşaat Müh Öğretim Planı.txt": {"EN": "Civil Eng Curriculum.txt", "DE": "Bauingenieurwesen Lehrplan.txt"},
    "Makine Müh Öğretim Planı.txt": {"EN": "Mechanical Eng Curriculum.txt", "DE": "Maschinenbau Ing Lehrplan.txt"},
    "Mekatronik Müh Öğretim Planı.txt": {"EN": "Mechatronics Eng Curriculum.txt", "DE": "Mechatronik Ing Lehrplan.txt"}
}

def translate_path(path_str, lang):
    parts = path_str.replace('\\', '/').split('/')
    translated_parts = []
    for p in parts:
        if p in PATH_TRANSLATIONS:
            translated_parts.append(PATH_TRANSLATIONS[p][lang])
        else:
            translated_parts.append(p)
    return os.path.join(*translated_parts)

def is_turkish(text):
    text_upper = text.upper()
    for kw in TR_KEYWORDS:
        if kw.upper() in text_upper:
            return True
    return False

def number_to_roman(name):
    mapping = {' 1': ' I', ' 2': ' II', ' 3': ' III', ' 4': ' IV', ' 5': ' V', ' 6': ' VI', ' 7': ' VII'}
    for k, v in mapping.items():
        if name.endswith(k):
            return name[:-len(k)] + v
    return name

def split_course_name(name_str, header_hint=None):
    # Returns (tr, en, de)
    tags = []
    tag_matches = re.finditer(r'\{([^\}]+)\}', name_str)
    for m in tag_matches:
        tags.append(m.group(1))
    
    name_str = re.sub(r'\{[^\}]+\}', '', name_str)
    name_str = re.sub(r'\s*\([^\)]*\)\s*$', '', name_str).strip()

    if '/' not in name_str:
        tr = en = de = name_str.strip()
    else:
        parts = [p.strip() for p in name_str.split('/') if p.strip()]
        parts = [number_to_roman(p) for p in parts]
        
        tr = en = de = None
        
        if header_hint and len(parts) == len(header_hint):
            for i, p in enumerate(parts):
                if header_hint[i] == 'TR': tr = p
                elif header_hint[i] == 'EN': en = p
                elif header_hint[i] == 'DE': de = p
        else:
            # Fallback keyword logic
            tr_found = False
            for p in parts:
                if not tr_found and is_turkish(p):
                    tr = p
                    tr_found = True
            
            if len(parts) == 2:
                if tr == parts[1]:
                    en = parts[0]
                    de = parts[0]
                elif tr == parts[0]:
                    en = parts[1]
                    de = parts[1]
                else:
                    # Default: determine order from header_hint if available
                    tr_first = True
                    if header_hint and 'TR' in header_hint:
                        en_idx = header_hint.index('EN') if 'EN' in header_hint else 0
                        tr_idx = header_hint.index('TR')
                        if tr_idx > en_idx:
                            tr_first = False
                            
                    if tr_first:
                        tr = parts[0]
                        en = parts[1]
                        de = parts[1]
                    else:
                        tr = parts[1]
                        en = parts[0]
                        de = parts[0]
            elif len(parts) >= 3:
                if tr_found:
                    tr_idx = parts.index(tr)
                    if tr_idx == 1: # DE / TR / EN
                        de = parts[0]
                        en = parts[2]
                    elif tr_idx == 2: # DE / EN / TR
                        de = parts[0]
                        en = parts[1]
                    else: # TR / EN / DE
                        en = parts[1]
                        de = parts[2]
                else:
                    de, en, tr = parts[0], parts[1], parts[2]
        
        # Defaults
        if not en: en = parts[0]
        if not de: de = en
        if not tr: tr = parts[0]
        
    # Format the tags to put them at the end
    tag_str = " ".join([f"{{{t}}}" for t in tags])
    if tag_str:
        tr = f"{tr} {tag_str}"
        en = f"{en} {tag_str}"
        de = f"{de} {tag_str}"
        
    return tr, en, de

def process_file_multilang(lines):
    lines_tr = []
    lines_en = []
    lines_de = []
    
    pool_courses = []
    current_header_hint = None
    last_table_border = "+--------------------------------------------------------------------------------------------------+\n"
    last_table_header = "| KOD    | DERS ADI                                                   | ÖN KOS | DİL | T | U | AKTS |\n"
    
    def flush_pool_courses():
        res_tr, res_en, res_de = [], [], []
        if not pool_courses: return res_tr, res_en, res_de
        
        from collections import OrderedDict
        groups = OrderedDict()
        
        for p in pool_courses:
            key = (p[0], p[2], p[3], p[4], p[5], p[6]) # code, pre, lang, t, u, l
            if key not in groups:
                groups[key] = []
            groups[key].append(p)
            
        for key, items in groups.items():
            if len(items) > 1:
                count = len(items)
                base = items[0]
                
                try: total_ects = str(int(base[7]) * count)
                except: total_ects = base[7]
                
                # base[1] is a tuple of (name_tr, name_en, name_de)
                name_tr = base[1][0]
                name_en = base[1][1]
                name_de = base[1][2]
                
                if "{SECIM" not in name_tr:
                    name_tr = f"{name_tr} {{SECIM:{count}}}"
                    name_en = f"{name_en} {{SECIM:{count}}}"
                    name_de = f"{name_de} {{SECIM:{count}}}"
                
                parts = base[8].split('|')
                name_idx = 2
                ects_idx = len(parts) - 2
                
                parts_tr = list(parts)
                parts_tr[name_idx] = " " + name_tr.ljust(len(parts_tr[name_idx])-2) + " "
                parts_tr[ects_idx] = " " + total_ects.center(len(parts_tr[ects_idx])-2) + " "
                res_tr.append("|".join(parts_tr))
                
                parts_en = list(parts)
                parts_en[name_idx] = " " + name_en.ljust(len(parts_en[name_idx])-2) + " "
                parts_en[ects_idx] = " " + total_ects.center(len(parts_en[ects_idx])-2) + " "
                res_en.append("|".join(parts_en))
                
                parts_de = list(parts)
                parts_de[name_idx] = " " + name_de.ljust(len(parts_de[name_idx])-2) + " "
                parts_de[ects_idx] = " " + total_ects.center(len(parts_de[ects_idx])-2) + " "
                res_de.append("|".join(parts_de))
            else:
                res_tr.append(items[0][8])
                res_en.append(items[0][9])
                res_de.append(items[0][10])
                
        pool_courses.clear()
        return res_tr, res_en, res_de

    for line in lines:
        if line.strip().startswith('+--'):
            last_table_border = line
            ftr, fen, fde = flush_pool_courses()
            lines_tr.extend(ftr); lines_en.extend(fen); lines_de.extend(fde)
            lines_tr.append(line); lines_en.append(line); lines_de.append(line)
            continue
            
        if line.strip().startswith('|'):
            if 'KOD' in line and 'DERS' in line:
                last_table_header = line
                ftr, fen, fde = flush_pool_courses()
                lines_tr.extend(ftr); lines_en.extend(fen); lines_de.extend(fde)
                
                # Try to extract language hint
                match = re.search(r'DERS ADI \((.*?)\)', line)
                if match:
                    hint = match.group(1).replace(' ', '').upper()
                    current_header_hint = hint.split('/')
                else:
                    current_header_hint = None
                    
                lines_tr.append(line); lines_en.append(line); lines_de.append(line)
                continue
                
            if 'TOPLAM' in line:
                ftr, fen, fde = flush_pool_courses()
                lines_tr.extend(ftr); lines_en.extend(fen); lines_de.extend(fde)
                
                # Clear the contents of the DERS ADI column (which is parts[2]) if it exists
                parts = line.split('|')
                if len(parts) >= 3:
                    # Empty the cell but keep its width
                    parts[2] = " " * len(parts[2])
                    line = "|".join(parts)
                
                lines_tr.append(line); lines_en.append(line); lines_de.append(line)
                continue
                
            parts = line.split('|')
            if len(parts) >= 7:
                code = parts[1].strip()
                name_cell = parts[2].strip()
                
                name_tr, name_en, name_de = split_course_name(name_cell, current_header_hint)
                
                is_pool = any(code.startswith(prefix) for prefix in ['SD', 'ZSD', 'ÜSD', 'USD', 'SIP', 'SUP'])
                
                parts_tr = list(parts); parts_tr[2] = " " + name_tr.ljust(len(parts[2])-2) + " "
                parts_en = list(parts); parts_en[2] = " " + name_en.ljust(len(parts[2])-2) + " "
                parts_de = list(parts); parts_de[2] = " " + name_de.ljust(len(parts[2])-2) + " "
                
                line_tr = "|".join(parts_tr)
                line_en = "|".join(parts_en)
                line_de = "|".join(parts_de)
                
                if is_pool:
                    ects = parts[-2].strip()
                    try: t, u, l = parts[-5].strip(), parts[-4].strip(), parts[-3].strip()
                    except: t, u, l = "", "", ""
                    lang = parts[4].strip() if len(parts)>8 else ""
                    pre = parts[3].strip()
                    
                    pool_courses.append((code, (name_tr, name_en, name_de), pre, lang, t, u, l, ects, line_tr, line_en, line_de))
                else:
                    ftr, fen, fde = flush_pool_courses()
                    lines_tr.extend(ftr); lines_en.extend(fen); lines_de.extend(fde)
                    lines_tr.append(line_tr); lines_en.append(line_en); lines_de.append(line_de)
            else:
                fen_sem_match = re.search(r'^\|\s*(\d+)\.\s*(Yarıyıl|Semester|Dönem)', line, re.IGNORECASE)
                fen_bse_match = re.search(r'^\|\s*BÖLÜM SEÇMELİ DERSLERİ \(BSE\) HAVUZU', line)
                fen_usd_match = re.search(r'^\|\s*(ÜNİVERSİTE SEÇMELİ DERSLER \(ÜSD\)|ÜSD HAVUZU)', line, re.IGNORECASE)
                fen_zsd_match = re.search(r'^\|\s*ZORUNLU SEÇMELİ DERSLER \(ZSD\)', line)
                fen_zsd_malzeme_match = re.search(r'^\|\s*(ZSD\s*[IVX]+)\s*-\s*\d+\s*AKTS', line, re.IGNORECASE)
                fen_sd_molekuler_match = re.search(r'^\|\s*(SD(?:BIO|MAT)[IVX]+)\s+SEÇMELİ DERSLER', line, re.IGNORECASE)
                
                if fen_sem_match or fen_bse_match or fen_usd_match or fen_zsd_match or fen_zsd_malzeme_match or fen_sd_molekuler_match:
                    ftr, fen, fde = flush_pool_courses()
                    lines_tr.extend(ftr); lines_en.extend(fen); lines_de.extend(fde)
                    
                    if len(lines_tr) > 0 and lines_tr[-1].startswith('+---'):
                        pass # Table is already closed by previous line
                    else:
                        lines_tr.append(last_table_border)
                        lines_en.append(last_table_border)
                        lines_de.append(last_table_border)
                    
                    banner_tr = banner_en = banner_de = ""
                    if fen_sem_match:
                        sem_num_str = fen_sem_match.group(1)
                        try:
                            sem_num = int(sem_num_str)
                            sinif = (sem_num + 1) // 2
                            yariyil = 1 if sem_num % 2 != 0 else 2
                            season = "GÜZ" if sem_num % 2 != 0 else "BAHAR"
                            banner_tr = banner_en = banner_de = f"\n{'-'*100}\n{sem_num}. DÖNEM ({sinif}. SINIF / {yariyil}. YARIYIL ({season}))\n{'-'*100}\n"
                        except:
                            banner_tr = banner_en = banner_de = f"\n{'-'*100}\n{sem_num_str}. DÖNEM\n{'-'*100}\n"
                    elif fen_bse_match:
                        banner_tr = f"\n{'-'*100}\n[BSE] BÖLÜM SEÇMELİ DERSLERİ HAVUZU\n{'-'*100}\n"
                        banner_en = f"\n{'-'*100}\n[BSE] DEPARTMENTAL ELECTIVE COURSES POOL\n{'-'*100}\n"
                        banner_de = f"\n{'-'*100}\n[BSE] ABTEILUNGSWAHLFÄCHER POOL\n{'-'*100}\n"
                    elif fen_usd_match:
                        banner_tr = f"\n{'-'*100}\n[ÜSD] ÜNİVERSİTE SEÇMELİ DERSLER HAVUZU\n{'-'*100}\n"
                        banner_en = f"\n{'-'*100}\n[ÜSD] UNIVERSITY ELECTIVE COURSES POOL\n{'-'*100}\n"
                        banner_de = f"\n{'-'*100}\n[ÜSD] UNIVERSITÄTSWAHLFÄCHER POOL\n{'-'*100}\n"
                    elif fen_zsd_match:
                        banner_tr = f"\n{'-'*100}\n[ZSD] ZORUNLU SEÇMELİ DERSLER HAVUZU\n{'-'*100}\n"
                        banner_en = f"\n{'-'*100}\n[ZSD] COMPULSORY ELECTIVE COURSES POOL\n{'-'*100}\n"
                        banner_de = f"\n{'-'*100}\n[ZSD] PFLICHTWAHLFÄCHER POOL\n{'-'*100}\n"
                    elif fen_zsd_malzeme_match:
                        pool_id_raw = fen_zsd_malzeme_match.group(1) # e.g. "ZSD V"
                        pool_id = pool_id_raw.replace(' ', '').upper() # "ZSDV"
                        roman = pool_id.replace('ZSD', '')
                        banner_tr = f"\n{'-'*100}\n[{pool_id}] ZORUNLU SEÇMELİ DERSLER HAVUZU {roman}\n{'-'*100}\n"
                        banner_en = f"\n{'-'*100}\n[{pool_id}] COMPULSORY ELECTIVE COURSES POOL {roman}\n{'-'*100}\n"
                        banner_de = f"\n{'-'*100}\n[{pool_id}] PFLICHTWAHLFÄCHER POOL {roman}\n{'-'*100}\n"
                    elif fen_sd_molekuler_match:
                        pool_id = fen_sd_molekuler_match.group(1).upper()
                        pool_name_raw = line.strip('| ').strip()
                        pool_name = pool_name_raw[len(pool_id):].strip().rstrip('|').strip()
                        banner_tr = banner_en = banner_de = f"\n{'-'*100}\n[{pool_id}] {pool_name}\n{'-'*100}\n"
                        
                    lines_tr.append(banner_tr)
                    lines_en.append(banner_en)
                    lines_de.append(banner_de)
                    
                    lines_tr.append(last_table_border)
                    lines_en.append(last_table_border)
                    lines_de.append(last_table_border)
                    if 'last_table_header' in locals() or 'last_table_header' in globals():
                        lines_tr.append(last_table_header)
                        lines_en.append(last_table_header)
                        lines_de.append(last_table_header)
                    lines_tr.append(last_table_border)
                    lines_en.append(last_table_border)
                    lines_de.append(last_table_border)
                else:
                    ftr, fen, fde = flush_pool_courses()
                    lines_tr.extend(ftr); lines_en.extend(fen); lines_de.extend(fde)
                    lines_tr.append(line); lines_en.append(line); lines_de.append(line)
        else:
            ftr, fen, fde = flush_pool_courses()
            lines_tr.extend(ftr); lines_en.extend(fen); lines_de.extend(fde)
            
            # Pool banner check
            match = re.search(r'^(.*?)\s*-\s*([A-Z0-9x,]+)\s*(?:\((.*?)\))?\s*$', line.strip())
            
            # Semester header check
            sem_match = re.search(r'^(\d+)\.\s*DÖNEM', line.strip())
            
            if line.strip().startswith('========'):
                line = "-" * 100 + "\n"
                
            if match and "SEÇMELİ" in line.upper() and not line.strip().startswith('['):
                name = match.group(1).strip()
                code = match.group(2).strip()
                extra = f" ({match.group(3).strip()})" if match.group(3) else ""
                banner = f"[{code}] {name}{extra}"
                lines_tr.append(line.replace(line.strip(), banner))
                lines_en.append(line.replace(line.strip(), banner))
                lines_de.append(line.replace(line.strip(), banner))
            elif "ZORUNLU SEÇMELİ DERSLER (ZSD) HAVUZU" in line.upper() or "ZORUNLU SEÇMELİ DERS ALANI (ZSD) [Genel Havuz]" in line:
                banner = "[ZSD] ZORUNLU SEÇMELİ DERSLER HAVUZU"
                lines_tr.append(line.replace(line.strip(), banner))
                lines_en.append(line.replace(line.strip(), banner).replace("ZORUNLU SEÇMELİ DERSLER HAVUZU", "COMPULSORY ELECTIVE COURSES POOL"))
                lines_de.append(line.replace(line.strip(), banner).replace("ZORUNLU SEÇMELİ DERSLER HAVUZU", "PFLICHTWAHLFÄCHER POOL"))
            elif "SEÇMELİ DERS ALANI I - PROJE (SDP I)" in line:
                banner_tr = "[SDP I] SEÇMELİ DERS ALANI I - PROJE HAVUZU"
                banner_en = "[SDP I] ELECTIVE COURSE AREA I - PROJECT POOL"
                banner_de = "[SDP I] WAHLFACHBEREICH I - PROJEKT POOL"
                lines_tr.append(banner_tr + "\n")
                lines_en.append(banner_en + "\n")
                lines_de.append(banner_de + "\n")
            elif "SEÇMELİ DERS ALANI II - PROJE (SDP II)" in line:
                banner_tr = "[SDP II] SEÇMELİ DERS ALANI II - PROJE HAVUZU"
                banner_en = "[SDP II] ELECTIVE COURSE AREA II - PROJECT POOL"
                banner_de = "[SDP II] WAHLFACHBEREICH II - PROJEKT POOL"
                lines_tr.append(banner_tr + "\n")
                lines_en.append(banner_en + "\n")
                lines_de.append(banner_de + "\n")
            elif "[SDUa] UZMANLIK ALANI A" in line:
                super_pool_tr = """[SDUx] UZMANLIK ALANLARI SÜPER HAVUZU
----------------------------------------------------------------------------------------------------
+--------+------------------------------------------------------------+--------+----------------------------+
| KOD    | DERS ADI                                                   | ÖN KOS | DİL | T | U | L | AKTS |
+--------+------------------------------------------------------------+--------+----------------------------+
| HAVUZ  | UZMANLIK ALANI A: ÜRETİM TEKNİKLERİ                        | -      | SDUa                       |
| HAVUZ  | UZMANLIK ALANI B: TASARIM                                  | -      | SDUb                       |
| HAVUZ  | UZMANLIK ALANI C: UZAY HAVACILIK                           | -      | SDUc                       |
| HAVUZ  | UZMANLIK ALANI D: TAŞIT SİSTEMLERİ                         | -      | SDUd                       |
| HAVUZ  | UZMANLIK ALANI E: İŞLETMEDE MESLEKİ EĞİTİM                 | -      | SDUe                       |
+--------+------------------------------------------------------------+--------+----------------------------+

----------------------------------------------------------------------------------------------------
"""
                super_pool_en = super_pool_tr.replace("SÜPER HAVUZU", "SUPER POOL").replace("HAVUZ", "POOL").replace("UZMANLIK ALANLARI", "SPECIALIZATION AREAS").replace("UZMANLIK ALANI A: ÜRETİM TEKNİKLERİ", "SPECIALIZATION AREA A: PRODUCTION TECHNIQUES").replace("UZMANLIK ALANI B: TASARIM", "SPECIALIZATION AREA B: DESIGN").replace("UZMANLIK ALANI C: UZAY HAVACILIK", "SPECIALIZATION AREA C: AEROSPACE").replace("UZMANLIK ALANI D: TAŞIT SİSTEMLERİ", "SPECIALIZATION AREA D: VEHICLE SYSTEMS").replace("UZMANLIK ALANI E: İŞLETMEDE MESLEKİ EĞİTİM", "SPECIALIZATION AREA E: CO-OPERATIVE EDUCATION")
                super_pool_de = super_pool_tr.replace("SÜPER HAVUZU", "SUPER POOL").replace("HAVUZ", "POOL").replace("UZMANLIK ALANLARI", "SPEZIALISIERUNGSBEREICHE").replace("UZMANLIK ALANI A: ÜRETİM TEKNİKLERİ", "SPEZIALISIERUNGSBEREICH A: PRODUKTIONSTECHNIK").replace("UZMANLIK ALANI B: TASARIM", "SPEZIALISIERUNGSBEREICH B: KONSTRUKTION").replace("UZMANLIK ALANI C: UZAY HAVACILIK", "SPEZIALISIERUNGSBEREICH C: LUFT- UND RAUMFAHRTTECHNIK").replace("UZMANLIK ALANI D: TAŞIT SİSTEMLERİ", "SPEZIALISIERUNGSBEREICH D: FAHRZEUGTECHNIK").replace("UZMANLIK ALANI E: İŞLETMEDE MESLEKİ EĞİTİM", "SPEZIALISIERUNGSBEREICH E: BERUFSAUSBILDUNG IM UNTERNEHMEN")
                
                lines_tr.append(super_pool_tr)
                lines_en.append(super_pool_en)
                lines_de.append(super_pool_de)
                
                banner = "[SDUa] UZMANLIK ALANI A: ÜRETİM TEKNİKLERİ HAVUZU"
                lines_tr.append(banner + "\n")
                lines_en.append(banner.replace("HAVUZU", "POOL") + "\n")
                lines_de.append(banner.replace("HAVUZU", "POOL") + "\n")
            elif "[SDIa/IIa/III/IV] UYGULAMALI BİLGİSAYAR MÜHENDİSLİĞİ HAVUZU" in line:
                # Dinamik Süper Havuz Dönüşümü
                super_pool_tr = """[SDIII, SDIV] SEÇMELİ DERSLER III/IV SÜPER HAVUZU
----------------------------------------------------------------------------------------------------
+--------+------------------------------------------------------------+--------+----------------------------+
| KOD    | DERS ADI                                                   | ÖN KOS | DİL | T | U | L | AKTS |
+--------+------------------------------------------------------------+--------+----------------------------+
| HAVUZ  | UYGULAMALI BİLGİSAYAR MÜHENDİSLİĞİ HAVUZU                  | -      | SDIa, SDIIa                |
| HAVUZ  | BİLGİSAYAR DONANIMI HAVUZU                                 | -      | SDIb, SDIIb                |
| HAVUZ  | KURAMSAL TEMELLER VE MATEMATİK HAVUZU                      | -      | SDIc, SDIIc                |
| HAVUZ  | İŞLETME ENFORMATİĞİ HAVUZU                                 | -      | SDId, SDIId                |
| HAVUZ  | GENEL SEÇMELİ DERSLER HAVUZU                               | -      | SDIe, SDIIe                |
+--------+------------------------------------------------------------+--------+----------------------------+

----------------------------------------------------------------------------------------------------
"""
                super_pool_en = super_pool_tr.replace("SÜPER HAVUZU", "SUPER POOL").replace("HAVUZU", "POOL").replace("DERS ADI", "COURSE NAME").replace("ÖN KOS", "PRE-REQ").replace("DİL", "LANG").replace("AKTS", "ECTS")
                super_pool_de = super_pool_tr.replace("SÜPER HAVUZU", "SUPER POOL").replace("HAVUZU", "POOL").replace("DERS ADI", "KURSNAME").replace("ÖN KOS", "VORAUS").replace("DİL", "SPRA").replace("AKTS", "ECTS")
                
                for l in super_pool_tr.split('\n')[:-1]: lines_tr.append(l + "\n")
                for l in super_pool_en.split('\n')[:-1]: lines_en.append(l + "\n")
                for l in super_pool_de.split('\n')[:-1]: lines_de.append(l + "\n")
                    
                new_banner_tr = line.replace("[SDIa/IIa/III/IV]", "[SDIa, SDIIa]")
                lines_tr.append(new_banner_tr)
                lines_en.append(new_banner_tr.replace("HAVUZU", "POOL"))
                lines_de.append(new_banner_tr.replace("HAVUZU", "POOL"))
                
            elif "[SDIb/IIb/III/IV] BİLGİSAYAR DONANIMI HAVUZU" in line:
                new_banner_tr = line.replace("[SDIb/IIb/III/IV]", "[SDIb, SDIIb]")
                lines_tr.append(new_banner_tr)
                lines_en.append(new_banner_tr.replace("HAVUZU", "POOL"))
                lines_de.append(new_banner_tr.replace("HAVUZU", "POOL"))
                
            elif "[SDIc/IIc/III/IV] KURAMSAL TEMELLER VE MATEMATİK HAVUZU" in line:
                new_banner_tr = line.replace("[SDIc/IIc/III/IV]", "[SDIc, SDIIc]")
                lines_tr.append(new_banner_tr)
                lines_en.append(new_banner_tr.replace("HAVUZU", "POOL"))
                lines_de.append(new_banner_tr.replace("HAVUZU", "POOL"))
                
            elif "[SDIII/IV] İŞLETME ENFORMATİĞİ HAVUZU" in line:
                new_banner_tr = line.replace("[SDIII/IV]", "[SDId, SDIId]")
                lines_tr.append(new_banner_tr)
                lines_en.append(new_banner_tr.replace("HAVUZU", "POOL"))
                lines_de.append(new_banner_tr.replace("HAVUZU", "POOL"))
                
            elif "[SDIII/IV] GENEL SEÇMELİ DERSLER HAVUZU" in line:
                new_banner_tr = line.replace("[SDIII/IV]", "[SDIe, SDIIe]")
                lines_tr.append(new_banner_tr)
                lines_en.append(new_banner_tr.replace("HAVUZU", "POOL"))
                lines_de.append(new_banner_tr.replace("HAVUZU", "POOL"))
            elif sem_match:
                # Rewrite semester header
                sem_num = int(sem_match.group(1))
                sinif = (sem_num + 1) // 2
                yariyil = ((sem_num - 1) % 2) + 1
                
                tr_season = "GÜZ" if yariyil == 1 else "BAHAR"
                en_season = "FALL" if yariyil == 1 else "SPRING"
                de_season = "WINTER" if yariyil == 1 else "SOMMER"
                
                new_header = f"{sem_num}. DÖNEM ({sinif}. SINIF / {yariyil}. YARIYIL ({tr_season}))"
                
                # We need to replace the content of the line, keeping leading/trailing spaces
                replaced_line = re.sub(r'^\d+\.\s*DÖNEM.*$', new_header, line.strip())
                # Just formatting it properly with original whitespace (usually none)
                lines_tr.append(replaced_line + "\n")
                
                # EN and DE translations for the semester header
                en_header = f"{sem_num}. SEMESTER (YEAR {sinif} / TERM {yariyil} ({en_season}))"
                de_header = f"{sem_num}. SEMESTER (JAHR {sinif} / SEMESTER {yariyil} ({de_season}))"
                
                lines_en.append(en_header + "\n")
                lines_de.append(de_header + "\n")
            else:
                lines_tr.append(line); lines_en.append(line); lines_de.append(line)
                
    ftr, fen, fde = flush_pool_courses()
    lines_tr.extend(ftr); lines_en.extend(fen); lines_de.extend(fde)
    
    return lines_tr, lines_en, lines_de

def main():
    if os.path.exists(OUTPUT_DIR):
        import shutil
        # We want to preserve curriculum_format_rules.md if it's there, but it's easier to just recreate it or copy it from a safe place.
        # Let's just rmtree and we'll copy it back.
        shutil.rmtree(OUTPUT_DIR)
        
    for root, dirs, files in os.walk(INPUT_DIR):
        for file in files:
            if file.endswith('.txt'):
                input_path = os.path.join(root, file)
                rel_path = os.path.relpath(input_path, INPUT_DIR)
                
                print(f"Processing: {rel_path}")
                with open(input_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                lines_tr, lines_en, lines_de = process_file_multilang(lines)
                    
                tr_path = os.path.join(OUTPUT_DIR, 'TR', rel_path)
                en_path = os.path.join(OUTPUT_DIR, 'EN', translate_path(rel_path, 'EN'))
                de_path = os.path.join(OUTPUT_DIR, 'DE', translate_path(rel_path, 'DE'))
                
                os.makedirs(os.path.dirname(tr_path), exist_ok=True)
                os.makedirs(os.path.dirname(en_path), exist_ok=True)
                os.makedirs(os.path.dirname(de_path), exist_ok=True)
                
                with open(tr_path, 'w', encoding='utf-8') as f: f.writelines(lines_tr)
                with open(en_path, 'w', encoding='utf-8') as f: f.writelines(lines_en)
                with open(de_path, 'w', encoding='utf-8') as f: f.writelines(lines_de)

    # Always ensure the curriculum rules file is placed in OUTPUT_DIR after running
    import shutil
    rules_src = r"d:\Git_Projects\School-Planning\docs\curriculum_format_rules.md"
    rules_dst = os.path.join(OUTPUT_DIR, "curriculum_format_rules.md")
    
    # Check if we have a backup in docs to copy from, otherwise check if we have one in the original DB folder
    if os.path.exists(rules_src):
        shutil.copy(rules_src, rules_dst)
    elif os.path.exists(os.path.join(INPUT_DIR, "curriculum_format_rules.md")):
        shutil.copy(os.path.join(INPUT_DIR, "curriculum_format_rules.md"), rules_dst)
        # also copy to docs for safety
        os.makedirs(os.path.dirname(rules_src), exist_ok=True)
        shutil.copy(os.path.join(INPUT_DIR, "curriculum_format_rules.md"), rules_src)
                    
if __name__ == "__main__":
    main()
