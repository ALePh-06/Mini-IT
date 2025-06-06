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
from collections import defaultdict
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
    email = db.Column(db.String(120), unique=True, nullable=False)
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False, index=True)
    password = db.Column(db.String, nullable=False)
    user_type = db.Column(db.String, nullable=False)

    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'))

class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    trimester = db.Column(db.Integer, nullable=False)
    code = db.Column(db.String, nullable=False)
    content = db.Column(db.String, nullable=False)

    lecturer_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    lecturer = db.relationship('Users', backref='courses') 
    templates = db.relationship('Template', backref='course', lazy=True)
    groups = db.relationship('Group', backref='course', lazy=True)


class Template(db.Model):
    __tablename__ = 'templates'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)

    fields = db.relationship('TemplateField', backref='template', cascade="all, delete-orphan")
    lecturer_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable = True)

class TemplateField(db.Model):
    __tablename__ = 'template_fields'
    id = db.Column(db.Integer, primary_key=True)
    field_name = db.Column(db.String, nullable=False)
    field_type = db.Column(db.String, nullable=False, default='text')
    field_order = db.Column(db.Integer, nullable=False)

    template_id = db.Column(db.Integer, db.ForeignKey('templates.id'), nullable=False)

class AssignedTemplate(db.Model):
    __tablename__ = 'assigned_templates'
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    template_id = db.Column(db.Integer, db.ForeignKey('templates.id'), nullable=False)

    # Relationships
    course = db.relationship('Course', backref='assigned_templates', lazy='joined')
    template = db.relationship('Template', backref='assignments', lazy='joined')
    
    def __repr__(self):
        return f'<AssignedTemplate {self.template.name} -> {self.course.title}>'

#Database model
class Submission(db.Model):
    __tablename__ = 'submissions'
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    template_id = db.Column(db.Integer, db.ForeignKey('templates.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=malaysia_time())
    due_date = db.Column(db.DateTime)
    status = db.Column(db.String(50), default='Pending')
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    edited = db.Column(db.Boolean, default=False)  
    original_id = db.Column(db.Integer, db.ForeignKey('submissions.id'), nullable=True) # Original submission ID for edits
    values = db.relationship('SubmissionFieldAnswer', backref='submission', cascade="all, delete-orphan")

    edits = db.relationship(
        "Submission",
        cascade="all, delete-orphan",
        backref=db.backref("original", remote_side=[id])
    )

class SubmissionFieldAnswer(db.Model):
    __tablename__ = 'submission_field_answer'
    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'), nullable=False)
    field_id = db.Column(db.Integer, db.ForeignKey('template_fields.id'), nullable=False)  
    value = db.Column(db.String)
    
    field = db.relationship('TemplateField', backref='answers')

#FormTemplate
class FormTemplate(db.Model):
    __tablename__ = 'form_templates'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    description = db.Column(db.Text)
    filename = db.Column(db.String(255))
    due_date = db.Column(db.DateTime)

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

#Student course model
class StudentCourse(db.Model):
    __tablename__ = 'student_course'
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

class Group(db.Model):
    __tablename__ = 'groups'
    id = db.Column(db.Integer, primary_key=True)
    group_code = db.Column(db.String, nullable=False, unique=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)

    members = db.relationship('GroupMembers', backref='group', cascade="all, delete-orphan")

class GroupMembers(db.Model):
    __tablename__ = 'group_members'
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    student = db.relationship('Users', backref='group_memberships')

# Functions start here

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

def get_current_user():
    return Users.query.filter_by(username=session.get('username')).first()


def get_student_group_id(course_id):
    student_id = get_current_user()

    group_member = db.session.query(Group.id).join(GroupMembers).filter(
        Group.course_id == course_id,
        GroupMembers.student_id == student_id
    ).first()

    return group_member.id if group_member else None


with app.app_context():
    db.create_all()

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
        email = request.form.get("email", "").strip().lower()
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
            existing_email = Users.query.filter_by(email=email).first()

            if existing_user:
                flash("Username already exists. Please choose a different username.")
                return redirect(url_for("signup"))
            
            if existing_email:
                flash("This Email has been taken")
                return redirect(url_for("signup"))
            
            # Save user to database
            new_user = Users(username=username, email=email, password=hashed_password, user_type=user_type)
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
        course_code = request.form['course_code'].strip()
        student_id = Users.query.filter_by(username=session['username']).first().id
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

@app.route('/course/<int:course_id>/JoinGroup', methods=['GET', 'POST'])
def join_group(course_id):
    if 'user_type' not in session or session['user_type'] != 'student':
        flash('You must be logged in as a student to join a group.')
        return redirect(url_for('login'))

    user = get_current_user()
    if not user:
        flash('User not found.')
        return redirect(url_for('login'))

    if request.method == 'POST':
        group_name = request.form['group_name'].strip()

        group = Group.query.filter_by(name=group_name).first()
        if not group:
            flash('Group not found. Please check the group name.')
            return redirect(url_for('join_group'))

        # Check if already in a group for this course
        course_id = group.course_id
        joined_group_ids = db.session.query(Group.id).join(GroupMembers).filter(
            Group.course_id == course_id,
            GroupMembers.user_id == user.id
        ).all()

        if joined_group_ids:
            flash('You have already joined a group for this course.')
            return redirect(url_for('join_group'))

        # Check group member count
        member_count = GroupMembers.query.filter_by(group_id=group.id).count()
        if member_count >= 4:
            flash('Group is full (max 4 members).')
            return redirect(url_for('join_group'))

        # Join the group
        membership = GroupMembers(group_id=group.id, user_id=user.id)
        db.session.add(membership)
        db.session.commit()

        flash(f"You have successfully joined group '{group.name}'.")
        return redirect(url_for('index'))

    return render_template('GroupJoining.html')  # Create this template

@app.route("/Logout")
def logout():
    session.clear()
    flash("You have logged out succesfully")
    return redirect(url_for("login"))

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
    assigned_templates = AssignedTemplate.query.filter_by(course_id=course_id).all()

    if session['user_type'] == 'lecturer':
        return render_template('view_course.html', course=course, assigned_templates=assigned_templates)  # Create this template
    else:
        return render_template('view_course_s.html', course=course, assigned_templates=assigned_templates)

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
    current_user = get_current_user()
    
    if request.method == 'POST':
        template_name = request.form['name']
        field_names = request.form.getlist('field_name[]')
        field_types = request.form.getlist('field_type[]')  # <-- collect types properly

        if not template_name:
            flash('Template name is required.')
        elif not field_names or all(f.strip() == '' for f in field_names):
            flash('At least one field name is required.')
        else:
            # Create the template
            new_template = Template(name=template_name, lecturer_id=current_user.id)
            db.session.add(new_template)
            db.session.commit()

            # Add fields linked to the template
            for i, (fname, ftype) in enumerate(zip(field_names, field_types)):
                if fname.strip():
                    new_field = TemplateField(
                        field_name=fname.strip(),
                        field_type=ftype.strip() if ftype else 'text',  # default to 'text' if empty
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

@app.route('/course/<int:course_id>/assign_template', methods=['GET', 'POST'])
def assign_template_to_course(course_id):
    # Only lecturers can assign
    if session.get('user_type') != 'lecturer':
        flash('Access denied: Only lecturers can assign templates.')
        return redirect(url_for('index_s'))

    course = get_course(course_id)
    current_user = get_current_user()

    # Ensure the lecturer owns this course
    if course.lecturer_id != current_user.id:
        flash('You can only assign templates to your own courses.')
        return redirect(url_for('view_course', course_id=course_id))

    templates = Template.query.filter_by(lecturer_id=current_user.id).all()
    current_assignment = AssignedTemplate.query.filter_by(course_id=course_id).first()

    if request.method == 'POST':
        action = request.form.get('action')
        
        # Handle template removal
        if action == 'remove':
            if current_assignment:
                db.session.delete(current_assignment)
                db.session.commit()
                flash('Template removed from course.', 'success')
            else:
                flash('No template was assigned.', 'info')
            return redirect(url_for('view_course', course_id=course_id))
        
        # Assign new or replace
        template_id = request.form.get('template_id')
        if not template_id:
            flash('Please select a template.', 'warning')
            return redirect(request.url)
        
        if current_assignment:
            current_assignment.template_id = template_id  # Replace existing
        else:
            new_assignment = AssignedTemplate(course_id=course_id, template_id=template_id)
            db.session.add(new_assignment)

        db.session.commit()
        flash('Template assigned/replaced successfully.', 'success')
        return redirect(url_for('view_course', course_id=course_id))

    return render_template(
        'assign_template.html',
        course=course,
        templates=templates,
        current_assignment=current_assignment
    )


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

@app.route('/course/<int:id>/delete', methods=('POST',))
def delete_course(id):
    course = get_course(id)
    db.session.delete(course)
    db.session.commit()
    flash(f'Course "{course.title}" was successfully deleted!')
    return redirect(url_for('index'))

#Time zone
def malaysia_time():
    return datetime.now(pytz.timezone('Asia/Kuala_Lumpur'))

@app.route('/course/<int:course_id>/fill_template', methods=['GET', 'POST'])
def fill_template(course_id):
    if session.get('user_type') != 'student':
        flash('Access denied: Only students can fill templates.')
        return redirect(url_for('index'))

    group_id = session.get("user_id")
    # Get assigned template for this course
    assignment = AssignedTemplate.query.filter_by(course_id=course_id).first()
    if not assignment:
        flash('No template assigned to this course yet.')
        return redirect(url_for('view_course', course_id=course_id))

    template = Template.query.get(assignment.template_id)
    fields = TemplateField.query.filter_by(template_id=template.id).all()

    if request.method == 'POST':
        # Create submission record
        submission = Submission(
            group_id=group_id,
            template_id=template.id,
            course_id=course_id,
        )
        db.session.add(submission)
        db.session.commit()

        # Save each field answer
        for field in fields:
            answer = request.form.get(str(field.id))
            field_answer = SubmissionFieldAnswer(
                submission_id=submission.id,
                field_id=field.id,
                value=answer
            )
            db.session.add(field_answer)

        db.session.commit()
        flash('Template submitted successfully.', 'success')
        return redirect(url_for('view_course', course_id=course_id))

    return render_template('fill_template.html', template=template, fields=fields, course_id=course_id)

# Naufal Codes 
# The code has been arranged to be more organized and readable.
# ALL CODE RELATED TO STUDENT!!!!!!!!!!!!!!!!!!!!
# Route to view student submission history
@app.route('/Student/History')
def student_history():
    if 'username' not in session:
        flash("Please log in to view your submission history.")
        return redirect(url_for('login'))

    user = get_current_user()
    if user.user_type != "student":
        abort(403)

    group_id = session.get("user_id")
    all_submissions = Submission.query.filter_by(group_id=group_id).order_by(Submission.date.desc()).all()

    chains = defaultdict(list)
    for s in all_submissions:
        key = s.original_id if s.original_id else s.id
        chains[key].append(s)

    submissions_dict = {}
    for chain in chains.values():
        sorted_chain = sorted(chain, key=lambda x: x.date, reverse=True)
        latest = sorted_chain[0]
        previous = sorted_chain[1] if len(sorted_chain) > 1 else None

        # Fetch answers for each version
        latest_answers = SubmissionFieldAnswer.query.filter_by(submission_id=latest.id).all()
        previous_answers = SubmissionFieldAnswer.query.filter_by(submission_id=previous.id).all() if previous else []

        if latest:
            submissions_dict[latest] = {
                'latest_answers': latest_answers,
                'previous_answers': previous_answers
            }

    return render_template("StudentHistory.html", submissions=submissions_dict)

# LECTURER CODE!!!!!
# Route to edit a submission
@app.route('/edit_submission/<int:submission_id>', methods=['GET'])
def edit_submission(submission_id):
    submission = Submission.query.get_or_404(submission_id)
    group_id = session.get("user_id")

    # Access control: check if user is owner or in same group
    if submission.group_id != group_id:
        abort(403)

    form = FormTemplate.query.first()  # adjust as needed
    return render_template('edit_template.html', submission=submission, form=form)

# Route for submission history lecturer
@app.route('/SubmissionHistory')
def history():
    user_type = session.get('user_type')
    username = session.get('username')

    if not username:
        flash("Please log in.")
        return redirect(url_for('login'))

    if user_type != 'lecturer':
        flash("You are not authorized to view this page.")
        return redirect(url_for('index'))

    user = Users.query.filter_by(username=username).first()
    if not user:
        flash("User not found.")
        return redirect(url_for('login'))

    # Get all groups for the dropdown filter
    groups = Group.query.order_by(Group.name).all()

    # Get selected group_id from query string, convert to int or None
    selected_group_id = request.args.get('group_id', type=int)

    # Filter submissions by group_id if selected, else all
    if selected_group_id:
        all_submissions = Submission.query.filter(
            Submission.group_id == selected_group_id
        ).order_by(Submission.date.desc()).all()
    else:
        all_submissions = Submission.query.order_by(Submission.date.desc()).all()

    # Group submissions into chains by original_id (or self id if original_id is None)
    chains = defaultdict(list)
    for s in all_submissions:
        key = s.original_id if s.original_id else s.id
        chains[key].append(s)

    # For each chain, keep the latest and one previous version (if exists)
    submissions_dict = {}
    for chain_submissions in chains.values():
        sorted_chain = sorted(chain_submissions, key=lambda x: x.date, reverse=True)
        latest = sorted_chain[0]
        previous = sorted_chain[1] if len(sorted_chain) > 1 else None
        submissions_dict[latest] = [previous] if previous else []

    return render_template(
        'SubmissionHistory.html',
        submissions=submissions_dict,
        groups=groups,
        selected_group_id=selected_group_id
    )

# Route to view a specific submission for lecturers 
@app.route('/viewsubmission/<int:submission_id>')
def view_submission(submission_id):
    if 'user_type' not in session:
        flash("Please log in first.")
        return redirect(url_for('login'))

    submission = Submission.query.get_or_404(submission_id)
    answers = SubmissionFieldAnswer.query.filter_by(submission_id=submission_id).all()

    # Preload form fields (assuming your field model is TemplateField)
    field_ids = [a.field_id for a in answers]
    fields = TemplateField.query.filter(TemplateField.id.in_(field_ids)).all()
    fields_dict = {f.id: f for f in fields}

    comments = Comment.query.filter_by(submission_id=submission.id).order_by(Comment.timestamp.desc()).all()

    user_type = session.get('user_type')

    if user_type == 'lecturer':
        return render_template('view_submission.html', submission=submission, comments=comments, fields=fields_dict, answers=answers)
    elif user_type == 'student':
        return render_template('view_comment.html', submission=submission, comments=comments, fields=fields_dict, answers=answers)
    else:
        abort(403)  # Forbidden for other user types

#ALL CODE RELATED TO BOTH STUDENT AND LECTURER!!!!!!!!!!!!!!
# Route for submission status
@app.route('/Status')
def status():
    current_user = Users.query.filter_by(username=session["username"]).first()

    if session['user_type'] == 'lecturer':
        # Get all courses owned by this lecturer
        courses = Course.query.filter_by(lecturer_id=current_user.id).all()
        course_ids = [course.id for course in courses]

        submissions = []
        if course_ids:
            submissions = Submission.query.filter(Submission.course_id.in_(course_ids)).all()
        return render_template("status.html", submissions=submissions)

    else:
        # Get all submissions in the user's group
        group_id = session.get("user_id")
        all_submissions = Submission.query.filter_by(group_id=group_id).order_by(Submission.date.desc()).all()

        # Group by original submission ID or own ID
        chains = defaultdict(list)
        for s in all_submissions:
            key = s.original_id if s.original_id else s.id
            chains[key].append(s)

        # Keep only the latest version of each chain
        latest_submissions = [sorted(subs, key=lambda x: x.date, reverse=True)[0] for subs in chains.values()]

        return render_template("status_s.html", submissions=latest_submissions)


#ALL CODE RELATED TO SUBMIT, DOWNLOAD, AND ETC!!!!!!!!!!!!!!!!!!!!!
# Route to handle student form submission
@app.route('/submit', methods=['POST'])
def submit():
    if 'username' not in session:
        flash("You must be logged in to submit.") 
        return redirect(url_for('login'))

    user = Users.query.filter_by(username=session['username']).first()
    if not user:
        flash("User not found.")
        return redirect(url_for('login'))

    # Get form data
    group_name = request.form['Group_Name']
    title = request.form['Title']
    description = request.form['Description']
    file = request.files.get('Upload_file')
    submission_id = request.form.get("submission_id")

    filename = None
    if file and file.filename:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    form_id = request.form.get('form_id')  
    due_date = None
    form = None
    is_late = False  

    now = datetime.now(malaysia_time)  # Timezone-aware
    if form_id:
        try:
            form_id_int = int(form_id)
            form = FormTemplate.query.get(form_id_int)
            if form and form.due_date:
                due_date = form.due_date
        except ValueError:
            flash("Invalid form ID.", "danger")
            return redirect(url_for('StudentForm'))
        
        if due_date and due_date.tzinfo is None:
            malaysia = timezone('Asia/Kuala_Lumpur')
            due_date = malaysia.localize(due_date)

        if due_date and now > due_date:
            is_late = True

    # Use submission_id to check if editing
    existing_submission = None
    if submission_id:
        try:
            existing_submission = Submission.query.get(int(submission_id))
        except ValueError:
            flash("Invalid submission ID.")
            return redirect(url_for('StudentForm'))

    if existing_submission and existing_submission.user_id == user.id:
    # Update existing submission
        existing_submission.group_name = group_name
        existing_submission.title = title
        existing_submission.description = description
        if filename:
            existing_submission.filename = filename
            existing_submission.timestamp = now
            existing_submission.is_late = is_late
            existing_submission.due_date = due_date
            existing_submission.edited = True
            db.session.commit()
            flash("Submission updated successfully!", "info")
            return redirect(url_for('student_history'))  
    else:
        # New submission
        new_submission = Submission(
            user_id=user.id,
            group_name=group_name,
            title=title,
            description=description,
            filename=filename,
            timestamp=now,
            is_late=is_late,
            due_date=due_date,
            edited=False
        )
        db.session.add(new_submission)
        db.session.commit()
        flash("Submission successful!", "success")
        return redirect(url_for('StudentForm'))

# Route to handle comment submission
@app.route('/submit_comment/<int:submission_id>', methods=['POST'])
def submit_comment(submission_id):
    
    # Only allow lecturers to submit comments
    if 'user_type' not in session or session['user_type'] != 'lecturer':
        flash("Access denied: You must be a lecturer to view this page.", "danger")
        return redirect(url_for('index'))  
    
    # Ensure user is logged in and user_id is in session
    if 'user_id' not in session:
        abort(403)  # or redirect to login page
    
    comment_text = request.form.get('comment')
    if not comment_text:
        flash("Comment cannot be empty.")
        return redirect(url_for('review_submission', submission_id=submission_id))

    # Create and save the comment
    new_comment = Comment(
        submission_id=submission_id,
        user_id=session['user_id'],
        text=comment_text,
        timestamp=datetime.now(malaysia_time)  
    )
    db.session.add(new_comment)
    db.session.commit()

    flash("Comment submitted successfully!")
    return redirect(url_for('review_submission', submission_id=submission_id))

# Route for updating both status and adding comment
@app.route("/update_status/<int:submission_id>", methods=["POST"])
def update_status_and_comment(submission_id):
    submission = Submission.query.get_or_404(submission_id)

    malaysia_time = pytz.timezone('Asia/Kuala_Lumpur')

    if session.get("user_type") != "lecturer":
        abort(403)

    new_status = request.form.get("status")
    comment_text = request.form.get("comment")

    if new_status:
        submission.status = new_status

    if comment_text:
        current_user = Users.query.filter_by(username=session["username"]).first()
        comment = Comment(
            submission_id=submission.id,
            user_id=current_user.id,
            text=comment_text,
            timestamp=datetime.now(malaysia_time)  
        )
        db.session.add(comment)

    db.session.commit()

    flash("Submission status and comment updated.")
    return redirect(url_for("view_submission", submission_id=submission.id))

malaysia_time = pytz.timezone('Asia/Kuala_Lumpur')

# Route to update a submission
@app.route('/submit_edit/<int:submission_id>', methods=['POST'])
def submit_edit(submission_id):
    old_submission = Submission.query.get_or_404(submission_id)
    if old_submission.user_id != session.get('user_id'):
        abort(403)

    original_id = old_submission.original_id if old_submission.original_id else old_submission.id
    user_id = session.get('user_id')

    file = request.files.get('Upload_file')
    filename = None
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    new_submission = Submission(
        user_id=user_id,
        group_name=request.form.get('Group_Name'),
        title=request.form.get('Title'),
        description=request.form.get('Description'),
        filename=filename if filename else old_submission.filename,
        timestamp=datetime.now(malaysia_time),
        is_late=False,
        due_date=old_submission.due_date,
        form_id=old_submission.form_id,
        status='Pending',
        course_id=old_submission.course_id,
        edited=True,
        original_id=original_id
    )

    db.session.add(new_submission)
    db.session.commit()

    # Copy field answers from form
    old_field_answers = SubmissionFieldAnswer.query.filter_by(submission_id=submission_id).all()
    for old_answer in old_field_answers:
        field_key = f"field_{old_answer.field_id}"
        new_value = request.form.get(field_key)
        if new_value is not None:
            new_answer = SubmissionFieldAnswer(
                submission_id=new_submission.id,
                field_id=old_answer.field_id,
                value=new_value
            )
            db.session.add(new_answer)

    # Copy old comments
    old_comments = Comment.query.filter_by(submission_id=original_id).all()
    for comment in old_comments:
        copied_comment = Comment(
            submission_id=new_submission.id,
            user_id=comment.user_id,
            text=f"[Comment from previous version]\n{comment.text}",
            timestamp=datetime.now(malaysia_time)
        )
        db.session.add(copied_comment)

    db.session.commit()

    flash('Submission updated successfully with previous comments and answers carried over.')
    return redirect(url_for('student_history'))

# Route to delete a submission
@app.route('/delete_submission/<int:submission_id>', methods=['POST'])
def delete_submission(submission_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    
    group_id = session.get("user_id")
    user = Users.query.filter_by(username=session['username']).first()
    submission = Submission.query.get_or_404(submission_id)

    if submission.group_id != group_id:
        abort(403)

    # Find the original submission
    if submission.original_id:
        original = Submission.query.get(submission.original_id)
    else:
        original = submission

    # Find all edits and the original
    # Find all edits and the original
    edits = Submission.query.filter_by(original_id=original.id).all()
    all_to_delete = edits + [original]

    # Delete all comments linked to each submission/edit
    for sub in all_to_delete:
        for comment in sub.comments:
            db.session.delete(comment)

    # Now delete the submissions
    for sub in all_to_delete:
        db.session.delete(sub)
    all_to_delete = edits + [original]

    # Delete all comments linked to each submission/edit
    for sub in all_to_delete:
        for comment in sub.comments:
            db.session.delete(comment)

    # Now delete the submissions
    for sub in all_to_delete:
        db.session.delete(sub)

    db.session.commit()

    flash("Submission and all edits deleted successfully.", "info")
    return redirect(url_for('student_history'))



app.run(host="0.0.0.0", port=5000, debug=True)