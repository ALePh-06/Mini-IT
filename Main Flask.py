import sqlite3
# Added render template and more
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import abort
import os

basedir = os.path.abspath(os.path.dirname(__file__))


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
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



app = Flask(__name__)
# Adding app secret key
app.secret_key = "#83yUi_a"



@app.route('/', methods=["GET", "POST"])
def Login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = db.session.get(users, )
        cursor = conn.cursor()
        cursor.execute("SELECT password, user_type FROM users WHERE username=?",  (username,))
        user = cursor.fetchone()
        conn.close()

        # Verify stored hashed password
        if user :
            session["username"] = username
            session["user_type"] = user[1] # This code is for differentiate between students and lecturers
            return redirect(Homepage)
        else:
            return "Invalid username or password. Try again."

    return render_template("Login.html") # This is the render template!!!!!!!!!!!!!!!!!!!!#

# Configuring SignUp to differentiate Students and Lecturers
@app.route('/Signup', methods=("GET", "POST"))
def signup():
    if request.method == "POST": 
        username = request.form["username"]
        password = request.form["password"]
        confirm_password = request.form["ConfirmPassword"]
        _code = request.form["special_code"]

        if password != confirm_password:
            flash('Passwords do not match. Try again.')    
            return redirect(url_for("Signup"))    
        else:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO users (username, password, user_type) VALUES (?, ?, ?)",
                               (username, password, "student"))  
                conn.commit()
                conn.close()
                return redirect(url_for("Login"))
            except sqlite3.IntegrityError:
                flash ('Username already exist!')
                return redirect(url_for('Signup'))

    return render_template("Signup.html") # This is the render template!!!!!!!!!!!!!!!!!!!!#

@app.route('/Homepage')
def Homepage():
    return render_template("Homepage.html")

@app.route('/FormStudent')
def formstudent():
    return render_template("FormStudent.html")

@app.route('/Create_Student_Submission_Form')
def form():
    return render_template("")

app.run(host="0.0.0.0", port=5000, debug=True)
# This code creates a simple Flask web application that returns when accessed at the root URL. a