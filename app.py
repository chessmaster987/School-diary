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


@app.route("/main", methods=['GET', 'POST'])
def main():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'crud':
            return redirect('/crud')
        elif action == 'logout':
            return redirect('/logout')

    return render_template('main.html')


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM login WHERE username = %s AND password = %s", (username, password))
        rows = cur.fetchall()
        # conn.close()

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
            print(session['username'])
            return redirect('/student')
        # if len(rows) > 0:
            # assuming the username is in your login table
            # session['username'] = username
            # flash(f'Logged in as {session["username"]}')
            # return redirect('/main')
        else:
            return 'Неправильний логін або пароль'

    return render_template('login.html')


@app.route('/admin', methods=['GET'])
def admin():
    username = session.get('username', None)
    return render_template('admin/admin.html', username=username)
    

@app.route('/teacher', methods=['GET'])
def teacher():
    username = session.get('username', None)
    return render_template('teacher/teacher.html', username=username)
    
@app.route('/student', methods=['GET'])
def student():
    username = session.get('username', None)
    return render_template('student/student.html', username=username)

@app.route('/logout')
def logout():
    if request.method == 'GET':
        # Код для виходу
        # ...
        return redirect(url_for('login'))  # Переадресація на сторінку login

    # удалить из сессии имя пользователя, если оно там есть
    # session.pop('username', None)
    # return redirect(url_for('login'))


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
        fname = request.form['fname']
        lname = request.form['lname']
        email = request.form['email']
        cur.execute(
            "INSERT INTO students (fname, lname, email) VALUES (%s,%s,%s)", (fname, lname, email))
        conn.commit()
        flash('Student Added successfully')
        return redirect(url_for('Index'))


# @app.route('/info', methods=['GET'])
# def infO():
#    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
#    cur.execute(
#        "SELECT * FROM student")
#    conn.commit()

@app.route('/edit/<id>', methods=['POST', 'GET'])
def get_employee(id):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute('SELECT * FROM students WHERE id = %s', (id,))
    data = cur.fetchall()
    cur.close()
    print(data[0])
    return render_template('edit.html', student=data[0])


@app.route('/update/<id>', methods=['POST'])
def update_student(id):
    if request.method == 'POST':
        fname = request.form['fname']
        lname = request.form['lname']
        email = request.form['email']

        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            UPDATE students
            SET fname = %s,
                lname = %s,
                email = %s
            WHERE id = %s
        """, (fname, lname, email, id))
        flash('Student Updated Successfully')
        conn.commit()
        return redirect(url_for('Index'))


@app.route('/delete/<string:id>', methods=['POST', 'GET'])
def delete_student(id):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute('DELETE FROM students WHERE id = {0}'.format(id))
    conn.commit()
    flash('Student Removed Successfully')
    return redirect(url_for('Index'))

if __name__ == "__main__":
    app.run(debug=True)
