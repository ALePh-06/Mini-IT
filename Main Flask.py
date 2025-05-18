import sqlite3
# Added render template and more
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import abort
import os
import bcrypt
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'mydatabase.db')


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

if os.path.exists(db_path):
    try:
        os.remove(db_path)
        print("Database deleted.")
    except PermissionError:
        print("Database is in use. Close other processes using it first.")

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
def get_template(template_id):
    template = db.session.get(Template, template_id)
    if template is None:
        abort(404)
    return template

with app.app_context():
    db.create_all()

# Adding app secret key
app.secret_key = "#83yUi_a"

@app.before_request
def require_login():
    allowed_routes = ['login', 'signup', 'static']
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect(url_for('Login'))

@app.route('/Login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

            # Users checker
        user = Users.query.filter_by(username=username).first()

        if user and bcrypt.checkpw(password.encode("utf-8"), user.password.encode("utf-8")):
            session["username"] = username
            session["user_type"] = user[1]
            
            # Redirect based on user type
            if user.user_type == "student":
                flash("Login successful! Welcome, student!")
                return redirect(url_for("#"))  # Redirect to student homepage
            elif user.user_type == "lecturer":
                flash("Login successful! Welcome, lecturer!")
                return redirect(url_for("index"))  # Redirect to lecturer homepage

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
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        # Determine user type
        if special_code == "Lecturer123": 
            user_type = "lecturer"
        else:
            user_type = "student"

        # Check if username is unique
        try:
            existing_user = Users.query.filter_by(username=username).first()
            if existing_user:
                flash("Username already exists. Please choose a different username.")
                return redirect(url_for("signup"))
            
            # Save user to database
            new_user = Users(username=username, password=hashed_password, user_type=user_type)
            db.session.add(new_user)
            db.session.commit()

            flash("Account created successfully! Please log in.")
            return redirect(url_for("login"))

        except sqlite3.IntegrityError:
            flash("Username already exists. Please choose a different username.")
            return redirect(url_for("signup"))

    return render_template("Signup.html") # This is the render template!!!!!!!!!!!!!!!!!!!!#


@app.route('/')
def index():
    courses = Course.query.all()
    
    if session['user_type'] == 'lecturer':
        return render_template('Index.html', courses=courses)  # Create this template
    else:
        return render_template('Index_s.html', courses=courses)
    

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
def edit_course(id):
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

    return render_template('edit_course.html', course=course)

@app.route('/<int:id>/edit', methods=('GET', 'POST'))
def edit_template(id):
    template = get_template(id)

    if request.method == 'POST':
        title = request.form['title']
        field_name = request.form['field_name']

        if not title:
            flash('Title is required!')
        else:
            template.title = title
            template.field_name = field_name
            db.session.commit()
            return redirect(url_for('index'))

    return render_template('edit.html', template=template)

@app.route('/<int:id>/delete', methods=('POST',))
def delete(id):
    course = get_course(id)
    db.session.delete(course)
    db.session.commit()
    flash(f'Course "{course.title}" was successfully deleted!')
    return redirect(url_for('index'))

app.run(host="0.0.0.0", port=5000, debug=True)
