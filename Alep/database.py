from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, Boolean, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.inspection import inspect
from datetime import datetime

Base = declarative_base()

# Define User table
class User(Base):
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
class Lecturer(Base):
    __tablename__ = 'lecturers'
    id = Column(Integer, ForeignKey('users.id'), nullable=False)
    lecturer_id = Column(Integer, primary_key=True, autoincrement=True)

    # Relationship back to User
    user = relationship('User', back_populates='lecturer_details')

# Define Team table
class Team(Base):
    __tablename__ = 'teams'
    team_id = Column(String, primary_key=True, nullable=False)
    lecturer_id = Column(Integer, ForeignKey('lecturers.lecturer_id'), nullable=False)
    student_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    # Define relationship
    student_name = relationship('User', foreign_keys=[student_id])

# Define Submission table
class Submission(Base):
    __tablename__ = 'submissions'
    id = Column(Integer, unique=True, autoincrement=True, primary_key=True)
    team_id = Column(String, ForeignKey('teams.team_id'), nullable=False)
    lecturer_id = Column(Integer, ForeignKey('teams.lecturer_id'), nullable=False)
    time = Column(DateTime, nullable=False, default=datetime.now)
    title = Column(String, nullable=False)
    field1 = Column(String, nullable=False)
    field2 = Column(String) 
    field3 = Column(String) 
    field4 = Column(String) 
    field5 = Column(String) 
    field6 = Column(String) 
    field7 = Column(String) 
    field8 = Column(String) 
    field9 = Column(String) 

    # Define relationship to history
    histories = relationship('History', back_populates='submission')

# Define Submission History table
class History(Base):
    __tablename__ = 'history'
    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    submission_id = Column(Integer, ForeignKey('submissions.id'), nullable=False)
    team_id = Column(String, nullable=False)
    lecturer_id = Column(Integer, nullable=False)
    time = Column(DateTime, nullable=False)
    title = Column(String, nullable=False)
    field1 = Column(String, nullable=False)
    field2 = Column(String)
    field3 = Column(String)
    field4 = Column(String)
    field5 = Column(String)
    field6 = Column(String)
    field7 = Column(String)
    field8 = Column(String)
    field9 = Column(String)
    # Define relationship to submission
    submission = relationship('Submission', back_populates='histories')

# Define Approval Status table
class Status(Base):
    __tablename__ = 'status'
    id = Column(Integer, ForeignKey('submissions.id'), nullable=False, primary_key=True)
    team_id = Column(Integer, ForeignKey('submissions.team_id'), nullable=False)
    lecturer_id = Column(Integer, ForeignKey('submissions.lecturer_id'), nullable=False)
    status = Column(String, default="pending")

# Define Comment
class Comment(Base):
    __tablename__ = 'comments'
    id = Column(Integer, unique=True, autoincrement=True, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    time = Column(DateTime, default=datetime.now)
    message = Column(String, nullable=False)

    # Set relationship to user so that user name will show up
    user = relationship('User', foreign_keys=[user_id], back_populates='comments')

# Event listener for automatically creating a Lecturer entry after a User insert
@event.listens_for(User, 'after_insert')
def create_lecturer_entry(mapper, connection, target):
    if target.lecturer:  # Check if the user is a lecturer
        # Automatically create a Lecturer entry
        lecturer = Lecturer(id=target.id)  # Use the user's ID as the foreign key
        connection.execute(
            Lecturer.__table__.insert().values(id=target.id)
        )

def create_submission_snapshot(submission):
    snapshot_data = {}
    mapper = inspect(History)

    # Loop through History's column names
    for column in mapper.attrs:
        col_name = column.key
        
        # Copy fields if they exist in Submission
        if hasattr(submission, col_name):
            snapshot_data[col_name] = getattr(submission, col_name)
    
    # Set submission_id manually (if not set yet)
    snapshot_data['submission_id'] = submission.id

    return History(**snapshot_data)

# Initialize DB connection
engine = create_engine('sqlite:///mydatabase.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

session.add_all([
    User(lecturer=False, name='Ah Chong'),
    User(lecturer=True, name='Vin Diesel'),

])