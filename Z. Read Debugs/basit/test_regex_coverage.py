import re

def test_regex():
    # Current match1 regex (requires number/roman)
    pool_code_regex = re.compile(r'([A-ZİĞÜŞÖÇ0-9_]*SD[A-ZİĞÜŞÖÇ0-9_]*)\s*([IVX]+|\d+)', re.IGNORECASE)
    
    # Match2 regex (handles parentheses, optional number)
    match2_regex = re.compile(r'\((ZSD[IVX]*|SD[IVX]*|ÜSD[IVX]*|HUKSD[0-9]*)\)')

    lines = [
        "| ÜNİVERSİTE SEÇMELİ DERSLER (ÜSD) - KISA LİSTE |",  # Malzeme
        "| HAVUZ 1: SOZSDII/SOZSDIV |",                      # Sosyoloji
        "| ZSD I - 12 AKTS |"                                # Malzeme
    ]

    print("Testing match1 (only):")
    for line in lines:
        match = pool_code_regex.search(line)
        if match:
            print(f"MATCH: '{line.strip()}' -> Groups: {match.groups()}")
        else:
            print(f"NO MATCH: '{line.strip()}'")

    print("\nTesting match2:")
    for line in lines:
        match = match2_regex.search(line)
        if match:
            print(f"MATCH: '{line.strip()}' -> Groups: {match.groups()}")
        else:
            print(f"NO MATCH: '{line.strip()}'")

if __name__ == "__main__":
    test_regex()
