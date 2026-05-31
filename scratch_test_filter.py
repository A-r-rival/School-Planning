import re

def normalize_tr(s):
    if not s:
        return ""
    s = str(s).upper()
    tr_map = {
        'İ': 'I', 'Ş': 'S', 'Ğ': 'G', 'Ü': 'U', 'Ö': 'O', 'Ç': 'C'
    }
    for k, v in tr_map.items():
        s = s.replace(k, v)
    return s.strip()

def clean_course_name(course_disp):
    name = re.sub(r'^\[[^\]]*\]\s*', '', course_disp)
    name = re.sub(r'\s*\([^)]*\)\s*$', '', name)
    return normalize_tr(name)

mandatory_courses = set()
names = ["İş Sağlığı ve Güvenliği II", "İleri İngilizce II", "Nümerik Analiz", "Bilgisayar Programlama II"]

for n in names:
    mandatory_courses.add(normalize_tr(n))

print("Mandatory Set:", mandatory_courses)

db_courses = [
    "[ISG002] İş Sağlığı ve Güvenliği II (Teori)",
    "[ENG302] İleri İngilizce II (Teori)",
    "[EBT302] Nümerik Analiz (T)",
    "[BIL102] Bilgisayar Programlama II (Uygulama)"
]

for dc in db_courses:
    c_name = clean_course_name(dc)
    print(f"'{c_name}' in mandatory? {c_name in mandatory_courses}")

