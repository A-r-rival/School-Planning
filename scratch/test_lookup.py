import sys, re, sqlite3
sys.path.insert(0, 'd:/Git_Projects/School-Planning')
sys.path.insert(0, 'd:/Git_Projects/School-Planning/database')
from database import curriculum_data

lookup = {}
lookup_by_dept = {}
data = curriculum_data.DEPARTMENTS_DATA
for dept, details in data.items():
    curr = details.get('curriculum', {})
    for sem_key, courses in curr.items():
        match = re.search(r'\d+', sem_key)
        if match:
            sem_num = int(match.group())
            semester = 'Güz' if (sem_num % 2 != 0) else 'Bahar'
            if not isinstance(courses, list):
                continue
            for course in courses:
                if isinstance(course, list) and len(course) >= 2:
                    code = str(course[0]).strip()
                    name = str(course[1]).strip()
                    if code:
                        lookup.setdefault(code, set()).add(semester)
                        lookup_by_dept.setdefault((dept, code), set()).add(semester)
                    # ALSO expand pools inline
                    pools = details.get('pools', {})
                    if code in pools:
                        for pool_course in pools[code]:
                            if len(pool_course) >= 2:
                                pc = str(pool_course[0]).strip()
                                pn = str(pool_course[1]).strip()
                                if pc:
                                    lookup.setdefault(pc, set()).add(semester)
                                    lookup_by_dept.setdefault((dept, pc), set()).add(semester)

print('ZSD in lookup:', lookup.get('ZSD'))
print('SD  in lookup:', lookup.get('SD'))

conn = sqlite3.connect('d:/Git_Projects/School-Planning/database/okul_veritabani.db')
c = conn.cursor()
c.execute("SELECT COUNT(*) FROM Dersler WHERE ders_kodu IS NULL OR ders_kodu = ''")
print('Courses with no code in DB:', c.fetchone()[0])
c.execute("SELECT ders_adi, ders_kodu FROM Dersler WHERE ders_kodu IS NULL OR ders_kodu = '' LIMIT 10")
for r in c.fetchall():
    print(' ', r)
conn.close()

# Summary: how many courses would pass each filter
conn = sqlite3.connect('d:/Git_Projects/School-Planning/database/okul_veritabani.db')
c = conn.cursor()
c.execute("SELECT ders_adi, ders_kodu FROM Dersler")
all_courses = c.fetchall()
conn.close()

guz_pass = 0
bahar_pass = 0
both_pass = 0
no_match = 0
no_match_list = []

for name, code in all_courses:
    code = str(code or '').strip()
    name_s = str(name or '').strip()
    
    sem_set = lookup.get(code, set()) | lookup.get(name_s, set())
    
    is_guz = 'Güz' in sem_set
    is_bahar = 'Bahar' in sem_set
    
    if is_guz and is_bahar:
        both_pass += 1
    elif is_guz:
        guz_pass += 1
    elif is_bahar:
        bahar_pass += 1
    else:
        no_match += 1
        no_match_list.append((code, name_s[:40]))

print(f'\n=== Filter Simulation ===')
print(f'Total courses: {len(all_courses)}')
print(f'  Güz only: {guz_pass}')
print(f'  Bahar only: {bahar_pass}')
print(f'  Both: {both_pass}')
print(f'  No match (would be DROPPED): {no_match}')
print(f'No-match sample:')
for code, name in no_match_list[:10]:
    print(f'  code={code!r} name={name!r}')
