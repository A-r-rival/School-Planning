import os
import glob
import shutil

moves = [
    ("check_*.py", "scripts"),
    ("diagnose*.py", "scripts"),
    ("diagnostic.py", "scripts")
]

for pattern, dest in moves:
    for f in glob.glob(pattern):
        try:
            shutil.move(f, dest)
            print(f"Moved {f} to {dest}/")
        except Exception as e:
            print(f"Skipped {f}: {e}")

deletes = [
    "tmp_*.py",
    "test_db.py",
    "test_pool.py",
    "test_robotik*.py",
    "patch_now.py",
    "crash_test_output.txt",
    "room_preference_debug.txt",
    "results.txt",
    "tests/verify_*.py",
    "tests/reproduce_*.py",
    "tests/test_infeasible_diag.py"
]

for pattern in deletes:
    for f in glob.glob(pattern):
        try:
            if os.path.isdir(f):
                shutil.rmtree(f)
            else:
                os.remove(f)
            print(f"Deleted {f}")
        except Exception as e:
            print(f"Skipped {f}: {e}")

try:
    if os.path.isdir("diagnostics"):
        shutil.rmtree("diagnostics")
        print("Deleted empty diagnostics dir")
except Exception as e:
    pass

print("Cleanup complete!")
