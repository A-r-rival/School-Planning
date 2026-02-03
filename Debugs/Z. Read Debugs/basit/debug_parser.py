from scripts.parse_curriculum import parse_file
import os

# Path to a curriculum file
filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Curriculum", "Fen Fakültesi", "Enerji Bilimi ve Teknolojileri Öğretim Planı.txt")

try:
    curriculum, pools, match_counts = parse_file(filepath)
    print("Success!")
    print(f"Curriculum keys: {list(curriculum.keys())}")
    print(f"Pool keys: {list(pools.keys())}")
    print(f"Match counts (match2, match3, match4): {match_counts}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
