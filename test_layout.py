import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.layout_solver import solve_layout, cp_model
events = [
    {
        'course_data': {
            'course': '[WIN314] Kalite Yönetimi (Teori)',
            'extra': 'Öğretmen: Ahmet\nOda: 101',
            'start_str': '14:00',
            'end_str': '17:00'
        },
        'start_slot': 10,
        'end_slot': 16,
        'base_center': 0.5,
        'col_idx': 0
    }
]
slot_occ = {i: events for i in range(10, 16)}
px_reqs = {
    ('[WIN314] Kalite Yönetimi (Teori)', 'Öğretmen: Ahmet\nOda: 101', '14:00', '17:00'): {
        'code': {'min': 50, 'max': 50},
        'name': {'min': 100, 'max': 150},
        'teacher': {'min': 40, 'max': 60},
        'room': {'min': 30, 'max': 40}
    }
}
try:
    res = solve_layout(events, slot_occ, widget_width=800, px_reqs=px_reqs)
    print("Result:", res is not None)
except Exception as e:
    print("Exception:", e)
