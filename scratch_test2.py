import sys
import os
sys.path.append('d:/Git_Projects/School-Planning/database')
import curriculum_data
import re

def normalize_tr(s):
    if not s:
        return ''
    s = str(s).upper()
    tr_map = {'İ': 'I', 'Ş': 'S', 'Ğ': 'G', 'Ü': 'U', 'Ö': 'O', 'Ç': 'C'}
    for k, v in tr_map.items():
        s = s.replace(k, v)
    return s.strip()

def clean_course_name(course_disp):
    name = re.sub(r'^\[[^\]]*\]\s*', '', course_disp)
    name = re.sub(r'\s*\([^)]*\)\s*$', '', name)
    return normalize_tr(name)

dept_data = curriculum_data.DEPARTMENTS_DATA.get('Enerji Bilimi ve Teknolojileri')
sem_key = '6. Dönem / 3. Yıl Bahar Dönemi'
courses = dept_data['curriculum'].get(sem_key, [])

mandatory = set()
for course in courses:
    code, name, akts = course[0], course[1], course[2]
    is_elective_kw = 'seçmeli' in name.lower() or 'elective' in name.lower() or 'havuz' in name.lower()
    is_usd = 'usd' in code.lower() or 'üsd' in code.lower() or 'üniversite seçmeli' in name.lower()
    if not is_elective_kw and not is_usd:
        mandatory.add(normalize_tr(name))

print('Mandatory:', mandatory)

db_courses = [
    '[EBT302] Nümerik Analiz (T)',
    '[EBT308] Uygulamalı Enerji Bilimi Laboratuvarı (U)',
    '[EBT306] Isı Transferi (T)'
]

for db_c in db_courses:
    c_name = clean_course_name(db_c)
    print(f"MATCH: '{c_name}' in mandatory? {c_name in mandatory}")
