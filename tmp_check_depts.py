import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from database import curriculum_data

def check():
    print("Departments inside curriculum_data.py:")
    for k in curriculum_data.DEPARTMENTS_DATA.keys():
        print(" -", k)

if __name__ == "__main__":
    check()
