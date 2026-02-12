
from ortools.sat.python import cp_model
from ortools.sat import cp_model_pb2
import sys
from google.protobuf import text_format

# Load model from file
filename = "model_dump_PHASE1_CORE.txt"
print(f"Loading model from {filename}...")

model_proto = cp_model_pb2.CpModelProto()
try:
    with open(filename, "r", encoding="utf-8") as f:
        text_format.Parse(f.read(), model_proto)
except Exception as e:
    print(f"Error reading model file: {e}")
    sys.exit(1)

print("Model loaded.")
print(f"Variables: {len(model_proto.variables)}")
print(f"Constraints: {len(model_proto.constraints)}")

# Reconstruct CpModel wrapper?
# Or solve directly?
# Solver.Solve accepts wrapper.
# Solver.SolveWithProto accepts proto!

print("Creating Solver...")
solver = cp_model.CpSolver()
solver.parameters.log_search_progress = True
solver.parameters.log_to_stdout = True

print("Solving...")
# Inspecting ortools src... SolveWithProto is not exposed in public python API usually?
# Let's check.
# If not, we can wrap it in CpModel.
# model = cp_model.CpModel()
# model._model_proto = model_proto 

model = cp_model.CpModel()
model._model_proto = model_proto

try:
    status = solver.Solve(model)
except Exception as e:
    print(f"CRITICAL ERROR in Solve: {e}")
    sys.exit(1)

print(f"Status: {solver.StatusName(status)}")
