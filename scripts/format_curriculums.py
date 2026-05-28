import os
import re
import shutil

INPUT_DIR = r"d:\Git_Projects\School-Planning\database\Curriculum"
OUTPUT_DIR = r"d:\Git_Projects\School-Planning\database\Curriculum_Reformatted"

def number_to_roman(name):
    # Replaces trailing ' 1', ' 2', ' 3' etc with ' I', ' II', ' III'
    mapping = {' 1': ' I', ' 2': ' II', ' 3': ' III', ' 4': ' IV', ' 5': ' V', ' 6': ' VI', ' 7': ' VII'}
    for k, v in mapping.items():
        if name.endswith(k):
            return name[:-len(k)] + v
    # Also handle things like 'Analiz 1' -> 'Analiz I' when not at end
    # e.g. "Analiz 1 (DE / EN / TR)" - wait, we do this BEFORE combining
    return name

def format_course_name_cell(cell_text):
    # Extract tags
    tags = []
    
    # Extract anything inside {}
    tag_matches = re.finditer(r'\{([^\}]+)\}', cell_text)
    for m in tag_matches:
        tags.append(m.group(1))
    
    # Remove tags from the cell_text temporarily
    cell_text = re.sub(r'\{[^\}]+\}', '', cell_text)
    
    # Also clean up trailing parenthesis like (Z), (S), (DE/EN/TR) because they are messy
    # But wait, (DE/EN/TR) is language info, not part of the name.
    # The rule says: "Türkçe / İngilizce / Almanca isimlendirilmeli"
    # Some older names are: "Ders Adı (DE / EN / TR)", or "Ders Adi"
    cell_text = re.sub(r'\s*\([^\)]*\)\s*$', '', cell_text).strip()
    
    # Split by /
    parts = [p.strip() for p in cell_text.split('/') if p.strip()]
    
    if len(parts) == 0:
        return cell_text # Should not happen
        
    # Re-apply roman numerals on each part
    parts = [number_to_roman(p) for p in parts]
    
    # Force 3 parts
    if len(parts) == 1:
        parts = [parts[0], parts[0], parts[0]]
    elif len(parts) == 2:
        parts = [parts[0], parts[1], parts[1]]
    elif len(parts) > 3:
        parts = parts[:3]
        
    final_name = " / ".join(parts)
    
    if tags:
        # Re-attach tags at the end
        tag_str = " ".join([f"{{{t}}}" for t in tags])
        final_name = f"{final_name} {tag_str}"
        
    return final_name

def process_table_lines(lines):
    # Process a block of lines containing a table
    new_lines = []
    
    # To handle consecutive pool courses
    pool_courses = []
    
    def flush_pool_courses():
        res = []
        if not pool_courses: return res
        
        # Group by course name without SECIM tag
        from collections import OrderedDict
        groups = OrderedDict()
        
        for p in pool_courses:
            # p is (code, name_cell, pre, lang, t, u, l, ects, line)
            key = (p[0], p[1], p[2], p[3], p[4], p[5], p[6])
            if key not in groups:
                groups[key] = []
            groups[key].append(p)
            
        for key, items in groups.items():
            if len(items) > 1:
                # Merge
                count = len(items)
                base = items[0]
                # Try to sum ECTS
                try:
                    total_ects = str(int(base[7]) * count)
                except:
                    total_ects = base[7] # Fallback if ECTS is not a clean number
                
                # Add {SECIM:X} to the name
                name = base[1].strip()
                if "{SECIM" not in name:
                    name = f"{name} {{SECIM:{count}}}"
                    
                # Reconstruct line
                parts = base[8].split('|')
                # Modify name and ECTS
                # parts[2] is name, parts[-2] is ECTS (assuming last is empty string after |)
                # Let's find exactly which index
                name_idx = 2
                ects_idx = len(parts) - 2 # usually AKTS is the last column before |
                
                parts[name_idx] = " " + name + " "
                parts[ects_idx] = " " + total_ects.center(len(parts[ects_idx])-2) + " "
                
                merged_line = "|".join(parts)
                res.append(merged_line)
            else:
                res.append(items[0][8])
                
        pool_courses.clear()
        return res

    in_table = False
    
    for line in lines:
        if line.strip().startswith('+--'):
            # Table border
            new_lines.extend(flush_pool_courses())
            new_lines.append(line)
            continue
            
        if line.strip().startswith('|'):
            # It's a table row
            if 'KOD' in line and 'DERS ADI' in line:
                # Header row
                new_lines.extend(flush_pool_courses())
                new_lines.append(line)
                continue
            if 'TOPLAM' in line:
                new_lines.extend(flush_pool_courses())
                new_lines.append(line)
                continue
                
            parts = line.split('|')
            if len(parts) >= 7:
                code = parts[1].strip()
                name_cell = parts[2].strip()
                
                # Reformat the name cell
                new_name_cell = format_course_name_cell(name_cell)
                
                # Check if it's a pool course (code is like SD, ZSD, SDII etc)
                is_pool = False
                if any(code.startswith(prefix) for prefix in ['SD', 'ZSD', 'ÜSD', 'USD', 'SIP', 'SUP']):
                    is_pool = True
                    
                # We need to construct the line back, substituting the name cell
                parts[2] = " " + new_name_cell.ljust(len(parts[2])-2) + " "
                modified_line = "|".join(parts)
                
                if is_pool:
                    ects = parts[-2].strip()
                    try:
                        t = parts[-5].strip()
                        u = parts[-4].strip()
                        l = parts[-3].strip()
                    except:
                        t,u,l="","",""
                    
                    lang = parts[4].strip() if len(parts)>8 else "" # Rough guess
                    pre = parts[3].strip()
                    
                    pool_courses.append((code, new_name_cell, pre, lang, t, u, l, ects, modified_line))
                else:
                    new_lines.extend(flush_pool_courses())
                    new_lines.append(modified_line)
            else:
                new_lines.extend(flush_pool_courses())
                new_lines.append(line)
        else:
            new_lines.extend(flush_pool_courses())
            # Check for pool banners
            # e.g. SEÇMELİ DERS ALANI II - SDII (2. Dönem) -> [SDII] Seçmeli Ders Alanı II (2. Dönem)
            match = re.search(r'^(.*?)\s*-\s*([A-Z0-9x,]+)\s*(?:\((.*?)\))?\s*$', line.strip())
            if match and "SEÇMELİ" in line.upper() and not line.strip().startswith('['):
                name = match.group(1).strip()
                code = match.group(2).strip()
                extra = f" ({match.group(3).strip()})" if match.group(3) else ""
                banner = f"[{code}] {name}{extra}"
                new_lines.append(line.replace(line.strip(), banner))
            else:
                new_lines.append(line)
                
    new_lines.extend(flush_pool_courses())
    return new_lines

def process_file(file_path, output_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    new_lines = process_table_lines(lines)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        for line in new_lines:
            f.write(line)

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    for root, dirs, files in os.walk(INPUT_DIR):
        if 'Fen Fakültesi' in root or 'Mühendislik Fakültesi' in root:
            for file in files:
                if file.endswith('.txt'):
                    input_path = os.path.join(root, file)
                    rel_path = os.path.relpath(input_path, INPUT_DIR)
                    output_path = os.path.join(OUTPUT_DIR, rel_path)
                    
                    print(f"Processing: {rel_path}")
                    process_file(input_path, output_path)

if __name__ == "__main__":
    main()
