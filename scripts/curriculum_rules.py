import re

def is_pool_code_pattern(code):
    """
    Check if a code matches pool code patterns (SD*, ZSD*, ÜSD*, etc.)
    These should not be treated as actual course codes.
    """
    if not code:
        return False
    
    code_upper = code.strip().upper()
    pool_patterns = [
        r'^SD[IVX]*$',           # SD, SDI, SDII, SDIII, SDV, SDVI, SDVII, SDVIII
        r'^ZSD[IVX]*$',          # ZSD, ZSDI, ZSDII, etc.
        r'^ÜSD[IVX]*$',          # ÜSD, ÜSDI, etc.
        r'^HUKSD[0-9]*$',        # HUKSD, HUKSD1, etc.
        r'^POLSD[IVXa-z]*$',     # POLSDI, POLSDV, etc.
        r'^SDBIO[IVXa-z]*$',     # SDBIOI, SDBIOII, etc.
        r'^SDMAT[IVXa-z]*$',     # SDMATI, SDMATII, etc.
        r'^SDP$', r'^SDT$', r'^SDM$',  # Special project/topic/math pools
        r'^USD[0-9]*$',          # USD000, USD001, etc.
    ]
    
    for pattern in pool_patterns:
        if re.match(pattern, code_upper):
            return True
    return False

class Regexes:
    # Matches "1. YARIYIL", "I. YARIYIL", "1. DÖNEM", "I. DÖNEM"
    semester_term = re.compile(r'([IVX]+|\d+)\.\s*(YARIYIL|DÖNEM|SEMESTER|SEMESTIR)', re.IGNORECASE)
    # Matches "1. YIL", "I. YIL"
    year = re.compile(r'([IVX]+|\d+)\.\s*YIL', re.IGNORECASE)
    # Matches "1. GÜZ", "2. BAHAR"
    season = re.compile(r'([IVX]+|\d+)\.\s*(GÜZ|BAHAR)', re.IGNORECASE)
    
    pool_header = re.compile(r'SEÇMELİ DERS|SEÇMELİLER|MODÜL|SD|HAVUZU', re.IGNORECASE)


    pool_code = re.compile(r'([A-ZİĞÜŞÖÇ0-9_]*SD[A-ZİĞÜŞÖÇ0-9_]*)\s*([IVX0-9]+[a-zA-Z]?)?', re.IGNORECASE)
