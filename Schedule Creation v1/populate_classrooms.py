
import sqlite3
import os
import sys

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir)) # Up one level from 'Schedule Creation v1', then one more? No, check path.
# d:\D.P. Projesi\Schedule Creation v1\populate_classrooms.py
# project root is d:\D.P. Projesi
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from models.schedule_model import ScheduleModel

def populate_classrooms():
    model = ScheduleModel()
    
    # Enable FKs
    model.c.execute("PRAGMA foreign_keys = ON")
    
    # Check existing
    model.c.execute("SELECT COUNT(*) FROM Derslikler WHERE silindi=0")
    count = model.c.fetchone()[0]
    
    if count > 0:
        print(f"Found {count} classrooms. Skipping population.")
        return

    print("Populating classrooms...")
    
    # 1. Amphi-theaters (Large capacity)
    for i in range(1, 6):
        model.derslik_ekle(f"Amfi-{i}", "amfi", 100, "Projeksiyon, Ses Sistemi")
        print(f"Added Amfi-{i}")

    # 2. Classrooms (Medium capacity)
    for i in range(101, 111):
        model.derslik_ekle(f"Derslik-{i}", "amfi", 50, "Projeksiyon")
        print(f"Added Derslik-{i}")

    # 3. Labs
    for i in range(1, 6):
        model.derslik_ekle(f"Lab-{i}", "lab", 30, "Bilgisayar, Ekipman")
        print(f"Added Lab-{i}")

    print("Classroom population complete.")
    model.close_connections()

if __name__ == "__main__":
    populate_classrooms()
