# -*- coding: utf-8 -*-
"""
Unit tests for entity classes
Run with: python test_entities.py
"""
from models.entities import ScheduleSlot, CourseInput, ScheduledCourse
from datetime import time


if __name__ == "__main__":
    print("🧪 Running Entity Tests...")
    print("=" * 50)
    
    # Test 1: ScheduleSlot creation and overlap
    print("\n1️⃣ Testing ScheduleSlot...")
    try:
        slot1 = ScheduleSlot.from_strings("Pazartesi", "09:00", "10:50")
        slot2 = ScheduleSlot.from_strings("Pazartesi", "10:00", "11:50")
        slot3 = ScheduleSlot.from_strings("Salı", "09:00", "10:50")
        
        # Test overlap detection
        assert slot1.overlaps(slot2), "❌ Overlapping slots should overlap"
        assert not slot1.overlaps(slot3), "❌ Different days should not overlap"
        
        # Test adjacent slots
        slot4 = ScheduleSlot.from_strings("Pazartesi", "09:00", "10:00")
        slot5 = ScheduleSlot.from_strings("Pazartesi", "10:00", "11:00")
        assert not slot4.overlaps(slot5), "❌ Adjacent slots should not overlap"
        
        # Test display
        assert slot1.to_display_string() == "09:00-10:50"
        assert slot1.to_db_tuple() == ("Pazartesi", "09:00", "10:50")
        
        print("   ✅ ScheduleSlot creation: PASSED")
        print("   ✅ Overlap detection: PASSED")
        print("   ✅ Display formatting: PASSED")
    except AssertionError as e:
        print(f"   ❌ FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        exit(1)
    
    # Test 2: ScheduleSlot validation
    print("\n2️⃣ Testing ScheduleSlot validation...")
    try:
        # Invalid day
        try:
            ScheduleSlot(day="Monday", start=time(9, 0), end=time(10, 50))
            print("   ❌ Should have rejected invalid day")
            exit(1)
        except ValueError as e:
            print(f"   ✅ Invalid day rejected: {e}")
        
        # Start after end
        try:
            ScheduleSlot(day="Pazartesi", start=time(11, 0), end=time(9, 0))
            print("   ❌ Should have rejected start >= end")
            exit(1)
        except ValueError as e:
            print(f"   ✅ Invalid time range rejected: {e}")
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        exit(1)
    
    # Test 3: CourseInput validation
    print("\n3️⃣ Testing CourseInput...")
    try:
        # Valid input
        course = CourseInput(
            ders="Matematik",
            hoca="Prof. Dr. Ali",
            gun="Pazartesi",
            baslangic="09:00",
            bitis="10:50"
        )
        assert course.ders == "Matematik"
        print("   ✅ Valid input created successfully")
        
        # Test whitespace trimming
        course2 = CourseInput(
            ders="  Matematik  ",
            hoca=" Prof. Dr. Ali ",
            gun=" Pazartesi ",
            baslangic=" 09:00 ",
            bitis=" 10:50 "
        )
        assert course2.ders == "Matematik", "Whitespace not trimmed"
        assert course2.hoca == "Prof. Dr. Ali", "Whitespace not trimmed"
        print("   ✅ Whitespace trimming: PASSED")
        
        # Missing field
        try:
            CourseInput(
                ders="",
                hoca="Prof. Dr. Ali",
                gun="Pazartesi",
                baslangic="09:00",
                bitis="10:50"
            )
            print("   ❌ Should have rejected empty field")
            exit(1)
        except ValueError as e:
            print(f"   ✅ Empty field rejected: {e}")
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        exit(1)
    
    # Test 4: ScheduledCourse formatting
    print("\n4️⃣ Testing ScheduledCourse...")
    try:
        # Minimal fields
        course1 = ScheduledCourse(
            program_id=1,
            ders_adi="Matematik",
            ders_instance=1,
            ders_kodu="MAT101",
            hoca="Prof. Dr. Ali",
            gun="Pazartesi",
            baslangic="09:00",
            bitis="10:50"
        )
        expected1 = "[MAT101] Matematik - Prof. Dr. Ali (Pazartesi 09:00-10:50)"
        assert course1.to_display_string() == expected1
        print(f"   ✅ Minimal: {course1.to_display_string()}")
        
        # With all fields
        course2 = ScheduledCourse(
            program_id=2,
            ders_adi="Veri Madenciliği",
            ders_instance=1,
            ders_kodu="SDIa",
            hoca="Dr. Mehmet",
            gun="Salı",
            baslangic="13:00",
            bitis="14:50",
            siniflar="Bilgisayar Müh. 3. Sınıf",
            havuz_kodlari="SDIa/SDIb"
        )
        expected2 = "[SDIa] Veri Madenciliği [SDIa/SDIb] - Dr. Mehmet (Salı 13:00-14:50) [Bilgisayar Müh. 3. Sınıf]"
        assert course2.to_display_string() == expected2
        print(f"   ✅ Full: {course2.to_display_string()}")
        
    except AssertionError as e:
        print(f"   ❌ FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        exit(1)
    
    print("\n" + "=" * 50)
    print("✅ ALL TESTS PASSED!")
    print("=" * 50)
