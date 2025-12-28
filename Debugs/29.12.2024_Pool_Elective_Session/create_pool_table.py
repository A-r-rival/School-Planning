# Force table creation by initializing ScheduleModel
import sys
sys.path.insert(0, r'd:\Git_Projects\School-Planning')

from models.schedule_model import ScheduleModel

print("Initializing ScheduleModel to create tables...")
model = ScheduleModel()
print("✅ Tables created successfully!")

# Verify table exists
import sqlite3
conn = sqlite3.connect('okul_veritabani.db')
c = conn.cursor()

c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Ders_Havuz_Iliskisi'")
result = c.fetchone()

if result:
    print(f"✅ Ders_Havuz_Iliskisi table exists!")
    
    # Check schema
    c.execute("PRAGMA table_info(Ders_Havuz_Iliskisi)")
    print("\nTable schema:")
    for col in c.fetchall():
        print(f"  {col[1]} ({col[2]})")
else:
    print("❌ Table not found!")

conn.close()
model.close_connections()
