import sqlite3

connection = sqlite3.connect('users_database.db')

cur = connection.cursor()

cur.execute("INSERT INTO users (username, password, user_type) VALUES (?, ?, ?)",
            ('abu', 'abc123', 'lecturer')
            )



connection.commit()
connection.close()