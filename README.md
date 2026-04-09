# 📘 School Diary – Information System

![Python](https://img.shields.io/badge/Python-3.x-blue)
![Flask](https://img.shields.io/badge/Flask-Web%20Framework-black)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-blue)
![Status](https://img.shields.io/badge/status-academic%20project-green)
![License](https://img.shields.io/badge/license-educational-lightgrey)

Web-based information system for managing school processes: students, teachers, classes, schedules, homework, and grades.

This project was developed as a **course project in "Database Organization"**.

---

## 🎯 Project Goal

The goal of this project is to design and implement an information system that:

* simplifies the educational process
* provides centralized data management
* ensures role-based access for different users

---

## 🧑‍🤝‍🧑 User Roles

The system supports 3 types of users:
<img src="https://img.shields.io/badge/Administrator-👨‍💼-blue" style="vertical-align: middle; height: 25px;">
<img src="https://img.shields.io/badge/Teacher-👨‍🏫-green" style="vertical-align: middle; height: 25px;">
<img src="https://img.shields.io/badge/Student-👨‍🎓-orange" style="vertical-align: middle; height: 25px;">

### 👨‍💼 Administrator

* Manage students, teachers, classes, and subjects
* Create and edit schedules
* Assign teachers to subjects
* View statistics of teacher activity

### 👨‍🏫 Teacher

* Add homework and comments
* Publish announcements
* Conduct lessons (assign grades, attendance)
* View student performance and statistics

### 👨‍🎓 Student

* View homework
* Check grades and comments
* View schedule
* Read announcements

---

## 🏗️ Architecture

The system is built using a **three-tier architecture**:

1. **Presentation Layer** – HTML templates (Jinja2)
2. **Application Layer** – Flask backend
3. **Data Layer** – PostgreSQL database

Additionally, the project follows the **MVVM (Model-View-ViewModel)** pattern:

* **Model** → Database
* **View** → HTML templates
* **ViewModel** → Flask routes and logic

---

## 🧠 Database Design

The database includes the following main entities:

* `student`
* `teacher`
* `classes`
* `subject`
* `schedule`
* `timetable`
* `grade`
* `homework`
* `homework_comment`
* `notification`

### 🔗 Relationships

* One-to-many relationships (e.g. student → grades)
* Conditional relationships (e.g. class teacher)

### 🗺️ ER Diagram (Crow's Foot notation)

![ER Diagram](https://raw.githubusercontent.com/chessmaster987/School-diary/docs/readme-improvements/database/er_diagram.jpg)

*ER Diagram illustrating the database structure using Crow's Foot notation. This diagram helps understand the overall database design and how data flows between different tables in the system.*

The database structure is defined in:

```bash
database/schema.sql
```

---

## 🛠️ Tech Stack

* **Backend:** Python, Flask
* **Database:** PostgreSQL
* **Frontend:** HTML, CSS, Bootstrap
* **Template Engine:** Jinja2
* **DB Adapter:** psycopg2

---

## 📦 Installation

### 1. Clone repository

```bash
git clone https://github.com/chessmaster987/School-diary.git
cd School-diary
```

---

### 2. Create virtual environment

```bash
python -m venv venv
```

---

### 3. Activate environment

**Windows:**

```bash
venv\Scripts\activate
```

**Linux/Mac:**

```bash
source venv/bin/activate
```

---

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 🐘 Database Setup (PostgreSQL)

### Create database

```sql
CREATE DATABASE "Bazu Danych";
```

---

### Import schema

```bash
psql -U connection_user -d "Bazu Danych" -f database/schema.sql
```

---

## ⚙️ Configuration

Database connection is defined in `app.py`.

Example:

```python
connection = {
    "database": "Bazu Danych",
    "user": "connection_user",
    "password": "connection_user",
    "host": "localhost",
    "port": "5432"
}
```

---

## ▶️ Running the App

```bash
python app.py
```

Open in browser:

```
http://127.0.0.1:5000
```

---

## 📊 System Features

### 📌 Core functionality

* User authentication
* Role-based access control
* Schedule management
* Homework system
* Grade tracking
* Notifications system

---

### 📈 Advanced features

* Student performance statistics
* Attendance tracking
* Teacher activity reports
* Class ranking system

---

## 🔐 Security

The system implements:

* Authentication system
* Role-based authorization
* Separation of user permissions

---

## 🧪 Testing

Manual testing approach:

1. Verify login & roles
2. Check CRUD operations
3. Validate database interactions
4. Test edge cases

---

## 📁 Project Structure

```
School-diary/
│
├── app.py
├── requirements.txt
│
├── database/
│   └── schema.sql
│
├── templates/
│
├── static/
│
└──
```

---

## 📚 Academic Context

This project was developed at:

**Odesa National University named after I. I. Mechnikov**

Course: *Database Organization*

---

## 👨‍💻 Author

**Vladyslav Lavrov**

* GitHub: https://github.com/chessmaster987
* LinkedIn: https://www.linkedin.com/in/vlad-lavrov

---

## 📄 License

This project is created for educational purposes.
