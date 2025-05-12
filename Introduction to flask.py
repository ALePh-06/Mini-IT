import sqlite3
# Added render template and more
from flask import Flask, render_template, request, redirect, url_for, session
# Putting bcrypt
import bcrypt

app = Flask(__name__)
# Adding app secret key
app.secret_key = "#83yUi_a"

# Creating database
def create_database():
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        user_type TEXT CHECK(user_type IN ('lecturer', 'student')) NOT NULL
    )
    ''')
    conn.commit()
    conn.close()


# Added the variable calling
create_database()

@app.route('/', methods=["GET", "POST"])
def Login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"].encode("utf-8")

        conn = sqlite3.connect("users_database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT password, user_type FROM users WHERE username=?",  (username,))
        user = cursor.fetchone()
        conn.close()

        # Verify stored hashed password
        if user and bcrypt.check(password, user[0].encode("utf-8")):
            session["username"] = username
            session["user_type"] = user[1] # This code is for differentiate between students and lecturers
            return redirect(url_for(f"{user[1]}_home"))
        else:
            return "Invalid username or password. Try again."

    return render_template("Login.html") # This is the render template!!!!!!!!!!!!!!!!!!!!#

# Configuring SignUp to differentiate Students and Lecturers
@app.route('/Signup', methods=["GET", "POST"])
def signup():
    if request.method == "POST": 
        username = request.form["Username"]
        password = request.form["password"]
        confirm_password = request.form["ConfirmPassword"]
        special_key = request.form["Special_Key"]

        if password != confirm_password:
            return "Passwords do not match. Try again."

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        conn = sqlite3.connect("users_database.db")
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password, user_type) VALUES (?, ?, ?)",
                           (username, hashed_password.decode('utf-8'), "student"))  
            conn.commit()
            return redirect(url_for("Login"))
        except sqlite3.IntegrityError:
            return "Username already exist!"
        finally:
            conn.close()

    return render_template("Signup.html") # This is the render template!!!!!!!!!!!!!!!!!!!!#

@app.route('/Homepage')
def Homepage():
    return render_template("Homepage.html")

@app.route('/FormStudent')
def formstudent():
    return render_template("FormStudent.html")

@app.route('/Create_Student_Submission_Form')
def form():
    return render_template("Form.html")

app.run(host="0.0.0.0", port=5000, debug=True)
# This code creates a simple Flask web application that returns when accessed at the root URL.