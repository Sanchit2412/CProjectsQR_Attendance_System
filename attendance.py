from datetime import datetime

def mark_attendance(student_id):

    date = datetime.now().date()

    time = datetime.now().time()

    print("Attendance Marked")

    print("Student:", student_id)

    print("Date:", date)

    print("Time:", time)