from scripts import curriculum_data
from scripts.parse_curriculum import Regexes

def is_elective_course(course_code: str, course_name: str, dept_name: str = None) -> bool:
    """
    Determine if a course is an elective using a centralized logic.
    Priority:
    1. Curriculum Data (Truth) - checks if course is in any pool for the department.
    2. Regex (Pattern) - checks code against known pool patterns.
    3. Fallback (String) - checks for keywords like 'Seçmeli'.
    
    Args:
        course_code (str): Course Code (e.g. CSE301, SDIa)
        course_name (str): Course Name
        dept_name (str, optional): Department name for precise lookup.
        
    Returns:
        bool: True if elective, False otherwise.
    """
    # 1. Curriculum Data Lookup (Truth)
    if dept_name:
        dept_data = curriculum_data.DEPARTMENTS_DATA.get(dept_name)
        # Check both 'pool_codes' (new format) and 'pools' (old format if exists)
        # Based on user feedback, structure is likely 'pool_codes' or we should check both to be safe.
        # User snippet showed: if dept_data and 'pool_codes' in dept_data:
        if dept_data:
            # Check 'pool_codes'
            if 'pool_codes' in dept_data:
                clean_name = course_name.split(" (S")[0].strip() # Cleanup " (Seçmeli)"
                for p_code_key, p_course_names in dept_data['pool_codes'].items():
                     for db_name in p_course_names:
                         if db_name.lower().strip() == clean_name.lower().strip() or \
                            db_name.lower().strip() in clean_name.lower().strip() or \
                            clean_name.lower().strip() in db_name.lower().strip():
                              return True
            
            # Check 'pools' (if legacy structure persists)
            if 'pools' in dept_data:
                lower_text = course_name.lower()
                for pool_key, pool_courses in dept_data['pools'].items():
                    for _, p_name, _, _, _, _ in pool_courses:
                        if p_name.lower() in lower_text:
                            return True

    # 2. Regex Pattern
    if course_code:
        if Regexes.pool_code.search(course_code):
            return True
        upper_code = course_code.upper()
        if "SDI" in upper_code or "GSD" in upper_code or "USD" in upper_code:
            return True

    # 3. Fallback String Check
    if "seçmeli" in course_name.lower():
        return True
        
    return False


def identify_pools(course_name, dept_name):
    """
    Identify which pools the courses in 'course_name' belong to.
    
    Args:
        course_name (str): Name of the course (can include extra info).
        dept_name (str): Department name to look up in curriculum data.
        
    Returns:
        set: A set of pool codes (e.g. {'SDIa', 'ÜSD'}).
    """
    found = set()
    dept_data = curriculum_data.DEPARTMENTS_DATA.get(dept_name)
    if not dept_data or 'pools' not in dept_data:
        return found
        
    lower_text = course_name.lower()
    
    # 'pools' key in DEPARTMENTS_DATA maps pool_key (e.g. 'SDIa') to a list of course tuples
    for pool_key, pool_courses in dept_data['pools'].items():
        # Check if any course name in this pool matches our text
        for _, p_name, _, _, _, _ in pool_courses:
            if p_name.lower() in lower_text:
                found.add(pool_key)
                break 
    return found
