from scripts.parse_curriculum import parse_file
import os

# Path to a curriculum file
filepath = r"c:\Users\taha_\OneDrive\Masaüstü\D.P. Projesi\ders_programi_Antigravity\Curriculum\Fen Fakültesi\Enerji Bilimi ve Teknolojileri Öğretim Planı.txt"

try:
    curriculum, pools = parse_file(filepath)
    print("Success!")
    print(f"Curriculum keys: {list(curriculum.keys())}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
