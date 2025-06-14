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
from sqlalchemy import or_
from itsdangerous import URLSafeTimedSerializer

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

# Token utilities
serializer = URLSafeTimedSerializer(app.secret_key)

def generate_token(email):
    return serializer.dumps(email, salt='password-reset-salt')

def verify_token(token, expiration=3600):
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=expiration)
    except:
        return None
    return email


class Users(db.Model):
    __tablename__ = 'users'
    email = db.Column(db.String(150), unique=True, nullable=False)
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False, index=True)
    password = db.Column(db.String, nullable=False)
    user_type = db.Column(db.String, nullable=False)


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
    due_date = db.Column(db.DateTime)

    # Relationships
    course = db.relationship('Course', backref='assigned_templates', lazy='joined')
    template = db.relationship('Template', backref='assignments', lazy='joined')
    
    def __repr__(self):
        return f'<AssignedTemplate {self.template.name} -> {self.course.title}>'

#Database model
class Submission(db.Model):
    __tablename__ = 'submissions'
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.String, db.ForeignKey('groups.group_code'), nullable=False)
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
    group_code = db.Column(db.String(100), nullable=False)  # <-- important
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    members = db.relationship('GroupMembers', backref='group', cascade="all, delete-orphan")
    deadline = db.Column(db.DateTime, nullable=True)

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
    student_id = get_current_user().id

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
        user_input = request.form["user_input"]
        password = request.form["password"]


            # Users checker
        user = Users.query.filter(or_(Users.username == user_input, Users.email == user_input)).first()

        if user and bcrypt.checkpw(password.encode("utf-8"), user.password.encode("utf-8")):
            session["username"] = user.username
            session["email"] = user.email
            session["user_type"] = user.user_type
            session["user_id"] = user.id
            
            # Redirect to a single index route
            flash(f"Login successful! Welcome, {user.username}!")
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
            return redirect(url_for("signup"))

    return render_template("Signup.html") # This is the render template!!!!!!!!!!!!!!!!!!!!#

# Forgot Password Route
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = Users.query.filter_by(email=email).first()
        if user:
            token = generate_token(email)
            reset_url = url_for('reset_password', token=token, _external=True)
            print(f"[DEBUG] Password reset link: {reset_url}")  # Replace with email logic
            flash('Reset link sent to your email. (Simulated in console for now)')
        else:
            flash('Email not found.')
    return render_template('templates/forgot_password.html')

# Reset Password Route
@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    email = verify_token(token)
    if not email:
        flash('Reset link is invalid or has expired.')
        return redirect(url_for('login'))

    if request.method == 'POST':
        new_password = request.form['password']
        hashed_pw = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        user = Users.query.filter_by(email=email).first()
        user.password = hashed_pw
        db.session.commit()
        flash('Password reset successful. You can now log in.')
        return redirect(url_for('login'))

    return render_template('templates/reset_password.html')


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
            flash('You have already enrolled in this course.')
            
            return redirect(url_for('JoinCourse'))

        # Join course
        join = StudentCourse(student_id=student_id, course_id=course.id)
        db.session.add(join)
        db.session.commit()
        flash(f"You've successfully joined {course.title}.")
<<<<<<< HEAD
        return redirect(url_for('JoinCourse'), course_id=course.id) # Change the join_group to JoinCourse atm

    return render_template('JoinCourse.html')

'''@app.route('/course/<int:course_id>/join_group', methods=['GET', 'POST'])
def join_group(course_id):
    user = get_current_user()
    course = Course.query.get_or_404(course_id)

    if request.method == 'POST':
        group_name = request.form.get('group_code', '').strip()

        if not group_name:
            flash("Group name is required.")
            return redirect(url_for('join_group', course_id=course.id))

        # Check if group name already exists in this course
        existing_named_group = Group.query.filter_by(group_code=group_name, course_id=course.id).first()
        if existing_named_group:
            flash("Group name already exists. Please choose a different name.")
            return redirect(url_for('join_group', course_id=course.id))

        # Generate CourseCode-XX format for group_code
        existing_groups = Group.query.filter_by(course_id=course.id).count()
        next_group_number = existing_groups + 1
        group_code = f"{course.code}-{next_group_number:02d}"

        # Create new group
        new_group = Group(group_code=group_code, course_id=course.id)
        db.session.add(new_group)
        db.session.commit()

        # Add current student as member
        new_member = GroupMembers(group_id=new_group.id, student_id=user.id)
        db.session.add(new_member)
        db.session.commit()

        flash(f"Group '{group_name}' created and you have been added.")
        return redirect(url_for('view_course_s', course_id=course.id))

    return render_template("GroupJoining.html", course=course)'''

=======
        return redirect(url_for('index'))

    return render_template('JoinCourse.html')

>>>>>>> main
@app.route('/course/<int:course_id>/access')
def access_course(course_id):
    if 'user_type' not in session or session['user_type'] != 'student':
        flash("Access denied.")
        return redirect(url_for('login'))

    user = get_current_user()
    course = Course.query.get_or_404(course_id)

    # Ensure student is enrolled
    enrolled = StudentCourse.query.filter_by(course_id=course.id, student_id=user.id).first()
    if not enrolled:
        flash("You are not enrolled in this course.")
        return redirect(url_for('index'))

    # Ensure student has joined a group
    if not user.group_id:
        return redirect(url_for('join_group', course_id=course.id))

    return redirect(url_for('view_course_s', course_id=course.id))

# Lecturer Group Assignment
@app.route('/course/<int:course_id>/assign_groups', methods=['GET', 'POST'])
def assign_groups(course_id):
    course = Course.query.get(course_id)
    if request.method == 'POST':
        try:
            num_groups = int(request.form['num_groups'])
            deadline_str = request.form['deadline']
            
            # Localize to Malaysia time
            malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
            naive_deadline = datetime.strptime(deadline_str, '%Y-%m-%dT%H:%M')
            deadline = malaysia_tz.localize(naive_deadline)

            if num_groups < 1:
                flash("Minimum one group required.")
                return redirect(url_for('assign_groups', course_id=course_id))

            existing_count = Group.query.filter_by(course_id=course_id).count()
            for i in range(existing_count + 1, existing_count + num_groups + 1):
                group_c = f"{course.code}-{str(i).zfill(2)}"
                new_group = Group(group_code=group_c, course_id=course_id, deadline=deadline)
                db.session.add(new_group)

            db.session.commit()
            flash("Groups created successfully.")
            return redirect(url_for('view_course', course_id=course_id))
        except Exception as e:
            flash(str(e))

    return render_template('assign_groups.html', course=course)

# Student Join/Leave Group
@app.route('/course/<int:course_id>/join_group', methods=['GET', 'POST'])
def join_group(course_id):
    course = Course.query.get(course_id)
    user = get_current_user()

    # To check already in a group
    group_member = GroupMembers.query.join(Group).filter(GroupMembers.student_id == user.id, Group.course_id == course_id).first()
    my_group = group_member.group if group_member else None
    groups = Group.query.filter_by(course_id=course_id).all()

    # Time
    # Malaysia time
    malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
    malaysia_now = datetime.now(malaysia_tz)

    # Convert deadlines to aware datetimes
    for g in groups:
        if g.deadline and g.deadline.tzinfo is None:
            g.deadline = malaysia_tz.localize(g.deadline)

    if request.method == 'POST':
        action = request.form.get('action')
        group_id = int(request.form.get('group_id'))

        if action == 'join':
            target_group = Group.query.get_or_404(group_id)
            member_count = GroupMembers.query.filter_by(group_id=group_id).count()
            
            if member_count >= 4:
                flash("Group is full")
            elif my_group:
                flash("You already joined the group")
            else:
                new_member = GroupMembers(group_id=group_id, student_id=user.id)
                db.session.add(new_member)
                db.session.commit()
                flash(f'You have joined {target_group.group_code}')
                return redirect(url_for('join_group', course_id=course_id))
            
        elif action == 'leave' and my_group and my_group.id == group_id:
            GroupMembers.query.filter_by(group_id=group_id, student_id=user.id).delete()
            db.session.commit()
            flash('You have left the group.')
            return redirect(url_for('join_group', course_id=course_id))

    return render_template('select_group.html', course=course, groups=groups, group=my_group, malaysia_now=malaysia_now)

@app.route('/course/<int:course_id>/leave_group', methods=['POST'])
def leave_group(course_id):
    user = Users.query.filter_by(username=session['username']).first()
    membership = GroupMembers.query.join(Group).filter(GroupMembers.student_id == user.id, Group.course_id == course_id).first()

    if membership:
        malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
        now = datetime.now(malaysia_tz)

        if now < membership.group.deadline.astimezone(malaysia_tz):
            db.session.delete(membership)
            db.session.commit()
            flash("You have left the group.")
        else:
            flash("Deadline to leave the group has passed.")
    else:
        flash("You are not in a group.")

    return redirect(url_for('join_group', course_id=course_id))

@app.route('/course/<int:course_id>/select_group')
def select_group(course_id):
    course = Course.query.get_or_404(course_id)
    groups = (
        db.session.query(Group)
        .filter_by(course_id=course_id)
        .options(db.joinedload(Group.members).joinedload(GroupMembers.student))
        .all()
    )
    user = get_current_user()
    malaysia_now = datetime.now(pytz.timezone('Asia/Kuala_Lumpur'))

    group = (
        db.session.query(Group)
        .join(GroupMembers)
        .filter(Group.course_id == course_id, GroupMembers.student_id == user.id)
        .first()
    )

    return render_template('select_group.html', course=course, groups=groups, group=group, malaysia_now=malaysia_now)

@app.route("/Logout")
def logout():
    session.clear()
    flash("You have logged out succesfully")
    return redirect(url_for("login"))

@app.route('/')
def index():
    if 'user_type' not in session:
        return redirect(url_for('login'))  # force login if not authenticated
    
    if session['user_type'] == 'lecturer':
        courses = Course.query.all()
        return render_template('Index.html', courses=courses)  # Create this template
    else:
        student_id = get_current_user().id
        courses = db.session.query(Course).join(StudentCourse).filter(StudentCourse.student_id == student_id).all()

        return render_template('Index_s.html', courses=courses)
    

@app.route('/course/<int:course_id>', methods=['GET', 'POST'])
def view_course(course_id):
<<<<<<< HEAD
    course = get_course(course_id)
    assigned_template = AssignedTemplate.query.filter_by(course_id=course_id).first()
    user = get_current_user()
    group =  db.session.query(Group.id).join(GroupMembers).filter(Group.course_id == course.id, GroupMembers.student_id == user.id)
=======

    malaysia_tz = timezone('Asia/Kuala_Lumpur')
    course = get_course(course_id)
    assigned_template = AssignedTemplate.query.filter_by(course_id=course_id).first()
    user = get_current_user()

    group =  (
        db.session.query(Group)
        .join(GroupMembers)
        .filter(Group.course_id == course.id, GroupMembers.student_id == user.id)
        .first()
    )
     # The groups for this course (to display group boxes later)
    groups = (
        db.session.query(Group)
        .filter_by(course_id=course.id)
        .options(db.joinedload(Group.members).joinedload(GroupMembers.student))
        .all()
    )
>>>>>>> main

    if session['user_type'] == 'lecturer':
        return render_template('view_course.html', course=course, assigned_template=assigned_template.id if assigned_template else None)  # Create this template
    else:
        # Check enrollment
        enrolled = StudentCourse.query.filter_by(course_id=course.id, student_id=user.id).first()
        if not enrolled:
            flash("You are not enrolled in this course.")
            return redirect(url_for('index'))

        return render_template(
            'view_course_s.html',
            course=course,
            assigned_template=assigned_template,
            group=group,
            groups=groups,
            namespace={'utcnow': datetime.now(malaysia_tz)}
        )

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
    current_lecturer = get_current_user().id
    templates = db.session.query(Template).filter(Template.lecturer_id == current_lecturer)
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
        due_date_str = request.form.get('due_date')
        due_date = None
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                flash('Invalid date format.', 'danger')
                return redirect(request.url)
        if not template_id:
            flash('Please select a template.', 'warning')
            return redirect(request.url)
        
        if current_assignment:
            current_assignment.template_id = template_id  # Replace existing
        else:
            new_assignment = AssignedTemplate(course_id=course_id, template_id=template_id, due_date=due_date if due_date else None)
            db.session.add(new_assignment)

        db.session.commit()
        flash('Template assigned/replaced successfully.', 'success')
        return redirect(url_for('view_course', course_id=course_id))

    return render_template('assign_template.html', course=course, templates=templates, current_assignment=current_assignment)


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

    group_id = get_current_user().id
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
        flash('Form submitted successfully.', 'success')
        return redirect(url_for('view_course', course_id=course_id))

    return render_template('fill_template.html', template=template, fields=fields, course_id=course_id)

# Naufal Codes 
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

# Route to edit a submission
@app.route('/submission/<int:submission_id>/edit', methods=['GET'])
def edit_submission(submission_id):
    submission = Submission.query.get_or_404(submission_id)
    if submission.group_id != session.get("user_id"):
        abort(403)

    template = Template.query.get(submission.template_id)
    fields = TemplateField.query.filter_by(template_id=template.id).all()

    # Get the current answers
    answers = {
        a.field_id: a.value
        for a in SubmissionFieldAnswer.query.filter_by(submission_id=submission.id).all()
    }

    return render_template(
        'edit_template_submission.html',
        submission=submission,
        template=template,
        fields=fields,
        answers=answers
    )

# Route to display lecturer form creation page
@app.route('/create_form', methods=['GET', 'POST'])
def create_form():
    # Restrict access to lecturers only
    if 'user_type' not in session or session['user_type'] != 'lecturer':
        flash("Access denied: You must be a lecturer to view this page.", "danger")
        return redirect(url_for('index'))  
    
    if request.method == 'POST':
        title = request.form['Title']
        description = request.form['Description']
        file = request.files.get('Upload_file')
        due_date_str = request.form.get('due_date')

        due_date = None

        try:
            if due_date_str:
                due_date = datetime.strptime(due_date_str, "%Y-%m-%dT%H:%M")
        except ValueError:
            flash("Invalid date format.", "error")
            return render_template('LecturerForm.html')

        filename = None
        if file and file.filename:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Localize due_date to Malaysia time
        malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
        if due_date:
            due_date = malaysia_tz.localize(due_date)

        new_form = FormTemplate(
            title=title,
            description=description,
            filename=filename,
            due_date=due_date
        )
        db.session.add(new_form)
        db.session.commit()

        flash("Form created successfully!", "success")
        return render_template('LecturerForm.html')

    # For GET requests
    return render_template('LecturerForm.html')

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

    # Optional group filter
    selected_group_id = request.args.get('group_id', type=int)
    groups = Group.query.order_by(Group.id).all()

    # Filter by group if selected
    if selected_group_id:
        all_submissions = Submission.query.filter_by(
            group_id=selected_group_id
        ).order_by(Submission.date.desc()).all()
    else:
        all_submissions = Submission.query.order_by(Submission.date.desc()).all()

    # Group submissions into chains
    chains = defaultdict(list)
    for s in all_submissions:
        key = s.original_id if s.original_id else s.id
        chains[key].append(s)

    # Final structure with answer lists
    submissions_dict = {}
    for chain_submissions in chains.values():
        sorted_chain = sorted(chain_submissions, key=lambda x: x.date, reverse=True)
        latest = sorted_chain[0]
        previous = sorted_chain[1] if len(sorted_chain) > 1 else None

        latest_answers = SubmissionFieldAnswer.query.filter_by(submission_id=latest.id).all()
        previous_answers = (
        SubmissionFieldAnswer.query
            .filter_by(submission_id=previous.id)
            .options(db.joinedload(SubmissionFieldAnswer.submission))  
            .all()
            if previous else []
        )
        submissions_dict[latest] = {
            "latest_answers": latest_answers,
            "previous_answers": previous_answers
        }

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
        abort(403)  

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
            # Get all submissions for those courses
            all_submissions = Submission.query.filter(Submission.course_id.in_(course_ids)).order_by(Submission.date.desc()).all()

            # Group submissions into chains using original_id or own id
            chains = defaultdict(list)
            for s in all_submissions:
                key = s.original_id if s.original_id else s.id
                chains[key].append(s)

            # Get only the latest submission per chain
            submissions = [sorted(subs, key=lambda x: x.date, reverse=True)[0] for subs in chains.values()]

        return render_template("status.html", submissions=submissions)

    else:
        # Student view
        group_id = session.get("user_id")
        all_submissions = Submission.query.filter_by(group_id=group_id).order_by(Submission.date.desc()).all()

        # Group submissions into chains
        chains = defaultdict(list)
        for s in all_submissions:
            key = s.original_id if s.original_id else s.id
            chains[key].append(s)

        # Get the latest version of each chain
        latest_submissions = [sorted(subs, key=lambda x: x.date, reverse=True)[0] for subs in chains.values()]

        return render_template("status_s.html", submissions=latest_submissions)

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
    if old_submission.group_id != session.get('user_id'):
        abort(403)

    original_id = old_submission.original_id if old_submission.original_id else old_submission.id

    new_submission = Submission(
        group_id=old_submission.group_id,
        template_id=old_submission.template_id,
        course_id=old_submission.course_id,
        date=datetime.now(malaysia_time),
        status='Pending',
        edited=True,
        original_id=original_id
    )
    db.session.add(new_submission)
    db.session.commit()

    # Copy updated answers
    fields = TemplateField.query.filter_by(template_id=old_submission.template_id).all()
    for field in fields:
        new_value = request.form.get(f'field_{field.id}')
        if new_value is not None:
            answer = SubmissionFieldAnswer(
                submission_id=new_submission.id,
                field_id=field.id,
                value=new_value
            )
            db.session.add(answer)

    # Copy old comments from the original submission chain
    old_comments = Comment.query.filter_by(submission_id=original_id).all()
    for comment in old_comments:
        copied_comment = Comment(
            submission_id=new_submission.id,
            user_id=comment.user_id,
            text=f"[Copied from previous version]\n{comment.text}",
            timestamp=datetime.now(malaysia_time)
        )
        db.session.add(copied_comment)

    db.session.commit()
    flash("Edited submission saved successfully.")
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
    edits = Submission.query.filter_by(original_id=original.id).all()
    all_to_delete = edits + [original]

    # Delete all comments linked to each submission/edit
    for sub in all_to_delete:
        for comment in sub.comments:
            db.session.delete(comment)

    #  delete the submissions
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


app.run(host="0.0.0.0", port=5000, debug = True)