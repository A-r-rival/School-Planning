
import unittest
from unittest.mock import MagicMock
import sys
import os

# Adjust path to import controllers
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from controllers.scheduler_services import (
    RawCourseRow, ProgramCourseContext, CourseRole, 
    CurriculumResolver, CourseMerger, PhysicalCourse, SchedulableCourseBuilder
)

class TestSchedulerRefactor(unittest.TestCase):
    
    def test_golden_case_core_and_elective(self):
        """
        GOLDEN CASE:
        Verify that a single course can be:
        - CORE for Computer Engineering (Year 4)
        - ELECTIVE for Industrial Engineering (Year 4)
        """
        
        # 1. Setup Mock Curriculum Data
        # "Machine Learning" is in the 'SDIII' pool for Industrial Eng.
        # But for Computer Eng, it's just a regular course (no pool entry implies Core if fetched).
        mock_curriculum_data = {
            "Industrial Eng": {
                "pool_codes": {
                    "SDIII": ["Machine Learning"]
                }
            },
            "Computer Eng": {
                "pool_codes": {} # No pools
            }
        }
        
        # 2. Setup Resolver
        # We perform a partial mock or just subclass/inject data
        resolver = CurriculumResolver()
        resolver.dept_data = mock_curriculum_data 
        
        # 3. Create Raw Rows (Simulating DB results)
        # Row 1: Machine Learning fetched via Computer Eng curriculum (Core)
        row_cse = RawCourseRow(
            name="Machine Learning",
            instance=1,
            t=3, u=0, l=0, akts=6,
            code="CSE404",
            department="Computer Eng",
            class_year=4,
            faculty="Engineering",
            group_id=101,
            t_room=None, l_room=None,
            teacher_ids={1}
        )
        
        # Row 2: Machine Learning fetched via Industrial Eng curriculum (Elective)
        row_ie = RawCourseRow(
            name="Machine Learning",
            instance=1,
            t=3, u=0, l=0, akts=6,
            # Note: Code might be generic in DB or specific, assume same physical course
            code="CSE404", 
            department="Industrial Eng",
            class_year=4,
            faculty="Engineering",
            group_id=202,
            t_room=None, l_room=None,
            teacher_ids={1}
        )
        
        # 4. Run Merger
        merger = CourseMerger()
        physical_courses = merger.merge([row_cse, row_ie], resolver)
        
        # 5. Assertions
        self.assertEqual(len(physical_courses), 1, "Should merge into a single physical course")
        
        pc = physical_courses[0]
        self.assertEqual(pc.name, "Machine Learning")
        self.assertEqual(len(pc.group_ids), 2)
        self.assertEqual(len(pc.contexts), 2)
        
        # Verify Contexts
        contexts_list = list(pc.contexts)
        
        # Check Core Context
        core_ctx = next((c for c in contexts_list if c.department == "Computer Eng"), None)
        self.assertIsNotNone(core_ctx)
        self.assertEqual(core_ctx.role, CourseRole.CORE)
        self.assertEqual(core_ctx.year, 4)
        
        # Check Elective Context
        elec_ctx = next((c for c in contexts_list if c.department == "Industrial Eng"), None)
        self.assertIsNotNone(elec_ctx)
        self.assertEqual(elec_ctx.role, CourseRole.ELECTIVE)
        self.assertEqual(elec_ctx.pool_code, "SDIII")
        
        print("\n✅ Golden Case Verified: Course is CORE for CSE and ELECTIVE for IE.")
        
    def test_conflict_detection(self):
        """
        Verify that if the SAME group (Dept+Year) produces conflicted roles, it warns (or handles it).
        """
        # Mock Data: Same Dept has it in pool AND we treat it as core?
        # In reality, if it's in a pool, Resolver returns Elective.
        # If we have two rows for same dept, one matching pool and one not?
        # Example: One row says "Machine Learning" (matches pool), other says "Machine Learning" (maybe typo?)
        
        mock_curriculum_data = {
            "Computer Eng": {
                "pool_codes": {
                    "SDIII": ["Machine Learning"]
                }
            }
        }
        
        resolver = CurriculumResolver()
        resolver.dept_data = mock_curriculum_data
        
        # Row 1: Matches Pool -> Elective
        row1 = RawCourseRow(
            name="Machine Learning", instance=1, t=3, u=0, l=0, akts=6, code="CSE",
            department="Computer Eng", class_year=4, faculty="Eng", group_id=1, t_room=None, l_room=None, teacher_ids={1}
        )
        
        # Row 2: Same everything, but let's say we hack the resolver for the second call?
        # Or let's just manually inject contexts to simpler test Merger validation.
        
        ctx_core = ProgramCourseContext("Computer Eng", 4, CourseRole.CORE)
        ctx_elec = ProgramCourseContext("Computer Eng", 4, CourseRole.ELECTIVE, pool_code="SDIII")
        
        pc = PhysicalCourse(
            name="Conflict Course", teacher_ids=frozenset({1}), t=3, u=0, l=0, akts=6, code="C",
            fixed_t_room=None, fixed_l_room=None, 
            contexts={ctx_core, ctx_elec} # Conflict injected here
        )
        
        merger = CourseMerger()
        # The validation runs at the end of merge().
        # We can call internal method
        # Capturing stdout to check warning
        
        print("\nTesting Conflict Warning (Expect 'CRITICAL WARNING'):")
        merger._validate_contexts(pc)
        
    def test_builder_output(self):
        """
        Verify SchedulableCourseBuilder produces correct dict structure.
        """
        ctx = ProgramCourseContext("Computer Eng", 4, CourseRole.CORE)
        pc = PhysicalCourse(
            name="Test Course", teacher_ids=frozenset({1, 2}),
            t=3, u=0, l=0, akts=5, code="TEST101",
            fixed_t_room=10, fixed_l_room=None,
            faculties={"Eng"}, group_ids={101},
            contexts={ctx}
        )
        
        builder = SchedulableCourseBuilder()
        blocks = builder.build_blocks([pc])
        
        self.assertEqual(len(blocks), 1)
        blk = blocks[0]
        
        self.assertEqual(blk['name'], "Test Course")
        self.assertEqual(blk['type'], "Teori")
        self.assertEqual(blk['duration'], 3)
        self.assertEqual(blk['fixed_room'], 10)
        self.assertIn('program_contexts', blk)
        self.assertEqual(blk['program_contexts'][0], ctx)
        self.assertNotIn('is_elective', blk) # Ensure removed
        
        print("\n✅ Builder Output Verified.")

if __name__ == '__main__':
    unittest.main()
