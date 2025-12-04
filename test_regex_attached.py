import re

def test_regex():
    # Greedy regex with spaces (original)
    regex = re.compile(r'\s*([A-ZİĞÜŞÖÇ0-9_]*SD[A-ZİĞÜŞÖÇ0-9_]*)\s*([IVX]+|\d+)\s*', re.IGNORECASE)
    
    cases = [
        "SOZSDI",
        "SOZSDII",
        "SDBIOIV",
        "SDMATI",
        "ZSD I",
        "HUKSD5",
        "SOZSDIV"
    ]

    print("Testing non-greedy regex:")
    for case in cases:
        match = regex.search(case)
        if match:
            print(f"MATCH: '{case}' -> Code: '{match.group(1)}', Suffix: '{match.group(2)}'")
        else:
            print(f"NO MATCH: '{case}'")

if __name__ == "__main__":
    test_regex()
