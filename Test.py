import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, session
import bcrypt

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Replace with a more secure key in production

def get_db_connection():
    conn = sqlite3.connect('users_database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/Signup', methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()
        special_code = request.form.get("special_code", "").strip()

        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        # Determine user type
        user_type = "student"
        if special_code == "Lecturer123":  # Replace with your actual lecturer code
            user_type = "lecturer"

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

    return render_template("Signup.html")

@app.route('/', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
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

    return render_template("Login.html")

@app.route('/homepage')
def homepage():
    if "username" in session:
        return f"Welcome, {session['username']}! You are logged in as a {session['user_type']}."
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)