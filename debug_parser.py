from scripts.parse_curriculum import parse_file
import os

# Path to a curriculum file
filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Curriculum", "Fen Fakültesi", "Enerji Bilimi ve Teknolojileri Öğretim Planı.txt")

try:
    curriculum, pools = parse_file(filepath)
    print("Success!")
    print(f"Curriculum keys: {list(curriculum.keys())}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
