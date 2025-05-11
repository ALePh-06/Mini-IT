import sqlite3

connection = sqlite3.connect('database.db')


with open('Alep/schema.sql') as f:
    connection.executescript(f.read())

cur = connection.cursor()

cur.execute("INSERT INTO posts (title, content) VALUES (?, ?)",
            ('First Post', 'Content for the first post')
            )

cur.execute("INSERT INTO posts (title, content) VALUES (?, ?)",
            ('Second Post', 'Content for the second post')
            )

cur.execute("INSERT INTO posts (title, content) VALUES (?, ?)",
            ('Nopal got no pull game', 'As in the title. This is all riyal. You must believe me')
            )


connection.commit()
connection.close()