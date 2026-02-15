
import sys

def dump_lines():
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
            if '"7": [' in line:
                in_sem6 = False 
                
            if in_sem6:
                if "ZSD" in line or "Seçmeli" in line or "12" in line:
                    print(f"{i+1}: {line.strip()}")
        
        if in_energy and '},' in line and line.strip() == '},':
            if in_energy: # Only break if we were in energy
               # print(f"Energy End: Line {i+1}")
               in_energy = False

dump_lines()
