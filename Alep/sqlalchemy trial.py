import sqlalchemy as db 
  
# Defining the Engine 
engine = db.create_engine('sqlite:///users.db', echo=True) 
  
# Create the Metadata Object 
metadata_obj = db.MetaData() 
  
# Define the profile table 
  
# database name 
students = db.Table( 
    'students',                                         
    metadata_obj,                                     
    db.Column('first_name', db.String),   
    db.Column('last_name', db.String),                     
    db.Column('course', db.String),
    db.Column('score', db.Integer),        
) 
  
# Create the profile table 
metadata_obj.create_all(engine) 

statement1  = students.insert().values(first_name = "Asish",
                                      last_name = "Mysterio",
                                      course = "Statistics",
                                      score = 90)