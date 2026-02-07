# -*- coding: utf-8 -*-
"""
Schedule merging utilities.
Pure functions for combining consecutive course blocks.

These were extracted from ScheduleController to separate
pure algorithms from controller logic.
"""
from typing import List, Dict
import re


def merge_course_strings(course_list: List[str]) -> List[str]:
    """
    Merge consecutive course blocks in formatted strings.
    
    Input format: "[Code] Name - Teacher (Day Start-End) [Classes]"
    
    Example:
        Input: [
            "[CODE] Math - Dr. Smith (Monday 09:00-10:00)",
            "[CODE] Math - Dr. Smith (Monday 10:00-11:00)"
        ]
        Output: [
            "[CODE] Math - Dr. Smith (Monday 09:00-11:00)"
        ]
    
    Args:
        course_list: List of formatted course strings
    
    Returns:
        List with consecutive blocks merged
    """
    if not course_list:
        return []
   
    # Regex to parse: [Code] Name - Teacher (Day Start-End) [Classes]
    # Added (.*) at end to capture suffix (student groups, etc.)
    pattern = re.compile(r"\[(.*?)\] (.*?) - (.*?) \((.*?) (\d{2}:\d{2})-(\d{2}:\d{2})\)(.*)")
    
    parsed_items = []
    unparsed_items = []
    
    for item in course_list:
        match = pattern.match(item)
        if match:
            code, name, teacher, day, start, end, suffix = match.groups()
            parsed_items.append({
                'code': code,
                'name': name,
                'teacher': teacher,
                'day': day,
                'start': start,
                'end': end,
                'suffix': suffix,  # Store classes info
                'original': item
            })
        else:
            unparsed_items.append(item)
    
    # Sort by (Name, Code, Teacher, Day, Start) to group mergeable items
    day_map = {"Pazartesi": 0, "Salı": 1, "Çarşamba": 2, "Perşembe": 3, "Cuma": 4}
    
    def sort_key(x):
        return (
            x['name'],
            x['teacher'],
            day_map.get(x['day'], 99),
            x['start']
        )
    
    parsed_items.sort(key=sort_key)
    
    # Merge consecutive blocks
    merged_items = []
    if parsed_items:
        current = parsed_items[0]
        
        for i in range(1, len(parsed_items)):
            next_item = parsed_items[i]
            
            # Check if mergeable: same course, teacher, day, and consecutive time
            if (current['name'] == next_item['name'] and
                current['teacher'] == next_item['teacher'] and
                current['day'] == next_item['day'] and
                current['end'] == next_item['start']):  # Consecutive
                
                # Merge: extend end time
                current['end'] = next_item['end']
            else:
                # Push current and start new block
                merged_items.append(current)
                current = next_item
        
        # Push last block
        merged_items.append(current)
    
    # Reconstruct strings
    final_list = []
    for item in merged_items:
        s = f"[{item['code']}] {item['name']} - {item['teacher']} ({item['day']} {item['start']}-{item['end']}){item['suffix']}"
        final_list.append(s)
    
    # Add back unparsed items
    final_list.extend(unparsed_items)
    
    return final_list


def merge_consecutive_blocks(schedule_data):
    """
    Merge consecutive course blocks in tuple format.
    
    Input: List of tuples (day, start, end, display, extra, is_elec, course, [code, pools])
    Output: Merged tuples with extended time ranges for consecutive blocks
    
    Args:
        schedule_data: List of schedule tuples
    
    Returns:
        List with consecutive blocks merged
    """
    if not schedule_data:
        return schedule_data
    
    # Group by day
    day_groups = {}
    for item in schedule_data:
        day = item[0]
        if day not in day_groups:
            day_groups[day] = []
        day_groups[day].append(item)
    
    merged = []
    for day, items in day_groups.items():
        # Sort by start time
        items.sort(key=lambda x: x[1])
        
        i = 0
        while i < len(items):
            current = items[i]
            # Extract fields from tuple
            day, start, end, display, extra, is_elec, course_name = current[:7]
            code = current[7] if len(current) > 7 else None
            pools = current[8] if len(current) > 8 else []
            
            # Check for consecutive blocks
            span = 1
            while i + span < len(items):
                next_item = items[i + span]
                # Merge if: same course, same teacher/room, consecutive hours
                if (next_item[6] == course_name and  # Same course name
                    next_item[1] == end and  # Next starts where current ends
                    next_item[4] == extra):  # Same teacher/room
                    end = next_item[2]  # Extend end time
                    span += 1
                else:
                    break
            
            # Add merged block
            merged_item = (day, start, end, display, extra, is_elec, course_name)
            if code is not None:
                merged_item = merged_item + (code, pools)
            merged.append(merged_item)
            
            i += span
    
    return merged

def merge_schedule_items_dicts(items: List[Dict]) -> List[Dict]:
    """
    Merge consecutive schedule items (dicts).
    Used for the Table View.
    """
    if not items:
        return []
    
    # Sort by Name, Teacher, Day, Start
    day_map = {"Pazartesi": 0, "Salı": 1, "Çarşamba": 2, "Perşembe": 3, "Cuma": 4}
    
    def sort_key(x):
        return (
            x['name'],
            x['teacher'],
            day_map.get(x['day'], 99),
            x['start']
        )
            
    items.sort(key=sort_key)
    
    merged = []
    if items:
        current = items[0].copy() # Copy to avoid mutating original
        # Track IDs for deletion. Note: 'id' in current is int. 
        # structure: { ..., 'ids': [id1, id2] }
        current['ids'] = [current['id']]
        
        for i in range(1, len(items)):
            next_item = items[i]
            
            if (current['name'] == next_item['name'] and
                current['teacher'] == next_item['teacher'] and
                current['day'] == next_item['day'] and
                current['end'] == next_item['start']):
                
                # Merge
                current['end'] = next_item['end']
                current['ids'].append(next_item['id'])
            else:
                merged.append(current)
                current = next_item.copy()
                current['ids'] = [current['id']]
        
        merged.append(current)
        
    return merged
