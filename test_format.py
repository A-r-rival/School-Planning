from collections import defaultdict

def format_classes(rows_regular, rows_pool):
    # data[program_id][bolum_adi] = {
    #     'regular': set(), 
    #     'pools': defaultdict(set)
    # }
    data = defaultdict(lambda: defaultdict(lambda: {'regular': set(), 'pools': defaultdict(set)}))
    
    for pid, bolum, sinif, _ in rows_regular:
        data[pid][bolum]['regular'].add(sinif)
        
    for pid, bolum, sinif, havuz in rows_pool:
        # sinif could be 0, which means "Ortak"
        data[pid][bolum]['pools'][sinif].add(havuz)
        
    result = {}
    for pid, depts in data.items():
        dept_strings = []
        for bolum, info in depts.items():
            regular_classes = sorted(list(info['regular']))
            pools = info['pools']
            
            parts = []
            
            # Format regular classes
            for r_sinif in regular_classes:
                parts.append(f"{r_sinif}. Sınıf")
                
            # Format pools
            if pools:
                pool_parts = []
                for p_sinif in sorted(pools.keys()):
                    pool_codes = ", ".join(sorted(list(pools[p_sinif])))
                    if p_sinif > 0:
                        pool_parts.append(f"{p_sinif}.Sınıf: {pool_codes}")
                    else:
                        pool_parts.append(f"Ortak: {pool_codes}")
                parts.append("(" + " ; ".join(pool_parts) + ")")
                
            if parts:
                dept_strings.append(f"{bolum} {' '.join(parts)}")
                
        result[pid] = ", ".join(dept_strings)
        
    return result

# Test cases
rows_reg = [
    (1, "Bilgisayar Müh", 1, None),
    (2, "Endüstri Müh", 2, None)
]
rows_pool = [
    (1, "Bilgisayar Müh", 3, "SD"),
    (1, "Bilgisayar Müh", 3, "GSD"),
    (1, "Bilgisayar Müh", 4, "ZSD"),
    (2, "Endüstri Müh", 0, "ÜSD")
]

print(format_classes(rows_reg, rows_pool))
