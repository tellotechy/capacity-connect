from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid


app = Flask(__name__)
app.secret_key = "capacity-connect-secret-key"


# ==================================================
# DATABASE CONNECTION
# ==================================================

def get_db_connection():
    connection = sqlite3.connect("capacity_connect.db")
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


# ==================================================
# CERTIFICATE CODE GENERATOR
# ==================================================

def generate_certificate_code():
    return (
        "CC-"
        + datetime.now().strftime("%Y%m%d")
        + "-"
        + uuid.uuid4().hex[:8].upper()
    )


# ==================================================
# CREATE DATABASE
# ==================================================

def create_database():

    connection = get_db_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS user_skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            skill_name TEXT NOT NULL,
            current_level INTEGER NOT NULL,
            required_level INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            skill_name TEXT NOT NULL,
            description TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            duration TEXT NOT NULL,
            modules INTEGER NOT NULL
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS enrollments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            progress INTEGER DEFAULT 0,
            status TEXT DEFAULT 'Enrolled',
            score INTEGER,
            UNIQUE(user_id, course_id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (course_id) REFERENCES courses(id)
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS course_modules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            module_order INTEGER NOT NULL,
            FOREIGN KEY (course_id) REFERENCES courses(id)
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS module_completions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            module_id INTEGER NOT NULL,
            completed INTEGER DEFAULT 1,
            UNIQUE(user_id, module_id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (module_id) REFERENCES course_modules(id)
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER UNIQUE NOT NULL,
            title TEXT NOT NULL,
            passing_score INTEGER DEFAULT 60,
            FOREIGN KEY (course_id) REFERENCES courses(id)
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assessment_id INTEGER NOT NULL,
            question TEXT NOT NULL,
            option_a TEXT NOT NULL,
            option_b TEXT NOT NULL,
            option_c TEXT NOT NULL,
            option_d TEXT NOT NULL,
            correct_answer TEXT NOT NULL,
            FOREIGN KEY (assessment_id) REFERENCES assessments(id)
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS assessment_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            assessment_id INTEGER NOT NULL,
            score INTEGER NOT NULL,
            passed INTEGER NOT NULL,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (assessment_id) REFERENCES assessments(id)
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS certificates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            certificate_code TEXT UNIQUE NOT NULL,
            issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, course_id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (course_id) REFERENCES courses(id)
        )
    """)


    # ==================================================
    # DEMO EMPLOYEE
    # ==================================================

    employee = connection.execute("""
        SELECT *
        FROM users
        WHERE email = ?
    """, (
        "rahul@demo.com",
    )).fetchone()

    if employee is None:

        employee_password = generate_password_hash(
            "demo123"
        )

        cursor = connection.execute("""
            INSERT INTO users
            (
                name,
                email,
                password,
                role
            )
            VALUES (?, ?, ?, ?)
        """, (
            "Rahul Sharma",
            "rahul@demo.com",
            employee_password,
            "employee"
        ))

        employee_id = cursor.lastrowid

    else:
        employee_id = employee["id"]


    # ==================================================
    # ADMIN
    # ==================================================

    admin = connection.execute("""
        SELECT *
        FROM users
        WHERE email = ?
    """, (
        "admin@capacityconnect.com",
    )).fetchone()

    if admin is None:

        admin_password = generate_password_hash(
            "admin123"
        )

        connection.execute("""
            INSERT INTO users
            (
                name,
                email,
                password,
                role
            )
            VALUES (?, ?, ?, ?)
        """, (
            "System Administrator",
            "admin@capacityconnect.com",
            admin_password,
            "admin"
        ))


    # ==================================================
    # DEMO EMPLOYEE SKILLS
    # ==================================================

    skill_count = connection.execute("""
        SELECT COUNT(*) AS total
        FROM user_skills
        WHERE user_id = ?
    """, (
        employee_id,
    )).fetchone()["total"]

    if skill_count == 0:

        demo_skills = [
            ("HTML", 75, 80),
            ("CSS", 60, 80),
            ("JavaScript", 35, 80),
            ("SQL", 55, 75)
        ]

        for skill in demo_skills:

            connection.execute("""
                INSERT INTO user_skills
                (
                    user_id,
                    skill_name,
                    current_level,
                    required_level
                )
                VALUES (?, ?, ?, ?)
            """, (
                employee_id,
                skill[0],
                skill[1],
                skill[2]
            ))


    # ==================================================
    # COURSES
    # ==================================================

    course_count = connection.execute("""
        SELECT COUNT(*) AS total
        FROM courses
    """).fetchone()["total"]

    if course_count == 0:

        courses_data = [
            (
                "JavaScript Core Skills",
                "JavaScript",
                "Build strong JavaScript fundamentals including variables, functions, DOM concepts and modern programming techniques.",
                "Intermediate",
                "6 Hours",
                6
            ),
            (
                "Modern CSS Essentials",
                "CSS",
                "Learn responsive layouts, Flexbox, Grid and modern styling techniques for professional web applications.",
                "Beginner",
                "4 Hours",
                5
            ),
            (
                "SQL Fundamentals",
                "SQL",
                "Learn database fundamentals, queries, filtering, joins and practical relational database concepts.",
                "Beginner",
                "5 Hours",
                5
            ),
            (
                "HTML Advanced Concepts",
                "HTML",
                "Improve semantic HTML, accessibility, forms and professional web page structure.",
                "Intermediate",
                "3 Hours",
                4
            )
        ]

        for course in courses_data:

            connection.execute("""
                INSERT INTO courses
                (
                    title,
                    skill_name,
                    description,
                    difficulty,
                    duration,
                    modules
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, course)

        connection.commit()


    # ==================================================
    # COURSE MODULES
    # ==================================================

    all_courses = connection.execute("""
        SELECT *
        FROM courses
        ORDER BY id
    """).fetchall()

    for course in all_courses:

        module_count = connection.execute("""
            SELECT COUNT(*) AS total
            FROM course_modules
            WHERE course_id = ?
        """, (
            course["id"],
        )).fetchone()["total"]

        if module_count == 0:

            if course["skill_name"] == "JavaScript":

                modules = [
                    (
                        "JavaScript Fundamentals",
                        """JavaScript is a programming language used to add logic and interactivity to web applications.

HTML provides structure.
CSS provides design.
JavaScript provides behaviour and functionality.

JavaScript can respond to user actions such as button clicks, form submissions and keyboard input.""",
                        1
                    ),
                    (
                        "Variables & Data Types",
                        """Variables are used to store information inside a JavaScript program.

Modern JavaScript commonly uses let and const.

Example:

let userName = "Rahul";
const requiredLevel = 80;

Common data types include strings, numbers, booleans, arrays and objects.""",
                        2
                    ),
                    (
                        "Operators & Conditions",
                        """Operators allow JavaScript to perform calculations and comparisons.

Examples include +, -, *, /, ===, > and <.

Conditions allow a program to make decisions.

Example:

if (score >= 60) {
    console.log("Passed");
} else {
    console.log("Try Again");
}""",
                        3
                    ),
                    (
                        "Functions",
                        """Functions are reusable blocks of code.

They help keep applications organized and reduce repeated code.

Example:

function calculateGap(required, current) {
    return required - current;
}""",
                        4
                    ),
                    (
                        "DOM Basics",
                        """DOM stands for Document Object Model.

JavaScript can use the DOM to interact with elements on a webpage.

Example:

document.getElementById("message");

Developers can dynamically change page content using DOM methods.""",
                        5
                    ),
                    (
                        "Course Summary",
                        """You have covered JavaScript fundamentals, variables, operators, conditions, functions and DOM basics.

Complete the final assessment to demonstrate your improved competency.""",
                        6
                    )
                ]

            elif course["skill_name"] == "CSS":

                modules = [
                    (
                        "CSS Fundamentals",
                        "Learn how CSS controls the visual appearance of web pages.",
                        1
                    ),
                    (
                        "Box Model",
                        "Understand margin, border, padding and content.",
                        2
                    ),
                    (
                        "Flexbox",
                        "Create flexible layouts using Flexbox.",
                        3
                    ),
                    (
                        "CSS Grid",
                        "Build responsive layouts using CSS Grid.",
                        4
                    ),
                    (
                        "Responsive Design",
                        "Use media queries for different screen sizes.",
                        5
                    )
                ]

            elif course["skill_name"] == "SQL":

                modules = [
                    (
                        "Database Fundamentals",
                        "Understand relational databases, tables, rows and columns.",
                        1
                    ),
                    (
                        "SELECT Queries",
                        "Learn how to retrieve information using SELECT.",
                        2
                    ),
                    (
                        "Filtering Data",
                        "Use WHERE to filter database records.",
                        3
                    ),
                    (
                        "SQL Joins",
                        "Combine related information from multiple tables.",
                        4
                    ),
                    (
                        "SQL Practice",
                        "Apply SQL concepts to practical database problems.",
                        5
                    )
                ]

            else:

                modules = [
                    (
                        "Semantic HTML",
                        "Learn semantic HTML structure.",
                        1
                    ),
                    (
                        "Forms",
                        "Create structured HTML forms.",
                        2
                    ),
                    (
                        "Accessibility",
                        "Learn web accessibility principles.",
                        3
                    ),
                    (
                        "Advanced Structure",
                        "Build professional HTML page structures.",
                        4
                    )
                ]

            for module in modules:

                connection.execute("""
                    INSERT INTO course_modules
                    (
                        course_id,
                        title,
                        content,
                        module_order
                    )
                    VALUES (?, ?, ?, ?)
                """, (
                    course["id"],
                    module[0],
                    module[1],
                    module[2]
                ))


    # ==================================================
    # ASSESSMENTS + QUESTIONS
    # ==================================================

    all_courses = connection.execute("""
        SELECT *
        FROM courses
        ORDER BY id
    """).fetchall()

    for course in all_courses:

        assessment = connection.execute("""
            SELECT *
            FROM assessments
            WHERE course_id = ?
        """, (
            course["id"],
        )).fetchone()

        if assessment is None:

            cursor = connection.execute("""
                INSERT INTO assessments
                (
                    course_id,
                    title,
                    passing_score
                )
                VALUES (?, ?, ?)
            """, (
                course["id"],
                course["skill_name"] + " Final Assessment",
                60
            ))

            assessment_id = cursor.lastrowid

        else:
            assessment_id = assessment["id"]

        question_count = connection.execute("""
            SELECT COUNT(*) AS total
            FROM questions
            WHERE assessment_id = ?
        """, (
            assessment_id,
        )).fetchone()["total"]

        if question_count == 0:

            if course["skill_name"] == "JavaScript":

                questions = [
                    (
                        "Which keyword can be used to declare a variable in modern JavaScript?",
                        "style",
                        "let",
                        "select",
                        "print",
                        "b"
                    ),
                    (
                        "Which method selects an HTML element using its ID?",
                        "document.query",
                        "document.getElementById",
                        "document.selectId",
                        "document.find",
                        "b"
                    ),
                    (
                        "Which operator checks strict equality in JavaScript?",
                        "=",
                        "==",
                        "===",
                        "!=",
                        "c"
                    ),
                    (
                        "Which statement prints information to the browser console?",
                        "console.log()",
                        "print()",
                        "echo()",
                        "document.print()",
                        "a"
                    ),
                    (
                        "What can JavaScript be used for on a webpage?",
                        "Handling user interactions",
                        "Changing page content",
                        "Form validation",
                        "All of the above",
                        "d"
                    )
                ]

            elif course["skill_name"] == "CSS":

                questions = [
                    (
                        "What does CSS stand for?",
                        "Cascading Style Sheets",
                        "Computer Style System",
                        "Creative Style Syntax",
                        "Color Style Sheet",
                        "a"
                    ),
                    (
                        "Which CSS system is commonly used for one-dimensional layouts?",
                        "Table",
                        "Flexbox",
                        "Canvas",
                        "DOM",
                        "b"
                    ),
                    (
                        "Which property adds space inside an element's border?",
                        "margin",
                        "display",
                        "padding",
                        "position",
                        "c"
                    ),
                    (
                        "Which feature is commonly used for responsive breakpoints?",
                        "@media",
                        "@screen",
                        "@responsive",
                        "@mobile",
                        "a"
                    ),
                    (
                        "Which system is designed for two-dimensional layouts?",
                        "Grid",
                        "Float",
                        "Text Align",
                        "Border",
                        "a"
                    )
                ]

            elif course["skill_name"] == "SQL":

                questions = [
                    (
                        "Which command retrieves data from a table?",
                        "GET",
                        "SELECT",
                        "OPEN",
                        "READ",
                        "b"
                    ),
                    (
                        "Which clause filters rows?",
                        "WHERE",
                        "ORDER",
                        "TABLE",
                        "DATABASE",
                        "a"
                    ),
                    (
                        "Which operation combines related rows from tables?",
                        "JOIN",
                        "PRINT",
                        "CONNECT",
                        "MERGEFILE",
                        "a"
                    ),
                    (
                        "SQL is mainly used with what?",
                        "Images",
                        "Relational databases",
                        "CSS files",
                        "Videos",
                        "b"
                    ),
                    (
                        "Which command adds a new record?",
                        "INSERT",
                        "SELECT",
                        "SHOW",
                        "PRINT",
                        "a"
                    )
                ]

            else:

                questions = [
                    (
                        "Which HTML element represents the main heading?",
                        "<h1>",
                        "<p>",
                        "<div>",
                        "<span>",
                        "a"
                    ),
                    (
                        "Which element is used to create a form?",
                        "<input>",
                        "<form>",
                        "<section>",
                        "<table>",
                        "b"
                    ),
                    (
                        "Which attribute provides alternative text for an image?",
                        "title",
                        "src",
                        "alt",
                        "href",
                        "c"
                    ),
                    (
                        "Semantic HTML mainly improves what?",
                        "Structure and accessibility",
                        "Internet speed",
                        "Database storage",
                        "JavaScript execution",
                        "a"
                    ),
                    (
                        "Which element is used for navigation links?",
                        "<nav>",
                        "<img>",
                        "<footer-only>",
                        "<style>",
                        "a"
                    )
                ]

            for question in questions:

                connection.execute("""
                    INSERT INTO questions
                    (
                        assessment_id,
                        question,
                        option_a,
                        option_b,
                        option_c,
                        option_d,
                        correct_answer
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    assessment_id,
                    question[0],
                    question[1],
                    question[2],
                    question[3],
                    question[4],
                    question[5]
                ))


    # ==================================================
    # BACKFILL CERTIFICATES
    # ==================================================
    # Agar koi course pehle se Completed hai lekin
    # certificate missing hai, automatically create hoga.
    # ==================================================

    completed_enrollments = connection.execute("""
        SELECT
            user_id,
            course_id
        FROM enrollments
        WHERE status = 'Completed'
    """).fetchall()

    for completed in completed_enrollments:

        existing_certificate = connection.execute("""
            SELECT id
            FROM certificates
            WHERE user_id = ?
            AND course_id = ?
        """, (
            completed["user_id"],
            completed["course_id"]
        )).fetchone()

        if existing_certificate is None:

            connection.execute("""
                INSERT INTO certificates
                (
                    user_id,
                    course_id,
                    certificate_code
                )
                VALUES (?, ?, ?)
            """, (
                completed["user_id"],
                completed["course_id"],
                generate_certificate_code()
            ))

    connection.commit()
    connection.close()


# ==================================================
# DEFAULT SKILLS FOR NEW EMPLOYEE
# ==================================================

def create_default_skills(user_id):

    connection = get_db_connection()

    skills = [
        ("HTML", 40, 80),
        ("CSS", 35, 80),
        ("JavaScript", 20, 80),
        ("SQL", 25, 75)
    ]

    for skill in skills:

        connection.execute("""
            INSERT INTO user_skills
            (
                user_id,
                skill_name,
                current_level,
                required_level
            )
            VALUES (?, ?, ?, ?)
        """, (
            user_id,
            skill[0],
            skill[1],
            skill[2]
        ))

    connection.commit()
    connection.close()


# ==================================================
# UPDATE COURSE PROGRESS
# ==================================================

def update_course_progress(user_id, course_id):

    connection = get_db_connection()

    enrollment = connection.execute("""
        SELECT *
        FROM enrollments
        WHERE user_id = ?
        AND course_id = ?
    """, (
        user_id,
        course_id
    )).fetchone()

    if enrollment is None:
        connection.close()
        return

    # Completed course ko dobara downgrade nahi karenge.
    if enrollment["status"] == "Completed":
        connection.close()
        return

    total_modules = connection.execute("""
        SELECT COUNT(*) AS total
        FROM course_modules
        WHERE course_id = ?
    """, (
        course_id,
    )).fetchone()["total"]

    completed_modules = connection.execute("""
        SELECT COUNT(*) AS total

        FROM module_completions

        JOIN course_modules
        ON module_completions.module_id = course_modules.id

        WHERE module_completions.user_id = ?
        AND course_modules.course_id = ?
        AND module_completions.completed = 1
    """, (
        user_id,
        course_id
    )).fetchone()["total"]

    if total_modules > 0:

        progress = int(
            (completed_modules / total_modules) * 100
        )

    else:
        progress = 0

    if progress >= 100:
        status = "Learning Completed"

    elif progress > 0:
        status = "In Progress"

    else:
        status = "Enrolled"

    connection.execute("""
        UPDATE enrollments

        SET
            progress = ?,
            status = ?

        WHERE user_id = ?
        AND course_id = ?
    """, (
        progress,
        status,
        user_id,
        course_id
    ))

    connection.commit()
    connection.close()


# ==================================================
# UPDATE EMPLOYEE SKILL
# ==================================================

def update_employee_skill(user_id, course_id):

    connection = get_db_connection()

    course = connection.execute("""
        SELECT *
        FROM courses
        WHERE id = ?
    """, (
        course_id,
    )).fetchone()

    if course:

        connection.execute("""
            UPDATE user_skills

            SET current_level = required_level

            WHERE user_id = ?
            AND skill_name = ?
        """, (
            user_id,
            course["skill_name"]
        ))

    connection.commit()
    connection.close()


# ==================================================
# CREATE CERTIFICATE
# ==================================================

def create_certificate(user_id, course_id):

    connection = get_db_connection()

    existing = connection.execute("""
        SELECT *
        FROM certificates

        WHERE user_id = ?
        AND course_id = ?
    """, (
        user_id,
        course_id
    )).fetchone()

    if existing is None:

        connection.execute("""
            INSERT INTO certificates
            (
                user_id,
                course_id,
                certificate_code
            )
            VALUES (?, ?, ?)
        """, (
            user_id,
            course_id,
            generate_certificate_code()
        ))

        connection.commit()

    connection.close()


# ==================================================
# HOME
# ==================================================

@app.route("/")
def home():
    return render_template("index.html")


# ==================================================
# REGISTER
# ==================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    error = None

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        if (
            not name
            or not email
            or not password
            or not confirm_password
        ):

            error = "Please fill all fields."

        elif password != confirm_password:

            error = "Passwords do not match."

        elif len(password) < 6:

            error = (
                "Password must be at least 6 characters."
            )

        else:

            connection = get_db_connection()

            existing = connection.execute("""
                SELECT *
                FROM users
                WHERE email = ?
            """, (
                email,
            )).fetchone()

            if existing:

                error = (
                    "An account with this email already exists."
                )

                connection.close()

            else:

                hashed_password = generate_password_hash(
                    password
                )

                cursor = connection.execute("""
                    INSERT INTO users
                    (
                        name,
                        email,
                        password,
                        role
                    )
                    VALUES (?, ?, ?, ?)
                """, (
                    name,
                    email,
                    hashed_password,
                    "employee"
                ))

                new_user_id = cursor.lastrowid

                connection.commit()
                connection.close()

                create_default_skills(
                    new_user_id
                )

                flash(
                    "Account created successfully. Please login."
                )

                return redirect(
                    url_for("login")
                )

    return render_template(
        "register.html",
        error=error
    )


# ==================================================
# LOGIN
# ==================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    error = None

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        connection = get_db_connection()

        user = connection.execute("""
            SELECT *
            FROM users
            WHERE email = ?
        """, (
            email,
        )).fetchone()

        connection.close()

        if (
            user
            and check_password_hash(
                user["password"],
                password
            )
        ):

            session["user_id"] = user["id"]
            session["name"] = user["name"]
            session["email"] = user["email"]
            session["role"] = user["role"]

            if user["role"] == "admin":

                return redirect(
                    url_for("admin_dashboard")
                )

            return redirect(
                url_for("dashboard")
            )

        error = "Invalid email or password."

    return render_template(
        "login.html",
        error=error
    )


# ==================================================
# EMPLOYEE DASHBOARD
# ==================================================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(
            url_for("login")
        )

    if session["role"] != "employee":

        return redirect(
            url_for("admin_dashboard")
        )

    connection = get_db_connection()

    user_id = session["user_id"]


    # ==================================================
    # DASHBOARD STATS
    # ==================================================

    stats = connection.execute("""
        SELECT

            COUNT(*) AS total_enrolled,

            SUM(
                CASE
                    WHEN status = 'Completed'
                    THEN 1
                    ELSE 0
                END
            ) AS total_completed,

            ROUND(
                AVG(progress)
            ) AS average_progress

        FROM enrollments

        WHERE user_id = ?
    """, (
        user_id,
    )).fetchone()


    # ==================================================
    # SKILLS
    # ==================================================

    employee_skills = connection.execute("""
        SELECT
            id,
            skill_name,
            current_level,
            required_level,

            CASE
                WHEN required_level > current_level
                THEN required_level - current_level
                ELSE 0
            END AS skill_gap

        FROM user_skills

        WHERE user_id = ?

        ORDER BY
            skill_gap DESC,
            id ASC

        LIMIT 4
    """, (
        user_id,
    )).fetchall()


    # ==================================================
    # PRIORITY SKILL
    # ==================================================

    priority_skill = connection.execute("""
        SELECT
            id,
            skill_name,
            current_level,
            required_level,

            (
                required_level - current_level
            ) AS skill_gap

        FROM user_skills

        WHERE user_id = ?
        AND required_level > current_level

        ORDER BY
            skill_gap DESC,
            id ASC

        LIMIT 1
    """, (
        user_id,
    )).fetchone()


    # ==================================================
    # RECOMMENDED COURSE
    # ==================================================

    recommended_course = None

    if priority_skill:

        recommended_course = connection.execute("""
            SELECT

                courses.*,

                enrollments.status
                AS enrollment_status,

                enrollments.progress
                AS enrollment_progress,

                enrollments.score
                AS enrollment_score,

                certificates.certificate_code

            FROM courses

            LEFT JOIN enrollments

            ON courses.id = enrollments.course_id
            AND enrollments.user_id = ?

            LEFT JOIN certificates

            ON certificates.course_id = courses.id
            AND certificates.user_id = ?

            WHERE courses.skill_name = ?

            ORDER BY courses.id

            LIMIT 1
        """, (
            user_id,
            user_id,
            priority_skill["skill_name"]
        )).fetchone()


    # ==================================================
    # CURRENT COURSE
    # ==================================================

    current_course = connection.execute("""
        SELECT

            courses.id,
            courses.title,
            courses.skill_name,
            courses.duration,
            courses.difficulty,

            enrollments.progress,
            enrollments.status,
            enrollments.score,

            certificates.certificate_code

        FROM enrollments

        JOIN courses
        ON enrollments.course_id = courses.id

        LEFT JOIN certificates

        ON certificates.course_id = courses.id
        AND certificates.user_id = enrollments.user_id

        WHERE enrollments.user_id = ?

        ORDER BY

            CASE
                WHEN enrollments.status != 'Completed'
                THEN 0
                ELSE 1
            END,

            enrollments.id DESC

        LIMIT 1
    """, (
        user_id,
    )).fetchone()

    connection.close()

    return render_template(
        "dashboard.html",
        name=session["name"],
        stats=stats,
        skills=employee_skills,
        priority_skill=priority_skill,
        recommended_course=recommended_course,
        current_course=current_course
    )


# ==================================================
# SKILLS
# ==================================================

@app.route("/skills")
def skills():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    if session["role"] != "employee":

        return redirect(
            url_for("admin_dashboard")
        )

    connection = get_db_connection()

    employee_skills = connection.execute("""
        SELECT
            id,
            skill_name,
            current_level,
            required_level,

            CASE
                WHEN required_level > current_level
                THEN required_level - current_level
                ELSE 0
            END AS skill_gap

        FROM user_skills

        WHERE user_id = ?

        ORDER BY
            skill_gap DESC,
            id ASC
    """, (
        session["user_id"],
    )).fetchall()

    connection.close()

    return render_template(
        "skills.html",
        name=session["name"],
        skills=employee_skills
    )


# ==================================================
# COURSES
# ==================================================

@app.route("/courses")
def courses():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    if session["role"] != "employee":

        return redirect(
            url_for("admin_dashboard")
        )

    connection = get_db_connection()

    user_id = session["user_id"]

    priority_skill = connection.execute("""
        SELECT
            id,
            skill_name,
            current_level,
            required_level,

            (
                required_level - current_level
            ) AS skill_gap

        FROM user_skills

        WHERE user_id = ?
        AND required_level > current_level

        ORDER BY
            skill_gap DESC,
            id ASC

        LIMIT 1
    """, (
        user_id,
    )).fetchone()

    all_courses = connection.execute("""
        SELECT

            courses.*,

            enrollments.status
            AS enrollment_status,

            enrollments.progress
            AS enrollment_progress,

            enrollments.score
            AS enrollment_score,

            certificates.certificate_code

        FROM courses

        LEFT JOIN enrollments

        ON courses.id = enrollments.course_id
        AND enrollments.user_id = ?

        LEFT JOIN certificates

        ON certificates.course_id = courses.id
        AND certificates.user_id = ?

        ORDER BY courses.id
    """, (
        user_id,
        user_id
    )).fetchall()

    connection.close()

    return render_template(
        "courses.html",
        name=session["name"],
        courses=all_courses,
        priority_skill=priority_skill
    )


# ==================================================
# ENROLL
# ==================================================

@app.route(
    "/enroll/<int:course_id>",
    methods=["POST"]
)
def enroll(course_id):

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    if session["role"] != "employee":

        return redirect(
            url_for("admin_dashboard")
        )

    connection = get_db_connection()

    course = connection.execute("""
        SELECT *
        FROM courses
        WHERE id = ?
    """, (
        course_id,
    )).fetchone()

    if course is None:

        connection.close()

        flash("Course not found.")

        return redirect(
            url_for("courses")
        )

    existing = connection.execute("""
        SELECT *
        FROM enrollments

        WHERE user_id = ?
        AND course_id = ?
    """, (
        session["user_id"],
        course_id
    )).fetchone()

    if existing is None:

        connection.execute("""
            INSERT INTO enrollments
            (
                user_id,
                course_id,
                progress,
                status
            )
            VALUES (?, ?, ?, ?)
        """, (
            session["user_id"],
            course_id,
            0,
            "Enrolled"
        ))

        connection.commit()

    connection.close()

    return redirect(
        url_for(
            "course_learning",
            course_id=course_id
        )
    )


# ==================================================
# COURSE LEARNING
# ==================================================

@app.route("/course/<int:course_id>")
def course_learning(course_id):

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    if session["role"] != "employee":

        return redirect(
            url_for("admin_dashboard")
        )

    connection = get_db_connection()

    course = connection.execute("""
        SELECT *
        FROM courses
        WHERE id = ?
    """, (
        course_id,
    )).fetchone()

    if course is None:

        connection.close()

        flash("Course not found.")

        return redirect(
            url_for("courses")
        )

    enrollment = connection.execute("""
        SELECT *
        FROM enrollments

        WHERE user_id = ?
        AND course_id = ?
    """, (
        session["user_id"],
        course_id
    )).fetchone()

    if enrollment is None:

        connection.close()

        flash(
            "Please enroll in the course first."
        )

        return redirect(
            url_for("courses")
        )

    modules = connection.execute("""
        SELECT

            course_modules.*,

            CASE
                WHEN module_completions.id IS NOT NULL
                THEN 1
                ELSE 0
            END AS is_completed

        FROM course_modules

        LEFT JOIN module_completions

        ON course_modules.id =
           module_completions.module_id

        AND module_completions.user_id = ?

        WHERE course_modules.course_id = ?

        ORDER BY
            course_modules.module_order
    """, (
        session["user_id"],
        course_id
    )).fetchall()

    certificate_data = connection.execute("""
        SELECT certificate_code
        FROM certificates

        WHERE user_id = ?
        AND course_id = ?
    """, (
        session["user_id"],
        course_id
    )).fetchone()

    connection.close()

    return render_template(
        "course_learning.html",
        name=session["name"],
        course=course,
        enrollment=enrollment,
        modules=modules,
        certificate=certificate_data
    )


# ==================================================
# COMPLETE MODULE
# ==================================================

@app.route(
    "/complete-module/<int:course_id>/<int:module_id>",
    methods=["POST"]
)
def complete_module(course_id, module_id):

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    if session["role"] != "employee":

        return redirect(
            url_for("admin_dashboard")
        )

    connection = get_db_connection()

    enrollment = connection.execute("""
        SELECT *
        FROM enrollments

        WHERE user_id = ?
        AND course_id = ?
    """, (
        session["user_id"],
        course_id
    )).fetchone()

    if enrollment is None:

        connection.close()

        flash("Please enroll first.")

        return redirect(
            url_for("courses")
        )

    module = connection.execute("""
        SELECT *
        FROM course_modules

        WHERE id = ?
        AND course_id = ?
    """, (
        module_id,
        course_id
    )).fetchone()

    if module is None:

        connection.close()

        flash("Module not found.")

        return redirect(
            url_for(
                "course_learning",
                course_id=course_id
            )
        )

    connection.execute("""
        INSERT OR IGNORE INTO module_completions
        (
            user_id,
            module_id,
            completed
        )
        VALUES (?, ?, 1)
    """, (
        session["user_id"],
        module_id
    ))

    connection.commit()
    connection.close()

    update_course_progress(
        session["user_id"],
        course_id
    )

    flash(
        "Module completed successfully."
    )

    return redirect(
        url_for(
            "course_learning",
            course_id=course_id
        )
    )


# ==================================================
# ASSESSMENT
# ==================================================

@app.route(
    "/assessment/<int:course_id>",
    methods=["GET", "POST"]
)
def assessment(course_id):

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    if session["role"] != "employee":

        return redirect(
            url_for("admin_dashboard")
        )

    connection = get_db_connection()

    user_id = session["user_id"]

    course = connection.execute("""
        SELECT *
        FROM courses
        WHERE id = ?
    """, (
        course_id,
    )).fetchone()

    enrollment = connection.execute("""
        SELECT *
        FROM enrollments

        WHERE user_id = ?
        AND course_id = ?
    """, (
        user_id,
        course_id
    )).fetchone()

    if course is None or enrollment is None:

        connection.close()

        flash(
            "Course enrollment not found."
        )

        return redirect(
            url_for("courses")
        )

    if enrollment["progress"] < 100:

        connection.close()

        flash(
            "Complete all modules before taking the assessment."
        )

        return redirect(
            url_for(
                "course_learning",
                course_id=course_id
            )
        )

    assessment_data = connection.execute("""
        SELECT *
        FROM assessments
        WHERE course_id = ?
    """, (
        course_id,
    )).fetchone()

    if assessment_data is None:

        connection.close()

        flash(
            "Assessment not available."
        )

        return redirect(
            url_for("courses")
        )

    questions = connection.execute("""
        SELECT *
        FROM questions

        WHERE assessment_id = ?

        ORDER BY id
    """, (
        assessment_data["id"],
    )).fetchall()

    if request.method == "POST":

        correct = 0

        for question in questions:

            answer = request.form.get(
                "question_" + str(question["id"])
            )

            if answer == question["correct_answer"]:
                correct += 1

        if len(questions) > 0:

            score = round(
                (correct / len(questions)) * 100
            )

        else:
            score = 0

        passed = (
            score
            >= assessment_data["passing_score"]
        )

        connection.execute("""
            INSERT INTO assessment_results
            (
                user_id,
                assessment_id,
                score,
                passed
            )
            VALUES (?, ?, ?, ?)
        """, (
            user_id,
            assessment_data["id"],
            score,
            1 if passed else 0
        ))

        old_score = enrollment["score"] or 0

        best_score = max(
            old_score,
            score
        )

        # ==========================================
        # PASSED
        # ==========================================

        if passed:

            connection.execute("""
                UPDATE enrollments

                SET
                    score = ?,
                    status = 'Completed',
                    progress = 100

                WHERE user_id = ?
                AND course_id = ?
            """, (
                best_score,
                user_id,
                course_id
            ))

        # ==========================================
        # FAILED
        # ==========================================

        else:

            # Agar pehle se Completed hai to failed
            # retry se Completed status nahi hatega.
            if enrollment["status"] != "Completed":

                connection.execute("""
                    UPDATE enrollments

                    SET score = ?

                    WHERE user_id = ?
                    AND course_id = ?
                """, (
                    best_score,
                    user_id,
                    course_id
                ))

        connection.commit()
        connection.close()

        if passed:

            update_employee_skill(
                user_id,
                course_id
            )

            create_certificate(
                user_id,
                course_id
            )

        return render_template(
            "quiz.html",
            name=session["name"],
            course=course,
            assessment=assessment_data,
            questions=questions,
            result=True,
            score=score,
            correct=correct,
            total=len(questions),
            passed=passed
        )

    connection.close()

    return render_template(
        "quiz.html",
        name=session["name"],
        course=course,
        assessment=assessment_data,
        questions=questions,
        result=False
    )


# ==================================================
# PROGRESS
# ==================================================

@app.route("/progress")
def progress():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    if session["role"] != "employee":

        return redirect(
            url_for("admin_dashboard")
        )

    connection = get_db_connection()

    user_id = session["user_id"]

    enrollments = connection.execute("""
        SELECT

            courses.id AS course_id,
            courses.title,
            courses.skill_name,
            courses.duration,
            courses.difficulty,

            enrollments.progress,
            enrollments.status,
            enrollments.score,

            certificates.certificate_code

        FROM enrollments

        JOIN courses
        ON enrollments.course_id = courses.id

        LEFT JOIN certificates

        ON certificates.course_id = courses.id
        AND certificates.user_id = enrollments.user_id

        WHERE enrollments.user_id = ?

        ORDER BY enrollments.id DESC
    """, (
        user_id,
    )).fetchall()

    stats = connection.execute("""
        SELECT

            COUNT(*) AS total_enrolled,

            SUM(
                CASE
                    WHEN status = 'Completed'
                    THEN 1
                    ELSE 0
                END
            ) AS total_completed,

            ROUND(
                AVG(progress)
            ) AS average_progress,

            ROUND(
                AVG(
                    CASE
                        WHEN score IS NOT NULL
                        THEN score
                    END
                )
            ) AS average_score

        FROM enrollments

        WHERE user_id = ?
    """, (
        user_id,
    )).fetchone()

    employee_skills = connection.execute("""
        SELECT

            skill_name,
            current_level,
            required_level,

            CASE
                WHEN required_level > current_level
                THEN required_level - current_level
                ELSE 0
            END AS skill_gap

        FROM user_skills

        WHERE user_id = ?

        ORDER BY
            skill_gap DESC,
            id ASC
    """, (
        user_id,
    )).fetchall()

    connection.close()

    return render_template(
        "progress.html",
        name=session["name"],
        enrollments=enrollments,
        stats=stats,
        skills=employee_skills
    )


# ==================================================
# CERTIFICATE
# ==================================================

@app.route("/certificate/<int:course_id>")
def certificate(course_id):

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    if session["role"] != "employee":

        return redirect(
            url_for("admin_dashboard")
        )

    connection = get_db_connection()

    certificate_data = connection.execute("""
        SELECT

            certificates.certificate_code,
            certificates.issued_at,

            users.name AS employee_name,

            courses.id AS course_id,
            courses.title AS course_title,
            courses.skill_name,

            enrollments.score

        FROM certificates

        JOIN users
        ON certificates.user_id = users.id

        JOIN courses
        ON certificates.course_id = courses.id

        JOIN enrollments

        ON enrollments.user_id =
           certificates.user_id

        AND enrollments.course_id =
            certificates.course_id

        WHERE certificates.user_id = ?
        AND certificates.course_id = ?
        AND enrollments.status = 'Completed'
    """, (
        session["user_id"],
        course_id
    )).fetchone()

    connection.close()

    if certificate_data is None:

        flash(
            "Certificate is available only after passing the assessment."
        )

        return redirect(
            url_for("progress")
        )

    try:

        issued_date = datetime.strptime(
            certificate_data["issued_at"],
            "%Y-%m-%d %H:%M:%S"
        ).strftime(
            "%d %B %Y"
        )

    except (ValueError, TypeError):

        issued_date = str(
            certificate_data["issued_at"]
        )

    return render_template(
        "certificate.html",
        certificate=certificate_data,
        issued_date=issued_date
    )


# ==================================================
# ADMIN DASHBOARD
# ==================================================

@app.route("/admin")
def admin_dashboard():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    if session["role"] != "admin":

        return redirect(
            url_for("dashboard")
        )

    connection = get_db_connection()


    # ==================================================
    # ORGANIZATION STATISTICS
    # ==================================================

    total_employees = connection.execute("""
        SELECT COUNT(*) AS total

        FROM users

        WHERE role = 'employee'
    """).fetchone()["total"]


    total_courses = connection.execute("""
        SELECT COUNT(*) AS total
        FROM courses
    """).fetchone()["total"]


    completed_trainings = connection.execute("""
        SELECT COUNT(*) AS total

        FROM enrollments

        WHERE status = 'Completed'
    """).fetchone()["total"]


    average_score = connection.execute("""
        SELECT ROUND(
            AVG(score)
        ) AS average

        FROM enrollments

        WHERE score IS NOT NULL
    """).fetchone()["average"]

    if average_score is None:
        average_score = 0


    # ==================================================
    # EMPLOYEE ANALYTICS
    # ==================================================

    employees = connection.execute("""
        SELECT

            users.id,
            users.name,
            users.email,

            COUNT(
                enrollments.id
            ) AS enrolled_courses,

            SUM(
                CASE
                    WHEN enrollments.status = 'Completed'
                    THEN 1
                    ELSE 0
                END
            ) AS completed_courses,

            ROUND(
                AVG(
                    enrollments.progress
                )
            ) AS average_progress,

            ROUND(
                AVG(
                    CASE
                        WHEN enrollments.score IS NOT NULL
                        THEN enrollments.score
                    END
                )
            ) AS average_score

        FROM users

        LEFT JOIN enrollments
        ON users.id = enrollments.user_id

        WHERE users.role = 'employee'

        GROUP BY
            users.id,
            users.name,
            users.email

        ORDER BY users.id
    """).fetchall()


    # ==================================================
    # ORGANIZATION SKILL GAPS
    # ==================================================

    top_skill_gaps = connection.execute("""
        SELECT

            skill_name,

            ROUND(
                AVG(current_level)
            ) AS average_current,

            ROUND(
                AVG(required_level)
            ) AS average_required,

            ROUND(
                AVG(
                    CASE
                        WHEN required_level > current_level
                        THEN required_level - current_level
                        ELSE 0
                    END
                )
            ) AS average_gap,

            SUM(
                CASE
                    WHEN required_level > current_level
                    THEN 1
                    ELSE 0
                END
            ) AS employees_with_gap

        FROM user_skills

        GROUP BY skill_name

        ORDER BY
            average_gap DESC,
            skill_name ASC
    """).fetchall()


    # ==================================================
    # COURSE ANALYTICS
    # ==================================================

    course_analytics = connection.execute("""
        SELECT

            courses.id,
            courses.title,
            courses.skill_name,

            COUNT(
                enrollments.id
            ) AS total_enrollments,

            SUM(
                CASE
                    WHEN enrollments.status = 'Completed'
                    THEN 1
                    ELSE 0
                END
            ) AS completions,

            ROUND(
                AVG(
                    enrollments.progress
                )
            ) AS average_progress,

            ROUND(
                AVG(
                    CASE
                        WHEN enrollments.score IS NOT NULL
                        THEN enrollments.score
                    END
                )
            ) AS average_score

        FROM courses

        LEFT JOIN enrollments
        ON courses.id = enrollments.course_id

        GROUP BY
            courses.id,
            courses.title,
            courses.skill_name

        ORDER BY
            total_enrollments DESC,
            courses.id ASC
    """).fetchall()


    # ==================================================
    # RECENT ASSESSMENTS
    # ==================================================

    recent_assessments = connection.execute("""
        SELECT

            users.name AS employee_name,

            courses.title AS course_title,

            assessment_results.score,

            assessment_results.passed,

            assessment_results.completed_at

        FROM assessment_results

        JOIN users
        ON assessment_results.user_id = users.id

        JOIN assessments

        ON assessment_results.assessment_id =
           assessments.id

        JOIN courses
        ON assessments.course_id = courses.id

        ORDER BY
            assessment_results.id DESC

        LIMIT 8
    """).fetchall()

    connection.close()


    stats = {
        "total_employees": total_employees,
        "total_courses": total_courses,
        "completed_trainings": completed_trainings,
        "average_score": average_score
    }

    return render_template(
        "admin.html",
        name=session["name"],
        stats=stats,
        employees=employees,
        top_skill_gaps=top_skill_gaps,
        course_analytics=course_analytics,
        recent_assessments=recent_assessments
    )


# ==================================================
# LOGOUT
# ==================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# ==================================================
# START APPLICATION
# ==================================================

if __name__ == "__main__":

    create_database()

    app.run(debug=True)