def build_master_grid_sheet(ws_name, id_func, name_func, cell_content_func, schedule_data, days, time_slots):
    entities = {} # id -> name
    for item in schedule_data:
        e_id = id_func(item)
        e_name = name_func(item)
        if e_id and e_name:
            entities[e_id] = e_name
    
    sorted_entities = sorted(entities.items(), key=lambda x: str(x[1]))
    
    grid_data = {}
    for item in schedule_data:
        e_id = id_func(item)
        if not e_id: continue
        
        day = item.get('day')
        # Simulate get_time_index
        start_idx = 0 # Dummy
        end_idx = 2   # Dummy
        
        d_idx = days.index(day)
        for i in range(start_idx, end_idx):
            key = (e_id, d_idx, i)
            if key not in grid_data:
                grid_data[key] = []
            grid_data[key].append(cell_content_func(item))
            
    print(f"Creating {ws_name} with {len(sorted_entities)} rows and {len(days)*len(time_slots)} cols")
    
if __name__ == "__main__":
    days = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma"]
    time_slots = [f"{8+i//2:02d}:{30 if i%2==0 else 0:02d}" for i in range(18)]
    data = [
        {"teacher_name": "Ahmet Hoca", "day": "Pazartesi", "code": "MEC101"},
        {"teacher_name": "Mehmet Hoca", "day": "Salı", "code": "ENG101"}
    ]
    build_master_grid_sheet("ÖĞR", lambda x: x['teacher_name'], lambda x: x['teacher_name'], lambda x: x['code'], data, days, time_slots)
