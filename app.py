from flask import Flask, session, render_template, request, redirect, url_for, flash
import psycopg2  # pip install psycopg2
import psycopg2.extras
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from datetime import datetime
from collections import defaultdict

app = Flask(__name__)
app.secret_key = "vlad"

connect_user = {
    'database': 'Bazu Danych',
    'user': 'connect_user',
    'password': 'connect_user',
    'host': 'localhost',
    'port': '5432'
}

administrator = {
    'database': 'Bazu Danych',
    'user': 'administrator',
    'password': 'administrator',
    'host': 'localhost',
    'port': '5432'
}

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = psycopg2.connect(**connect_user)
        conn.commit()  
        cur = conn.cursor()
        cur.execute("""select * from current_user""")
        result = cur.fetchall()
        print(result)
        cur.execute(
            "SELECT username FROM login WHERE username = %s AND password = %s", (username, password))
        user = cur.fetchone()

        if user:
            cur.execute(
                "SELECT role FROM login WHERE username = %s", (username,))
            role = cur.fetchone()
            conn.close()
            if role and role[0] == 'admin':
                session['username'] = username
                conn = psycopg2.connect(**administrator)
                conn.commit()
                cur = conn.cursor()
                cur.execute("""select * from current_user""")
                result = cur.fetchall()
                print(result)
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
    cur.execute("""select class_number, class_name from classes""")
    classes = cur.fetchall()
    return render_template('admin/info_student.html', student_data=student_data, classes=classes)


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
    cur.execute("""select subject_number, subject_name from subject""")
    subjects = cur.fetchall()
    cur.execute(
        """select teacher.employee_number, teacher.full_name from teacher""")
    teachers = cur.fetchall()
    return render_template('admin/timetable.html', timetable_data=timetable_data, subjects=subjects, teachers=teachers)


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

        # Отримуємо усі існуючі назви класів
        cur.execute("""SELECT class_name FROM classes""")
        class_names = [row['class_name'] for row in cur.fetchall()]

        # Перевіряємо, чи назва класу вже існує
        if class_name in class_names:
            return 'Цей клас вже існує!'

        # Якщо назва класу унікальна, додаємо її до бази даних
        cur.execute("INSERT INTO classes (class_name) VALUES (%s)",
                    (class_name,))
        conn.commit()
        return redirect(url_for('info_classes'))


@app.route('/add_subject', methods=['POST'])
def add_subject():
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if request.method == 'POST':
        subject_name = request.form['subject_name']

        # Отримуємо усі існуючі назви предметів
        cur.execute("""SELECT subject_name FROM subject""")
        existing_subjects = [row['subject_name'] for row in cur.fetchall()]

        # Перевіряємо, чи назва предмету вже існує
        if subject_name in existing_subjects:
            return 'Цей предмет вже існує!'

        # Якщо назва предмету унікальна, додаємо її до бази даних
        cur.execute(
            "INSERT INTO subject (subject_name) VALUES (%s)", (subject_name,))
        conn.commit()
        return redirect(url_for('info_subject'))


@app.route('/add_timetable', methods=['POST'])
def add_timetable():
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if request.method == 'POST':
        subject_name = request.form['subject_name']
        teacher_name = request.form['teacher_name']
        # Перевірка, чи існує вже запис в розкладі з такими ж значеннями subject_name і teacher_name
        cur.execute("""SELECT * FROM timetable
                       INNER JOIN subject ON timetable.subject_number = subject.subject_number
                       INNER JOIN teacher ON timetable.employee_number = teacher.employee_number
                       WHERE subject.subject_number = %s AND teacher.employee_number = %s""", (subject_name, teacher_name))
        existing_entry = cur.fetchone()

        if existing_entry:
            return 'Запис в розкладі з такими ж значеннями предмету і вчителя вже існує!'

        # Якщо запис унікальний, додаємо його до таблиці розкладу
        cur.execute("INSERT INTO timetable (subject_number, employee_number) VALUES (%s, %s)",
                    (subject_name, teacher_name))
        conn.commit()
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
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""SELECT s.full_name AS student_name, c.class_name, t.full_name AS class_teacher
                FROM Student s
                JOIN Classes c ON s.class_number = c.class_number
                INNER JOIN Teacher t ON c.class_number = t.class_number
                INNER JOIN Timetable tt ON t.employee_number = tt.employee_number
                INNER JOIN Subject sub ON tt.subject_number = sub.subject_number
                WHERE s.login = %s
                GROUP BY s.full_name, c.class_name, t.full_name;""", (username,))
    student_info = cur.fetchone()
    return render_template('student/student.html', username=username, student_info=student_info)


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

    cur.execute("""SELECT DISTINCT teacher.full_name, subject.subject_name
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


@app.route('/teacher_classes_detail/<class_name>', methods=['GET', 'POST'])
def teacher_classes_detail(class_name):
    username = session.get('username', None)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    selected_student = request.args.get('selected_student')
    session['selected_student'] = selected_student
    print(session['selected_student'])
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
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    zvit_info = []
    cur.execute(
        """select teacher.employee_number, teacher.full_name from teacher""")
    teacher_data = cur.fetchall()
    if request.method == 'POST':
        teacher = request.form['teacher']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(
            """SELECT * FROM teacher_report(%s, %s, %s)""", (teacher, start_date, end_date))
        zvit_info = cur.fetchall()

    return render_template('admin/zvit_teacher.html', zvit_data=zvit_info, teacher_data=teacher_data)


################################
@app.route('/homework', methods=['GET', 'POST'])
def homework():
    username = session.get('username', None)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if request.method == 'POST':
        selected_class = request.form['selected_class']
        session['selected_class'] = selected_class
        print(selected_class)
        return redirect(url_for('add_homework', class_name=selected_class))
    cur.execute("""SELECT DISTINCT classes.class_number, classes.class_name 
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
        SELECT DISTINCT subject.subject_name
        FROM teacher
        INNER JOIN timetable on teacher.employee_number = timetable.employee_number
        INNER JOIN subject on timetable.subject_number = subject.subject_number
		INNER JOIN schedule on timetable.timetable_id = schedule.timetable_id
		INNER JOIN classes on schedule.class_number = classes.class_number
		WHERE teacher.login = %s and classes.class_number = %s""", (username, session['selected_class']))

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
        cur.execute("""SELECT schedule_id 
                    FROM schedule 
                    INNER JOIN timetable on schedule.timetable_id = timetable.timetable_id
                    INNER JOIN subject on timetable.subject_number = subject.subject_number
                    INNER JOIN classes on schedule.class_number = classes.class_number
                    WHERE classes.class_number = %s and subject.subject_number = %s""", (session['selected_class'], teacher_subject))
        lesson_id_data = cur.fetchone()[0]
        homework_description = request.form['homework_description']

        cur.execute(
            "INSERT INTO homework (homework_text, lesson_id, date) VALUES (%s,%s,%s)", (homework_description, lesson_id_data, date))
        conn.commit()
        return redirect(url_for('add_homework'))

    cur.execute("""SELECT homework.homework_number, homework.date, subject.subject_name, homework.homework_text
                FROM homework
                INNER JOIN schedule on homework.lesson_id = schedule.schedule_id
                INNER JOIN timetable on schedule.timetable_id = timetable.timetable_id
                INNER JOIN subject on timetable.subject_number = subject.subject_number
                INNER JOIN teacher on timetable.employee_number = teacher.employee_number
                INNER JOIN classes on schedule.class_number = classes.class_number
                WHERE teacher.login = %s and classes.class_number = %s""", (username, session['selected_class']))
    teacher_homework = cur.fetchall()
    cur.close()
    teacher_subjects = get_teacher_subjects()
    return render_template('teacher/add_homework.html', teacher_subjects=teacher_subjects, teacher_homework=teacher_homework)


@app.route('/homework_comment', methods=['GET', 'POST'])
def homework_comment():
    username = session.get('username', None)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""select homeworkcomment.comment_number, homeworkcomment.date, homeworkcomment.login, classes.class_name, subject.subject_name, homeworkcomment.comment
                from homeworkcomment
                INNER JOIN homework on homeworkcomment.homework_number = homework.homework_number
                INNER JOIN schedule on homework.lesson_id = schedule.schedule_id
                INNER JOIN timetable on schedule.timetable_id = timetable.timetable_id
                INNER JOIN subject on timetable.subject_number = subject.subject_number
                INNER JOIN teacher on timetable.employee_number = teacher.employee_number
                INNER JOIN student on homeworkcomment.login = student.login
                INNER JOIN classes on student.class_number = classes.class_number
                WHERE teacher.login = %s""", (username,))
    homework_comment = cur.fetchall()
    cur.execute("""select distinct student.login from student
                inner join homeworkcomment on student.login = homeworkcomment.login
                inner join homework on homeworkcomment.homework_number = homework.homework_number
                inner join schedule on homework.lesson_id = schedule.schedule_id
                inner join classes on schedule.class_number = classes.class_number 
                where classes.class_number = %s""", (session['selected_class'],))
    students = cur.fetchall()
    if request.method == 'POST':
        students_list = request.form['students_list']
        homework_number = request.form['homework_number']
        comment = request.form['comment']
        try:
            cur.execute("""INSERT INTO homeworkcomment (login, homework_number, comment) VALUES (%s, %s, %s)""",
                        (students_list, homework_number, comment))
            conn.commit()
            return redirect(url_for('add_homework'))
        except psycopg2.DatabaseError as e:
            error_message = str(e)
            if 'RAISE EXCEPTION' in error_message:
                # Обробка повідомлення про конфлікт
                conn.rollback()
                return f"Помилка: {error_message}"
            else:
                # Інші помилки бази даних
                conn.rollback()
                return f"Помилка бази даних: {error_message}"
        finally:
            cur.close()
    return render_template('teacher/homework_comment.html', homework_comment=homework_comment, students=students)


@app.route('/delete_comment/<id>', methods=['GET', 'POST'])
def delete_comment(id):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute('DELETE FROM homeworkcomment WHERE comment_number = %s', (id,))
    conn.commit()
    return redirect(url_for('add_homework'))

################################


@app.route('/edit_homework/<id>', methods=['GET', 'POST'])
def edit_homework(id):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute(
        """select homework_number, homework_text from homework where homework_number = %s""", (id,))
    homework_data = cur.fetchall()
    print(homework_data)
    return render_template('teacher/edit_homework.html', homework_data=homework_data[0])


@app.route('/update_homework/<id>', methods=['POST', 'GET'])
def update_homework(id):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if request.method == 'POST':
        homework_description = request.form['homework_description']
        cur.execute("""
            UPDATE homework
            SET homework_text = %s
            WHERE homework_number = %s
        """, (homework_description, id))
        conn.commit()
        return redirect(url_for('add_homework'))


@app.route('/delete_homework/<id>', methods=['GET', 'POST'])
def delete_homework(id):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute('DELETE FROM homework WHERE homework_number = %s', (id,))
    conn.commit()
    return redirect(url_for('add_homework'))


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
                SELECT DISTINCT classes.class_number, classes.class_name
                FROM teacher
                INNER JOIN timetable on teacher.employee_number = timetable.employee_number
                INNER JOIN schedule on timetable.timetable_id = schedule.timetable_id
                INNER JOIN classes on schedule.class_number = classes.class_number
                WHERE teacher.login = %s""", (username,))

    classes = cur.fetchall()
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

        try:
            cur.execute(
                "INSERT INTO schedule (class_number, timetable_id, subject_number, day) VALUES (%s, %s, %s, %s)",
                (class_name, timetable_id, subject_number, day_of_week)
            )
            conn.commit()
        except psycopg2.DatabaseError as e:
            error_message = str(e)
            if 'RAISE EXCEPTION' in error_message:
                # Обробка повідомлення про конфлікт
                conn.rollback()
                # return f"Помилка: {error_message}"
                return "Цей вчитель вже зайнятий на обраній парі у обраний день"
            else:
                # Інші помилки бази даних
                conn.rollback()
                # return f"Помилка бази даних: {error_message}"
                return "Цей вчитель вже зайнятий на обраній парі у обраний день"
        finally:
            cur.close()

        # cur.execute(
        #    "INSERT INTO schedule (class_number, timetable_id, subject_number, day) VALUES (%s, %s, %s, %s)", (class_name, timetable_id, subject_number, day_of_week))
        # conn.commit()
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


@app.route('/zvit_uchni_avg_grade/<selected_student>', methods=['POST', 'GET'])
def zvit_uchni_avg_grade(selected_student):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    session['selected_student'] = selected_student
    avg_grades = []
    if request.method == 'POST':
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        cur.execute("""WITH summary_data AS (
                SELECT grade.login, subject.subject_name,
                    AVG(grade) AS avg_grade
                  FROM Grade
	                INNER JOIN schedule on grade.lesson_id = schedule.schedule_id
                	INNER JOIN timetable on schedule.timetable_id = timetable.timetable_id
                	INNER JOIN subject on timetable.subject_number = subject.subject_number
				  WHERE date >= DATE %s AND date <= %s
                  GROUP BY login, subject_name
                )
                SELECT subject_name, avg_grade
                FROM
                  summary_data
                WHERE login = %s""", (start_date, end_date, selected_student))
        session['selected_student'] = selected_student
        avg_grades = cur.fetchall()
    return render_template('teacher/zvit_uchni_avg_grade.html', avg_grades=avg_grades)


@app.route('/teaching_lesson_class_choice', methods=['POST', 'GET'])
def teaching_lesson_class_choice():
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
    return render_template('teacher/teaching_lesson_class_choice.html', teacher_classes=teacher_classes)


@app.route('/teacher_lesson/<class_name>', methods=['POST', 'GET'])
def teacher_lesson(class_name):
    username = session.get('username', None)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    student_data = get_students(class_name)
    subjects = get_teacher_subjects()
    lesson_id = get_lesson_id(class_name)
    if request.method == 'POST':
        start_date = request.form['start_date']
        lesson_id = request.form['lesson_id']
        student_name = request.form['student_name']
        grade_status = request.form['grade_status']
        grade_number = request.form['grade_number']
        presence_mark = request.form['presence_mark']
        try:
            cur.execute("""INSERT INTO Grade (date, login, lesson_id, grade, grade_type, presence_mark) 
                    VALUES (%s, %s, %s, %s, %s, %s) """, (start_date, student_name, lesson_id, grade_number, grade_status, presence_mark))
            conn.commit()
            return redirect(url_for('teaching_lesson_class_choice'))
        except psycopg2.DatabaseError as e:
            error_message = str(e)
            if 'RAISE EXCEPTION' in error_message:
                # Обробка повідомлення про конфлікт
                conn.rollback()
                return f"Помилка: {error_message}"
            else:
                # Інші помилки бази даних
                conn.rollback()
                return f"Помилка бази даних: {error_message}"
        finally:
            cur.close()
    return render_template('teacher/teacher_lesson.html', student_data=student_data, subjects=subjects, lesson_id=lesson_id, class_name=class_name)


def get_lesson_id(class_name):
    username = session.get('username', None)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute(
        """SELECT class_number from classes where class_name = %s""", (class_name,))
    class_number = cur.fetchone()[0]
    cur.execute("""SELECT schedule.schedule_id, subject.subject_name, schedule.subject_number, schedule.day
                from schedule
                INNER JOIN classes on schedule.class_number = classes.class_number
                INNER JOIN timetable on schedule.timetable_id = timetable.timetable_id
                INNER JOIN subject on timetable.subject_number = subject.subject_number
                INNER JOIN teacher on timetable.employee_number = teacher.employee_number
                WHERE classes.class_number = %s and teacher.login = %s""", (class_number, username))
    lesson_id = cur.fetchall()
    return lesson_id


def get_students(class_name):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""SELECT login FROM student 
                INNER JOIN classes on student.class_number = classes.class_number
                WHERE classes.class_name =  %s""", (class_name,))
    students = cur.fetchall()
    return students


@app.route('/show_teacher_lessons/<class_name>', methods=['POST', 'GET'])
def show_teacher_lessons(class_name):
    username = session.get('username', None)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute(
        """SELECT class_number from classes where class_name = %s""", (class_name,))
    class_number = cur.fetchone()[0]
    session['class_name'] = class_name
    cur.execute("""select grade.grade_number, grade.date, grade.login, grade.lesson_id,grade.grade, grade_type, grade.presence_mark
                from grade
                INNER JOIN student on grade.login = student.login
                INNER JOIN classes on student.class_number = classes.class_number
                INNER JOIN schedule on grade.lesson_id = schedule.schedule_id
                INNER JOIN timetable on schedule.timetable_id = timetable.timetable_id
                INNER JOIN teacher on timetable.employee_number = teacher.employee_number
                WHERE classes.class_number = %s and teacher.login = %s""", (class_number, username))
    show_lessons = cur.fetchall()
    return render_template('teacher/show_teacher_lessons.html', show_lessons=show_lessons)


@app.route('/delete_show_lessons/<id>', methods=['POST', 'GET'])
def delete_show_lessons(id):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute('DELETE FROM grade WHERE grade_number = %s', (id,))
    conn.commit()
    return redirect(url_for('show_teacher_lessons', class_name=session['class_name']))


@app.route('/edit_show_lessons/<id>', methods=['POST', 'GET'])
def edit_show_lessons(id):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""select grade.grade_number, grade.grade, grade.grade_type, grade.presence_mark
                from grade
                where grade.grade_number = %s""", (id,))
    grade = cur.fetchone()
    return render_template('teacher/edit_show_lessons.html', grade=grade)


@app.route('/update_show_lessons/<id>', methods=['POST', 'GET'])
def update_show_lessons(id):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if request.method == 'POST':
        grade = request.form['grade']
        grade_type = request.form['grade_type']
        presence_mark = request.form['presence_mark']
        cur.execute("""
            UPDATE grade
            SET grade = %s, grade_type = %s, presence_mark = %s
            WHERE grade_number = %s
        """, (grade, grade_type, presence_mark, id))
        conn.commit()
    return redirect(url_for('show_teacher_lessons', class_name=session['class_name']))


@app.route('/absence_ranking', methods=['GET', 'POST'])
def absence_ranking():
    username = session.get('username', None)
    presence_data = []
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""SELECT DISTINCT classes.class_number, classes.class_name 
                FROM teacher 
                INNER JOIN timetable on teacher.employee_number = timetable.employee_number
                INNER JOIN schedule on timetable.employee_number = schedule.timetable_id
                INNER JOIN classes on schedule.class_number = classes.class_number
                WHERE teacher.login = %s""", (username,))
    class_data = cur.fetchall()
    if request.method == 'POST':
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        class_name = request.form['class_name']
        cur.execute("""select student.login, COUNT(grade.presence_mark)
                    from grade
	                INNER JOIN student on grade.login = student.login
					INNER JOIN schedule on grade.lesson_id = schedule.schedule_id
					INNER JOIN classes on schedule.class_number = classes.class_number
				  WHERE date >= DATE %s AND date <= %s AND classes.class_number = %s
                  GROUP BY student.login""", (start_date, end_date, class_name))
        presence_data = cur.fetchall()
    return render_template('teacher/absence_ranking.html', class_data=class_data, presence_data=presence_data)

# ОЦІНКИ УЧНЯ!!!


@app.route('/student_grades', methods=['GET', 'POST'])
def student_grades():
    username = session.get('username', None)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""select grade.date, subject.subject_name, grade.grade, grade.grade_type
                from grade
                INNER JOIN schedule on grade.lesson_id = schedule.schedule_id
                INNER JOIN timetable on schedule.timetable_id = timetable.timetable_id
                INNER JOIN subject on timetable.subject_number = subject.subject_number
                WHERE grade.login = %s
                ORDER BY date DESC""", (username,))
    grade_info = cur.fetchall()
    cur.execute("""select distinct subject.subject_name
                from grade
                INNER JOIN schedule on grade.lesson_id = schedule.schedule_id
                INNER JOIN timetable on schedule.timetable_id = timetable.timetable_id
                INNER JOIN subject on timetable.subject_number = subject.subject_number
                WHERE grade.login = %s""", (username,))
    subjects_for_grade = cur.fetchall()
    return render_template('student/student_grades.html', grade_info=grade_info, subjects_for_grade=subjects_for_grade)


@app.route('/academic_performance_ranking', methods=['GET', 'POST'])
def academic_performance_ranking():
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    data_academic_performance_ranking = []
    cur.execute("""select subject_number, subject_name from subject""")
    subject_info = cur.fetchall()
    cur.execute("""select class_number, class_name from classes""")
    classes_info = cur.fetchall()
    if request.method == 'POST':
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        subject = request.form['subject']
        class_number = request.form['class_number']
        cur.execute("""SELECT * FROM academic_performance_ranking(%s, %s, %s, %s)""",
                    (start_date, end_date, subject, class_number))
        data_academic_performance_ranking = cur.fetchall()
    return render_template('teacher/academic_performance_ranking.html', subject_info=subject_info, classes_info=classes_info, data_academic_performance_ranking=data_academic_performance_ranking)


@app.route('/statistics_poor_grades', methods=['GET', 'POST'])
def statistics_poor_grades():
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    data_statistics_poor_grades = []
    cur.execute("""select class_number, class_name from classes""")
    classes = cur.fetchall()
    if request.method == 'POST':
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        class_num = request.form['class_num']
        cur.execute("""SELECT * FROM statistics_poor_grades(%s, %s, %s)""",
                    (start_date, end_date, class_num))
        data_statistics_poor_grades = cur.fetchall()
    return render_template('teacher/statistics_poor_grades.html', classes=classes, data_statistics_poor_grades=data_statistics_poor_grades)


if __name__ == "__main__":
    app.run(debug=True)
