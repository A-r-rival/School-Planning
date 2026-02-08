import os
import sqlite3

class IDSeedingService:
    """
    Service to seed Faculty and Department IDs from a configuration file.
    Ensures that IDs are consistent even after database resets.
    """
    
    def __init__(self, conn: sqlite3.Connection, mapping_file: str = "faculty_department_codes.txt"):
        self.conn = conn
        # Resolve mapping_file relative to project root if not absolute
        if not os.path.isabs(mapping_file):
             # Assume project root is parent of parent of this file's dir (models/services/ -> models/ -> root)
             # Wait, models/services/seeder.py -> models/services -> models -> root? No.
             # models/services/seeder.py -> models/services -> models -> root
             # os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
             # But safer to just look for it in CWD if running from root, or relative to this file.
             # The app runs from root usually.
             project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
             self.mapping_file = os.path.join(project_root, mapping_file)
        else:
             self.mapping_file = mapping_file

    def seed(self):
        """
        Reads the mapping file and populates/updates Fakulteler and Bolumler tables.
        """
        if not os.path.exists(self.mapping_file):
            print(f"[SEEDER] Warning: {self.mapping_file} not found. Skipping seeding.")
            return

        print(f"[SEEDER] Seeding from {self.mapping_file}...")
        
        faculty_map = {} # ID -> Name
        dept_map = {}    # Name -> ID
        
        try:
            with open(self.mapping_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"): continue
                    
                    parts = line.split(":")
                    if len(parts) < 3: continue

                    if parts[0] == "F":
                        # F:ID:Name
                        f_id, f_name = int(parts[1]), parts[2]
                        faculty_map[f_id] = f_name
                    elif parts[0] == "D":
                        # D:ID:Name
                        d_id, d_name = int(parts[1]), parts[2]
                        dept_map[d_name] = d_id
            
            with self.conn:
                # 1. Seed Faculties
                for f_id, f_name in faculty_map.items():
                    # Insert or Update name if ID exists
                    self.conn.execute("INSERT OR REPLACE INTO Fakulteler (fakulte_num, fakulte_adi) VALUES (?, ?)", (f_id, f_name))
                
                # 2. Seed Departments
                for dept_name, d_id in dept_map.items():
                    # Determine Faculty ID
                    d_str = str(d_id).zfill(4) # 101 -> 0101
                    f_id = int(d_str[:2])
                    
                    # bolum_num and bolum_id are the same (d_id)
                    # Use INSERT OR IGNORE to avoid overwriting if exists (preserving other fields if any)
                    # But if we want to enforce ID->Name mapping, maybe REPLACE?
                    # The goal is to set IDs. Name logic in populate_students.py was complex (matching DEPARTMENTS_DATA keys).
                    # Here we just have the name from file.
                    # If we just INSERT OR IGNORE, we ensure IDs are reserved.
                    # But Schema requires fakulte_num.
                    
                    self.conn.execute("""
                        INSERT OR REPLACE INTO Bolumler (bolum_id, bolum_num, bolum_adi, fakulte_num) 
                        VALUES (?, ?, ?, ?)
                    """, (d_id, d_id, dept_name, f_id))
                    
            print(f"[SEEDER] ✅ Seeded {len(faculty_map)} Faculties and {len(dept_map)} Departments.")
            
        except Exception as e:
            print(f"[SEEDER] ❌ Error seeding data: {e}")
