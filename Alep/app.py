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

@app.route('/create_course', methods=('GET', 'POST'))
def create_course():
    if request.method == 'POST':
        title = request.form['title']
        trimester = request.form['trimester']
        code = request.form['code']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        elif not trimester:
            flash('Trimester is required!')
        elif not code:
            flash('Code is required!')
        else:
            conn = get_db_connection()
            conn.execute('INSERT INTO courses (title, trimester, code, content) VALUES (?, ?, ?, ?)',
                         (title, trimester, code, content))
            conn.commit()
            conn.close()
            return redirect(url_for('index'))

    return render_template('create_course.html')

@app.route('/create_template', methods=('GET', 'POST'))
def create_template():
    if request.method == 'POST':
        template_name = request.form['name']
        field_names = request.form.getlist['field_name']

        if not template_name:
            flash('Name of template is required!')
        elif not field_names or all(f.strip() == '' for f in field_names):
            flash('At least one field name is required!')
        else:
            conn = get_db_connection()
            for i, fname in enumerate(field_names):
                if fname.strip():  # skip empty field names
                    conn.execute('INSERT INTO templates (name, field_name, field_order) VALUES (?, ?, ?)',
                                 (template_name, fname.strip(), i))
                    conn.commit()
                    conn.close()
            return redirect(url_for('index'))

    return render_template('create_template.html')

@app.route('/<int:id>/edit', methods=('GET', 'POST'))
def edit(id):
    course = get_course(id)

    if request.method == 'POST':
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

@app.route('/<int:id>/delete', methods=('POST',))
def delete(id):
    course = get_course(id)
    conn = get_db_connection()
    conn.execute('DELETE FROM courses WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('"{}" was successfully deleted!'.format(course['title']))
    return redirect(url_for('index'))


app.run(host="0.0.0.0", port=5000, debug=True)

