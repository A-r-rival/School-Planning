import sys
sys.path.insert(0, 'scripts')

from curriculum_data import DEPARTMENTS_DATA

print("=" * 60)
print("POOL_CODES VERIFICATION")
print("=" * 60)

total_pools = 0
total_courses_in_pools = 0

for dept_name in sorted(DEPARTMENTS_DATA.keys())[:5]:  # First 5 departments
    dept = DEPARTMENTS_DATA[dept_name]
    pool_codes = dept.get('pool_codes', {})
    
    if pool_codes:
        print(f"\n✅ {dept_name}")
        for pool_code, courses in list(pool_codes.items())[:3]:  # First 3 pools
            print(f"   {pool_code}: {len(courses)} courses")
            total_courses_in_pools += len(courses)
        total_pools += len(pool_codes)
    else:
        print(f"\n❌ {dept_name}: NO POOLS")

print(f"\n{'=' * 60}")
print(f"Summary: {total_pools} pools, {total_courses_in_pools} courses in pools")
print(f"{'=' * 60}")
