
import unittest
import sys
import os
from unittest.mock import MagicMock

# Add project root to sys.path to allow imports from controllers
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from controllers.scheduler_services import (
    CurriculumResolver, CourseMerger, CourseRole, 
    PhysicalCourse, RawCourseRow, ProgramCourseContext
)

class TestPhase3Logic(unittest.TestCase):
    
    def setUp(self):
        # Mock Curriculum Data
        # Departments: "CS" (Computer Sci), "ME" (Mechanical Eng)
        # Pools: CS has "ZE" (Zorunlu) and "TE" (Technical Elective)
        
        self.mock_curr_data = {
            "CS": {
                "curriculum": {
                    1: {"Math101": "Z", "CS101": "Z", "Elective1": "S"}
                },
                "pool_codes": {
                    "TE": ["AdvAlgo", "AdvAI"], # Technical Electives
                    "HSS": ["History", "Art"]   # Social Electives
                }
            },
            "ME": {
                "curriculum": {
                    1: {"Math101": "Z"}
                },
                "pool_codes": {}
            }
        }
        
        self.resolver = CurriculumResolver()
        self.resolver.dept_data = self.mock_curr_data

    def test_curriculum_resolution_role(self):
        """Verify Resolver correctly assigns roles based on input context."""
        
        # Case 1: CS101 in CS Year 1 -> Should be CORE
        row_core = RawCourseRow(
            name="CS101", instance=1, t=3, u=0, l=0, akts=5, code="CS101",
            department="CS", class_year=1, faculty="Eng", group_id=10,
            t_room=None, l_room=None, teacher_ids={1}
        )

        ctx = self.resolver.resolve_context(row_core)
        self.assertEqual(ctx.role, CourseRole.CORE)
        self.assertEqual(ctx.department, "CS")

        # Case 2: AdvAlgo in CS -> Should be ELECTIVE (Pool TE)
        # Assuming resolver logic checks pool_codes
        row_elec = RawCourseRow(
            name="AdvAlgo", instance=1, t=3, u=0, l=0, akts=5, code="CS401",
            department="CS", class_year=4, faculty="Eng", group_id=11,
            t_room=None, l_room=None, teacher_ids={1}
        )
        ctx = self.resolver.resolve_context(row_elec)
        self.assertEqual(ctx.role, CourseRole.ELECTIVE)
        self.assertEqual(ctx.pool_code, "TE")

    def test_merger_same_course_different_roles(self):
        """Verify Merger handles a single physical course being Core for one dept and Elective for another."""
        merger = CourseMerger()
        
        # Situation: "Math101" is Core for CS (Year 1)
        # But let's pretend it's an Elective for "Arts" (Year 2) - just hypothetically
        
        row_cs = RawCourseRow(
            name="Math101", instance=1, t=3, u=0, l=0, akts=5, code="MAT101",
            department="CS", class_year=1, faculty="Eng", group_id=10,
            t_room=None, l_room=None, teacher_ids={100}
        )
        # Mock resolver for CS -> CORE
        ctx_cs = [ProgramCourseContext(department="CS", year=1, role=CourseRole.CORE)]
        
        # Row for Arts (Same course instance/teachers)
        row_arts = RawCourseRow(
            name="Math101", instance=1, t=3, u=0, l=0, akts=5, code="MAT101",
            department="Arts", class_year=2, faculty="Arts", group_id=20,
            t_room=None, l_room=None, teacher_ids={100}
        )
        # Mock resolver for Arts -> ELECTIVE
        ctx_arts = ProgramCourseContext(department="Arts", year=2, role=CourseRole.ELECTIVE, pool_code="BasicSci")

        # We must mock the resolver's behavior since we are passing it to merge
        mock_resolver = MagicMock()
        # Correctly mock resolve_context (singular)
        # Note: ctx_cs needs to be single object too
        ctx_cs_obj = ProgramCourseContext(department="CS", year=1, role=CourseRole.CORE)
        
        mock_resolver.resolve_context.side_effect = lambda r: ctx_cs_obj if r.department == "CS" else ctx_arts
        
        # Merge
        physical_courses = merger.merge([row_cs, row_arts], mock_resolver)
        
        self.assertEqual(len(physical_courses), 1)
        pc = physical_courses[0]
        
        # Verify it has BOTH contexts
        self.assertEqual(len(pc.contexts), 2)
        roles = [c.role for c in pc.contexts]
        self.assertIn(CourseRole.CORE, roles)
        self.assertIn(CourseRole.ELECTIVE, roles)
        
        # Verify group IDs aggregated
        self.assertEqual(pc.group_ids, {10, 20})

    def test_merger_conflict_validation(self):
        """Verify Merger raises ValueError if SAME group has conflicting roles for SAME course."""
        merger = CourseMerger()
        
        # Row 1: CS, Year 1, Core
        row_1 = RawCourseRow(
            name="Conflict101", instance=1, t=3, u=0, l=0, akts=5, code="C101",
            department="CS", class_year=1, faculty="Eng", group_id=10,
            t_room=None, l_room=None, teacher_ids={100}
        )
        
        # Row 2: CS, Year 1, Elective (Same group ID context)
        row_2 = RawCourseRow(
            name="Conflict101", instance=1, t=3, u=0, l=0, akts=5, code="C101",
            department="CS", class_year=1, faculty="Eng", group_id=10,
            t_room=None, l_room=None, teacher_ids={100}
        )

        ctx_core = ProgramCourseContext(department="CS", year=1, role=CourseRole.CORE)
        ctx_elec = ProgramCourseContext(department="CS", year=1, role=CourseRole.ELECTIVE)
        
        mock_resolver = MagicMock()
        # First call returns Core, second returns Elective
        mock_resolver.resolve_context.side_effect = [ctx_core, ctx_elec]
        
        # Expect Error
        with self.assertRaises(ValueError) as cm:
            merger.merge([row_1, row_2], mock_resolver)
        
        print(f"\nCaught Expected Error: {cm.exception}")

if __name__ == '__main__':
    unittest.main()
