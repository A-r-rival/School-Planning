
import os

fname = "final_debug_2.txt"
if os.path.exists(fname):
    print(f"Reading {fname}...")
    with open(fname, "rb") as f:
        content = f.read().decode('utf-8', errors='ignore')
        
    for line in content.splitlines():
        if "Status" in line or "INFEASIBLE" in line or "CRITICAL" in line:
            print(line)
        if "Teacher 73" in line: # Debug context
            print(line)
else:
    print("File not found.")
