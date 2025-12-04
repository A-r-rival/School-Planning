import re

# Test the regex
pool_code = re.compile(r'([A-ZİĞÜŞÖÇ0-9_]*SD[A-ZİĞÜŞÖÇ0-9_]*?)\s*([IVX0-9]*)', re.IGNORECASE)

test_line = "| SEÇMELİ DERSLER (SD)                                                                            |"

matches = pool_code.findall(test_line)
print(f"Line: {test_line}")
print(f"Matches: {matches}")

for i, m in enumerate(matches):
    print(f"Match {i+1}: Group1='{m[0]}', Group2='{m[1]}'")
    c = m[0].strip()
    if m[1]:
        c = f"{c} {m[1].strip()}"
    c = c.strip()
    print(f"  Combined: '{c}'")
    print(f"  Length: {len(c)}")
    if len(c) > 2:
        print(f"  ✓ WOULD BE ADDED")
    else:
        print(f"  ✗ TOO SHORT")
