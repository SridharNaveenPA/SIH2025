from ortools.sat.python import cp_model

# Initialize model
model = cp_model.CpModel()

# === INPUT DATA ===

days = 5
slots_per_day = 8
total_slots = days * slots_per_day  # 40 time slots

# Rooms and Courses
rooms = ['R1', 'R2', 'R3']
courses = ['AI', 'ML', 'Math', 'B.Ed_Psych', 'ITEP']
faculty = {
    'AI': 'Dr.A',
    'ML': 'Dr.B',
    'Math': 'Dr.C',
    'B.Ed_Psych': 'Dr.D',
    'ITEP': 'Dr.E'
}

# Shared students (courses that share students — can't be scheduled together)
shared_students = [('AI', 'ML'), ('Math', 'B.Ed_Psych')]

# Faculty unavailable slots (e.g., Dr.A not available in slots 0-3)
faculty_unavailability = {
    'Dr.A': list(range(0, 4)),
    'Dr.C': [10, 11],  # Dr.C unavailable during these periods
}

# === VARIABLES ===

room_indices = list(range(len(rooms)))
course_indices = list(range(len(courses)))

course_time = {}
course_room = {}

for c in course_indices:
    course_time[c] = model.NewIntVar(0, total_slots - 1, f'time_{c}')
    course_room[c] = model.NewIntVar(0, len(rooms) - 1, f'room_{c}')

# === CONSTRAINTS ===

# 1. No two courses in the same room at the same time
for i in course_indices:
    for j in course_indices:
        if i < j:
            # Create a boolean variable that is true iff course_room[i] == course_room[j]
            same_room = model.NewBoolVar(f'same_room_{i}_{j}')
            model.Add(course_room[i] == course_room[j]).OnlyEnforceIf(same_room)
            model.Add(course_room[i] != course_room[j]).OnlyEnforceIf(same_room.Not())

# Now enforce time inequality only if rooms are same
            model.Add(course_time[i] != course_time[j]).OnlyEnforceIf(same_room)


# 2. Faculty not double-booked
for i in course_indices:
    for j in course_indices:
        if i < j and faculty[courses[i]] == faculty[courses[j]]:
            model.Add(course_time[i] != course_time[j])

# 3. Faculty unavailable time slots
for i in course_indices:
    f_name = faculty[courses[i]]
    if f_name in faculty_unavailability:
        for slot in faculty_unavailability[f_name]:
            model.Add(course_time[i] != slot)

# 4. Avoid shared student conflicts
for pair in shared_students:
    i = courses.index(pair[0])
    j = courses.index(pair[1])
    model.Add(course_time[i] != course_time[j])

# === SOLVE ===

solver = cp_model.CpSolver()
status = solver.Solve(model)

# === OUTPUT ===

if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    print("📅 Generated Timetable:")
    print("-" * 50)
    for c in course_indices:
        course_name = courses[c]
        time_slot = solver.Value(course_time[c])
        room_name = rooms[solver.Value(course_room[c])]
        day = time_slot // slots_per_day + 1
        period = time_slot % slots_per_day + 1
        print(f"{course_name:12s} | Faculty: {faculty[course_name]:6s} | Day {day} | Period {period} | Room: {room_name}")
    print("-" * 50)
else:
    print("❌ No feasible timetable found.")
