from flask import Flask, session, render_template, request, redirect, url_for, flash
import psycopg2  # pip install psycopg2
import psycopg2.extras

app = Flask(__name__)
app.secret_key = "vlad"

DB_HOST = "localhost"
DB_NAME = "Bazu Danych"
DB_USER = "postgres"
DB_PASS = "25082003"

conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER,
                        password=DB_PASS, host=DB_HOST)


#@app.route("/main", methods=['GET', 'POST'])
#def main():
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
            "SELECT * FROM login WHERE username = %s AND password = %s", (username, password))
        rows = cur.fetchall()

        cur.execute("SELECT role FROM login WHERE username = %s", (username,))
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
    cur.execute("""SELECT student.login, student.full_name, classes.class_name FROM student 
                INNER JOIN classes ON classes.class_number = student.class_number""")
    student_data = cur.fetchall()
    return render_template('admin/info_student.html', student_data=student_data)


@app.route('/info_teacher', methods=['GET', 'POST'])
def info_teacher():
    cur = conn.cursor()
    cur.execute("""SELECT teacher.employee_number, teacher.login, teacher.full_name, subject.subject_name, COALESCE(classes.class_name, 'Нет класса') AS class_name
                FROM teacher
                LEFT JOIN classes ON classes.class_number = teacher.class_number
                INNER JOIN timetable on timetable.employee_number = teacher.employee_number
                INNER JOIN subject on subject.subject_number = timetable.subject_number
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


@app.route('/student', methods=['GET'])
def student():
    username = session.get('username', None)
    return render_template('student/student.html', username=username)


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
        full_name = request.form['full_name']
        class_number = request.form['class_number']
        cur.execute(
            "INSERT INTO student (login, full_name, class_number) VALUES (%s,%s,%s)", (login, full_name, class_number))
        conn.commit()
        flash('Student Added successfully')
        return redirect(url_for('info_student'))

@app.route('/edit/<id>', methods=['POST', 'GET'])
def get_employee(id):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute('SELECT * FROM student WHERE login = %s', (id,))
    data = cur.fetchall()
    cur.close()
    print(data[0])
    return render_template('edit.html', student=data[0])


@app.route('/update/<id>', methods=['POST', 'GET'])
def update_student(id):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if request.method == 'POST':
        login = request.form['login']
        full_name = request.form['full_name']
        class_number = request.form['class_number']

        cur.execute("""
            UPDATE student
            SET login = %s,
                full_name = %s,
                class_number = %s
            WHERE login = %s
        """, (login, full_name, class_number, id))
        flash('Student Updated Successfully')
        conn.commit()
        return redirect(url_for('info_student'))


@app.route('/delete/<id>', methods=['POST', 'GET'])
def delete_student(id):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute('DELETE FROM student WHERE login = %s', (id,))
    conn.commit()
    flash('Student Removed Successfully')
    return redirect(url_for('info_student'))


if __name__ == "__main__":
    app.run(debug=True)
