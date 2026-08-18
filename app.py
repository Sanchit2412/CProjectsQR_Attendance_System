from flask import Flask, render_template, request, redirect, url_for
from flask_mysqldb import MySQL
from datetime import datetime
import pandas as pd
import qrcode
import os
from flask import send_from_directory
app = Flask(__name__)

# MYSQL CONFIGURATION

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Sa@7355'  
app.config['MYSQL_DB'] = 'qr_attendance'

mysql = MySQL(app)

# LOGIN PAGE

@app.route('/', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        if username == "Sanchit" and password == "Sa@7355":
            return redirect('/dashboard')

        return "Invalid Login"

    return render_template('login.html')


# DASHBOARD

@app.route('/dashboard')
def dashboard():

    cur = mysql.connection.cursor()

    cur.execute("SELECT COUNT(*) FROM students")
    total_students = cur.fetchone()[0]

    cur.execute("""
    SELECT COUNT(*)
    FROM attendance
    WHERE attendance_date = CURDATE()
    """)

    present_today = cur.fetchone()[0]

    absent_today = total_students - present_today

    cur.close()

    return render_template(
        'dashboard.html',
        total_students=total_students,
        present_today=present_today,
        absent_today=absent_today
    )


# STUDENT REGISTRATION
@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        name = request.form['name']
        roll_no = request.form['roll_no']
        course = request.form['course']
        email = request.form['email']

        cur = mysql.connection.cursor()

        # Check Duplicate Roll No or Email

        cur.execute(
            "SELECT * FROM students WHERE roll_no=%s OR email=%s",
            (roll_no, email)
        )

        existing = cur.fetchone()

        if existing:

            cur.close()

            return render_template(
                "register.html",
                message="Roll Number or Email already registered!",
                qr_image=None,
                roll_no=""
            )

        # Insert Student

        cur.execute("""
        INSERT INTO students
        (name, roll_no, course, email)
        VALUES (%s,%s,%s,%s)
        """,
        (name, roll_no, course, email))

        mysql.connection.commit()

        # Generate QR

        qr_data = f"{name}|{roll_no}"

        img = qrcode.make(qr_data)

        filename = f"qr_codes/{roll_no}.png"

        img.save(filename)

        print("QR Saved:", filename)

        cur.close()

        return render_template(
            "register.html",
            message="Student Registered Successfully!",
            qr_image=f"/qr_codes/{roll_no}.png",
            roll_no=roll_no
        )

    return render_template(
        "register.html",
        message=None,
        qr_image=None,
        roll_no=""
    )
# ATTENDANCE PAGE

@app.route('/attendance', methods=['GET', 'POST'])
def attendance():

    if request.method == 'POST':

        roll_no = request.form['roll_no']

        cur = mysql.connection.cursor()

        cur.execute("""
        SELECT *
        FROM attendance
        WHERE roll_no=%s
        AND attendance_date=%s
        """,
        (roll_no, datetime.now().date()))

        record = cur.fetchone()

        if record:
            cur.close()
            return "Attendance Already Marked Today"

        cur.execute("""
        INSERT INTO attendance
        (roll_no, attendance_date, attendance_time, status)
        VALUES (%s,%s,%s,%s)
        """,
        (
            roll_no,
            datetime.now().date(),
            datetime.now().time(),
            "Present"
        ))

        mysql.connection.commit()
        cur.close()

        return "Attendance Marked Successfully"

    return render_template('attendance.html')


# REPORT PAGE

@app.route('/report')
def report():
    cursor = mysql.connection.cursor()

    cursor.execute("""
        SELECT
            attendance.id,
            students.name,
            attendance.roll_no,
            attendance.attendance_date,
            attendance.attendance_time,
            attendance.status
        FROM attendance
        INNER JOIN students
        ON attendance.roll_no = students.roll_no
        ORDER BY attendance.id
    """)

    records = cursor.fetchall()

    return render_template("report.html", records=records)
# STUDENT ATTENDANCE
@app.route('/present_students')
def present_students():

    cursor = mysql.connection.cursor()

    cursor.execute("""
        SELECT
            students.name,
            attendance.roll_no,
            attendance.attendance_date,
            attendance.attendance_time,
            attendance.status
        FROM attendance
        INNER JOIN students
        ON attendance.roll_no = students.roll_no
        WHERE attendance.attendance_date = CURDATE()
        ORDER BY students.name
    """)

    students = cursor.fetchall()

    return render_template("present_students.html", students=students)

@app.route('/student_attendance', methods=['GET', 'POST'])
def student_attendance():

    if request.method == 'POST':

        roll_no = request.form['roll_no']

        cur = mysql.connection.cursor()

        cur.execute("""
        SELECT COUNT(*) FROM attendance
        WHERE roll_no=%s
        """, (roll_no,))

        present = cur.fetchone()[0]

        total = 30

        percentage = round((present / total) * 100, 2)

        cur.execute("""
        SELECT name
        FROM students
        WHERE roll_no=%s
        """, (roll_no,))

        student = cur.fetchone()

        name = student[0] if student else "Not Found"

        cur.close()

        return render_template(
            'student_attendance.html',
            name=name,
            total=total,
            present=present,
            percentage=percentage
        )

    return render_template(
        'student_attendance.html',
        name="",
        total=0,
        present=0,
        percentage=0
    )


# EXPORT EXCEL
from flask import send_file
import pandas as pd
import os

@app.route('/export')
def export():

    cursor = mysql.connection.cursor()

    cursor.execute("""
        SELECT
            attendance.id,
            students.name,
            attendance.roll_no,
            attendance.attendance_date,
            attendance.attendance_time,
            attendance.status
        FROM attendance
        INNER JOIN students
        ON attendance.roll_no = students.roll_no
        ORDER BY attendance.id
    """)

    data = cursor.fetchall()

    df = pd.DataFrame(data, columns=[
        "ID",
        "Name",
        "Roll No",
        "Date",
        "Time",
        "Status"
    ])

    if not os.path.exists("exports"):
        os.makedirs("exports")

    file_path = "exports/attendance_report.xlsx"

    df.to_excel(file_path, index=False)

    return send_file(
        file_path,
        as_attachment=True,
        download_name="Attendance_Report.xlsx"
    )
@app.route('/all_students')
def all_students():

    cursor = mysql.connection.cursor()

    cursor.execute("""
        SELECT id, name, roll_no, course, email
        FROM students
        ORDER BY id
    """)

    students = cursor.fetchall()

    return render_template("all_students.html", students=students)
@app.route('/absent_students')
def absent_students():

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT *
        FROM students
        WHERE roll_no NOT IN
        (
            SELECT roll_no
            FROM attendance
            WHERE attendance_date = CURDATE()
        )
    """)

    students = cur.fetchall()

    cur.close()

    return render_template(
        'absent_students.html',
        students=students
    )
@app.route('/qr_codes/<filename>')
def qr_code(filename):
    return send_from_directory('qr_codes', filename)
# RUN APPLICATION

if __name__ == '__main__':
    app.run(debug=True)