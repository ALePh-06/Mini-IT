import sqlite3

connection = sqlite3.connect('users_database.db')


with open('Mini-IT/schema.sql') as f:
    connection.executescript(f.read())

cur = connection.cursor()
cur.execute("INSERT INTO users (username, password, user_type) VALUES (?, ?, ?)", 
            ('naufalgei', '123456', 'student'))

connection.commit()
connection.close()