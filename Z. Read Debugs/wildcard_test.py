
import sys
import unittest
from unittest.mock import patch, MagicMock

# 1. Mock the dependencies BEFORE importing the module to test
# We need to mock 'models' and other imports that populate_students uses
sys.modules['models'] = MagicMock()
sys.modules['models.schedule_model'] = MagicMock()
# We don't want to use the real curriculum data, we will inject our own
sys.modules['scripts.curriculum_data'] = MagicMock()

# 2. Now import the function to test
# We use a try-except block just in case the path isn't set up correctly in the test environment
try:
    from scripts.populate_students import get_courses_for_slot
    import scripts.populate_students as ps
except ImportError:
    # If running directly, might need to add root to path
    import os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from scripts.populate_students import get_courses_for_slot
    import scripts.populate_students as ps

# Define mock data for our tests
MOCK_DEPT_DATA = {
    "Engineering": {
        "TestDept": {
            "pools": {
                "SDUa": [("C1", "Course 1", 6)],
                "SDUb": [("C2", "Course 2", 6)],
                "SDUc": [("C3", "Course 3", 6)],
                "OtherPool": [("C4", "Course 4", 6)],
                "SDUHeader": [] 
            }
        }
    }
}

class TestSDUxWildcard(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        # Inject our mock data into the module
        self.original_data = getattr(ps, 'DEPARTMENTS_DATA', {})
        ps.DEPARTMENTS_DATA = MOCK_DEPT_DATA
    
    def tearDown(self):
        """Restore original data after test"""
        ps.DEPARTMENTS_DATA = self.original_data
    
    def test_sdux_wildcard_collection(self):
        """Test that SDUx correctly collects courses from all SDU* pools"""
        # Call the function with "SDUx"
        # Arguments: code, department, faculty, required_ects
        courses = get_courses_for_slot("SDUx", "TestDept", "Engineering", 6)
        
        # Verify result is not None
        self.assertIsNotNone(courses)
        
        # We asked for 6 ECTS, and each course is 6 ECTS, so we should get 1 course
        # But this depends on the logic. Let's inspect the process in a more granular way if possible,
        # or check if the selected course is one of the valid ones.
        
        if courses:
            selected_course = courses[0] # (code, name, ects)
            self.assertEqual(len(courses), 1, "Should pick exactly one 6 ECTS course")
            
            # The selected course must be from SDUa, SDUb, or SDUc
            valid_codes = ["C1", "C2", "C3"]
            self.assertIn(selected_course[0], valid_codes, f"Selected course {selected_course[0]} should be one of {valid_codes}")
            
    def test_sdux_wildcard_logic_coverage(self):
        """
        Since get_courses_for_slot returns a random selection, 
        we run it multiple times to ensure it can pick from all pools eventually.
        """
        found_codes = set()
        
        # Run 50 times to be statistically sure we hit all 3 pools
        for _ in range(50):
            courses = get_courses_for_slot("SDUx", "TestDept", "Engineering", 6)
            if courses:
                found_codes.add(courses[0][0])
                
        # We expect to have seen C1, C2, and C3
        self.assertIn("C1", found_codes, "Should eventually pick from SDUa")
        self.assertIn("C2", found_codes, "Should eventually pick from SDUb")
        self.assertIn("C3", found_codes, "Should eventually pick from SDUc")
        
        # Should NOT pick C4 (OtherPool)
        self.assertNotIn("C4", found_codes, "Should NEVER pick from OtherPool for SDUx")

    def test_normal_pool_access(self):
        """Verify normal specific pool access still works"""
        courses = get_courses_for_slot("SDUa", "TestDept", "Engineering", 6)
        self.assertIsNotNone(courses)
        self.assertEqual(courses[0][0], "C1")
        
    def test_missing_pool(self):
        """Test behavior for non-existent pool"""
        courses = get_courses_for_slot("NonExistent", "TestDept", "Engineering", 6)
        self.assertIsNone(courses)

if __name__ == '__main__':
    # Run the tests
    print("Running SDUx Wildcard Tests...")
    print("=" * 50)
    unittest.main(verbosity=2)
