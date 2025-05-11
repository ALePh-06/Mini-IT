import sqlite3

connection = sqlite3.connect('database.db')


with open('Alep/schema.sql') as f:
    connection.executescript(f.read())

cur = connection.cursor()

cur.execute("INSERT INTO courses (title, trimester, code, content) VALUES (?, ?, ?, ?)",
            ('First Course', '1', '123', 'Content for the first course')
            )

cur.execute("INSERT INTO courses (title, trimester, code, content) VALUES (?, ?, ?, ?)",
            ('Second Course', '2', 'ABC', 'Content for the second course')
            )

cur.execute("INSERT INTO courses (title, trimester, code, content) VALUES (?, ?, ?, ?)",
            ('Nopal got no pull game', '3', 'ABCDE12345^', 'As in the title. This is all riyal. You must believe me')
            )


connection.commit()
connection.close()