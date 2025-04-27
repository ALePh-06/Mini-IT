from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()

# Define User table
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    lecturer_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)

# Define Team table
class Team(Base):
    __tablename__ = 'teams'
    team_id = Column(String, primary_key=True, nullable=False)
    lecturer_id = Column(Integer, ForeignKey('users.lecturer_id'), nullable=False)
    student_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    # Define relationship
    student_name = relationship('User', foreign_keys=id)

# Define Submission table
class Submission(Base):
    __tablename__ = 'submissions'
    id = Column(Integer, unique=True, autoincrement=True)
    team_id = Column(String, ForeignKey('teams.team_id'), nullable=False)
    lecturer_id = Column(Integer, ForeignKey('teams.lecturer_id'), nullable=False)
    time = Column(DateTime, nullable=False, primary_key=True)
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

# Initialize DB connection
engine = create_engine('sqlite:///mydatabase.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()