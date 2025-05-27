import sqlite3
# Added render template and more
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename
import os
import bcrypt
import pytz
from pytz import timezone
from datetime import datetime
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'mydatabase.db')


app = Flask(__name__)
app.config['SECRET_KEY'] = '#83yUi_a'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)



db = SQLAlchemy(app)

'''if os.path.exists(db_path):
    try:
        os.remove(db_path)
        print("Database deleted.")
    except PermissionError:
        print("Database is in use. Close other processes using it first.")'''

# SQLAlchemy models //////

def malaysia_time():
    return datetime.now(pytz.timezone('Asia/Kuala_Lumpur'))

class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    user_type = db.Column(db.String, nullable=False)

    group_id = db.Column(db.Integer, db.ForeignKey('Group.id'))

class Group(db.Model):
    __tablename__ = 'Group'
    id = db.Column(db.Integer, primary_key=True)
    
    course = db.relationship

class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    trimester = db.Column(db.Integer, nullable=False)
    code = db.Column(db.String, nullable=False)
    content = db.Column(db.String, nullable=False)

    lecturer_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    lecturer = db.relationship('Users', backref='courses') 

class Template(db.Model):
    __tablename__ = 'templates'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)

    fields = db.relationship('TemplateField', backref='template', cascade="all, delete-orphan")

class TemplateField(db.Model):
    __tablename__ = 'template_fields'
    id = db.Column(db.Integer, primary_key=True)
    field_name = db.Column(db.String, nullable=False)
    field_order = db.Column(db.Integer, nullable=False)

    template_id = db.Column(db.Integer, db.ForeignKey('templates.id'), nullable=False)

# Database Models
class Submission(db.Model):
    __tablename__ = 'submissions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    group_name = db.Column(db.String(255), nullable=False)
    title = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=False)
    filename = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=malaysia_time)
    is_late = db.Column(db.Boolean, default=False)
    due_date = db.Column(db.DateTime)
    form_id = db.Column(db.Integer, db.ForeignKey('form_templates.id'), nullable=True)
    
    user = db.relationship('Users', backref='submissions')
    form = db.relationship('FormTemplate', backref='submissions')

#FormTemplate
class FormTemplate(db.Model):
    __tablename__ = 'form_templates'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    description = db.Column(db.Text)
    filename = db.Column(db.String(255))
    open_date = db.Column(db.DateTime)
    due_date = db.Column(db.DateTime)

    fields = db.relationship('FormField', backref='form', foreign_keys='FormField.form_template_id')
    # Relationship to link form fields to form templates
    fields = db.relationship('FormField', backref='form_templates', lazy=True)
    '''This line sets up a one-to-many relationship:
        FormTemplate > has many > FormFields.
        It allows you to access all fields in a form using form.fields.
        Also, backref allows you to go back like reverse from FormField to FormTemplate using form_field.form_template.'''
        
        
#Relationship to link submissions to form templates
class FormField(db.Model):
    __tablename__ = 'form_field'
    id = db.Column(db.Integer, primary_key=True)
    form_template_id = db.Column(db.Integer, db.ForeignKey('form_templates.id'), nullable=False)
    label = db.Column(db.String(255))  #Exp: "What is your name?"
    field_type = db.Column(db.String(50))  #Exp: "text", "number", "file", etc.
    
#Answer model to link submissions with form fields
#For asnwer of course
class SubmissionFieldAnswer(db.Model):
    __tablename__ = 'submissiondieldanswer'
    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'), nullable=False)
    field_id = db.Column(db.Integer, db.ForeignKey('form_field.id'), nullable=False)  
    value = db.Column(db.String)

#Submission template model
class SubmissionTemplate(db.Model):
    __tablename__ = 'submission_templates'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)    

#Setting for submission
class SubmissionSettings(db.Model):
    __tablename__ = 'submissions_settings'
    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer)
    due_date = db.Column(db.DateTime, nullable=False)
    allow_late = db.Column(db.Boolean, default=False)
    auto_close = db.Column(db.Boolean, default=False)
    late_penalty_info = db.Column(db.Text)  # e.g. "10% deduction per day"

#Student course model
class StudentCourse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    
#Comment model for lecturer's comments on submissions
class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Lecturer's ID
    text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    submission = db.relationship('Submission', backref='comments')
    user = db.relationship('Users', lazy='joined')  # To access lecturer info
    #This means:"When I load a Comment, immediately also load its related User, using a SQL JOIN." 
    #It makes things faster and avoids needing extra queries when you access comment.user.
    #Without this relationship, we have to manually query the user using the user_id.
    


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

def get_submission(submission_id):
    submission = db.session.get(Submission, submission_id)
    if submission is None:
        abort(404)
    return submission

with app.app_context():
    db.create_all()

# Muiz's codes

# Adding app secret key
app.secret_key = "#83yUi_a"

@app.before_request
def require_login():
    allowed_routes = ['login', 'signup', 'static']
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect(url_for('login'))

@app.route('/Login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

            # Users checker
        user = Users.query.filter_by(username=username).first()

        if user and bcrypt.checkpw(password.encode("utf-8"), user.password.encode("utf-8")):
            session["username"] = username
            session["user_type"] = user.user_type
            session["user_id"] = user.id
            
            # Redirect to a single index route
            flash(f"Login successful! Welcome, {user.user_type}!")
            return redirect(url_for("index"))

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

# Join course via code function
@app.route('/JoinCourse', methods=['GET', 'POST'])
def JoinCourse():
    if 'user_type' not in session or session.get('user_type') != 'student':
        flash('You must be logged in as a student to join courses.')
        return redirect(url_for('login'))

    if request.method == 'POST':
        course_code = request.form['code'].strip()
        student_id = session['user_type']
        course = Course.query.filter_by(code=course_code).first()

        if not course:
            flash('Invalid course code.')
            return redirect(url_for('JoinCourse'))

        # Check if already joined
        existing = StudentCourse.query.filter_by(student_id=student_id, course_id=course.id).first()
        if existing:
            flash('You have already joined this course.')
            return redirect(url_for('JoinCourse'))

        # Join course
        join = StudentCourse(student_id=student_id, course_id=course.id)
        db.session.add(join)
        db.session.commit()
        flash(f"You've successfully joined {course.title}.")
        return redirect(url_for('index'))

    return render_template('JoinCourse.html')

@app.route('/')
def index():
    courses = Course.query.all()

    if 'user_type' not in session:
        return redirect(url_for('login'))  # force login if not authenticated
    
    if session['user_type'] == 'lecturer':
        return render_template('Index.html', courses=courses)  # Create this template
    else:
        return render_template('Index_s.html', courses=courses)
    

@app.route('/course/<int:course_id>')
def view_course(course_id):
    course = get_course(course_id)
    return render_template('view_course.html', course=course)

@app.route('/create_course', methods=('GET', 'POST'))
def create_course():
    current_user = Users.query.filter_by(username=session["username"]).first()
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
            new_course = Course(title=title, trimester=int(trimester), code=code, content=content, lecturer_id=current_user.id)
            db.session.add(new_course)
            db.session.commit()
            return redirect(url_for('index'))

    return render_template('create_course.html')

@app.route('/create_template', methods=('GET', 'POST'))
def create_template():
    if request.method == 'POST':
        template_name = request.form['name']
        field_names = request.form.getlist('field_name[]')

        if not template_name:
            flash('Template name is required.')
        elif not field_names or all(f.strip() == '' for f in field_names):
            flash('At least one field name is required.')
        else:
            # Create the template
            new_template = Template(name=template_name)
            db.session.add(new_template)
            db.session.commit()

            # Add fields linked to the template
            for i, fname in enumerate(field_names):
                if fname.strip():
                    new_field = TemplateField(
                        field_name=fname.strip(),
                        field_order=i,
                        template_id=new_template.id
                    )
                    db.session.add(new_field)
            db.session.commit()
            flash('Template created successfully!')
            return redirect(url_for('index'))

    return render_template('create_template.html')

@app.route('/view_template')
def view_template():
    templates = Template.query.all()
    return render_template('view_template.html', templates=templates)

@app.route('/edit_course/<int:id>', methods=('GET', 'POST'))
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

@app.route('/edit_template/<int:id>', methods=('GET', 'POST'))
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

#Naufal

#Routes to student form
@app.route('/StudentForm')
def StudentForm():
    form = FormTemplate.query.first()  # Get any form
    return render_template('StudentForm.html', form=form)

#Route to display available forms for students
@app.route('/Student/AvailableForms')
def student_forms():
    now = malaysia_time()
    malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
    forms = FormTemplate.query.order_by(FormTemplate.due_date).all()

    #Localize any naive due_date
    for form in forms:
        if form.due_date and form.due_date.tzinfo is None:
            form.due_date = malaysia_tz.localize(form.due_date)

    return render_template('FormExist.html', forms=forms, malaysia_time=malaysia_time)

#Route to display lecturer form creation page
@app.route('/create_form', methods=['POST'])
def create_form():
    title = request.form['Title']
    description = request.form['Description']
    file = request.files.get('Upload_file')
    open_date_str = request.form.get('open_date')
    due_date_str = request.form.get('due_date')
    
    due_date = None
    open_date = None
    
    try:
        if open_date_str:
            open_date = datetime.strptime(open_date_str, "%Y-%m-%dT%H:%M")
        if due_date_str:
            due_date = datetime.strptime(due_date_str, "%Y-%m-%dT%H:%M")
    except ValueError:
        flash("Invalid date format.", "error")
        return redirect(url_for('lecturer'))
    
    filename = None
    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

 #Define Malaysia timezone and localize the datetime
    malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
    if open_date:
        open_date = malaysia_tz.localize(open_date)
    if due_date:
        due_date = malaysia_tz.localize(due_date)
        
    new_form = FormTemplate(
        title=title,
        description=description,
        filename=filename,
        open_date=open_date,
        due_date=due_date
    )
    db.session.add(new_form)
    db.session.commit()

    flash("Form created successfully!", "success")
    return render_template('LecturerForm.html')

#Route to handle student form submission
@app.route('/submit', methods=['POST'])
def submit():
    if 'username' not in session:  # Check if user is logged in
        flash("You must be logged in to submit.") 
        return redirect(url_for('login'))

    user = Users.query.filter_by(username=session['username']).first()  # Check if user exists
    if not user:
        flash("User not found.")
        return redirect(url_for('login'))

    # Get form data
    group_name = request.form['Group_Name']
    title = request.form['Title']
    description = request.form['Description']
    file = request.files.get('Upload_file')

    filename = None
    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    form_id = request.form.get('form_id')  
    due_date = None
    form = None
    is_late = False  

    # Convert form_id to integer safely and retrieve the form
    now = malaysia_time()  # Timezone-aware
    if form_id:
        try:
            form_id_int = int(form_id)
            form = FormTemplate.query.get(form_id_int)
            if form and form.due_date:
                due_date = form.due_date
        except ValueError:
            flash("Invalid form ID.", "danger")
            return redirect(url_for('StudentForm'))
        
        # Make due_date timezone-aware if it's not already
        if due_date and due_date.tzinfo is None:
            malaysia = timezone('Asia/Kuala_Lumpur')
            due_date = malaysia.localize(due_date)

        # Check if the submission is late
        if due_date and now > due_date:
            is_late = True

    # Create and save submission
    new_submission = Submission(
        user_id=user.id,
        group_name=group_name,
        title=title,
        description=description,
        filename=filename,
        timestamp=now,
        is_late=is_late,
        due_date=due_date
    )

    db.session.add(new_submission)
    db.session.commit()

    flash("Submission successful!", "success")
    return redirect(url_for('StudentForm'))


#Route to display submission history
@app.route('/SubmissionHistory')
def history():
    user_type = session.get('user_type')
    username = session.get('username')
    
    if not username:
        flash("Please log in.")
        return redirect(url_for('login'))
    
    user = Users.query.filter_by(username=username).first()
    if not user:
        flash("User not found.")
        return redirect(url_for('login'))

    #Get list of distinct group names for filter dropdown (if any)
    group_names = [g[0] for g in db.session.query(Submission.group_name).distinct().all()]
    
    if user_type == 'lecturer':
        selected_group = request.args.get('group_name')

        #Get all user_ids for students
        student_ids = [u.id for u in Users.query.filter_by(user_type='student').all()]

        if selected_group:
            submissions = Submission.query.filter(
                Submission.group_name == selected_group,
                Submission.user_id.in_(student_ids)
            ).order_by(Submission.timestamp.desc()).all()
        else:
            submissions = Submission.query.filter(
                Submission.user_id.in_(student_ids)
            ).order_by(Submission.timestamp.desc()).all()
    
    elif user_type == 'student':
        #Student sees only their own submissions
        submissions = Submission.query.filter_by(user_id=user.id).order_by(Submission.timestamp.desc()).all()
        selected_group = None
    
    else:
        submissions = []
        selected_group = None

    return render_template('SubmissionHistory.html',
                           submissions=submissions,
                           group_names=group_names,
                           selected_group=selected_group)


#Route to review a submission
@app.route('/review/<int:submission_id>')
def review_submission(submission_id):
    submission = Submission.query.get_or_404(submission_id)

    #Optionally: restrict access to lecturers only
    if session.get('user_type') != 'lecturer':
        abort(403)

    form_fields = FormField.query.filter_by(form_template_id=submission.form_id).order_by(FormField.id).all()
    answers = SubmissionFieldAnswer.query.filter_by(submission_id=submission.id).order_by(SubmissionFieldAnswer.field_id).all()


    #Pair up questions and answers
    qa_pairs = []
    for field in form_fields:
        answer = next((a for a in answers if a.field_id == field.id), None)
        qa_pairs.append({
            'question': field.label,
            'answer': answer.value if answer else 'N/A'
        })

    comments = Comment.query.filter_by(submission_id=submission_id).order_by(Comment.timestamp.desc()).all()
     
    return render_template('ReviewSubmission.html', submission=submission, qa_pairs=qa_pairs, comments=comments)

#Route to handle comment submission
@app.route('/submit_comment/<int:submission_id>', methods=['POST'])
def submit_comment(submission_id):
    print("Submit comment user_type:", session.get('user_type'))
    print("Submit comment user_id:", session.get('user_id'))
    
    #Only allow lecturers to submit comments
    if session.get('user_type') != 'lecturer':
        abort(403)
    
    #Ensure user is logged in and user_id is in session
    if 'user_id' not in session:
        abort(403)  # or redirect to login page
    
    comment_text = request.form.get('comment')
    if not comment_text:
        flash("Comment cannot be empty.")
        return redirect(url_for('review_submission', submission_id=submission_id))
    
    #Create and save the comment
    new_comment = Comment(
        submission_id=submission_id,
        user_id=session['user_id'],
        text=comment_text,
        timestamp=datetime.utcnow()
    )
    db.session.add(new_comment)
    db.session.commit()

    flash("Comment submitted successfully!")
    return redirect(url_for('review_submission', submission_id=submission_id))

#Route for student history
@app.route('/StudentHistory')
def student_history():
    if 'username' not in session:
        flash("Please log in to view your submission history.")
        return redirect(url_for('login'))

    user = Users.query.filter_by(username=session['username']).first()
    if user.user_type != "student":
        abort(403)  # Only students should access this page

    submissions = Submission.query.filter_by(user_id=user.id).order_by(Submission.timestamp.desc()).all()
    return render_template("StudentHistory.html", submissions=submissions)

#Route to download a file
@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

#Route for lecturer form
@app.route('/LecturerForm')
def LecturerForm():
    if 'user_type' not in session or session['user_type'] != 'lecturer':
        flash("Access denied: You must be a lecturer to view this page.", "danger")
        return redirect(url_for('login'))  # Or a different page, like 'index'
    
    return render_template('LecturerForm.html')
    
#Route for submission status
@app.route('/Status')
def status():
    current_user = Users.query.filter_by(username=session["username"]).first()

    if session['user_type'] == 'lecturer':
        # Get all courses owned by this lecturer
        courses = Course.query.filter_by(lecturer_id=current_user.id).all()
        course_ids = [course.id for course in courses]

        # Get all submissions related to those courses (assuming submissions link to course/group with course_id)
        submissions = Submission.query.filter(Submission.course_id.in_(course_ids)).all()

        return render_template("status.html", submissions=submissions)

    else:
        # Show only submissions from this user's group
        submissions = Submission.query.join(Users).filter(
            Users.group_id == current_user.group_id
        ).all()

        return render_template("status_s.html", submissions=submissions)

#Route to view a specific submission
@app.route('/viewsubmission/<int:submission_id>')
def view_submission(submission_id):
    submission = get_submission(submission_id)
    if session['user_type'] == 'lecturer':
        return render_template('view_submission.html', submission=submission)
    
    else:
        return render_template('view_submission_s.html', submission=submission)

#Route to update submission status  
@app.route("/update_status/<int:submission_id>", methods=["POST"])
def update_status(submission_id):
    new_status = request.form["status"]
    
    # Get the actual SQLAlchemy model instance
    submission = Submission.query.get_or_404(submission_id)

    # Only allow lecturers to update
    if session.get("user_type") != "lecturer":
        abort(403)

    submission.status = new_status
    db.session.commit()

    flash("Submission status updated.")
    return redirect(url_for("view_submission", submission_id=submission.id))

app.run(host="0.0.0.0", port=5000, debug=True)