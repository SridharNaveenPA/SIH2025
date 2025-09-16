from ortools.sat.python import cp_model
from prettytable import PrettyTable
import csv
from datetime import datetime

# === INPUT DATA ===

days = 5
slots_per_day = 8
total_slots = days * slots_per_day  # 40 time slots

rooms = ['R1', 'R2', 'R3']

courses = [
    'AI', 'ML', 'Math', 'B.Ed_Psych', 'ITEP',
    'DBMS', 'OS', 'Networking', 'English', 'Physics'
]

faculty = {
    'AI': 'Dr.A',
    'ML': 'Dr.B',
    'Math': 'Dr.C',
    'B.Ed_Psych': 'Dr.D',
    'ITEP': 'Dr.E',
    'DBMS': 'Dr.F',
    'OS': 'Dr.G',
    'Networking': 'Dr.H',
    'English': 'Dr.I',
    'Physics': 'Dr.J'
}

# Shared students (no overlap constraint)
shared_students = [
    ('AI', 'ML'),
    ('Math', 'B.Ed_Psych'),
    ('DBMS', 'OS'),
    ('Networking', 'OS'),
    ('English', 'Physics')
]

# Minimum lectures per course per week
course_min_lectures = {
    'AI': 3,
    'ML': 3,
    'Math': 3,
    'DBMS': 3,
    'OS': 3,
    'Networking': 2,
    'English': 2,
    'Physics': 2,
    'B.Ed_Psych': 2,
    'ITEP': 2
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
            x[c, t, r] = model.NewBoolVar(f'x_{c}{t}{r}')

# === CONSTRAINTS ===

# 1. Only one course per room at each time slot
for t in time_slots:
    for r in room_indices:
        model.AddAtMostOne(x[c, t, r] for c in course_indices)

# 2. A course can't be in two rooms at the same time
for c in course_indices:
    for t in time_slots:
        model.AddAtMostOne(x[c, t, r] for r in room_indices)

# 3. Faculty cannot be in more than one place at the same time
for t in time_slots:
    for f in set(faculty.values()):
        relevant_courses = [c for c in course_indices if faculty[courses[c]] == f]
        model.AddAtMostOne(x[c, t, r] for c in relevant_courses for r in room_indices)

# 4. Shared students – no overlap
for (course1, course2) in shared_students:
    i = courses.index(course1)
    j = courses.index(course2)
    for t in time_slots:
        model.Add(
            sum(x[i, t, r1] for r1 in room_indices) +
            sum(x[j, t, r2] for r2 in room_indices)
            <= 1
        )

# 5. Each course must be scheduled multiple times per week
for c in course_indices:
    cname = courses[c]
    min_lectures = course_min_lectures[cname]
    model.Add(sum(x[c, t, r] for t in time_slots for r in room_indices) >= min_lectures)

# === SOLVER ===

solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30
status = solver.Solve(model)

# === OUTPUT ===

if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    # Initialize timetable grid: days × slots
    timetable = [[[] for _ in range(slots_per_day)] for _ in range(days)]

    for c in course_indices:
        for t in time_slots:
            for r in room_indices:
                if solver.Value(x[c, t, r]) == 1:
                    day = t // slots_per_day
                    period = t % slots_per_day
                    course_name = courses[c]
                    faculty_name = faculty[course_name]
                    room_name = rooms[r]
                    timetable[day][period].append(f"{course_name} ({faculty_name}, {room_name})")

    # Prepare PrettyTable
    headers = ["Day/Period"] + [f"P{p}" for p in range(1, slots_per_day + 1)]
    table_data = []

    for day in range(days):
        row = [f"Day {day + 1}"]
        for period in range(slots_per_day):
            cell_entries = timetable[day][period]
            if cell_entries:
                cell_text = "\n".join(cell_entries)
            else:
                cell_text = "Free"
            row.append(cell_text)
        table_data.append(row)

    x_table = PrettyTable()
    x_table.field_names = headers

    for row in table_data:
        x_table.add_row(row)

    for field in headers:
        x_table.align[field] = "c"

    print(x_table)

    # === CSV EXPORT ===
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"timetable_{timestamp}.csv"
    
    # Write to CSV file
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write header
        writer.writerow(headers)
        
        # Write data rows
        for row in table_data:
            # Replace newlines with semicolons for better CSV compatibility
            csv_row = []
            for cell in row:
                if isinstance(cell, str) and '\n' in cell:
                    csv_row.append(cell.replace('\n', '; '))
                else:
                    csv_row.append(cell)
            writer.writerow(csv_row)
    
    print(f"\n✅ Timetable successfully exported to: {csv_filename}")
    
    # Also create a detailed CSV with separate entries for each class
    detailed_csv_filename = f"timetable_detailed_{timestamp}.csv"
    
    with open(detailed_csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write detailed header
        writer.writerow(['Day', 'Period', 'Course', 'Faculty', 'Room', 'Day_Number', 'Period_Number'])
        

    # Print summary
    print("\n=== SUMMARY ===")
    total_lectures = 0
    for c in course_indices:
        course_name = courses[c]
        lectures_scheduled = sum(solver.Value(x[c, t, r]) for t in time_slots for r in room_indices)
        total_lectures += lectures_scheduled
        print(f"{course_name}: {lectures_scheduled} lectures (min: {course_min_lectures[course_name]})")
    
    print(f"\nTotal lectures scheduled: {total_lectures}")
    print(f"Total available slots: {len(rooms) * total_slots}")

else:
    print("❌ No feasible timetable found.")

