
import sys
import os
import inspect

# Add current directory to path
current_dir = os.getcwd()
sys.path.insert(0, current_dir)

from controllers.scheduler import ORToolsScheduler

def verify_method_presence():
    print("Verifying ORToolsScheduler attributes...")
    if hasattr(ORToolsScheduler, '_clear_existing_schedule'):
        print("SUCCESS: '_clear_existing_schedule' method found in class.")
    else:
        print("FAIL: '_clear_existing_schedule' method NOT found in class.")
        print(f"Directory: {dir(ORToolsScheduler)}")
        
    # Also check a fresh instance
    try:
        scheduler = ORToolsScheduler(None)
        if hasattr(scheduler, '_clear_existing_schedule'):
            print("SUCCESS: '_clear_existing_schedule' method found in instance.")
        else:
            print("FAIL: '_clear_existing_schedule' method NOT found in instance.")
    except Exception as e:
        print(f"Could not instantiate: {e}")

if __name__ == "__main__":
    verify_method_presence()
