
import sys

def find_lines():
    filepath = "database/curriculum_data.py"
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(e)
        return

    in_energy = False
    in_sem6 = False
    
    for i, line in enumerate(lines):
        if '"Enerji Bilimi ve Teknolojileri": {' in line:
            print(f"Energy Start: Line {i+1}")
            in_energy = True
            
        if in_energy and '"6": [' in line:
            print(f"Energy Semester 6 Start: Line {i+1}")
            in_sem6 = True
            
        if in_energy and in_sem6:
            if '"7": [' in line or '},' in line and line.strip() == '},':
                in_sem6 = False # End of Sem 6 block
                
            if in_sem6:
                if '"ZSDIII",' in line or '12,' in line:
                    print(f"Candidate at Line {i+1}: {line.strip()}")
        
        if in_energy and '},' in line and line.strip() == '},':
            pass

find_lines()
