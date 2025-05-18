from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.utils import secure_filename
import os
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(BASE_DIR, 'form.db')
# Setup Flask
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Setup SQLAlchemy
db = SQLAlchemy(app)

# Define database model
class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_name = db.Column(db.String(255), nullable=False) # Nullable means this column is required (can’t be empty), if true it meant optional
    title = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=False)
    filename = db.Column(db.String(255))

# Create tables
with app.app_context():
    db.create_all()

# Routes
@app.route('/')
def index():
    return render_template('Form.html')

@app.route('/submit', methods=['POST'])
def submit():
    group_name = request.form['Group_Name']
    title = request.form['Title']
    description = request.form['Description']
    file = request.files.get('Upload_file')

    filename = None
    if file and file.filename:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    # Insert into database
    new_submission = Submission(
    group_name=group_name,
    title=title,
    description=description,
    filename=filename
)
    print("Saving file:", filename)
    print("Saving to DB:", group_name, title, description)

    try:
        db.session.add(new_submission)
        db.session.commit()
        print("Saved to database!")
    except Exception as e:
        print("Database error:", e)

    rows = Submission.query.all()
    print("Rows in DB:", rows)
    
    print(group_name, title, description, filename)

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
# This code creates a simple Flask web application that allows users to submit a form with a file upload.