from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def Login():
    return render_template("Login.html")

@app.route('/Signup')
def signup():
    return render_template('Signup.html')

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