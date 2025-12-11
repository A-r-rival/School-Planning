
# -*- coding: utf-8 -*-
import os
import sys
import random
import sqlite3

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from models.schedule_model import ScheduleModel
from scripts.curriculum_data import DEPARTMENTS_DATA

# Turkish Names and Surnames
NAMES = [
    "Ahmet", "Mehmet", "Mustafa", "Ali", "Hüseyin", "Hasan", "İbrahim", "İsmail", "Osman", "Yusuf",
    "Ömer", "Halil", "Süleyman", "Abdullah", "Mahmut", "Salih", "Kemal", "Ramazan", "Recep", "Murat",
    "Ayşe", "Fatma", "Emine", "Hatice", "Zeynep", "Elif", "Meryem", "Şerife", "Zehra", "Sultan",
    "Hanife", "Merve", "Havva", "Zeliha", "Esra", "Fadime", "Özlem", "Hacer", "Yasemin", "Hülya"
]

SURNAMES = [
    "Yılmaz", "Kaya", "Demir", "Çelik", "Şahin", "Yıldız", "Yıldırım", "Öztürk", "Aydın", "Özdemir",
    "Arslan", "Doğan", "Kılıç", "Aslan", "Çetin", "Kara", "Koç", "Kurt", "Özkan", "Şimşek",
    "Polat", "Özhan", "Korkmaz", "Erdoğan", "Yavuz", "Can", "Acar", "Çakır", "Erkan", "Sönmez", 
    "Taş", "Kocaman", "Bakırcı", "Duran", "Turan", "Uysal", "Yüksel", "Avcı", "Bulut", "Keskin"
]

TITLES = ["Prof. Dr.", "Doç. Dr.", "Dr. Öğr. Üyesi", "Arş. Gör.", "Öğr. Gör."]

DAYS = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma']

TIME_SLOTS = [
    ("09:00", "12:00"),
    ("13:00", "17:00"),
    ("09:00", "10:00"),
    ("10:00", "11:00"),
    ("14:00", "15:00"),
    ("15:00", "16:00")
]

def populate_teachers():
    print("Initializing ScheduleModel...")
    model = ScheduleModel()
    
    # Enable FKs just in case
    model.c.execute("PRAGMA foreign_keys = ON")
    
    # 1. Clear existing teachers/constraints? NO, let's append.
    # But for a clean start on a test DB, you might want to clear. 
    # The user didn't ask to clear, but "create a list" implies populating. 
    # I'll check if table is empty, if so populate. If not, maybe ask or just add more?
    # Let's assume we add if count is low (< 5), otherwise we might duplicate.
    
    model.c.execute("SELECT COUNT(*) FROM Ogretmenler")
    count = model.c.fetchone()[0]
    
    if count > 50:
        print(f"There are already {count} teachers. Skipping population to avoid duplicates.")
        # But we might still want to add constraints if none exist?
        pass
    else:
        print(f"Found {count} teachers. Adding more...")

        departments = list(DEPARTMENTS_DATA.keys())
        if not departments:
            # Fallback if curriculum_data is empty or structure detailed differently
            departments = ["Enerji ve Malzeme Mühendisliği", "Bilgisayar Mühendisliği", "Makine Mühendisliği"]

        created_count = 0
        
        # General pool teachers
        for _ in range(10):
            fn = random.choice(NAMES)
            sn = random.choice(SURNAMES)
            title = random.choice(TITLES)
            
            # Check existence
            model.c.execute("SELECT ogretmen_num FROM Ogretmenler WHERE ad=? AND soyad=?", (fn, sn))
            if model.c.fetchone():
                continue
                
            model.c.execute(
                "INSERT INTO Ogretmenler (ad, soyad, unvan, bolum_adi) VALUES (?, ?, ?, ?)",
                (fn, sn, title, "Genel")
            )
            created_count += 1
            
        # Department specific teachers
        for dept in departments:
            # Add 5-8 teachers per department
            for _ in range(random.randint(5, 8)):
                fn = random.choice(NAMES)
                sn = random.choice(SURNAMES)
                title = random.choice(TITLES)
                
                # Check exist
                model.c.execute("SELECT ogretmen_num FROM Ogretmenler WHERE ad=? AND soyad=?", (fn, sn))
                if model.c.fetchone():
                    continue

                model.c.execute(
                    "INSERT INTO Ogretmenler (ad, soyad, unvan, bolum_adi) VALUES (?, ?, ?, ?)",
                    (fn, sn, title, dept)
                )
                created_count += 1
        
        model.conn.commit()
        print(f"Added {created_count} new teachers.")

    # 2. Add Constraints
    print("Adding unavailability constraints...")
    
    model.c.execute("SELECT ogretmen_num, ad, soyad FROM Ogretmenler")
    all_teachers = model.c.fetchall()
    
    constraint_count = 0
    for t_id, t_name, t_surname in all_teachers:
        # 30% chance to have a constraint
        if random.random() < 0.30:
            # Pick a random day
            day = random.choice(DAYS)
            # Pick a random slot
            slot = random.choice(TIME_SLOTS)
            start, end = slot
            
            success = model.add_teacher_unavailability(t_id, day, start, end)
            if success:
                print(f"Added constraint for {t_name} {t_surname}: {day} {start}-{end}")
                constraint_count += 1
    
    print(f"Total constraints added: {constraint_count}")
    model.close_connections()

if __name__ == "__main__":
    populate_teachers()
