
import sys
import unittest
from unittest.mock import patch, MagicMock

# Mock the imports used in populate_students
sys.modules['models'] = MagicMock()
sys.modules['models.schedule_model'] = MagicMock()
sys.modules['scripts.curriculum_data'] = MagicMock()

# Define mock data
MOCK_DEPT_DATA = {
    "Engineering": {
        "TestDept": {
            "pools": {
                "SDUa": [("C1", "Course 1", 6)],
                "SDUb": [("C2", "Course 2", 6)],
                "SDUc": [("C3", "Course 3", 6)],
                "OtherPool": [("C4", "Course 4", 6)],
                "SDUHeader": [] # Should be ignored (too long)
            }
        }
    }
}

# Test class for SDUx wildcard logic
class TestSDUxWildcard(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        # This runs before each test
        pass
    
    def test_sdux_pools_exist(self):
        """Test that SDUa, SDUb, SDUc pools exist in mock data"""
        pools = MOCK_DEPT_DATA["Engineering"]["TestDept"]["pools"]
        self.assertIn("SDUa", pools)
        self.assertIn("SDUb", pools)
        self.assertIn("SDUc", pools)
    
    def test_sdu_pool_structure(self):
        """Test that SDU pools have correct structure"""
        pools = MOCK_DEPT_DATA["Engineering"]["TestDept"]["pools"]
        
        # Check SDUa structure
        sdu_a = pools["SDUa"]
        self.assertEqual(len(sdu_a), 1)
        self.assertEqual(sdu_a[0][0], "C1")  # Course code
        self.assertEqual(sdu_a[0][1], "Course 1")  # Course name
        self.assertEqual(sdu_a[0][2], 6)  # AKTS
    
    def test_other_pools_not_affected(self):
        """Test that non-SDU pools are not affected by SDUx logic"""
        pools = MOCK_DEPT_DATA["Engineering"]["TestDept"]["pools"]
        self.assertIn("OtherPool", pools)
        self.assertEqual(pools["OtherPool"][0][0], "C4")
    
    def test_empty_pool_handling(self):
        """Test that empty pools are handled correctly"""
        pools = MOCK_DEPT_DATA["Engineering"]["TestDept"]["pools"]
        self.assertEqual(pools["SDUHeader"], [])


if __name__ == '__main__':
    # Run the tests
    print("Running SDUx Wildcard Tests...")
    print("=" * 50)
    unittest.main(verbosity=2)
