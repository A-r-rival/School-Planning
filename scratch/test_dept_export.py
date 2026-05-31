        # Inside ExcelExporter.export_schedule_to_excel
        def build_department_sheets():
            # dept_data: { department_name: { category_name: [(course_name, code), ...] } }
            # schedule_data: list of dicts with course_name, code, day, start, end, classroom_name, teacher_name
            
            # Map course_name to its scheduled slots
            # Note: A course could have multiple instances, but schedule_data currently just groups by course_name
            course_sched_map = {}
            for item in schedule_data:
                c_name = item.get('course_name')
                if c_name not in course_sched_map:
                    course_sched_map[c_name] = {d: [] for d in days}
                
                d = item.get('day')
                if d in course_sched_map[c_name]:
                    room = item.get('classroom_name') or "Yok"
                    time_str = f"{item.get('start')} - {item.get('end')}\n{room}"
                    course_sched_map[c_name][d].append(time_str)
            
            # Header Format for Departments
            dept_header_format = workbook.add_format({
                'bold': True, 'bg_color': '#D9D9D9', 'border': 1, 'align': 'center', 'valign': 'vcenter'
            })
            group_header_format = workbook.add_format({
                'bold': True, 'bg_color': '#FCE4D6', 'border': 1, 'align': 'center', 'valign': 'vcenter'
            })
            
            for dept_name, categories in sorted(dept_data.items()):
                # Create a sheet for this department. Sheet names max 31 chars
                sheet_name = dept_name[:31]
                ws = workbook.add_worksheet(sheet_name)
                
                # Column widths
                ws.set_column(0, 0, 15)  # Kod (internal)
                ws.set_column(1, 1, 15)  # Ders Kodu
                ws.set_column(2, 2, 40)  # Ders Adı
                ws.set_column(3, 7, 20)  # Pazartesi - Cuma
                
                r = 0
                for cat_name, courses in sorted(categories.items()):
                    # Draw Category Header
                    ws.merge_range(r, 0, r, 7, cat_name, group_header_format)
                    r += 1
                    
                    # Draw Column Headers
                    headers = ["Kod", "Ders Kodu", "Ders Adı"] + days
                    for col, h in enumerate(headers):
                        ws.write(r, col, h, dept_header_format)
                    r += 1
                    
                    # Draw courses
                    for c_name, c_code in courses:
                        # Write fixed cols
                        ws.write(r, 0, c_code, cell_format)
                        ws.write(r, 1, c_code, cell_format) # The user image has Kod and Ders Kodu, often same or similar
                        ws.write(r, 2, c_name, cell_left)
                        
                        # Write days
                        sched = course_sched_map.get(c_name, {})
                        for d_idx, day in enumerate(days):
                            day_times = sched.get(day, [])
                            ws.write(r, 3 + d_idx, "\n".join(day_times), cell_format)
                        r += 1
