import re

def parse_bracket(line):
    found_codes = []
    bracket_match = re.search(r'\[(.*?)\]', line)
    if bracket_match:
        inner_text = bracket_match.group(1)
        parts = [p.strip() for p in inner_text.split('/')]
        prefix = ""
        for p in parts:
            prefix_match = re.match(r'^([A-ZİĞÜŞÖÇ_]*SD)', p, re.IGNORECASE)
            if prefix_match:
                prefix = prefix_match.group(1)
                found_codes.append(p)
            else:
                if prefix:
                    if p.startswith(' '):
                        found_codes.append(prefix + p)
                    else:
                        # If p is roman numeral and prefix was 'ZSD ', wait prefix is just 'ZSD'
                        found_codes.append(prefix + p)
                else:
                    found_codes.append(p)
    return found_codes

print(parse_bracket("[SDIa/IIa/III/IV] UYGULAMALI BİLGİSAYAR MÜHENDİSLİĞİ HAVUZU"))
print(parse_bracket("[ZSD I/II/III] ZORUNLU SEÇMELİ DERS"))
print(parse_bracket("[SDP] PROJE HAVUZU"))
