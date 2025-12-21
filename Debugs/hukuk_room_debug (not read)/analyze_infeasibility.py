# -*- coding: utf-8 -*-
"""
Analyze why strict constraints and teacher unavailability constraints are infeasible
"""
import sqlite3
from collections import defaultdict

DB_PATH = 'okul_veritabani.db'

def to_minutes(time_str):
    """Convert HH:MM string to minutes since midnight."""
    try:
        if not time_str or ':' not in time_str:
            return 0
        h, m = map(int, time_str.split(':'))
        return h * 60 + m
    except ValueError:
        return 0

def analyze_fixed_room_availability():
    """Check if fixed room constraints are too restrictive"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    print("="*80)
    print("ANALYSIS 1: FIXED ROOM AVAILABILITY")
    print("="*80)
    
    # Get all courses with fixed rooms
    c.execute('''
        SELECT ders_adi, ders_instance, teori_odasi, lab_odasi
        FROM Dersler
        WHERE teori_odasi IS NOT NULL OR lab_odasi IS NOT NULL
    ''')
    courses_with_fixed = c.fetchall()
    
    # Get total active rooms
    c.execute('SELECT COUNT(*) FROM Derslikler WHERE silindi = 0')
    total_rooms = c.fetchone()[0]
    
    # Count room usage
    room_demand = defaultdict(int)
    for ders_adi, instance, teori, lab in courses_with_fixed:
        fixed_room = teori if teori else lab
        if fixed_room:
            room_demand[fixed_room] += 1
    
    print(f"\nTotal Active Rooms: {total_rooms}")
    print(f"Courses with Fixed Rooms: {len(courses_with_fixed)}")
    print(f"\nRoom Demand (courses per room):")
    
    # Calculate time slots available
    time_slots = 5 * 8  # 5 days * 8 hours = 40 slots
    
    saturated_rooms = []
    for room, count in sorted(room_demand.items(), key=lambda x: x[1], reverse=True):
        saturation = (count / time_slots) * 100
        status = "⚠️ SATURATED" if saturation > 50 else "✓ OK"
        print(f"  Room {room}: {count} courses ({saturation:.1f}% of {time_slots} slots) {status}")
        if saturation > 50:
            saturated_rooms.append((room, count, saturation))
    
    if saturated_rooms:
        print(f"\n❌ PROBLEM: {len(saturated_rooms)} room(s) are over 50% saturated!")
        print("   This makes scheduling very difficult with fixed room constraints.")
    else:
        print("\n✓ Fixed room demand looks reasonable.")
    
    conn.close()
    return len(saturated_rooms) > 0

def analyze_teacher_unavailability():
    """Check if teacher unavailability is too restrictive"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    print("\n" + "="*80)
    print("ANALYSIS 2: TEACHER UNAVAILABILITY")
    print("="*80)
    
    # Get all teachers
    c.execute('SELECT ogretmen_num, ad, soyad FROM Ogretmenler')
    teachers = c.fetchall()
    
    # Define time slots
    days = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma']
    hours = ['09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00']
    time_slots = []
    for d_idx, day in enumerate(days):
        for h_idx, hour in enumerate(hours):
            end_hour = f"{int(hour[:2])+1}:00"
            time_slots.append({
                'id': d_idx * 8 + h_idx,
                'day': day,
                'start_str': hour,
                'end_str': end_hour,
                'start_min': to_minutes(hour),
                'end_min': to_minutes(end_hour)
            })
    
    total_slots = len(time_slots)
    problematic_teachers = []
    
    for teacher in teachers:
        t_id, ad, soyad = teacher
        
        # Get courses for this teacher
        c.execute('''
            SELECT COUNT(*) 
            FROM Ders_Ogretmen_Iliskisi
            WHERE ogretmen_id = ?
        ''', (t_id,))
        course_count = c.fetchone()[0]
        
        if course_count == 0:
            continue
        
        # Get unavailability (musaitlik = availability, these are unavailable times)
        c.execute('''
            SELECT gun, baslangic, bitis, id
            FROM Ogretmen_Musaitlik
            WHERE ogretmen_id = ?
        ''', (t_id,))
        unavail = c.fetchall()
        
        # Count blocked slots
        blocked_slots = 0
        for u in unavail:
            u_day, u_start_str, u_end_str, _ = u
            u_start_min = to_minutes(u_start_str)
            u_end_min = to_minutes(u_end_str)
            
            for s in time_slots:
                if s['day'] == u_day:
                    slot_start = s['start_min']
                    slot_end = s['end_min']
                    
                    # Check overlap
                    if (u_start_min < slot_end and u_end_min > slot_start):
                        blocked_slots += 1
        
        available_slots = total_slots - blocked_slots
        availability_pct = (available_slots / total_slots) * 100
        
        if availability_pct < 50:
            status = "❌ CRITICAL"
            problematic_teachers.append((ad, soyad, course_count, available_slots, availability_pct))
        elif availability_pct < 75:
            status = "⚠️ WARNING"
            problematic_teachers.append((ad, soyad, course_count, available_slots, availability_pct))
        else:
            status = "✓ OK"
        
        if course_count > 0 and (blocked_slots > 0 or course_count > 5):
            print(f"\nTeacher: {ad} {soyad}")
            print(f"  Courses: {course_count}")
            print(f"  Blocked Slots: {blocked_slots}/{total_slots}")
            print(f"  Available Slots: {available_slots} ({availability_pct:.1f}%) {status}")
            print(f"  Slots Needed: ≥{course_count} (minimum)")
    
    if problematic_teachers:
        print(f"\n❌ PROBLEM: {len(problematic_teachers)} teacher(s) have limited availability!")
        print("   Teachers with <75% availability:")
        for ad, soyad, courses, avail, pct in problematic_teachers:
            print(f"     - {ad} {soyad}: {courses} courses, {avail} slots ({pct:.1f}%)")
    else:
        print("\n✓ Teacher availability looks reasonable.")
    
    conn.close()
    return len(problematic_teachers) > 0

def analyze_combined_constraints():
    """Analyze the combination of fixed rooms + teacher unavailability"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    print("\n" + "="*80)
    print("ANALYSIS 3: COMBINED CONSTRAINT CONFLICTS")
    print("="*80)
    
    # Get courses that have BOTH a fixed room AND a teacher with unavailability
    c.execute('''
        SELECT 
            d.ders_adi,
            d.ders_instance,
            d.teori_odasi,
            d.lab_odasi,
            doi.ogretmen_id,
            o.ad,
            o.soyad
        FROM Dersler d
        LEFT JOIN Ders_Ogretmen_Iliskisi doi ON d.ders_adi = doi.ders_adi AND d.ders_instance = doi.ders_instance
        LEFT JOIN Ogretmenler o ON doi.ogretmen_id = o.ogretmen_num
        WHERE (d.teori_odasi IS NOT NULL OR d.lab_odasi IS NOT NULL)
          AND doi.ogretmen_id IS NOT NULL
    ''')
    
    constrained_courses = c.fetchall()
    
    print(f"\nCourses with BOTH fixed room AND assigned teacher: {len(constrained_courses)}")
    print("\nThese courses are doubly constrained:")
    
    conflict_count = 0
    for ders_adi, instance, teori, lab, t_id, ad, soyad in constrained_courses[:10]:  # Show first 10
        fixed_room = teori if teori else lab
        
        # Check if teacher has unavailability
        c.execute('''
            SELECT COUNT(*) 
            FROM Ogretmen_Musaitlik
            WHERE ogretmen_id = ?
        ''', (t_id,))
        has_unavail = c.fetchone()[0] > 0
        
        if has_unavail:
            conflict_count += 1
            print(f"  - {ders_adi} (inst:{instance}): Room {fixed_room} + Teacher {ad} {soyad} (has unavailability)")
    
    if conflict_count > 10:
        print(f"  ... and {conflict_count - 10} more courses")
    
    print(f"\n{'❌ PROBLEM' if conflict_count > 20 else '⚠️ WARNING'}: {conflict_count} courses have both room AND teacher constraints!")
    print("   This creates a constraint satisfaction problem that may be over-constrained.")
    
    conn.close()

def main():
    print("\n" + "="*80)
    print(" INFEASIBILITY ANALYSIS")
    print("="*80)
    print("\nAnalyzing why strict constraints fail...\n")
    
    room_issue = analyze_fixed_room_availability()
    teacher_issue = analyze_teacher_unavailability()
    analyze_combined_constraints()
    
    print("\n" + "="*80)
    print("SUMMARY & RECOMMENDATIONS")
    print("="*80)
    
    if room_issue and teacher_issue:
        print("\n❌ BOTH room saturation AND teacher unavailability are problematic!")
        print("\nWhy Attempt 1 (Strict) FAILS:")
        print("  - Fixed rooms are over-saturated")
        print("  - Teacher unavailability blocks many slots")
        print("  - Combined constraints make problem INFEASIBLE")
        print("\nWhy Attempt 2 (Relax Teacher) FAILS:")
        print("  - Even without teacher constraints, fixed rooms are still saturated")
        print("  - Not enough room capacity to accommodate all courses")
        print("\nWhy Attempt 3 (Relax All) SUCCEEDS:")
        print("  - Allows courses to use ANY room (not just fixed ones)")
        print("  - Distributes load across all 20 rooms")
        print("  - Much more flexible solution space")
    elif room_issue:
        print("\n❌ Room saturation is the PRIMARY issue!")
        print("  - Certain rooms have too many assigned courses")
        print("  - 40 time slots per week cannot accommodate all courses in fixed rooms")
    elif teacher_issue:
        print("\n⚠️ Teacher unavailability is creating constraints")
        print("  - Some teachers have very limited availability")
        print("  - Combined with other constraints, this may cause conflicts")
    else:
        print("\n✓ Individual constraints look reasonable")
        print("  - The issue may be in the COMBINATION of all constraints")
    
    print("\nRECOMMENDATIONS:")
    print("  1. Review room assignments - are all fixed rooms necessary?")
    print("  2. Consider flexible room allocation for some courses")
    print("  3. Review teacher unavailability - can it be reduced?")
    print("  4. Consider allowing slight violations with soft constraints")
    print("="*80 + "\n")

if __name__ == '__main__':
    main()
