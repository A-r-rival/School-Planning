# -*- coding: utf-8 -*-
"""Verify MBT323 parsing"""
import os
import sys

# Add scripts to path
sys.path.append(os.path.join(os.getcwd(), 'scripts'))
import parse_curriculum as p

def verify():
    filepath = os.path.join(os.getcwd(), 'database', 'Curriculum', 'Fen Fakültesi', 'Moleküler Biyoteknoloji Öğretim Planı.txt')
    print(f"Parsing {filepath}...")
    
    curriculum, pools = p.parse_file(filepath)
    
    # Check Semester 5 for MBT323
    if 5 in curriculum:
        for course in curriculum[5]:
            # course tuple: (code, name, ects, t, u, l)
            if course[0] == 'MBT323':
                print(f"FOUND MBT323: {course}")
                t, u, l = course[3], course[4], course[5]
                expected = (2, 1, 2)
                if (t, u, l) == expected:
                    print("SUCCESS: Hours match 2+1+2")
                else:
                    print(f"FAILURE: Hours mismatch! Got {t}+{u}+{l}")
                return

    print("FAILURE: MBT323 not found in Semester 5")

if __name__ == "__main__":
    verify()
