import re
import sys
import os
import sqlite3

# Ensure we can import the database data
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.append(project_root)

from database.curriculum_data import DEPARTMENTS_DATA, COMMON_USD_POOL

def score_turkish(text):
    score = 0
    text_lower = text.lower()
    
    # Turkish specific characters
    tr_chars = set('çğışüöÇĞİÖŞÜ')
    for char in text:
        if char in tr_chars:
            score += 10
            
    # Common Turkish words/substrings
    tr_words = [' ve ', 'müh', 'giriş', 'sistem', 'seçilmiş', 'proje', 'uygulamalı', 'temel', 'analiz', 'staj', 'bilg', 'teknoloji', 'işletme', 'yöntem', 'tasarım', 'makine', 'devre']
    for word in tr_words:
        if word in text_lower:
            score += 5
            
    # Common English/German words/substrings
    non_tr_words = [' and ', ' to ', ' of ', ' in ', ' for ', 'intro', 'project', 'systems', 'advanced', 'topics', 'science', 'engineering', 'und', 'der', 'die', 'meth', 'tech', 'eng', 'basic', 'fund', 'design', 'calculus', 'analysis']
    for word in non_tr_words:
        if word in text_lower:
            score -= 5
            
    # English endings
    if re.search(r'(ing|tion|ics|sis)\b', text_lower):
        score -= 5
        
    return score

def choose_turkish(name):
    if " / " not in name:
        return name
        
    parts = [p.strip() for p in name.split(" / ")]
    scored = [(score_turkish(p), p) for p in parts]
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1]

def convert_roman_to_arabic(name):
    # Match Roman numerals that are distinct words
    # Only replace if it's I, II, III, IV, V, VI, VII, VIII, IX, X
    roman_pattern = r'\b(I|II|III|IV|V|VI|VII|VIII|IX|X)\b'
    
    def replacer(match):
        roman_map = {"I": "1", "II": "2", "III": "3", "IV": "4", "V": "5", "VI": "6", "VII": "7", "VIII": "8", "IX": "9", "X": "10"}
        return roman_map[match.group(1)]
        
    return re.sub(roman_pattern, replacer, name)

def get_all_names():
    names = set()
    for dept_name, dept_info in DEPARTMENTS_DATA.items():
        for semester, courses in dept_info.get("curriculum", {}).items():
            for course in courses:
                names.add(course[1])
        for pool_code, pool_courses in dept_info.get("pools", {}).items():
            for course in pool_courses:
                names.add(course[1])
        for pool_code, course_names in dept_info.get("pool_codes", {}).items():
            for name in course_names:
                names.add(name)
    for course in COMMON_USD_POOL:
        names.add(course[1])
    return names

def main():
    names = get_all_names()
    replacements = {}
    
    for old_name in names:
        # Step 1: Remove foreign language
        turkish_name = choose_turkish(old_name)
        
        # Step 2: Convert Roman numerals
        final_name = convert_roman_to_arabic(turkish_name)
        
        if old_name != final_name:
            replacements[old_name] = final_name
            
    # Read curriculum_data.py
    data_file_path = os.path.join(project_root, "database", "curriculum_data.py")
    with open(data_file_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Apply replacements safely
    # We only want to replace precise string literals, so we replace `"{old_name}"` with `"{final_name}"`
    # We will sort by length descending to avoid partial replacements if any name is a substring of another.
    sorted_replacements = sorted(replacements.items(), key=lambda x: len(x[0]), reverse=True)
    
    for old, new in sorted_replacements:
        content = content.replace(f'"{old}"', f'"{new}"')
        
    # Add Sanitized comment if not exists
    if "# Auto-generated curriculum data" in content and "# Sanitized by the script (sanitize_course_names.py)" not in content:
        content = content.replace(
            "# Auto-generated curriculum data", 
            "# Auto-generated curriculum data\n# Sanitized by the script (sanitize_course_names.py)"
        )
        
    with open(data_file_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    print(f"Successfully updated curriculum_data.py. Made {len(replacements)} replacements.")
    for old, new in sorted_replacements[:10]: # Print a few examples
        print(f"  '{old}' -> '{new}'")

    # Sync to SQLite Database
    db_path = os.path.join(project_root, "database", "okul_veritabani.db")
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        updated_count = 0
        try:
            cursor.execute("SELECT ders_kodu, ders_instance, ders_adi FROM Dersler")
            rows = cursor.fetchall()
            for row in rows:
                ders_kodu, ders_instance, current_name = row
                if ders_kodu in replacements:
                    new_name = replacements[ders_kodu]
                    if current_name != new_name:
                        try:
                            # Update the name
                            cursor.execute("""
                                UPDATE Dersler 
                                SET ders_adi = ? 
                                WHERE ders_instance = ? AND ders_adi = ?
                            """, (new_name, ders_instance, current_name))
                            updated_count += cursor.rowcount
                        except sqlite3.IntegrityError:
                            # Safely delete the old duplicated mapping
                            cursor.execute("DELETE FROM Dersler WHERE ders_instance = ? AND ders_adi = ?", (ders_instance, current_name))
                            updated_count += 1
                            
            # Now update relational tables that store ders_adi
            tables = [
                "Ders_Sinif_Iliskisi",
                "Ders_Havuz_Iliskisi",
                "Ders_Programi",
                "Ders_Ogretmen_Iliskisi",
                "Ogretmen_Ders_Tercihleri",
            ]
            for table in tables:
                cursor.execute(f"PRAGMA table_info({table})")
                if "ders_adi" not in [col[1] for col in cursor.fetchall()]: continue
                
                cursor.execute(f"SELECT DISTINCT ders_adi FROM {table}")
                rows = cursor.fetchall()
                for row in rows:
                    old_name = row[0]
                    if not old_name: continue
                    new_name = convert_roman_to_arabic(choose_turkish(old_name))
                    if old_name != new_name:
                        try:
                            cursor.execute(f"UPDATE {table} SET ders_adi = ? WHERE ders_adi = ?", (new_name, old_name))
                            updated_count += cursor.rowcount
                        except sqlite3.IntegrityError:
                            cursor.execute(f"DELETE FROM {table} WHERE ders_adi = ?", (old_name,))
                            updated_count += 1
                            
            conn.commit()
            print(f"Successfully synced {updated_count} course names to SQLite Database (okul_veritabani.db).")
        except Exception as e:
            conn.rollback()
            print(f"Database sync failed: {e}")
            sys.exit(1)
        finally:
            conn.close()
    else:
        print("Database not found, skipping sync.")

if __name__ == "__main__":
    main()
