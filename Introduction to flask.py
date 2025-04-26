from flask import Flask, render_template
app = Flask(__name__)

@app.route('/')
def home():
    return render_template("Index.html")

@app.route('/Login')
def index():
    return render_template("Login.html")

@app.route('/Signup')
def about():
    return render_template("Signup.html")

app.run(host="0.0.0.0", port=5000, debug=True)
# This code creates a simple Flask web application that returns when accessed at the root URL.