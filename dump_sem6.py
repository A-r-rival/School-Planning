
import sys

def dump_sem6():
    filepath = "database/curriculum_data.py"
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(e)
        return

    in_energy = False
    in_sem6 = False
    
    print("--- Scanning Semester 6 ---")
    for i, line in enumerate(lines):
        if '"Enerji Bilimi ve Teknolojileri": {' in line:
            in_energy = True
            
        if in_energy and '"6": [' in line:
            in_sem6 = True
            print(f"Sem 6 Start: Line {i+1}")
            
        if in_energy and in_sem6:
            if '"7": [' in line:
                in_sem6 = False 
                
            if in_sem6:
                if "[" in line and "]" not in line: # Start of a course block?
                     # Rough heuristic to print the block
                     # Print next 6 lines
                     print(f"Block at {i+1}:")
                     for j in range(7):
                         if i+j < len(lines):
                            print(lines[i+j].strip())
                     print("---")

        if in_energy and '},' in line and line.strip() == '},':
            if in_energy:
               in_energy = False

dump_sem6()
