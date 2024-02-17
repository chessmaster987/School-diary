from flask import Flask, session, render_template, request, redirect, url_for, flash
import psycopg2  # pip install psycopg2
import psycopg2.extras
import matplotlib.pyplot as plt
from io import BytesIO
import base64

app = Flask(__name__)
app.secret_key = "vlad"

DB_HOST = "localhost"
DB_NAME = "Bazu Danych"
DB_USER = "postgres"
DB_PASS = "25082003"

conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER,
                        password=DB_PASS, host=DB_HOST)


# @app.route("/main", methods=['GET', 'POST'])
# def main():
#    if request.method == 'POST':
#        action = request.form.get('action')
#        if action == 'crud':
#            return redirect('/crud')
#        elif action == 'logout':
#            return redirect('/logout')
#
#    return render_template('main.html')


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cur = conn.cursor()
        cur.execute(
            "SELECT username FROM login WHERE username = %s AND password = %s", (username, password))
        user = cur.fetchone()

        if user:
            cur.execute(
                "SELECT role FROM login WHERE username = %s", (username,))
            role = cur.fetchone()

            if role and role[0] == 'admin':
                session['username'] = username
                return redirect('/admin')
            elif role and role[0] == 'teacher':
                session['username'] = username
                return redirect('/teacher')
            elif role and role[0] == 'student':
                session['username'] = username
                return redirect('/student')
        else:
            return 'Неправильний логін або пароль'

    return render_template('login.html')


@app.route('/admin', methods=['GET'])
def admin():
    username = session.get('username', None)
    if username == 'admin':
        print(session.get('username', None))
        return render_template('admin/admin.html', username=username)
    else:
        return 'Недостатньо прав для доступу до адміністративної панелі'


@app.route('/info_student', methods=['GET', 'POST'])
def info_student():
    cur = conn.cursor()
    cur.execute("""SELECT student.login, login.password, student.full_name, classes.class_name FROM student 
                INNER JOIN classes ON classes.class_number = student.class_number
				INNER JOIN login ON login.username = student.login
                ORDER BY login ASC""")
    student_data = cur.fetchall()
    return render_template('admin/info_student.html', student_data=student_data)


@app.route('/info_teacher', methods=['GET', 'POST'])
def info_teacher():
    cur = conn.cursor()
    cur.execute("""SELECT teacher.login, teacher.employee_number, login.password, teacher.full_name
                FROM teacher
                INNER JOIN login on login.username = teacher.login
                ORDER BY login ASC
                """)
    teacher_data = cur.fetchall()
    return render_template('admin/info_teacher.html', teacher_data=teacher_data)


@app.route('/info_classes', methods=['GET', 'POST'])
def info_classes():
    cur = conn.cursor()
    cur.execute("""SELECT * FROM classes""")
    classes_data = cur.fetchall()
    return render_template('admin/info_classes.html', classes_data=classes_data)


@app.route('/info_subject', methods=['GET', 'POST'])
def info_subject():
    cur = conn.cursor()
    cur.execute("""SELECT * FROM subject""")
    subject_data = cur.fetchall()
    return render_template('admin/info_subject.html', subject_data=subject_data)


@app.route('/timetable', methods=['GET', 'POST'])
def timetable():
    cur = conn.cursor()
    cur.execute("""SELECT timetable.timetable_id, subject.subject_name, teacher.login, teacher.full_name
                FROM timetable
                INNER JOIN subject ON timetable.subject_number = subject.subject_number
                INNER JOIN teacher ON timetable.employee_number = teacher.employee_number""")
    timetable_data = cur.fetchall()
    return render_template('admin/timetable.html', timetable_data=timetable_data)


@app.route('/schedule', methods=['GET', 'POST'])
def schedule():
    return render_template('admin/schedule.html')


@app.route('/teacher', methods=['GET'])
def teacher():
    username = session.get('username', None)
    return render_template('teacher/teacher.html', username=username)


# @app.route('/student', methods=['GET'])
# def student():
#    username = session.get('username', None)
#    return render_template('student/student.html', username=username)


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    if request.method == 'POST':
        # Код для виходу
        # удалить из сессии имя пользователя, если оно там есть
        session.pop('username', None)
        print(session.get('username', None))
        return redirect(url_for('login'))  # Переадресація на сторінку login


@app.route('/crud')
def Index():
    # if 'logged_in' in session:
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    s = "SELECT * FROM student"
    cur.execute(s)  # Execute the SQL
    list_users = cur.fetchall()
    return render_template('index.html', list_users=list_users)
    # else:
    # return redirect(url_for('login'))

# ПЕРЕДЕЛАТЬ!!!


@app.route('/add_student', methods=['POST'])
def add_student():
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']
        full_name = request.form['full_name']
        class_number = request.form['class_number']
        role = request.form['student_role']
        print(role)
        cur.execute(
            "INSERT INTO student (login, full_name, class_number) VALUES (%s,%s,%s)", (login, full_name, class_number))
        conn.commit()
        cur.execute(
            "INSERT INTO login (username, password, role) VALUES (%s,%s,%s)", (login, password, role))
        conn.commit()
        flash('Student Added successfully')
        return redirect(url_for('info_student'))


@app.route('/add_teacher', methods=['POST'])
def add_teacher():
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if request.method == 'POST':
        login = request.form['teacher_login']
        password = request.form['teacher_password']
        full_name = request.form['teacher_name']
        class_number = request.form['teacher_class']
        role = request.form['teacher_role']
        print(role)
        if not class_number:
            # Якщо значення не введено, встановлюємо його як None (еквівалентно відображенню null у БД)
            class_number = None
        cur.execute(
            "INSERT INTO teacher (login, full_name, class_number) VALUES (%s,%s,%s)", (login, full_name, class_number))
        conn.commit()
        cur.execute(
            "INSERT INTO login (username, password, role) VALUES (%s,%s,%s)", (login, password, role))
        conn.commit()
        flash('Teacher Added successfully')
        return redirect(url_for('info_teacher'))


@app.route('/add_class', methods=['POST'])
def add_class():
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if request.method == 'POST':
        class_name = request.form['class_name']
        cur.execute(
            "INSERT INTO classes (class_name) VALUES (%s)", (class_name,))
        conn.commit()
        flash('Class Added successfully')
        return redirect(url_for('info_classes'))


@app.route('/add_subject', methods=['POST'])
def add_subject():
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if request.method == 'POST':
        subject_name = request.form['subject_name']
        cur.execute(
            "INSERT INTO subject (subject_name) VALUES (%s)", (subject_name,))
        conn.commit()
        flash('Subject Added successfully')
        return redirect(url_for('info_subject'))


@app.route('/add_timetable', methods=['POST'])
def add_timetable():
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if request.method == 'POST':
        subject_name = request.form['subject_name']
        teacher_name = request.form['teacher_name']
        cur.execute(
            "INSERT INTO timetable (subject_number, employee_number) VALUES (%s, %s)", (subject_name, teacher_name))
        conn.commit()
        flash('Timetable Added successfully')
        return redirect(url_for('timetable'))


@app.route('/edit_student/<id>', methods=['POST', 'GET'])
def get_employee(id):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""SELECT student.login, login.password, student.full_name, student.class_number
                FROM student 
                INNER JOIN login ON student.login = login.username
                WHERE login = %s""", (id,))
    data = cur.fetchall()
    cur.close()
    print(data[0])
    return render_template('edit_student.html', student=data[0])


@app.route('/edit_teacher/<id>', methods=['POST', 'GET'])
def get_teacher(id):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""SELECT teacher.login, login.password, teacher.full_name, teacher.class_number
                FROM teacher
                INNER JOIN login ON teacher.login = login.username
                WHERE login = %s""", (id,))
    data = cur.fetchall()
    cur.close()
    print(data[0])
    return render_template('edit_teacher.html', teacher=data[0])


@app.route('/edit_class/<id>', methods=['POST', 'GET'])
def get_class(id):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""SELECT class_number, class_name 
                FROM classes
                WHERE class_number = %s""", (id,))
    data = cur.fetchall()
    cur.close()
    print(data[0])
    return render_template('edit_class.html', classes=data[0])


@app.route('/edit_subject/<id>', methods=['POST', 'GET'])
def get_subject(id):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""SELECT subject_number, subject_name 
                FROM subject
                WHERE subject_number = %s""", (id,))
    data = cur.fetchall()
    cur.close()
    print(data[0])
    return render_template('edit_subject.html', subject=data[0])


@app.route('/edit_timetable/<id>', methods=['POST', 'GET'])
def get_timetable(id):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""SELECT timetable_id, subject_number, employee_number
                FROM timetable
                WHERE timetable_id = %s""", (id,))
    data = cur.fetchall()
    cur.close()
    print(data[0])
    return render_template('edit_timetable.html', timetable=data[0])


@app.route('/update_student/<id>', methods=['POST', 'GET'])
def update_student(id):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']
        full_name = request.form['full_name']
        class_number = request.form['class_number']

        cur.execute("""
            UPDATE student
            SET login = %s,
                full_name = %s,
                class_number = %s
            WHERE login = %s
        """, (login, full_name, class_number, id))
        conn.commit()
        cur.execute(
            """UPDATE login SET username = %s, password = %s WHERE username = %s""", (login, password, id))
        conn.commit()
        # flash('Student Updated Successfully')
        return redirect(url_for('info_student'))


@app.route('/update_teacher/<id>', methods=['POST', 'GET'])
def update_teacher(id):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']
        full_name = request.form['full_name']
        class_number = request.form['class_number']

        if not class_number:
            # Якщо значення не введено, встановлюємо його як None (еквівалентно відображенню null у БД)
            class_number = None
        cur.execute("""
            UPDATE teacher
            SET login = %s,
                full_name = %s,
                class_number = %s
            WHERE login = %s
        """, (login, full_name, class_number, id))
        conn.commit()
        cur.execute(
            """UPDATE login SET username = %s, password = %s WHERE username = %s""", (login, password, id))
        conn.commit()
        # flash('Teacher Updated Successfully')
        return redirect(url_for('info_teacher'))


@app.route('/update_class/<id>', methods=['POST', 'GET'])
def update_class(id):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if request.method == 'POST':
        class_name = request.form['class_name']
        cur.execute(
            """UPDATE classes SET class_name = %s WHERE class_number = %s""", (class_name, id))
        conn.commit()
        # flash('Class Updated Successfully')
        return redirect(url_for('info_classes'))


@app.route('/update_subject/<id>', methods=['POST', 'GET'])
def update_subject(id):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if request.method == 'POST':
        subject_name = request.form['subject_name']
        cur.execute(
            """UPDATE subject SET subject_name = %s WHERE subject_number = %s""", (subject_name, id))
        conn.commit()
        # flash('Subject Updated Successfully')
        return redirect(url_for('info_subject'))


@app.route('/update_timetable/<id>', methods=['POST', 'GET'])
def update_timetable(id):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if request.method == 'POST':
        subject_name = request.form['subject_name']
        teacher_name = request.form['teacher_name']
        cur.execute(
            """UPDATE timetable SET subject_number = %s, employee_number = %s WHERE timetable_id = %s""", (subject_name, teacher_name, id))
        conn.commit()
        # flash('Timetable Updated Successfully')
        return redirect(url_for('timetable'))


@app.route('/delete_student/<id>', methods=['POST', 'GET'])
def delete_student(id):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute('DELETE FROM student WHERE login = %s', (id,))
    conn.commit()
    cur.execute('DELETE FROM login WHERE username = %s', (id,))
    conn.commit()
    flash('Student Removed Successfully')
    return redirect(url_for('info_student'))


@app.route('/delete_teacher/<id>', methods=['POST', 'GET'])
def delete_teacher(id):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute('DELETE FROM teacher WHERE login = %s', (id,))
    conn.commit()
    cur.execute('DELETE FROM login WHERE username = %s', (id,))
    conn.commit()
    flash('Teacher Removed Successfully')
    return redirect(url_for('info_teacher'))


@app.route('/delete_class/<id>', methods=['POST', 'GET'])
def delete_class(id):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute('DELETE FROM classes WHERE class_number = %s', (id,))
    conn.commit()
    flash('Class Removed Successfully')
    return redirect(url_for('info_classes'))


@app.route('/delete_subject/<id>', methods=['POST', 'GET'])
def delete_subject(id):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute('DELETE FROM subject WHERE subject_number = %s', (id,))
    conn.commit()
    flash('Subject Removed Successfully')
    return redirect(url_for('info_subject'))


@app.route('/delete_timetable/<id>', methods=['POST', 'GET'])
def delete_timetable(id):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute('DELETE FROM timetable WHERE timetable_id = %s', (id,))
    conn.commit()
    flash('Timetable Removed Successfully')
    return redirect(url_for('timetable'))


##
##
# УЧЕНЬ!!!
##
##

@app.route('/student', methods=['GET'])
def student():
    username = session.get('username', None)
    print(session.get('username', None))
    return render_template('student/student.html', username=username)


@app.route('/info_homework', methods=['GET'])
def info_homework():
    username = session.get('username', None)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("""SELECT homework.date, subject.subject_name, homework.homework_text
                FROM homework
                INNER JOIN schedule on homework.lesson_id = schedule.schedule_id
                INNER JOIN timetable on schedule.timetable_id = timetable.timetable_id
                INNER JOIN subject on timetable.subject_number = subject.subject_number
                INNER JOIN classes on schedule.class_number = classes.class_number
                INNER JOIN student on classes.class_number = student.class_number
                WHERE student.login = %s""", (username,))

    homework = cur.fetchall()
    cur.close()
    return render_template('student/info_homework.html', homework=homework)


@app.route('/notification', methods=['GET'])
def notification():
    username = session.get('username', None)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("""SELECT notification.date, teacher.full_name, notification.description
                FROM notification
                INNER JOIN teacher on notification.employee_number = teacher.employee_number
                INNER JOIN classes on notification.class_number = classes.class_number
                INNER JOIN student on classes.class_number = student.class_number
                WHERE student.login = %s""", (username,))

    notif = cur.fetchall()
    cur.close()
    return render_template('student/notification.html', notif=notif)


@app.route('/my_teachers', methods=['GET'])
def my_teachers():
    username = session.get('username', None)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("""SELECT teacher.full_name, subject.subject_name
                FROM teacher
                INNER JOIN timetable on teacher.employee_number = timetable.employee_number
                INNER JOIN subject on timetable.subject_number = subject.subject_number
                INNER JOIN schedule on timetable.timetable_id = schedule.timetable_id
                INNER JOIN classes on schedule.class_number = classes.class_number
                INNER JOIN student on classes.class_number = student.class_number
                WHERE student.login = %s""", (username,))
    my_teachers = cur.fetchall()
    cur.close()
    return render_template('student/my_teachers.html', my_teachers=my_teachers)


##
##
# ВЧИТЕЛЬ!!!
##
##

@app.route('/teacher_detail', methods=['GET', 'POST'])
def teacher_classes():
    username = session.get('username', None)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("""SELECT DISTINCT classes.class_name 
                FROM teacher 
                INNER JOIN timetable on teacher.employee_number = timetable.employee_number
                INNER JOIN schedule on timetable.employee_number = schedule.timetable_id
                INNER JOIN classes on schedule.class_number = classes.class_number
                WHERE teacher.login = %s""", (username,))
    teacher_classes = cur.fetchall()
    cur.close()
    return render_template('teacher/teacher_classes.html', teacher_classes=teacher_classes)


@app.route('/teacher_classes_detail/<class_name>', methods=['GET'])
def teacher_classes_detail(class_name):
    username = session.get('username', None)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("""SELECT DISTINCT student.login, student.full_name 
                FROM teacher 
                INNER JOIN timetable on teacher.employee_number = timetable.employee_number
                INNER JOIN schedule on timetable.employee_number = schedule.timetable_id
                INNER JOIN classes on schedule.class_number = classes.class_number
                INNER JOIN student on classes.class_number = student.class_number
                WHERE teacher.login = %s AND classes.class_name = %s""", (username, class_name))
    teacher_classes_detail = cur.fetchall()
    cur.close()
    return render_template('teacher/teacher_classes_detail.html', teacher_classes_detail=teacher_classes_detail)


# for admin panel adding a new features

def get_teachers_for_zvit():
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT employee_number FROM teacher")
    teachers = cur.fetchall()
    conn.close()
    return teachers


@app.route('/zvit_teacher', methods=['GET', 'POST'])
def zvit_teacher():
    zvit_info = []
    if request.method == 'POST':
        teacher = request.form['teacher']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(
            """SELECT * FROM teacher_report(%s, %s, %s)""", (teacher, start_date, end_date))
        zvit_info = cur.fetchall()

    return render_template('admin/zvit_teacher.html', zvit_data=zvit_info)


@app.route('/homework', methods=['GET', 'POST'])
def homework():
    username = session.get('username', None)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("""SELECT DISTINCT classes.class_name 
                FROM teacher 
                INNER JOIN timetable on teacher.employee_number = timetable.employee_number
                INNER JOIN schedule on timetable.employee_number = schedule.timetable_id
                INNER JOIN classes on schedule.class_number = classes.class_number
                WHERE teacher.login = %s""", (username,))
    teacher_classes = cur.fetchall()
    cur.close()
    return render_template('teacher/homework.html', teacher_classes=teacher_classes)


def get_teacher_subjects():
    username = session.get('username', None)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""
        SELECT subject.subject_name
        FROM teacher
        INNER JOIN timetable on teacher.employee_number = timetable.employee_number
        INNER JOIN subject on timetable.subject_number = subject.subject_number
        WHERE teacher.login = %s """, (username,))
    
    subjects = [row[0] for row in cur.fetchall()]
    cur.close()
    return subjects

@app.route('/add_homework', methods=['GET', 'POST'])
def add_homework():
    username = session.get('username', None)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""SELECT homework.homework_number, homework.date, subject.subject_name, homework.homework_text
                FROM homework
                INNER JOIN schedule on homework.lesson_id = schedule.schedule_id
                INNER JOIN timetable on schedule.timetable_id = timetable.timetable_id
                INNER JOIN subject on timetable.subject_number = subject.subject_number
                INNER JOIN teacher on timetable.employee_number = teacher.employee_number
                WHERE teacher.login = %s""", (username,))
    teacher_homework = cur.fetchall()
    cur.close()
    teacher_subjects = get_teacher_subjects()
    return render_template('teacher/add_homework.html', teacher_subjects=teacher_subjects, teacher_homework=teacher_homework)

if __name__ == "__main__":
    app.run(debug=True)
