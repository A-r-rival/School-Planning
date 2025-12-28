import sqlite3
import sys
import os

# Add path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Connect to database
conn = sqlite3.connect('school_schedule.db')
cursor = conn.cursor()

# Test department: Enerji Bilimi (dept_id = 101), Year 4 (7th semester - Fall)
# We'll add 3 elective courses from different pools to same time slot

test_courses = [
    # ZSD Pool - Monday 09:00
    ("ZSD401", "Yenilenebilir Enerji Sistemleri", "Dr. Ahmet Yılmaz", 
     "Pazartesi", "09:00", "10:00", "Derslik-5", 101, 4, "Seçmeli"),
    
    # SD Pool - Monday 09:00 (SAME SLOT!)
    ("SD402", "Enerji Ekonomisi", "Dr. Ayşe Kaya", 
     "Pazartesi", "09:00", "10:00", "Derslik-6", 101, 4, "Seçmeli"),
    
    # ÜSD Pool - Monday 09:00 (SAME SLOT!)
    ("USD403", "Sürdürülebilir Enerji", "Dr. Mehmet Demir", 
     "Pazartesi", "09:00", "10:00", "Derslik-7", 101, 4, "Seçmeli"),
    
    # Another set: Tuesday 10:00
    ("ZSD404", "Rüzgar Enerjisi", "Dr. Fatma Çelik", 
     "Salı", "10:00", "11:00", "Derslik-8", 101, 4, "Seçmeli"),
    
    ("SD405", "Enerji Politikaları", "Dr. Ali Özkan", 
     "Salı", "10:00", "11:00", "Derslik-9", 101, 4, "Seçmeli"),
]

print("Adding test elective courses...")

for code, name, teacher, day, start, end, room, dept, year, dtype in test_courses:
    # Check if exists
    cursor.execute("SELECT COUNT(*) FROM Ders_Programi WHERE ders_kodu = ?", (code,))
    if cursor.fetchone()[0] > 0:
        print(f"  {code} already exists, skipping...")
        continue
    
    # Insert
    cursor.execute("""
        INSERT INTO Ders_Programi 
        (ders_kodu, ders_adi, ogretmen, gun, baslangic, bitis, derslik, bolum_num, sinif_yili, ders_tipi)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (code, name, teacher, day, start, end, room, dept, year, dtype))
    print(f"  Added: {code} - {name}")

conn.commit()
conn.close()

print("\nTest data added successfully!")
print("Now open calendar view for 'Enerji Bilimi ve Teknolojileri', Year 4")
print("Select elective pool checkboxes to see vertical split and colors!")
