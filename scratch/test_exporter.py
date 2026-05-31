import xlsxwriter

class ExcelExporter:
    @staticmethod
    def export_schedule_to_excel(file_path, schedule_data, assigned_data, unassigned_data):
        workbook = xlsxwriter.Workbook(file_path)
        
        # --- FORMATS ---
        header_format = workbook.add_format({
            'bold': True, 'bg_color': '#4F81BD', 'font_color': 'white',
            'border': 1, 'align': 'center', 'valign': 'vcenter'
        })
        cell_format = workbook.add_format({
            'border': 1, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True
        })
        cell_left = workbook.add_format({
            'border': 1, 'align': 'left', 'valign': 'vcenter', 'text_wrap': True
        })
        
        days = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma"]
        time_slots = []
        start_h, start_m = 8, 30
        for _ in range(18):
            time_slots.append(f"{start_h:02d}:{start_m:02d}")
            start_m += 30
            if start_m >= 60:
                start_m -= 60; start_h += 1
                
        def get_time_index(t_str):
            try:
                h, m = map(int, t_str.split(':'))
                minutes = h * 60 + m
                return (minutes - (8 * 60 + 30)) // 30
            except:
                return -1

        # Pre-process schedule_data
        # item: {'code', 'course_name', 'groups', 'day', 'start', 'end', 'teacher_name', 'classroom_name'}
        
        # --- SHEET 1: TÜM DERSLER ---
        ws_all = workbook.add_worksheet("TÜM DERSLER")
        headers_all = ["Ders Kodu", "Ders Adı", "Şube", "Öğretmen"] + days
        for col, h in enumerate(headers_all):
            ws_all.write(0, col, h, header_format)
            
        ws_all.set_column(0, 0, 15)
        ws_all.set_column(1, 1, 40)
        ws_all.set_column(2, 2, 10)
        ws_all.set_column(3, 3, 25)
        ws_all.set_column(4, 8, 20) # Days
        
        # Combine assigned and unassigned to get full course list
        all_courses = []
        for a in assigned_data:
            # (ders, instance, hoca, teacher_id, ders_kodu)
            all_courses.append({
                'name': a[0], 'instance': a[1], 'teacher': a[2], 'code': a[4] if len(a) > 4 else ""
            })
        for u in unassigned_data:
            all_courses.append({
                'name': u[0], 'instance': u[1], 'teacher': "Atanmamış", 'code': u[2] if len(u) > 2 else ""
            })
            
        # Group schedule by (course_name, teacher) to find their day slots
        course_sched_map = {}
        for item in schedule_data:
            key = (item.get('course_name'), item.get('teacher_name'))
            if key not in course_sched_map:
                course_sched_map[key] = {d: [] for d in days}
            
            d = item.get('day')
            if d in course_sched_map[key]:
                room = item.get('classroom_name') or "Yok"
                time_str = f"{item.get('start')} - {item.get('end')}\n{room}"
                course_sched_map[key][d].append(time_str)

        row = 1
        for c in all_courses:
            ws_all.write(row, 0, c['code'], cell_left)
            ws_all.write(row, 1, c['name'], cell_left)
            ws_all.write(row, 2, f"Şube {c['instance']}", cell_format)
            ws_all.write(row, 3, c['teacher'], cell_left)
            
            # Times
            sched = course_sched_map.get((c['name'], c['teacher']), {})
            for d_idx, day in enumerate(days):
                day_times = sched.get(day, [])
                ws_all.write(row, 4 + d_idx, "\n\n".join(day_times), cell_format)
                
            row += 1

        # --- HELPER TO BUILD GRIDS (BÖLÜMLER, ÖĞRETMENLER, DERSLİKLER) ---
        def build_grid_sheet(sheet_name, entity_key_func, name_func, cell_content_func):
            ws = workbook.add_worksheet(sheet_name)
            
            # We will put each entity in a block. But standard schedule is rows=hours, cols=days
            # To show many entities, we can stack them vertically:
            # Row 1: ENTITY NAME
            # Row 2: Hours -> Pazartesi, Salı, Çarşamba...
            
            # Gather data per entity
            entity_map = {}
            for item in schedule_data:
                e_id = entity_key_func(item)
                if not e_id: continue
                if e_id not in entity_map:
                    entity_map[e_id] = {'name': name_func(item), 'grid': {}}
                
                day = item.get('day')
                start_idx = get_time_index(item.get('start'))
                end_idx = get_time_index(item.get('end'))
                
                if start_idx == -1 or end_idx == -1 or day not in days:
                    continue
                    
                d_idx = days.index(day)
                for i in range(start_idx, end_idx):
                    entity_map[e_id]['grid'][(d_idx, i)] = cell_content_func(item)
                    
            r = 0
            for e_id, e_data in sorted(entity_map.items(), key=lambda x: str(x[1]['name'])):
                # Write Entity Header
                ws.merge_range(r, 0, r, len(days), e_data['name'], header_format)
                r += 1
                
                # Write Days
                ws.write(r, 0, "Saat", header_format)
                for d_idx, day in enumerate(days):
                    ws.write(r, d_idx + 1, day, header_format)
                ws.set_column(1, len(days), 20)
                r += 1
                
                # Write Grid
                for t_idx, time_lbl in enumerate(time_slots):
                    ws.write(r + t_idx, 0, time_lbl, cell_format)
                    for d_idx in range(len(days)):
                        content = e_data['grid'].get((d_idx, t_idx), "")
                        ws.write(r + t_idx, d_idx + 1, content, cell_format)
                        
                r += len(time_slots) + 2 # Add space between entities

        # Sheet 2: BÖLÜMLER / SINIFLAR
        build_grid_sheet(
            "BÖLÜMLER",
            lambda item: item.get('groups'),
            lambda item: item.get('groups') or "Genel Sınıf",
            lambda item: f"{item.get('code') or item.get('course_name')}\n{item.get('classroom_name') or ''}\n{item.get('teacher_name') or ''}"
        )

        # Sheet 3: ÖĞRETMENLER
        build_grid_sheet(
            "ÖĞRETMENLER",
            lambda item: item.get('teacher_name'),
            lambda item: item.get('teacher_name'),
            lambda item: f"{item.get('code') or item.get('course_name')}\n{item.get('classroom_name') or ''}\n{item.get('groups') or ''}"
        )

        # Sheet 4: DERSLİKLER
        build_grid_sheet(
            "DERSLİKLER",
            lambda item: item.get('classroom_name'),
            lambda item: item.get('classroom_name'),
            lambda item: f"{item.get('code') or item.get('course_name')}\n{item.get('teacher_name') or ''}\n{item.get('groups') or ''}"
        )

        workbook.close()
