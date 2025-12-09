import sys
sys.path.insert(0, 'scripts')

from parse_curriculum import parse_file

# Test the Mechanical Engineering file
filepath = "Curriculum/Mühendislik Fakültesi/Makine Müh Öğretim Planı.txt"
print("Parsing file:", filepath)
print("="*80)

curriculum, pools, _ = parse_file(filepath)

print("\nChecking for SDUx code in curriculum:")
found_sdux = False
for semester, courses in curriculum.items():
    for code, name, ects in courses:
        if code == 'SDUx':
            print(f"  Found SDUx in Semester {semester}: {name} ({ects} AKTS)")
            found_sdux = True

if not found_sdux:
    print("  ERROR: SDUx NOT found in any semester!")

print("\nChecking pools for SDU suffixes:")
for pool_code in sorted(pools.keys()):
    if pool_code.startswith('SDU'):
        print(f"  Found pool: {pool_code} with {len(pools[pool_code])} courses")
