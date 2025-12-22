import sys

# Read the file
with open(r'd:\D.P. Projesi\controllers\schedule_controller.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find and fix line 612
for i in range(len(lines)):
    if i == 611 and 'if len(item) == 7:' in lines[i]:  # Line 612 (0-indexed is 611)
        # Insert new lines before this
        indent = '                          '
        new_lines = [
            indent + 'if len(item) == 8:\n',
            indent + '    day, start, end, course, teacher, room, code, ders_tipi = item\n',
            indent + '    tip_label = ders_tipi if ders_tipi else "?"\n',
            indent + '    display_course = f"[{code}] {course} ({tip_label})"\n',
            indent + '    extra_info = f"{teacher}\\n{room}"\n',
            indent + '    schedule_data.append((day, start, end, display_course, extra_info))\n',
            indent + 'elif len(item) == 7:\n',
        ]
        lines[i] = ''.join(new_lines)
        # Also update comment on line 609
        if i >= 2 and '# Model:' in lines[i-2]:
            lines[i-2] = indent[:-10] + '# Model: (day, start, end, course, teacher, room, code, type)\n'
        break

# Write back
with open(r'd:\D.P. Projesi\controllers\schedule_controller.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("File fixed successfully!")
