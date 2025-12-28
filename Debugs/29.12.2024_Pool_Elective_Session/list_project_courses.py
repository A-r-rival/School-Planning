# Script to find all project courses in curriculum data
import sys
sys.path.insert(0, r'd:\Git_Projects\School-Planning')

from scripts.curriculum_data import DEPARTMENTS_DATA

project_courses = []

for dept_name, dept_data in DEPARTMENTS_DATA.items():
    if 'curriculum' in dept_data:
        for semester, courses in dept_data['curriculum'].items():
            for course in courses:
                if len(course) >= 2:
                    code = course[0]
                    name = course[1]
                    if 'proje' in name.lower() or 'project' in name.lower():
                        akts = course[2] if len(course) > 2 else 0
                        project_courses.append({
                            'dept': dept_name,
                            'semester': semester,
                            'code': code,
                            'name': name,
                            'akts': akts
                        })

# Write results to file
with open('project_courses_list.txt', 'w', encoding='utf-8') as f:
    f.write(f"Found {len(project_courses)} courses with 'proje/project' in name:\n\n")
    for i, course in enumerate(project_courses, 1):
        f.write(f"{i}. [{course['code']}] {course['name']} - {course['akts']} AKTS\n")
        f.write(f"   Bölüm: {course['dept']}, Dönem: {course['semester']}\n\n")

print(f"Results written to project_courses_list.txt ({len(project_courses)} courses)")
