# Check which departments in curriculum_data have pool_codes
import sys
sys.path.insert(0, r'd:\Git_Projects\School-Planning')

from scripts.curriculum_data import DEPARTMENTS_DATA

print("Departments with pool_codes:")
print("=" * 60)

has_pools = []
no_pools = []

for dept_name, dept_data in DEPARTMENTS_DATA.items():
    pool_codes = dept_data.get('pool_codes', {})
    
    if pool_codes:
        total_courses = sum(len(courses) for courses in pool_codes.values())
        has_pools.append((dept_name, len(pool_codes), total_courses))
        print(f"✅ {dept_name}")
        for pool, courses in pool_codes.items():
            print(f"   {pool}: {len(courses)} courses")
    else:
        no_pools.append(dept_name)

print(f"\n{'=' * 60}")
print(f"Summary:")
print(f"  ✅ With pools: {len(has_pools)} departments")
print(f"  ❌ No pools: {len(no_pools)} departments")

if no_pools:
    print(f"\nDepartments without pool_codes:")
    for dept in no_pools:
        print(f"  - {dept}")
