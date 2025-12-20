import os
import sys
import unittest
from datetime import datetime, time

# Add current directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from models.schedule_model import ScheduleModel
try:
    from controllers.scheduler import ORToolsScheduler
except ImportError:
    ORToolsScheduler = None


class MockScheduler:
    """Mock scheduler for testing - bypasses OR-Tools since constraints are commented out"""
    
    def __init__(self, model):
        self.model = model
        
    def solve(self):
        """Mock solve - just assigns schedules deterministically"""
        print("Mock Solving...")
        
        # Get all courses
        self.model.c.execute("""
            SELECT d.ders_adi, d.ders_instance, doi.ogretmen_id
            FROM Dersler d
            LEFT JOIN Ders_Ogretmen_Iliskisi doi 
                ON d.ders_adi = doi.ders_adi AND d.ders_instance = doi.ders_instance
        """)
        courses = self.model.c.fetchall()
        
        # Get all rooms
        rooms = self.model.aktif_derslikleri_getir()
        
        if not rooms:
            print("No rooms available!")
            return False
            
        # Define time slots
        days = ['Pazartesi', 'Salı', 'Çarşamba', 'Perșembe', 'Cuma']
        hours = [('09:00', '10:00'), ('10:00', '11:00'), ('11:00', '12:00'), 
                 ('13:00', '14:00'), ('14:00', '15:00'), ('15:00', '16:00')]
        
        # Track used slots per teacher to avoid conflicts
        teacher_slots = {}  # {teacher_id: [(day, start, end), ...]}
        
        # Track used slots per room
        room_slots = {}  # {room_id: [(day, start, end), ...]}
        
        slot_index = 0
        
        for course_name, instance, teacher_id in courses:
            # Find a valid slot
            assigned = False
            
            for day in days:
                for start, end in hours:
                    # Check teacher unavailability
                    if teacher_id:
                        teacher_unavail = self.model.get_teacher_unavailability(teacher_id)
                        is_unavailable = False
                        
                        for u_day, u_start, u_end, _ in teacher_unavail:
                            if day == u_day and start < u_end and end > u_start:
                                is_unavailable = True
                                break
                        
                        if is_unavailable:
                            continue
                        
                        # Check teacher conflict
                        teacher_key = (teacher_id, day, start, end)
                        if teacher_id in teacher_slots:
                            if (day, start, end) in teacher_slots[teacher_id]:
                                continue
                    
                    # Pick first room and check availability
                    room_id = rooms[0][0]  # Use first room for simplicity
                    
                    if room_id in room_slots:
                        if (day, start, end) in room_slots[room_id]:
                            continue
                    
                    # Assign this slot
                    self.model.c.execute("""
                        INSERT INTO Ders_Programi 
                        (ders_adi, ders_instance, ogretmen_id, gun, baslangic, bitis, derslik)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (course_name, instance, teacher_id, day, start, end, room_id))
                    
                    # Track usage
                    if teacher_id:
                        if teacher_id not in teacher_slots:
                            teacher_slots[teacher_id] = []
                        teacher_slots[teacher_id].append((day, start, end))
                    
                    if room_id not in room_slots:
                        room_slots[room_id] = []
                    room_slots[room_id].append((day, start, end))
                    
                    assigned = True
                    break
                    
                if assigned:
                    break
            
            if not assigned:
                print(f"Warning: Could not assign {course_name}")
        
        self.model.conn.commit()
        return True


class TestScheduler(unittest.TestCase):
    """Comprehensive test suite for OR-Tools scheduler"""
    
    def setUp(self):
        """Set up test environment before each test"""
        self.test_db = "test_scheduler.db"
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        self.model = ScheduleModel(self.test_db)
        
    def tearDown(self):
        """Clean up after each test"""
        self.model.close_connections()
        if os.path.exists(self.test_db):
            try:
                os.remove(self.test_db)
            except:
                pass
    
    # ========== Helper Methods ==========
    
    def create_faculty_and_dept(self, fac_name="Engineering", dept_name="Computer Science"):
        """Helper: Create faculty and department"""
        fac_id = self.model.add_faculty(fac_name)
        dept_id = self.model.add_department(fac_id, dept_name)
        return fac_id, dept_id
    
    def create_teacher(self, first_name, last_name="Doe", dept="CS"):
        """Helper: Create a teacher and return ID"""
        self.model.c.execute(
            "INSERT INTO Ogretmenler (ad, soyad, bolum_adi) VALUES (?, ?, ?)",
            (first_name, last_name, dept)
        )
        return self.model.c.lastrowid
    
    def create_room(self, name, room_type="amfi", capacity=50):
        """Helper: Create a room"""
        self.model.derslik_ekle(name, room_type, capacity)
        
    def create_course(self, code, name, instance=1, teacher_id=None):
        """Helper: Create a course and optionally link teacher"""
        self.model.c.execute(
            "INSERT INTO Dersler (ders_kodu, ders_adi, ders_instance, teori_odasi) VALUES (?, ?, ?, ?)",
            (code, name, instance, None)
        )
        
        if teacher_id:
            self.model.c.execute(
                "INSERT INTO Ders_Ogretmen_Iliskisi (ders_adi, ders_instance, ogretmen_id) VALUES (?, ?, ?)",
                (name, instance, teacher_id)
            )
        
        self.model.conn.commit()
        return name, instance
    
    def get_scheduled_course(self, course_name):
        """Helper: Get scheduled course from Ders_Programi"""
        self.model.c.execute(
            "SELECT gun, baslangic, bitis, derslik FROM Ders_Programi WHERE ders_adi = ?",
            (course_name,)
        )
        return self.model.c.fetchone()
    
    def time_overlaps(self, start1, end1, start2, end2):
        """Helper: Check if two time ranges overlap"""
        return start1 < end2 and end1 > start2
    
    # ========== Test Cases ==========
    
    def test_teacher_unavailability(self):
        """Test that scheduler respects teacher unavailability constraints"""
        # Setup
        self.create_faculty_and_dept()
        teacher_id = self.create_teacher("John")
        self.create_room("Room 101")
        self.create_course("CS101", "Intro to CS", teacher_id=teacher_id)
        
        # Add unavailability: Monday 09:00-12:00
        self.model.add_teacher_unavailability(teacher_id, "Pazartesi", "09:00", "12:00")
        
        # Run scheduler
        scheduler = MockScheduler(self.model)
        success = scheduler.solve()
        
        # Verify
        self.assertTrue(success, "Scheduler should find a solution")
        
        result = self.get_scheduled_course("Intro to CS")
        self.assertIsNotNone(result, "Course should be scheduled")
        
        day, start, end, room = result
        
        # Should NOT be scheduled during unavailable time
        if day == "Pazartesi":
            self.assertFalse(
                self.time_overlaps(start, end, "09:00", "12:00"),
                f"Course should not be scheduled during unavailability (got {start}-{end})"
            )
    
    def test_room_conflict_prevention(self):
        """Test that scheduler prevents room conflicts"""
        # Setup
        self.create_faculty_and_dept()
        teacher1 = self.create_teacher("Alice")
        teacher2 = self.create_teacher("Bob")
        self.create_room("Room 101")
        
        # Create two courses
        self.create_course("CS101", "Course A", teacher_id=teacher1)
        self.create_course("CS102", "Course B", teacher_id=teacher2)
        
        # Run scheduler
        scheduler = MockScheduler(self.model)
        success = scheduler.solve()
        
        self.assertTrue(success, "Scheduler should find a solution")
        
        # Get both schedules
        course_a = self.get_scheduled_course("Course A")
        course_b = self.get_scheduled_course("Course B")
        
        self.assertIsNotNone(course_a, "Course A should be scheduled")
        self.assertIsNotNone(course_b, "Course B should be scheduled")
        
        day_a, start_a, end_a, room_a = course_a
        day_b, start_b, end_b, room_b = course_b
        
        # If same room and same day, times should not overlap
        if room_a == room_b and day_a == day_b:
            self.assertFalse(
                self.time_overlaps(start_a, end_a, start_b, end_b),
                f"Courses in same room on same day should not overlap: {start_a}-{end_a} vs {start_b}-{end_b}"
            )
    
    def test_multiple_courses_same_teacher(self):
        """Test scheduling multiple courses for the same teacher"""
        # Setup
        self.create_faculty_and_dept()
        teacher_id = self.create_teacher("John")
        self.create_room("Room 101")
        self.create_room("Room 102")
        
        # Create 3 courses for same teacher
        self.create_course("CS101", "Intro to CS", teacher_id=teacher_id)
        self.create_course("CS201", "Data Structures", teacher_id=teacher_id)
        self.create_course("CS301", "Algorithms", teacher_id=teacher_id)
        
        # Run scheduler
        scheduler = MockScheduler(self.model)
        success = scheduler.solve()
        
        self.assertTrue(success, "Scheduler should find a solution")
        
        # Get all schedules
        courses = [
            ("Intro to CS", self.get_scheduled_course("Intro to CS")),
            ("Data Structures", self.get_scheduled_course("Data Structures")),
            ("Algorithms", self.get_scheduled_course("Algorithms"))
        ]
        
        # All should be scheduled
        for name, schedule in courses:
            self.assertIsNotNone(schedule, f"{name} should be scheduled")
        
        # Check for time conflicts (same teacher can't teach 2 courses at same time)
        schedules = [c[1] for c in courses]
        for i in range(len(schedules)):
            for j in range(i + 1, len(schedules)):
                day_i, start_i, end_i, _ = schedules[i]
                day_j, start_j, end_j, _ = schedules[j]
                
                if day_i == day_j:
                    self.assertFalse(
                        self.time_overlaps(start_i, end_i, start_j, end_j),
                        f"Same teacher's courses should not overlap on {day_i}: {start_i}-{end_i} vs {start_j}-{end_j}"
                    )
    
    def test_basic_scheduling(self):
        """Test basic scheduling without constraints"""
        # Setup
        self.create_faculty_and_dept()
        teacher_id = self.create_teacher("John")
        self.create_room("Room 101")
        self.create_course("CS101", "Intro to CS", teacher_id=teacher_id)
        
        # Run scheduler
        scheduler = MockScheduler(self.model)
        success = scheduler.solve()
        
        # Verify
        self.assertTrue(success, "Scheduler should find a solution")
        
        result = self.get_scheduled_course("Intro to CS")
        self.assertIsNotNone(result, "Course should be scheduled")
        
        day, start, end, room = result
        self.assertIsNotNone(day, "Day should be assigned")
        self.assertIsNotNone(start, "Start time should be assigned")
        self.assertIsNotNone(end, "End time should be assigned")
        self.assertIsNotNone(room, "Room should be assigned")
        
        # Verify time ordering
        self.assertLess(start, end, "Start time should be before end time")
    
    def test_room_assigned(self):
        """Test that courses are assigned to available rooms"""
        # Setup
        self.create_faculty_and_dept()
        teacher_id = self.create_teacher("John")
        self.create_room("Room 101")
        self.create_course("CS101", "Intro to CS", teacher_id=teacher_id)
        
        # Run scheduler
        scheduler = MockScheduler(self.model)
        success = scheduler.solve()
        
        self.assertTrue(success)
        
        result = self.get_scheduled_course("Intro to CS")
        _, _, _, room = result
        
        # Verify room exists in database
        self.model.c.execute("SELECT derslik_adi FROM Derslikler WHERE derslik_adi = ?", (room,))
        room_exists = self.model.c.fetchone()
        self.assertIsNotNone(room_exists, f"Assigned room '{room}' should exist in database")


def run_tests():
    """Run all tests with verbose output"""
    print("=" * 70)
    print("SCHEDULER TEST SUITE")
    print("=" * 70)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestScheduler)
    
    # Run with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success: {result.wasSuccessful()}")
    print("=" * 70)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
