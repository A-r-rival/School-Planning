# Fix indentation in schedule_controller.py
with open(r'd:\D.P. Projesi\controllers\schedule_controller.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Fix lines 612-628 with proper indentation
fixed_section = '''                          if len(item) == 8:
                              day, start, end, course, teacher, room, code, ders_tipi = item
                              tip_label = ders_tipi if ders_tipi else "?"
                              display_course = f"[{code}] {course} ({tip_label})"
                              extra_info = f"{teacher}\\n{room}"
                              schedule_data.append((day, start, end, display_course, extra_info))
                          elif len(item) == 7:
                              day, start, end, course, teacher, room, code = item
                              display_course = f"[{code}] {course}"
                              extra_info = f"{teacher}\\n{room}"
                              schedule_data.append((day, start, end, display_course, extra_info))
                          elif len(item) == 6: # Legacy/Fallback
                              day, start, end, course, teacher, room = item
                              extra_info = f"{teacher}\\n{room}"
                              schedule_data.append((day, start, end, course, extra_info))
                          else:
                              schedule_data.append(item)
'''

# Replace lines 612-628 (0-indexed 611-627)
lines[611:628] = [fixed_section]

with open(r'd:\D.P. Projesi\controllers\schedule_controller.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Indentation fixed!")
