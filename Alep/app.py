import sqlite3
from flask import Flask, render_template, request, url_for, flash, redirect
from werkzeug.exceptions import abort
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_course(course_id):
    conn = get_db_connection()
    course = conn.execute('SELECT * FROM courses WHERE id = ?',
                        (course_id,)).fetchone()
    conn.close()
    if course is None:
        abort(404)
    return course

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

@app.route('/')
def index():
    conn = get_db_connection()
    courses = conn.execute('SELECT * FROM courses').fetchall()
    conn.close()
    return render_template('index.html', courses = courses)

@app.route('/<int:course_id>')
def course(course_id):
    course = get_course(course_id)
    return render_template('course.html', course = course)

@app.route('/create', methods=('GET', 'COURSE'))
def create():
    if request.method == 'COURSE':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            conn = get_db_connection()
            conn.execute('INSERT INTO courses (title, content) VALUES (?, ?)',
                         (title, content))
            conn.commit()
            conn.close()
            return redirect(url_for('index'))

    return render_template('create.html')

@app.route('/<int:id>/edit', methods=('GET', 'course'))
def edit(id):
    course = get_course(id)

    if request.method == 'COURSE':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            conn = get_db_connection()
            conn.execute('UPDATE courses SET title = ?, content = ?'
                         ' WHERE id = ?',
                         (title, content, id))
            conn.commit()
            conn.close()
            return redirect(url_for('index'))

    return render_template('edit.html', course = course)

@app.route('/<int:id>/delete', methods=('COURSE',))
def delete(id):
    course = get_course(id)
    conn = get_db_connection()
    conn.execute('DELETE FROM courses WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('"{}" was successfully deleted!'.format(course['title']))
    return redirect(url_for('index'))


app.run(host="0.0.0.0", port=5000, debug=True)

