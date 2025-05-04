from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import Enum, Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.event import listens_for

# Initialize Flask app and Flask-SQLAlchemy
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mydatabase.db'  # Replace with your database URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable modification tracking
db = SQLAlchemy(app)

# Define User table
class User(db.Model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    lecturer = Column(Boolean, nullable=False, default=False)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)

    # Add relationship from the User side to access all comments
    comments = relationship('Comment', back_populates='user')

    # Relationship to Lecturer (one-to-one)
    lecturer_details = relationship('Lecturer', back_populates='user', uselist=False)

# Define Lecturer table
class Lecturer(db.Model):
    __tablename__ = 'lecturers'
    id = Column(Integer, ForeignKey('users.id'), primary_key=True, nullable=False)
    lecturer_id = Column(Integer, autoincrement=True)

    # Relationship back to User
    user = relationship('User', back_populates='lecturer_details')

# Define Team table
class Team(db.Model):
    __tablename__ = 'teams'
    team_id = Column(String, primary_key=True, nullable=False)
    lecturer_id = Column(Integer, ForeignKey('lecturers.lecturer_id'), nullable=False)
    student_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    # Define relationship
    student_name = relationship('User', foreign_keys=[student_id])
    comments = relationship('Comment', backref='team')
    submissions = relationship('Submission', backref='team')

class SubmissionTemplate(db.Model):
    __tablename__ = 'submission_templates'
    id = Column(Integer, primary_key=True, autoincrement=True)
    lecturer_id = Column(Integer, ForeignKey('lecturers.lecturer_id'), nullable=False)
    team_id = Column(String, ForeignKey('teams.team_id'), nullable=False)
    field_name = Column(String, nullable=False) 
    field_order = Column(Integer, nullable=False)  # For sorting

class SubmissionField(db.Model):
    __tablename__ = 'submission_fields'
    id = Column(Integer, primary_key=True)
    submission_id = Column(Integer, ForeignKey('submissions.id'), nullable=False)
    field_name = Column(String, nullable=False)  # Should match a template field
    field_value = Column(String, nullable=False)

    submission = relationship('Submission', back_populates='fields')

''' How to use Submission template, eg: Create template for team T001
fields = ['Project Title', 'Objective', 'Tools', 'Timeline']

for i, name in enumerate(fields):
    session.add(SubmissionTemplate(team_id='T001', lecturer_id=1, field_name=name, field_order=i))

session.commit()'''

# Define Submission table
class Submission(db.Model):
    __tablename__ = 'submissions'
    id = Column(Integer, unique=True, autoincrement=True, primary_key=True)
    team_id = Column(String, ForeignKey('teams.team_id'), nullable=False)
    lecturer_id = Column(Integer, ForeignKey('teams.lecturer_id'), nullable=False)
    time = Column(DateTime, nullable=False, default=datetime.now)
    title = Column(String, nullable=False)

    # Define relationship to history
    fields = relationship('SubmissionField', back_populates='submission')
    histories = relationship('History', back_populates='submission')

''' How student data will be entered into the database 
submission = Submission(team_id='T001', lecturer_id=1, title="Smart Garden")

# Assume this came from a form
field_inputs = {
    'Project Title': "Smart Garden",
    'Objective': "Automated watering system",
    'Tools': "Raspberry Pi, sensors",
    'Timeline': "Week 1: Setup, Week 2: Testing"
}

for field_name, value in field_inputs.items():
    submission.fields.append(SubmissionField(field_name=field_name, field_value=value))

session.add(submission)
session.commit()'''

# Define Submission History table
class SubmissionHistory(db.Model):
    __tablename__ = 'submission_history'
    id = Column(Integer, primary_key=True)
    submission_id = Column(Integer, ForeignKey('submissions.id'))
    time = Column(DateTime, default=datetime.now)
    field_name = Column(String, nullable=False)
    field_value = Column(String, nullable=False)

# Define Approval Status table
class Status(db.Model):
    __tablename__ = 'status'
    id = Column(Integer, ForeignKey('submissions.id'), nullable=False, primary_key=True)
    team_id = Column(String, ForeignKey('submissions.team_id'), nullable=False)
    lecturer_id = Column(Integer, ForeignKey('submissions.lecturer_id'), nullable=False)
    status = Column(Enum("pending", "approved", "rejected", name="status_enum"), default="pending")

# Define Comment
class Comment(db.Model):
    __tablename__ = 'comments'
    id = Column(Integer, unique=True, autoincrement=True, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    team_id = Column(String, ForeignKey('teams.team_id'), nullable=False)
    time = Column(DateTime, default=datetime.now)
    message = Column(String, nullable=False)

    # Set relationship to user so that user name will show up
    user = relationship('User', foreign_keys=[user_id], back_populates='comments')
    team = relationship('Team') 

# Event listener for automatically creating a Lecturer entry after a User insert
@listens_for(User, 'after_insert')
def create_lecturer_entry(mapper, connection, target):
    if target.lecturer:  # Check if the user is a lecturer
        # Automatically create a Lecturer entry
        lecturer = Lecturer(id=target.id)  # Use the user's ID as the foreign key
        connection.execute(
            Lecturer.__table__.insert().values(id=target.id)
        )

with app.app_context():
    db.create_all()

# Example of using Submission template to add fields
# @coofee3 kene buat la nanti
'''def create_submission_template():
    fields = ['Project Title', 'Objective', 'Tools', 'Timeline']
    for i, name in enumerate(fields):
        db.session.add(SubmissionTemplate(team_id='T001', lecturer_id=1, field_name=name, field_order=i))
    db.session.commit()'''

# Example of creating a submission
'''def create_submission():
    submission = Submission(team_id='T001', lecturer_id=1, title="Smart Garden")
    field_inputs = {
        'Project Title': "Smart Garden",
        'Objective': "Automated watering system",
        'Tools': "Raspberry Pi, sensors",
        'Timeline': "Week 1: Setup, Week 2: Testing"
    }
    for field_name, value in field_inputs.items():
        submission.fields.append(SubmissionField(field_name=field_name, field_value=value))
    db.session.add(submission)
    db.session.commit()'''

if __name__ == "__main__":
    app.run(debug=True)