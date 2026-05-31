import re

file_path = r'models/schedule_model.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. get_teacher_schedule
content = re.sub(
    r'def get_teacher_schedule\(self, teacher_id: int\) -> List\[Dict\]:\n(.*?)try:\n(.*?)WHERE dp.ogretmen_id = \?\n(.*?)\n(.*?)self.c.execute\(query, \(teacher_id,\)\)',
    r'def get_teacher_schedule(self, teacher_id: int, versiyon_id: int = None) -> List[Dict]:\n\1if versiyon_id is None:\n            versiyon_id = self.get_active_schedule_version()\n        try:\n\2WHERE dp.ogretmen_id = ? AND dp.versiyon_id = ?\n\3\n\4self.c.execute(query, (teacher_id, versiyon_id))',
    content, flags=re.DOTALL
)

# 2. get_room_schedule
content = re.sub(
    r'def get_room_schedule\(self, room_id: int\) -> List\[Dict\]:\n(.*?)try:\n(.*?)WHERE dp.derslik_id = \?\n(.*?)\n(.*?)self.c.execute\(query, \(room_id,\)\)',
    r'def get_room_schedule(self, room_id: int, versiyon_id: int = None) -> List[Dict]:\n\1if versiyon_id is None:\n            versiyon_id = self.get_active_schedule_version()\n        try:\n\2WHERE dp.derslik_id = ? AND dp.versiyon_id = ?\n\3\n\4self.c.execute(query, (room_id, versiyon_id))',
    content, flags=re.DOTALL
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Done updating script')
