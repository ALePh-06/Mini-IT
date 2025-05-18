import sqlite3
# Added render template and more
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import abort
import os
import bcrypt

basedir = os.path.abspath(os.path.dirname(__file__))


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'mydatabase.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# SQLAlchemy models

class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    user_type = db.Column(db.String, nullable=False)

class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    trimester = db.Column(db.Integer, nullable=False)
    code = db.Column(db.String, nullable=False)
    content = db.Column(db.String, nullable=False)

class Template(db.Model):
    __tablename__ = 'templates'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    field_name = db.Column(db.String, nullable=False)
    field_order = db.Column(db.Integer, nullable=False)

def get_course(course_id):
    course = db.session.get(Course, course_id)
    if course is None:
        abort(404)
    return course

with app.app_context():
    db.create_all()

app = Flask(__name__)
# Adding app secret key
app.secret_key = "#83yUi_a"

@app.before_request
def require_login():
    allowed_routes = ['Login', 'signup', 'static']
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect(url_for('Login'))

@app.route('/', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection() # Need to change
        cursor = conn.cursor()
        cursor.execute("SELECT password, user_type FROM users WHERE username=?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and bcrypt.checkpw(password.encode("utf-8"), user[0]):
            session["username"] = username
            session["user_type"] = user[1]
            flash("Login successful!")
            return redirect(url_for("homepage"))
        else:
            flash("Invalid username or password. Try again.")
            return redirect(url_for("login"))

    return render_template("Login.html") # This is the render template!!!!!!!!!!!!!!!!!!!!#

# Configuring SignUp to differentiate Students and Lecturers
@app.route('/Signup', methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        ConfirmPassword = request.form.get("ConfirmPassword", "").strip()
        special_code = request.form.get("special_code", "").strip()

        # Password match check
        if password != ConfirmPassword:
            flash("Passwords do not match. Please try again.")
            return redirect(url_for("signup"))

        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        # Determine user type
        if special_code == "Lecturer123": 
            user_type = "lecturer"
        else:
            user_type = "student"

        # Check if username is unique
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password, user_type) VALUES (?, ?, ?)", 
                           (username, hashed_password, user_type))
            conn.commit()
            conn.close()

            flash("Account created successfully! Please log in.")
            return redirect(url_for("login"))

        except sqlite3.IntegrityError:
            flash("Username already exists. Please choose a different username.")
            return redirect(url_for("signup"))

    return render_template("Signup.html") # This is the render template!!!!!!!!!!!!!!!!!!!!#


@app.route('/')
def index():
    courses = Course.query.all()
    return render_template('index.html', courses=courses)

@app.route('/<int:course_id>')
def view_course(course_id):
    course = get_course(course_id)
    return render_template('view_course.html', course=course)

@app.route('/create_course', methods=('GET', 'POST'))
def create_course():
    if request.method == 'POST':
        title = request.form['title']
        trimester = request.form['trimester']
        code = request.form['code']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        elif not trimester:
            flash('Trimester is required!')
        elif not code:
            flash('Code is required!')
        else:
            new_course = Course(title=title, trimester=int(trimester), code=code, content=content)
            db.session.add(new_course)
            db.session.commit()
            return redirect(url_for('index'))

    return render_template('create_course.html')

@app.route('/create_template', methods=('GET', 'POST'))
def create_template():
    if request.method == 'POST':
        template_name = request.form['name']
        field_names = request.form.getlist('field_name')

        if not template_name:
            flash('Name of template is required!')
        elif not field_names or all(f.strip() == '' for f in field_names):
            flash('At least one field name is required!')
        else:
            for i, fname in enumerate(field_names):
                if fname.strip():
                    new_template = Template(name=template_name, field_name=fname.strip(), field_order=i)
                    db.session.add(new_template)
            db.session.commit()
            return redirect(url_for('index'))

    return render_template('create_template.html')

@app.route('/<int:id>/edit', methods=('GET', 'POST'))
def edit(id):
    course = get_course(id)

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            course.title = title
            course.content = content
            db.session.commit()
            return redirect(url_for('index'))

    return render_template('edit.html', course=course)

@app.route('/<int:id>/delete', methods=('POST',))
def delete(id):
    course = get_course(id)
    db.session.delete(course)
    db.session.commit()
    flash(f'"{course.title}" was successfully deleted!')
    return redirect(url_for('index'))

app.run(host="0.0.0.0", port=5000, debug=True)
