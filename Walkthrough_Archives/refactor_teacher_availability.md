# Technical Walkthrough: Teacher Availability Refactor
**Date:** 2025-12-29
**Related Files:** `views/teacher_availability_view.py`, `models/schedule_model.py`, `controllers/schedule_controller.py`

## 1. Objective
Refactor the "Teacher Availability" module to support two distinct types of constraints:
1. **Specific Time Slots:** "Teacher X is busy on Monday 10:00-12:00".
2. **Day Span Constraints:** "Teacher X wants to come to school max 3 days a week" (Sliding Window constraint).

Additionally, improve the UI stability, user experience (searchable lists, validations), and code maintenance (MVC separation).

---

## 2. Database Changes
No schema changes were required for the *existing* time slots (`Ogretmen_Musaitlik`), but the "Day Span" constraint required the use of the `preferred_day_span` column in the `Ogretmenler` table.

- **Table:** `Ogretmenler`
- **Column:** `preferred_day_span` (INTEGER, Default 0)
- **Zero (0):** No constraint (can be scheduled any day).
- **Value (e.g., 3):** Schedule must fit within a 3-day window.

---

## 3. Model Logic (`ScheduleModel`)

### 3.1. Unified Data Access (`get_combined_availability`)
Previously, we had separate methods for fetching unavailability slots vs. day span info. This led to synchronization issues in the UI. We replaced them with a single `get_combined_availability` method.

**Logic:**
1. Fetch all teachers (sorted Alphabetically).
2. For each teacher, fetch their `preferred_day_span`.
3. For each teacher, fetch their `Ogretmen_Musaitlik` slots.
4. Return a flat list of dictionaries with a `'type'` field to distinguish them.

```python
def get_combined_availability(self, teacher_id=None):
    # ... connection setup ...
    
    # Fetch Spans
    spans = cursor.execute("SELECT id, ad_soyad, preferred_day_span FROM Ogretmenler ...")
    
    # Fetch Slots
    slots = cursor.execute("SELECT ... FROM Ogretmen_Musaitlik ...")
    
    combined_data = []
    
    # 1. Add "Span" Entries
    for t in spans:
        if t['preferred_day_span'] > 0:
            combined_data.append({
                'type': 'span',
                'teacher_id': t['id'],
                'teacher_name': t['ad_soyad'],
                'span_value': t['preferred_day_span']
            })
            
    # 2. Add "Slot" Entries
    for s in slots:
        combined_data.append({
            'type': 'slot',
            'id': s['id'], # Slot ID
            'teacher_id': s['teacher_id'],
            'day': s['gun'],
            'start': s['baslangic'],
            'end': s['bitis'],
            'description': s['description']
        })
        
    return combined_data
```

---

## 4. View Implementation (`TeacherAvailabilityView`)

### 4.1. Add Dialog (`AddUnavailabilityDialog`)
We moved the "Add" logic to a separate modal dialog to declutter the main view.
- **Tabs:** Separated "Günlük Blok" (Day Span) and "Saat Kısıtlaması" (Time Slot) into tabs.
- **Searchable Combo:** Used `QCompleter` to make the teacher dropdown searchable.
- **Safety:** Added `try-except` blocks to prevent crashes during initialization or execution.

### 4.2. Main List Rendering
The main table now renders different rows based on the `'type'` of data.

| Column | Span Row | Slot Row |
| :--- | :--- | :--- |
| **Tip** | "Haftalık Kısıt" | "Namüsaitlik" |
| **Detay** | "{X} Günlük Blok" | "{Gün} {Saat}-{Saat}" |
| **İşlem** | Deletes the constraint (sets to 0) | Deletes the specific slot ID |

**UI Polish:**
- "Tip" column fixed width (130px).
- "İşlem" column fixed width (fit to content).
- Sorting: Teachers appear A-Z.

---

## 5. Controller Logic (`ScheduleController`)

### 5.1. View Lifecycle Management
To prevent crashes when reopening the view, the controller now explicitly manages the view instance.

```python
def open_teacher_availability_view(self):
    # Cleanup old instance if exists
    if hasattr(self, 'availability_view') and self.availability_view:
        self.availability_view.close()
        self.availability_view.deleteLater()
        
    # Create new
    self.availability_view = TeacherAvailabilityView(...)
    self.availability_view.show()
```

### 5.2. Handling Deletion
A unified `handle_delete_request` was essentially created (though implemented via logic separation in View -> Controller calls). The View knows whether it's deleting a 'span' (calls `update_teacher_span`) or a 'slot' (calls `remove_teacher_unavailability`).

---

## 6. Verification Status
- **Functionality:** Confirmed. Validated adding/removing constraints of both types.
- **Stability:** Confirmed. Stress tested with rapid reopening, invalid text inputs, and empty selections.
- **UI/UX:** Confirmed. User approved the visual layout and text changes.
