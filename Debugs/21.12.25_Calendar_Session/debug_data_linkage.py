import sys
import os
import sqlite3

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.schedule_model import ScheduleModel

def debug_data_linkage():
    print("--- Data Linkage Debug ---")
    model = ScheduleModel()
    
    # 1. Faculties
    print("\n[Faculties]")
    model.c.execute("SELECT fakulte_num, fakulte_adi FROM Fakulteler")
    faculties = model.c.fetchall()
    fac_map = {}
    for f in faculties:
        print(f"  ID: {f[0]}, Name: {f[1]}")
        fac_map[f[0]] = f[1]
        
    # 2. Departments
    print("\n[Departments]")
    model.c.execute("SELECT bolum_id, bolum_adi, fakulte_num FROM Bolumler")
    departments = model.c.fetchall()
    
    fac_counts = {fid: 0 for fid in fac_map.keys()}
    
    for d in departments:
        # print(f"  DeptID: {d[0]}, Name: {d[1]}, FacID: {d[2]}")
        fid = d[2]
        if fid in fac_counts:
            fac_counts[fid] += 1
        else:
            print(f"  !! ORPHAN DEPARTMENT: {d[1]} (FacID: {fid})")
            
    # 3. Report
    print("\n[Linkage Report]")
    for fid, count in fac_counts.items():
        fname = fac_map.get(fid, "UNKNOWN")
        if count == 0:
            print(f"  [EMPTY] Faculty '{fname}' (ID: {fid}) has 0 departments.")
        else:
            print(f"  [OK]    Faculty '{fname}' (ID: {fid}) has {count} departments.")

if __name__ == "__main__":
    debug_data_linkage()
