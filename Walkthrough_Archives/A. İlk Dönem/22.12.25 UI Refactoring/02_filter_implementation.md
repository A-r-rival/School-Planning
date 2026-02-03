# detailed_filter_implementation_walkthrough

# Advanced Filtering Implementation Walkthrough

## 1. Introduction & Objectives

The goal was to transform the Course List from a static view into a dynamic, queryable tool. The user needed to filter courses by:
1.  **Faculty & Department:** (Existing basic implementation)
2.  **Year (Class Level):** e.g., "1. Sınıf"
3.  **Day:** e.g., "Pazartesi" (New Requirement)
4.  **Free Text:** Search by Course Name or Teacher Name (New Requirement)

This required changes across the full MVC stack: Model (Database queries), View (Filter widgets), and Controller (Filtering logic).

---

## 2. Model Updates (`schedule_model.py`)

To support filtering by Day and showing Teacher names, we could no longer rely on the `Dersler` (Curriculum) table alone, as it doesn't contain schedule info (Time/Day). We shifted to querying the `Ders_Programi` table.

### 2.1 Refactoring Queries

We updated `get_courses_by_faculty` and `get_courses_by_department` to perform complex joins.

**The SQL Query Structure:**
```sql
SELECT 
    dp.ders_adi, 
    GROUP_CONCAT(DISTINCT d.ders_kodu), -- Merge codes (e.g. CEN101, MCE101)
    (o.ad || ' ' || o.soyad) as hoca,   -- Concatenate Teacher Name
    dp.gun, 
    dp.baslangic, 
    dp.bitis
FROM Ders_Programi dp
JOIN Dersler d ON ... 
-- Join hierarchies (Ders -> Ders_Sinif -> Ogrenci_Donemleri -> Bolumler) to filter by Faculty/Dept
LEFT JOIN Ogretmenler o ON dp.ogretmen_id = o.ogretmen_num
WHERE b.fakulte_num = ? 
  AND dp.gun = ?  -- Optional Day Filter
  AND od.sinif_duzeyi = ? -- Optional Year Filter
GROUP BY dp.gun, ... -- Group to prevent duplicate rows for same course
```

### 2.2 Standardizing String Output

To make text filtering easy in the Controller, we standardized the string output format. This "Contract" allows the controller to reliably parse or search the string.

**Format:** `[CODE] Name - Teacher (Day Time)`

```python
    # Python Model Code
    def get_courses_by_faculty(self, faculty_id, year=None, day=None):
        # ... execute query ...
        result = []
        for r in rows:
            ders_adi = r[0]
            codes = r[1]
            hoca = r[2] if r[2] else "Belirsiz"
            gun = r[3]
            saat = f"{r[4]}-{r[5]}"
            
            # THE FORMAT
            result.append(f"[{codes}] {ders_adi} - {hoca} ({gun} {saat})")
        return result
```

---

## 3. View Updates (`schedule_view.py`)

We added new widgets to the filter bar in `_create_course_list`.

### 3.1 New Widgets

```python
    # Day Filter
    self.filter_day = QComboBox()
    self.filter_day.addItem("Tüm Günler", None) # Data is None for "All"
    self.filter_day.addItems(["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma"])
    self.filter_day.currentIndexChanged.connect(self._on_filter_changed)
    
    # Text Search Inputs
    self.search_input = QLineEdit()
    self.search_input.setPlaceholderText("🔍 Ders Ara...")
    
    self.search_teacher = QLineEdit()
    self.search_teacher.setPlaceholderText("👨‍🏫 Hoca Ara...")
```

### 3.2 Signal Logic

The `_on_filter_changed` method gathers all filter states into a dictionary. A key improvement here was handling the "None" state for dropdowns.

```python
    def _on_filter_changed(self):
        filters = {
            "faculty_id": self.filter_faculty.currentData(),
            # ...
            # Fix: Only include 'day' if not "Tüm Günler" (index 0)
            "day": self.filter_day.currentText() if self.filter_day.currentIndex() > 0 else None,
            "search_text": self.search_input.text(),
            "teacher_text": self.search_teacher.text()
        }
        self.filter_changed.emit(filters)
```

---

## 4. Controller Logic (`schedule_controller.py`)

The controller acts as the brain, orchestrating the multi-stage filtering process.

### 4.1 Stage 1: Database Filtering

First, we fetch the "Shortlist" from the database based on structural filters (Faculty, Dept, Year, Day). This is efficient as it uses SQL indexes.

```python
    def handle_schedule_view_filter(self, filters):
        # ... logic to determine which Model method to call ...
        
        if faculty_id:
             courses = self.model.get_courses_by_faculty(faculty_id, year, day)
        else:
             # Case: No Faculty Selected ("Show All")
             all_courses = self.model.get_all_courses()
             
             # Special Case: Filtering "All Courses" by Day
             # Since get_all_courses doesn't take parameters (design decision),
             # we filter this specific case in Python.
             if day:
                 courses = [c for c in all_courses if f"({day}" in c]
             else:
                 courses = all_courses
```

**Debug Highlight:**
We initially had a bug where selecting "Tüm Günler" caused the list to go blank.
*   **Cause:** The view was sending `"Tüm Günler"` string instead of `None`. The logic tried to find "Tüm Günler" in the course string.
*   **Fix:** Updated View to send `None` when index is 0. Updated Controller to check `if day:` before filtering.

### 4.2 Stage 2: Client-Side Text Filtering

After getting the structural list, we refine it further with the text inputs. This happens in Python.

```python
        # 3. Apply Text Filters
        search_text = filters.get("search_text", "").lower()
        teacher_text = filters.get("teacher_text", "").lower()
        
        if search_text or teacher_text:
            filtered_courses = []
            for course_str in courses:
                # Check Course Name/Code
                if search_text and search_text not in course_str.lower():
                    continue
                    
                # Check Teacher Name
                # Because we formatted the string as "... - Teacher Name ...",
                # simple string inclusion works perfect here.
                if teacher_text and teacher_text not in course_str.lower():
                     continue
                
                filtered_courses.append(course_str)
            courses = filtered_courses

        self.view.display_courses(courses)
```

---

## 5. Verification

We verified the implementation by:
1.  **Scenario A:** Select "Engineering Faculty" -> "Computer Dept" -> "Monday".
    *   *Result:* Only Monday courses for Computer Engineering appeared.
2.  **Scenario B:** Select "All Faculties" -> Search "Ahmet".
    *   *Result:* All courses taught by "Ahmet" across the university appeared.
3.  **Scenario C:** Select "Tüm Günler".
    *   *Result:* Full list restored (Correction of previous bug).

The implementation is robust, leveraging SQL for heavy lifting and Python for flexible text matching.
