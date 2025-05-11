import sqlite3

connection = sqlite3.connect('database.db')


with open('Alep/schema.sql') as f:
    connection.executescript(f.read())

cur = connection.cursor()

cur.execute("INSERT INTO courses (title, code, content) VALUES (?, ?, ?)",
            ('First Course', '123', 'Content for the first course')
            )

cur.execute("INSERT INTO courses (title, code, content) VALUES (?, ?, ?)",
            ('Second Course', 'ABC', 'Content for the second course')
            )

cur.execute("INSERT INTO courses (title, code, content) VALUES (?, ?, ?)",
            ('Nopal got no pull game', 'ABCDE12345^', 'As in the title. This is all riyal. You must believe me')
            )


connection.commit()
connection.close()