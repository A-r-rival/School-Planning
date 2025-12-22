# Quick fix script
import re

with open(r"d:\D.P. Projesi\controllers\schedule_controller.py", "r", encoding="utf-8") as f:
    content = f.read()

# Find and replace the student schedule section
old_pattern = r'''                      # Model: \(day, start, end, course, teacher, room, code\)
                      schedule_data = \[\]
                      for item in raw_schedule:
                          if len\(item\) == 7:
                              day, start, end, course, teacher, room, code = item
                              display_course = f"\[{code}\] {course}"
                              extra_info = f"{teacher}\\n{room}"
                              schedule_data\.append\(\(day, start, end, display_course, extra_info\)\)'''

new_text = '''                      # Model: (day, start, end, course, teacher, room, code, type)
                      schedule_data = []
                      for item in raw_schedule:
                          if len(item) == 8:
                              day, start, end, course, teacher, room, code, ders_tipi = item
                              tip_label = ders_tipi if ders_tipi else "?"
                              display_course = f"[{code}] {course} ({tip_label})"
                              extra_info = f"{teacher}\\n{room}"
                              schedule_data.append((day, start, end, display_course, extra_info))
                          elif len(item) == 7:
                              day, start, end, course, teacher, room, code = item
                              display_course = f"[{code}] {course}"
                              extra_info = f"{teacher}\\n{room}"
                              schedule_data.append((day, start, end, display_course, extra_info))'''

content = re.sub(old_pattern, new_text, content, flags=re.MULTILINE)

with open(r"d:\D.P. Projesi\controllers\schedule_controller.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed!")
