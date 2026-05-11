import time
from ortools.sat.python import cp_model

model = cp_model.CpModel()
PRECISION = 1000
MIN_WIDTH_BRANCH = 30

# Slot 1: A, B
l_A1 = model.NewIntVar(0, PRECISION, 'l_A1')
r_A1 = model.NewIntVar(0, PRECISION, 'r_A1')
w_A1 = model.NewIntVar(30, PRECISION, 'w_A1')
model.Add(w_A1 == r_A1 - l_A1)

l_B1 = model.NewIntVar(0, PRECISION, 'l_B1')
r_B1 = model.NewIntVar(0, PRECISION, 'r_B1')
w_B1 = model.NewIntVar(30, PRECISION, 'w_B1')
model.Add(w_B1 == r_B1 - l_B1)

model.AddNoOverlap([
    model.NewIntervalVar(l_A1, w_A1, r_A1, 'iv_A1'),
    model.NewIntervalVar(l_B1, w_B1, r_B1, 'iv_B1')
])
model.Add(l_A1 <= l_B1) # Ordering hint A < B
slack1 = model.NewIntVar(0, PRECISION, 'sk1')
model.Add(w_A1 + w_B1 + slack1 == PRECISION)
model.Add(10 * w_A1 <= 30 * w_B1)
model.Add(10 * w_B1 <= 30 * w_A1)

# Slot 2: A, B, C
l_A2 = model.NewIntVar(0, PRECISION, 'l_A2')
r_A2 = model.NewIntVar(0, PRECISION, 'r_A2')
w_A2 = model.NewIntVar(30, PRECISION, 'w_A2')
model.Add(w_A2 == r_A2 - l_A2)

l_B2 = model.NewIntVar(0, PRECISION, 'l_B2')
r_B2 = model.NewIntVar(0, PRECISION, 'r_B2')
w_B2 = model.NewIntVar(30, PRECISION, 'w_B2')
model.Add(w_B2 == r_B2 - l_B2)

l_C2 = model.NewIntVar(0, PRECISION, 'l_C2')
r_C2 = model.NewIntVar(0, PRECISION, 'r_C2')
w_C2 = model.NewIntVar(30, PRECISION, 'w_C2')
model.Add(w_C2 == r_C2 - l_C2)

model.AddNoOverlap([
    model.NewIntervalVar(l_A2, w_A2, r_A2, 'iv_A2'),
    model.NewIntervalVar(l_B2, w_B2, r_B2, 'iv_B2'),
    model.NewIntervalVar(l_C2, w_C2, r_C2, 'iv_C2')
])
model.Add(l_A2 <= l_B2)
model.Add(l_B2 <= l_C2)
slack2 = model.NewIntVar(0, PRECISION, 'sk2')
model.Add(w_A2 + w_B2 + w_C2 + slack2 == PRECISION)
model.Add(10 * w_A2 <= 30 * w_B2)
model.Add(10 * w_B2 <= 30 * w_A2)
model.Add(10 * w_A2 <= 30 * w_C2)
model.Add(10 * w_C2 <= 30 * w_A2)

# Staircase prevention for A
lmr_A = model.NewIntVar(0, PRECISION, 'lmr_A')
model.AddMaxEquality(lmr_A, [l_A2 - l_A1, 0])
rmr_A = model.NewIntVar(0, PRECISION, 'rmr_A')
model.AddMaxEquality(rmr_A, [r_A2 - r_A1, 0])
str_A = model.NewIntVar(0, PRECISION, 'str_A')
model.AddMinEquality(str_A, [lmr_A, rmr_A])
model.Add(str_A == 0)

lml_A = model.NewIntVar(0, PRECISION, 'lml_A')
model.AddMaxEquality(lml_A, [l_A1 - l_A2, 0])
rml_A = model.NewIntVar(0, PRECISION, 'rml_A')
model.AddMaxEquality(rml_A, [r_A1 - r_A2, 0])
stl_A = model.NewIntVar(0, PRECISION, 'stl_A')
model.AddMinEquality(stl_A, [lml_A, rml_A])
model.Add(stl_A == 0)

# Staircase prevention for B
lmr_B = model.NewIntVar(0, PRECISION, 'lmr_B')
model.AddMaxEquality(lmr_B, [l_B2 - l_B1, 0])
rmr_B = model.NewIntVar(0, PRECISION, 'rmr_B')
model.AddMaxEquality(rmr_B, [r_B2 - r_B1, 0])
str_B = model.NewIntVar(0, PRECISION, 'str_B')
model.AddMinEquality(str_B, [lmr_B, rmr_B])
model.Add(str_B == 0)

lml_B = model.NewIntVar(0, PRECISION, 'lml_B')
model.AddMaxEquality(lml_B, [l_B1 - l_B2, 0])
rml_B = model.NewIntVar(0, PRECISION, 'rml_B')
model.AddMaxEquality(rml_B, [r_B1 - r_B2, 0])
stl_B = model.NewIntVar(0, PRECISION, 'stl_B')
model.AddMinEquality(stl_B, [lml_B, rml_B])
model.Add(stl_B == 0)

solver = cp_model.CpSolver()
status = solver.Solve(model)
print("Status:", solver.StatusName(status))
