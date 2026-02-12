
import sys
import os
sys.path.append(os.path.join(os.getcwd(), "database"))
try:
    import curriculum_data
    print("Import Successful")
except Exception as e:
    print(f"Import Failed: {e}")
    import traceback
    traceback.print_exc()
