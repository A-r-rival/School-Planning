import os

filepath = r"c:\Users\taha_\OneDrive\Masaüstü\D.P. Projesi\ders_programi_Antigravity\Curriculum\Fen Fakültesi\Malzeme Bilimi ve Teknolojileri Öğretim Planı.txt"

with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "ZSD II" in line and "AKTS" in line:
        print(f"Line {i+1}:")
        for c in line.strip()[:20]:
            print(f"'{c}' : {ord(c)}")
