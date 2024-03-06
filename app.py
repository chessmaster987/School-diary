from flask import Flask, session, render_template, request, redirect, url_for, flash
import psycopg2  # pip install psycopg2
import psycopg2.extras
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from datetime import datetime

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


@app.route('/homework_comments', methods=['GET'])
def homework_comments():
    username = session.get('username', None)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""SELECT DISTINCT homeworkcomment.date, subject.subject_name, homeworkcomment.comment
                FROM homeworkcomment
                INNER JOIN homework on homeworkcomment.homework_number = homework.homework_number
                INNER JOIN schedule on homework.lesson_id = schedule.schedule_id
                INNER JOIN timetable on schedule.timetable_id = timetable.timetable_id
                INNER JOIN subject on timetable.subject_number = subject.subject_number
                WHERE homeworkcomment.login = %s""", (username,))
    comment_data = cur.fetchall()
    cur.close()
    return render_template('student/homework_comments.html', comment_data=comment_data)

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


################################
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

    if request.method == 'POST':
        date = request.form['start_date']
        teacher_subject_pre = request.form['teacher_subject']
        print(teacher_subject_pre)
        cur.execute(
            """SELECT subject_number FROM subject WHERE subject_name = %s""", (teacher_subject_pre,))
        teacher_subject = cur.fetchone()[0]
        print(teacher_subject)
        homework_description = request.form['homework_description']

        cur.execute(
            "INSERT INTO homework (homework_text, lesson_id, date) VALUES (%s,%s,%s)", (homework_description, teacher_subject, date))
        conn.commit()
        return redirect(url_for('add_homework'))

    class_name = request.args.get('class_name', None)
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

################################


@app.route('/teacher_notif', methods=['GET'])
def teacher_notif():
    return render_template('teacher/notif_event.html')


@app.route('/teacher_notif/classes', methods=['GET'])
def notif_classes():
    username = session.get('username', None)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute(
        """SELECT employee_number FROM teacher WHERE teacher.login = %s""", (username,))
    teacher_id = cur.fetchone()[0]
    cur.execute("""SELECT notification.notification_number, notification.date, classes.class_name, notification.description
                FROM notification
                INNER JOIN classes on notification.class_number = classes.class_number
                WHERE notification.employee_number = %s""", (teacher_id,))
    notif_classes_data = cur.fetchall()
    teacher_classes = get_teacher_classes()
    return render_template('teacher/notif_classes.html', notif_classes_data=notif_classes_data, teacher_classes=teacher_classes)


@app.route('/teacher_notif/students', methods=['GET'])
def notif_students():
    return render_template('teacher/notif_students.html')


def get_teacher_classes():
    username = session.get('username', None)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""
                SELECT DISTINCT classes.class_number 
                FROM teacher
                INNER JOIN timetable on teacher.employee_number = timetable.employee_number
                INNER JOIN schedule on timetable.timetable_id = schedule.timetable_id
                INNER JOIN classes on schedule.class_number = classes.class_number
                WHERE teacher.login = %s""", (username,))

    classes = [row[0] for row in cur.fetchall()]
    cur.close()
    return classes


@app.route('/teacher_notif/classes/add_classes_notif', methods=['GET', 'POST'])
def add_classes_notif():
    username = session.get('username', None)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if request.method == 'POST':
        class_number = request.form['teacher_classes']
        # class_number = request.form.get('teacher_classes')
        notif_text = request.form['notif_text']
        current_date = datetime.now().strftime("%Y-%m-%d")
        cur.execute(
            """SELECT employee_number FROM teacher WHERE teacher.login = %s""", (username,))
        teacher_id = cur.fetchone()[0]
        cur.execute(
            "INSERT INTO notification (date, class_number, employee_number, description) VALUES (%s,%s,%s,%s)", (current_date, class_number, teacher_id, notif_text))
        conn.commit()
        return redirect(url_for('notif_classes'))

    return render_template('teacher/notif_classes.html')


@app.route('/edit_classes_notif/<id>', methods=['POST', 'GET'])
def edit_classes_notif(id):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""SELECT notification_number, class_number, description
                FROM notification
                WHERE notification_number = %s""", (id,))
    data = cur.fetchall()
    cur.close()
    print(data[0])
    return render_template('teacher/edit_classes_notif.html', notification=data[0])


@app.route('/update_classes_notif/<id>', methods=['POST', 'GET'])
def update_classes_notif(id):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if request.method == 'POST':
        class_number = request.form['class_number']
        notif_text = request.form['notif_text']

        cur.execute("""
            UPDATE notification
            SET description = %s
            WHERE notification_number = %s
        """, (notif_text, id))
        conn.commit()
        return redirect(url_for('notif_classes'))


@app.route('/delete_classes_notif/<id>', methods=['POST', 'GET'])
def delete_classes_notif(id):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute('DELETE FROM notification WHERE notification_number = %s', (id,))
    conn.commit()
    return redirect(url_for('notif_classes'))

# for student: schedule


@app.route('/student_schedule', methods=['POST', 'GET'])
def student_schedule():
    username = session.get('username', None)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""SELECT classes.class_number FROM classes
                INNER JOIN student on classes.class_number = student.class_number
                WHERE student.login = %s""", (username,))
    class_numb = cur.fetchone()[0]
    cur.execute("""SELECT Classes.class_name, Schedule.day, Schedule.subject_number, Subject.subject_name, Teacher.full_name
                FROM Schedule
                INNER JOIN Classes ON Schedule.class_number = Classes.class_number
                INNER JOIN Timetable ON Schedule.timetable_id = Timetable.timetable_id
                INNER JOIN Teacher ON Timetable.employee_number = Teacher.employee_number
                INNER JOIN Subject ON Schedule.subject_number = Subject.subject_number
                WHERE Schedule.class_number = %s
                ORDER BY
                CASE Schedule.day
                	WHEN 'Monday' THEN 1
                	WHEN 'Tuesday' THEN 2
                	WHEN 'Wednesday' THEN 3
                	WHEN 'Thursday' THEN 4
                	WHEN 'Friday' THEN 5
                END, Schedule.subject_number""", (class_numb,))
    schedule_data = cur.fetchall()
    cur.close()
    return render_template('student/student_schedule.html', schedule_data=schedule_data)

# for teacher: schedule


@app.route('/teacher_schedule', methods=['POST', 'GET'])
def teacher_schedule():
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""SELECT Classes.class_name, Schedule.day, Schedule.subject_number, Subject.subject_name, Teacher.full_name
                FROM Schedule
                INNER JOIN Classes ON Schedule.class_number = Classes.class_number
                INNER JOIN Timetable ON Schedule.timetable_id = Timetable.timetable_id
                INNER JOIN Teacher ON Timetable.employee_number = Teacher.employee_number
                INNER JOIN Subject ON Schedule.subject_number = Subject.subject_number
                ORDER BY Classes.class_name,
                CASE Schedule.day
                	WHEN 'Monday' THEN 1
                	WHEN 'Tuesday' THEN 2
                	WHEN 'Wednesday' THEN 3
                	WHEN 'Thursday' THEN 4
                	WHEN 'Friday' THEN 5
                END, Schedule.subject_number""")
    schedule_data = cur.fetchall()
    cur.close()
    return render_template('teacher/teacher_schedule.html', schedule_data=schedule_data)

# for admin: schedule


@app.route('/admin_schedule', methods=['POST', 'GET'])
def admin_schedule():
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT subject_number, subject_name FROM Subject")
    subjects = cur.fetchall()
    timetable_data = get_timetable_info()
    classes_data = get_classes()
    cur.execute("""SELECT Schedule.schedule_id, Classes.class_name, Schedule.day, Schedule.subject_number, Subject.subject_name, Teacher.full_name
                FROM Schedule
                INNER JOIN Classes ON Schedule.class_number = Classes.class_number
                INNER JOIN Timetable ON Schedule.timetable_id = Timetable.timetable_id
                INNER JOIN Teacher ON Timetable.employee_number = Teacher.employee_number
                INNER JOIN Subject ON Schedule.subject_number = Subject.subject_number
                ORDER BY Classes.class_name,
                CASE Schedule.day
                	WHEN 'Monday' THEN 1
                	WHEN 'Tuesday' THEN 2
                	WHEN 'Wednesday' THEN 3
                	WHEN 'Thursday' THEN 4
                	WHEN 'Friday' THEN 5
                END, Schedule.subject_number""")
    schedule_data = cur.fetchall()
    cur.close()
    return render_template('admin/admin_schedule.html', schedule_data=schedule_data, subjects=subjects, classes_data=classes_data, timetable_data=timetable_data)


def get_timetable_info():
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""
        SELECT timetable.timetable_id, subject.subject_name, teacher.full_name
        FROM timetable
        INNER JOIN subject on timetable.subject_number = subject.subject_number
        INNER JOIN teacher on timetable.employee_number = teacher.employee_number
    """)
    timetable_data = cur.fetchall()
    return timetable_data

@app.route('/add_schedule_component', methods=['POST'])
def add_schedule_component():
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if request.method == 'POST':
        timetable_id = request.form['timetable_id']
        class_name = request.form['class_name']
        day_of_week = request.form['day_of_week']
        subject_number = request.form['subject_number']
        cur.execute(
            "INSERT INTO schedule (class_number, timetable_id, subject_number, day) VALUES (%s, %s, %s, %s)", (class_name, timetable_id, subject_number, day_of_week))
        conn.commit()
    return redirect(url_for('admin_schedule'))

def get_classes():
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""SELECT class_number, class_name from classes""")
    classes_data = cur.fetchall()
    return classes_data

@app.route('/delete_schedule_row/<id>', methods=['POST', 'GET'])
def delete_schedule_row(id):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute('DELETE FROM schedule WHERE schedule_id = %s', (id,))
    conn.commit()
    return redirect(url_for('admin_schedule'))


if __name__ == "__main__":
    app.run(debug=True)
