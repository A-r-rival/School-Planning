
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
    in_sem5 = False
    
    for i, line in enumerate(lines):
        if '"Enerji Bilimi ve Teknolojileri": {' in line:
            in_energy = True
            
        if in_energy and '"5": [' in line: # Changed to 5
            print(f"Energy Semester 5 Start: Line {i+1}")
            in_sem5 = True
            
        if in_energy and in_sem5:
            if '"6": [' in line: # Ends at 6
                in_sem5 = False 
                
            if in_sem5:
                if "ZSD" in line or "Seçmeli" in line or "12" in line:
                    print(f"{i+1}: {line.strip()}")
        
        if in_energy and '},' in line and line.strip() == '},':
            if in_energy:
               in_energy = False

dump_lines()
