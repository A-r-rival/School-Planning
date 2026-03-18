from models.schedule_model import ScheduleModel
model = ScheduleModel()
c = model.c

# 1. Room capacities grouped by room type (Derslik_Tipi)
c.execute('''
    SELECT d.derslik_tipi, MAX(d.kapasite), MIN(d.kapasite), ROUND(AVG(d.kapasite), 1), COUNT(d.derslik_num)
    FROM Derslikler d
    WHERE d.silindi = 0
    GROUP BY d.derslik_tipi
''')
rooms = c.fetchall()

print('\n--- ODA KAPASİTELERİ (Tipe Göre) ---')
print(f"| {'Oda Tipi':<15} | {'Min Kap.':<10} | {'Max Kap.':<10} | {'Ortalama':<9} | {'Adet':<6} |")
print('-' * 65)
for r in rooms:
    print(f"| {r[0]:<15} | {r[2]:<10} | {r[1]:<10} | {r[3]:<9} | {r[4]:<6} |")

from controllers.scheduler_services import SchedulableCourseBuilder
builder = SchedulableCourseBuilder(model)
physical_courses = builder.build()

print('\n--- OLUŞTURULAN DERS BLOKLARI KAPASİTE ANALİZİ ---')
sizes = [c.get('student_count', 0) for c in physical_courses]
if sizes:
    print(f"Toplam Fiziksel Ders Bloğu: {len(sizes)}")
    print(f"Minimum Öğrenci Sayısı (Bir Sınıf): {min(sizes)}")
    print(f"Maksimum Öğrenci Sayısı (Bir Sınıf): {max(sizes)}")
    print(f"Ortalama Öğrenci Sayısı: {round(sum(sizes)/len(sizes), 1)}")
    
    # Check what doesn't fit in the max generic room (70)
    max_room_cap = max([r[1] for r in rooms])
    oversized = [c for c in physical_courses if c.get('student_count', 0) > max_room_cap]
    print(f"\n{max_room_cap} kapasiteli en büyük odadan BÜYÜK olan ders blokları ({len(oversized)} adet):")
    
    # Group by base name for readability if there are many
    oversized.sort(key=lambda x: x.get('student_count', 0), reverse=True)
    for c in oversized[:15]:
        print(f"  - {c['name']} (Süre: {c['duration']}, Öğrenci: {c.get('student_count', 0)})")
    if len(oversized) > 15:
        print(f"  ... ve {len(oversized) - 15} ders daha.")
else:
    print("Hiç ders bulunamadı.")
