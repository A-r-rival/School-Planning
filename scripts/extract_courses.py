import os
import re
import json

INPUT_DIR = r"d:\Git_Projects\School-Planning\database\Curriculum"
OUTPUT_JSON = r"d:\Git_Projects\School-Planning\scripts\course_dict.json"

def extract_from_file(file_path, unique_courses):
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip().startswith('|') and 'KOD' not in line and 'TOPLAM' not in line:
                parts = line.split('|')
                if len(parts) >= 7:
                    name_cell = parts[2].strip()
                    # Remove trailing (DE/EN/TR) etc
                    name_cell = re.sub(r'\s*\([^\)]*\)\s*$', '', name_cell).strip()
                    # Remove {...}
                    name_cell = re.sub(r'\{[^\}]+\}', '', name_cell).strip()
                    if name_cell and name_cell not in unique_courses:
                        unique_courses[name_cell] = {"TR": "", "EN": "", "DE": ""}

def main():
    unique_courses = {}
    for root, dirs, files in os.walk(INPUT_DIR):
        if 'Fen Fakültesi' in root or 'Mühendislik Fakültesi' in root:
            for file in files:
                if file.endswith('.txt'):
                    input_path = os.path.join(root, file)
                    extract_from_file(input_path, unique_courses)
                    
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(unique_courses, f, ensure_ascii=False, indent=4)
        
    print(f"Extracted {len(unique_courses)} unique courses to {OUTPUT_JSON}")

if __name__ == "__main__":
    main()
