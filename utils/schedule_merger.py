# -*- coding: utf-8 -*-
"""
Schedule merging utilities.
Pure functions for combining consecutive course blocks.

These were extracted from ScheduleController to separate
pure algorithms from controller logic.
"""
from typing import List, Dict




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
            # Extract fields from tuple safely
            day = current[0]
            start = current[1]
            end = current[2]
            display = current[3]
            extra = current[4]
            is_elec = current[5]
            course_name = current[6]
            
            code = current[7] if len(current) > 7 else ""
            pools = current[8] if len(current) > 8 else []
            diff_color = current[9] if len(current) > 9 else None
            
            program_ids = []
            if len(current) > 10 and current[10]:
                if isinstance(current[10], list):
                    program_ids.extend(current[10])
                else:
                    program_ids.append(current[10])
            
            # Check for consecutive blocks
            span = 1
            while i + span < len(items):
                next_item = items[i + span]
                # Merge if: same course, same teacher/room, consecutive hours
                if (next_item[6] == course_name and  # Same course name
                    next_item[1] == end and  # Next starts where current ends
                    next_item[4] == extra):  # Same teacher/room
                    end = next_item[2]  # Extend end time
                    if len(next_item) > 10 and next_item[10]:
                        if isinstance(next_item[10], list):
                            program_ids.extend(next_item[10])
                        else:
                            program_ids.append(next_item[10])
                    span += 1
                else:
                    break
            
            # Add merged block - Always output 11-tuple format
            p_id = program_ids[0] if len(program_ids) == 1 else (program_ids if program_ids else None)
            merged_item = (day, start, end, display, extra, is_elec, course_name, code, pools, diff_color, p_id)
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
