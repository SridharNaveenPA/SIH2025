from ortools.sat.python import cp_model

# === INPUT DATA ===

days = 5
slots_per_day = 8
total_slots = days * slots_per_day  # 40 time slots

rooms = ['R1', 'R2', 'R3']
courses = ['AI', 'ML', 'Math', 'B.Ed_Psych', 'ITEP']
faculty = {
    'AI': 'Dr.A',
    'ML': 'Dr.B',
    'Math': 'Dr.C',
    'B.Ed_Psych': 'Dr.D',
    'ITEP': 'Dr.E'
}

shared_students = [('AI', 'ML'), ('Math', 'B.Ed_Psych')]

faculty_unavailability = {
    'Dr.A': list(range(0, 4)),
    'Dr.C': [10, 11],
}

room_indices = range(len(rooms))
course_indices = range(len(courses))
time_slots = range(total_slots)

model = cp_model.CpModel()

# === VARIABLES ===

# x[c][t][r] = 1 if course c is scheduled at time t in room r
x = {}
for c in course_indices:
    for t in time_slots:
        for r in room_indices:
            x[c, t, r] = model.NewBoolVar(f'x_{c}_{t}_{r}')

# === CONSTRAINTS ===

# 1. Only one course per room at each time slot
for t in time_slots:
    for r in room_indices:
        model.AddAtMostOne(x[c, t, r] for c in course_indices)

# 2. Each time slot must be used (i.e., scheduled with some course in some room)
#    (Optional: You could force a fixed number of time slots per course if desired)
for t in time_slots:
    model.Add(sum(x[c, t, r] for c in course_indices for r in room_indices) >= 1)

# 3. A course can't be in two rooms at the same time
for c in course_indices:
    for t in time_slots:
        model.AddAtMostOne(x[c, t, r] for r in room_indices)

# 4. Faculty cannot be in more than one place at the same time
for t in time_slots:
    for f in set(faculty.values()):
        relevant_courses = [c for c in course_indices if faculty[courses[c]] == f]
        model.AddAtMostOne(x[c, t, r] for c in relevant_courses for r in room_indices)

# 5. Faculty unavailability
for c in course_indices:
    f_name = faculty[courses[c]]
    if f_name in faculty_unavailability:
        for t in faculty_unavailability[f_name]:
            for r in room_indices:
                model.Add(x[c, t, r] == 0)

# 6. Shared students – no overlap
for (course1, course2) in shared_students:
    i = courses.index(course1)
    j = courses.index(course2)
    for t in time_slots:
        model.Add(
            sum(x[i, t, r1] for r1 in room_indices) +
            sum(x[j, t, r2] for r2 in room_indices)
            <= 1
        )

# === SOLVER ===

solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30
status = solver.Solve(model)

# === OUTPUT ===
# === FORMATTED TABLE OUTPUT ===

from collections import defaultdict

if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    # Create a structure to hold timetable: day → period → list of (course, faculty, room)
    timetable = defaultdict(lambda: defaultdict(list))

    for t in time_slots:
        day = t // slots_per_day + 1
        period = t % slots_per_day + 1
        for c in course_indices:
            for r in room_indices:
                if solver.Value(x[c, t, r]) == 1:
                    cname = courses[c]
                    fname = faculty[cname]
                    rname = rooms[r]
                    entry = f"{cname} ({fname}, {rname})"
                    timetable[day][period].append(entry)

    # Print table header
    print("📅 Weekly Timetable (Rows = Days, Columns = Periods)")
    print("=" * 100)
    header = ["Day/Period"] + [f"P{p}" for p in range(1, 9)]
    print(" | ".join(f"{h:^20s}" for h in header))
    print("-" * 100)

    # Print each day
    for day in range(1, days + 1):
        row = [f"Day {day}"]
        for period in range(1, slots_per_day + 1):
            cell_entries = timetable[day][period]
            if cell_entries:
                cell_text = "\n".join(cell_entries)
            else:
                cell_text = "Free"
            row.append(cell_text)
        print(" | ".join(f"{cell:^20s}" for cell in row))
        print("-" * 100)
else:
    print("❌ No feasible timetable found.")
