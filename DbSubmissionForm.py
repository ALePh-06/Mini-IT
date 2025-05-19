from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import JSON
from datetime import datetime
from werkzeug.utils import secure_filename
import pytz
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

#Time zone
def malaysia_time():
    return datetime.now(pytz.timezone('Asia/Kuala_Lumpur'))

# Define database model
class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_name = db.Column(db.String(255), nullable=False) # Nullable means this column is required (can’t be empty), if true it meant optional
    title = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=False)
    filename = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=malaysia_time)

# Create tables
with app.app_context():
    db.create_all()

# Routes
@app.route('/')
def index():
    return render_template('StudentForm.html')

@app.route('/submit', methods=['POST'])
def submit():
    group_name = request.form['Group_Name']
    title = request.form['Title']
    description = request.form['Description']
    file = request.files.get('Upload_file')
    topics = request.form.getlist('Topics[]')

    filename = None
    if file and file.filename:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    
    #topics = request.form.getlist('Topics[]')
    #subtopics = request.form.getlist('Subtopics[]')
    
    print("Submitted topics:", topics)  # for debug

    # Insert into database
    new_submission = Submission(
    group_name=group_name,
    title=title,
    description=description,
    filename=filename,
    timestamp=malaysia_time()
)
    
    print("Saving file:", filename)
    print("Saving to DB:", group_name, title, description, filename, malaysia_time())

    try:
        db.session.add(new_submission)
        db.session.commit()
        print("Saved to database!")
    except Exception as e:
        db.session.rollback()  # THIS IS IMPORTANT
        print("Database error:", e)

    rows = db.session.query(Submission).count()
    print("Rows in DB:", rows)
    
    print(group_name, title, description, filename)

    return redirect(url_for('index'))

@app.route('/SubmissionHistory')
def history():
    selected_group = request.args.get('group_name')
    
    if selected_group:
        submissions = Submission.query.filter_by(group_name=selected_group).order_by(Submission.timestamp.desc()).all()
    else:
        submissions = Submission.query.order_by(Submission.timestamp.desc()).all()

    group_names = db.session.query(Submission.group_name).distinct().all()
    group_names = [g[0] for g in group_names]

    return render_template('SubmissionHistory.html',
                           submissions=submissions,
                           group_names=group_names,
                           selected_group=selected_group,
                           )
    
@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)   

@app.route('/lecturerForm')
def lecturer():
    return render_template('lecturerForm.html')


if __name__ == '__main__':
    app.run(debug=True)
