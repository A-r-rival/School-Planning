import sys
import os
import collections

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from controllers.scheduler import ORToolsScheduler
from models.schedule_model import ScheduleModel

def analyze_parent_keys():
    model = ScheduleModel("database/okul_veritabani.db")
    scheduler = ORToolsScheduler(model)
    scheduler.load_data("Bahar")
    
    parent_keys = collections.Counter()
    for course in scheduler.courses:
        if 'parent_key' in course:
            parent_keys[course['parent_key']] += 1
            
    print("Top 20 most frequent parent_keys:")
    for k, v in parent_keys.most_common(20):
        if v > 1:
            print(f"{k}: {v} occurrences")

if __name__ == "__main__":
    analyze_parent_keys()
