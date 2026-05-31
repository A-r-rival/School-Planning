import os
import csv
from datetime import datetime
try:
    import xlsxwriter
except ImportError:
    xlsxwriter = None

class ExcelExporter:
    @staticmethod
    def export_assignments_to_excel(file_path, assigned_data, unassigned_data):
        """
        Exports teacher assignments to an Excel file with hyperlinked sheets.
        assigned_data: list of tuples (ders, instance, hoca, teacher_id, ders_kodu)
        unassigned_data: list of tuples (ders, instance, ders_kodu)
        """
        if not xlsxwriter:
            raise ImportError("xlsxwriter kütüphanesi kurulu değil. Lütfen 'pip install xlsxwriter' komutunu çalıştırın.")

        workbook = xlsxwriter.Workbook(file_path)
        
        # Formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4F81BD',
            'font_color': 'white',
            'border': 1
        })
        link_format = workbook.add_format({
            'font_color': 'blue',
            'underline': 1
        })
        cell_format = workbook.add_format({'border': 1})
        
        # Master Sheet
        ws_master = workbook.add_worksheet("Tüm Atamalar")
        headers = ["Ders Kodu", "Ders Adı", "Şube", "Öğretmen", "Durum"]
        for col, header in enumerate(headers):
            ws_master.write(0, col, header, header_format)
            
        ws_master.set_column(0, 0, 15)
        ws_master.set_column(1, 1, 40)
        ws_master.set_column(2, 2, 10)
        ws_master.set_column(3, 3, 30)
        ws_master.set_column(4, 4, 15)

        # Process data
        teachers_dict = {} # teacher_name -> list of courses
        
        row = 1
        for item in assigned_data:
            course_name = item[0]
            instance = item[1]
            hoca = item[2]
            teacher_id = item[3] if len(item) > 3 else None
            course_code = item[4] if len(item) > 4 else ""
            
            if hoca not in teachers_dict:
                teachers_dict[hoca] = []
            teachers_dict[hoca].append(item)
            
            ws_master.write(row, 0, course_code, cell_format)
            ws_master.write(row, 1, course_name, cell_format)
            ws_master.write(row, 2, f"Şube {instance}", cell_format)
            
            # Create a hyperlink to the teacher's sheet if it's a valid teacher name
            safe_sheet_name = "".join([c for c in hoca if c.isalnum() or c in (' ', '_')]).strip()[:31]
            if safe_sheet_name:
                ws_master.write_url(row, 3, f"internal:'{safe_sheet_name}'!A1", string=hoca, cell_format=link_format)
            else:
                ws_master.write(row, 3, hoca, cell_format)
                
            ws_master.write(row, 4, "Atandı", cell_format)
            row += 1
            
        for item in unassigned_data:
            course_name = item[0]
            instance = item[1]
            course_code = item[2] if len(item) > 2 else ""
            
            ws_master.write(row, 0, course_code, cell_format)
            ws_master.write(row, 1, course_name, cell_format)
            ws_master.write(row, 2, f"Şube {instance}", cell_format)
            ws_master.write(row, 3, "-", cell_format)
            ws_master.write(row, 4, "Atanmamış", cell_format)
            row += 1

        # Individual Teacher Sheets
        for hoca, courses in teachers_dict.items():
            safe_sheet_name = "".join([c for c in hoca if c.isalnum() or c in (' ', '_')]).strip()[:31]
            if not safe_sheet_name:
                continue
                
            try:
                ws_teacher = workbook.add_worksheet(safe_sheet_name)
            except Exception:
                continue # In case of duplicate or invalid name
                
            ws_teacher.write(0, 0, "Ders Kodu", header_format)
            ws_teacher.write(0, 1, "Ders Adı", header_format)
            ws_teacher.write(0, 2, "Şube", header_format)
            
            ws_teacher.set_column(0, 0, 15)
            ws_teacher.set_column(1, 1, 40)
            ws_teacher.set_column(2, 2, 10)
            
            ws_teacher.write_url(0, 4, "internal:'Tüm Atamalar'!A1", string="Ana Sayfaya Dön", cell_format=link_format)
            
            t_row = 1
            for item in courses:
                c_name = item[0]
                c_inst = item[1]
                c_code = item[4] if len(item) > 4 else ""
                
                ws_teacher.write(t_row, 0, c_code, cell_format)
                ws_teacher.write(t_row, 1, c_name, cell_format)
                ws_teacher.write(t_row, 2, f"Şube {c_inst}", cell_format)
                t_row += 1

    @staticmethod
    def export_schedule_to_excel(file_path, schedule_data, assigned_data, unassigned_data, dept_data=None):
        if not xlsxwriter:
            raise ImportError("xlsxwriter kütüphanesi kurulu değil. Lütfen 'pip install xlsxwriter' komutunu çalıştırın.")

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
        
        all_courses = []
        for a in assigned_data:
            all_courses.append({
                'name': a[0], 'instance': a[1], 'teacher': a[2], 'code': a[4] if len(a) > 4 else ""
            })
        for u in unassigned_data:
            all_courses.append({
                'name': u[0], 'instance': u[1], 'teacher': "Atanmamış", 'code': u[2] if len(u) > 2 else ""
            })
            
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
            
            sched = course_sched_map.get((c['name'], c['teacher']), {})
            for d_idx, day in enumerate(days):
                day_times = sched.get(day, [])
                ws_all.write(row, 4 + d_idx, "\n\n".join(day_times), cell_format)
                
            row += 1

        # --- HELPER TO BUILD GRIDS (BÖLÜMLER, ÖĞRETMENLER, DERSLİKLER) ---
        def build_grid_sheet(sheet_name, entity_key_func, name_func, cell_content_func):
            ws = workbook.add_worksheet(sheet_name)
            
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
                ws.merge_range(r, 0, r, len(days), e_data['name'], header_format)
                r += 1
                
                ws.write(r, 0, "Saat", header_format)
                for d_idx, day in enumerate(days):
                    ws.write(r, d_idx + 1, day, header_format)
                ws.set_column(1, len(days), 20)
                r += 1
                
                for t_idx, time_lbl in enumerate(time_slots):
                    ws.write(r + t_idx, 0, time_lbl, cell_format)
                    for d_idx in range(len(days)):
                        content = e_data['grid'].get((d_idx, t_idx), "")
                        ws.write(r + t_idx, d_idx + 1, content, cell_format)
                        
                r += len(time_slots) + 2

        # --- HELPER TO BUILD MASTER GRIDS (Genel Takvim) ---
        def build_master_grid_sheet(sheet_name, entity_key_func, name_func, cell_content_func):
            try:
                ws = workbook.add_worksheet(sheet_name[:31])
            except Exception:
                return

            entities = {}
            for item in schedule_data:
                e_id = entity_key_func(item)
                e_name = name_func(item)
                if e_id and e_name:
                    entities[e_id] = e_name
            
            sorted_entities = sorted(entities.items(), key=lambda x: str(x[1]))
            if not sorted_entities: return
            
            grid_data = {}
            for item in schedule_data:
                e_id = entity_key_func(item)
                if not e_id: continue
                
                day = item.get('day')
                start_idx = get_time_index(item.get('start'))
                end_idx = get_time_index(item.get('end'))
                
                if start_idx == -1 or end_idx == -1 or day not in days:
                    continue
                
                d_idx = days.index(day)
                for i in range(start_idx, end_idx):
                    key = (e_id, d_idx, i)
                    if key not in grid_data:
                        grid_data[key] = []
                    grid_data[key].append(cell_content_func(item))
            
            header_main = workbook.add_format({'bold': True, 'bg_color': '#4F81BD', 'font_color': 'white', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
            header_day = workbook.add_format({'bold': True, 'bg_color': '#D9D9D9', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
            header_time = workbook.add_format({'bold': True, 'border': 1, 'align': 'center', 'valign': 'vcenter'})
            cell_filled = workbook.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'bg_color': '#E2EFDA', 'font_size': 9})
            cell_empty = workbook.add_format({'border': 1})
            
            ws.write(0, 0, "İsim", header_main)
            ws.write(1, 0, "", header_main)
            ws.set_column(0, 0, 25)
            
            col = 1
            for d_idx, day in enumerate(days):
                ws.merge_range(0, col, 0, col + len(time_slots) - 1, day, header_day)
                for t_idx, time_lbl in enumerate(time_slots):
                    short_time = time_lbl.split(' - ')[0]
                    ws.write(1, col, short_time, header_time)
                    ws.set_column(col, col, 10)
                    col += 1
            
            ws.freeze_panes(2, 1) # Keep headers visible
            
            row = 2
            for e_id, e_name in sorted_entities:
                ws.write(row, 0, e_name, cell_left)
                col = 1
                for d_idx in range(len(days)):
                    for t_idx in range(len(time_slots)):
                        contents = grid_data.get((e_id, d_idx, t_idx), [])
                        if contents:
                            # Unique non-empty items
                            c_list = list(dict.fromkeys([c for c in contents if c]))
                            ws.write(row, col, "\n".join(c_list), cell_filled)
                        else:
                            ws.write(row, col, "", cell_empty)
                        col += 1
                row += 1

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

        # Department / Class Sheets (List format with merged class headers)
        if dept_data:
            dept_header_format = workbook.add_format({
                'bold': True, 'bg_color': '#D9D9D9', 'border': 1, 'align': 'center', 'valign': 'vcenter'
            })
            group_header_format = workbook.add_format({
                'bold': True, 'bg_color': '#FCE4D6', 'border': 1, 'align': 'center', 'valign': 'vcenter'
            })
            
            for dept_name, categories in sorted(dept_data.items()):
                # Create a sheet for this department. Sheet names max 31 chars
                # Replace invalid chars just in case
                safe_name = dept_name.replace(":", "").replace("/", "").replace("\\", "").replace("?", "").replace("*", "").replace("[", "").replace("]", "")
                sheet_name = safe_name[:31].strip()
                try:
                    ws_dept = workbook.add_worksheet(sheet_name)
                except Exception:
                    continue # Ignore duplicate or invalid sheet names
                
                # Column widths
                ws_dept.set_column(0, 0, 15)  # Kod
                ws_dept.set_column(1, 1, 15)  # Ders Kodu
                ws_dept.set_column(2, 2, 40)  # Ders Adı
                ws_dept.set_column(3, 7, 20)  # Pazartesi - Cuma
                
                r = 0
                # Sort categories: 1. Sınıf, 2. Sınıf, etc. first, then SD/ZSD
                def sort_cat(cat):
                    if "Sınıf" in cat: return (0, cat)
                    return (1, cat)
                    
                for cat_name, courses in sorted(categories.items(), key=lambda x: sort_cat(x[0])):
                    if not courses: continue
                    # Draw Category Header
                    ws_dept.merge_range(r, 0, r, 7, cat_name, group_header_format)
                    r += 1
                    
                    # Draw Column Headers
                    headers = ["Kod", "Ders Kodu", "Ders Adı"] + days
                    for col, h in enumerate(headers):
                        ws_dept.write(r, col, h, dept_header_format)
                    r += 1
                    
                    # Draw courses
                    for c_name, c_code in courses:
                        # Write fixed cols
                        ws_dept.write(r, 0, c_code, cell_format)
                        ws_dept.write(r, 1, c_code, cell_format)
                        ws_dept.write(r, 2, c_name, cell_left)
                        
                        # Write days
                        sched = course_sched_map.get((c_name, ""), {})
                        if not sched: # fallback try searching without teacher
                            for k_cname, k_teacher in course_sched_map.keys():
                                if k_cname == c_name:
                                    sched = course_sched_map[(k_cname, k_teacher)]
                                    break
                                    
                        for d_idx, day in enumerate(days):
                            day_times = sched.get(day, [])
                            ws_dept.write(r, 3 + d_idx, "\n\n".join(day_times), cell_format)
                        r += 1

        # Master Grid Sheets
        build_master_grid_sheet(
            "Genel Takvim (Öğr)",
            lambda item: item.get('teacher_name'),
            lambda item: item.get('teacher_name'),
            lambda item: item.get('code') or item.get('course_name')
        )
        
        build_master_grid_sheet(
            "Genel Takvim (Derslik)",
            lambda item: item.get('classroom_name'),
            lambda item: item.get('classroom_name'),
            lambda item: item.get('code') or item.get('course_name')
        )

        workbook.close()

    @staticmethod
    def export_assignments_to_csv(file_path, assigned_data, unassigned_data):
        """
        Exports teacher assignments to a CSV file.
        """
        with open(file_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["Ders Kodu", "Ders Adı", "Şube", "Öğretmen", "Durum"])
            
            for item in assigned_data:
                course_name = item[0]
                instance = item[1]
                hoca = item[2]
                course_code = item[4] if len(item) > 4 else ""
                writer.writerow([course_code, course_name, f"Şube {instance}", hoca, "Atandı"])
                
            for item in unassigned_data:
                course_name = item[0]
                instance = item[1]
                course_code = item[2] if len(item) > 2 else ""
                writer.writerow([course_code, course_name, f"Şube {instance}", "-", "Atanmamış"])
