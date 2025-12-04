import json
import os
import sys

# Add scripts dir to path to import curriculum_data
sys.path.append(os.path.join(os.getcwd(), 'scripts'))

try:
    import curriculum_data
    print("Keys in DEPARTMENTS_DATA:")
    for key in curriculum_data.DEPARTMENTS_DATA.keys():
        print(f"- {key}")
    
    if "Sosyoloji" in curriculum_data.DEPARTMENTS_DATA:
        print("\nSosyoloji Pools:")
        pools = curriculum_data.DEPARTMENTS_DATA["Sosyoloji"]["pools"]
        for pool_code in pools:
            print(f"- {pool_code}: {len(pools[pool_code])} courses")
    else:
        print("\nERROR: 'Sosyoloji' key not found in data!")

except ImportError:
    print("Could not import curriculum_data.py. Checking file content manually...")
    with open('scripts/curriculum_data.py', 'r', encoding='utf-8') as f:
        content = f.read()
        if "Sosyoloji" in content:
            print("'Sosyoloji' string FOUND in file.")
        else:
            print("'Sosyoloji' string NOT FOUND in file.")
