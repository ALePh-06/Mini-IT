from flask import Flask, render_template, request, url_for, flash, redirect
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import abort
import os

basedir = os.path.abspath(os.path.dirname(__file__))


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# SQLAlchemy models
class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    trimester = db.Column(db.Integer, nullable=False)
    code = db.Column(db.String, nullable=False)
    content = db.Column(db.String, nullable=False)

class Template(db.Model):
    __tablename__ = 'templates'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    field_name = db.Column(db.String, nullable=False)
    field_order = db.Column(db.Integer, nullable=False)

with app.app_context():
    db.create_all()

# Utility

def get_course(course_id):
    course = db.session.get(Course, course_id)
    if course is None:
        abort(404)
    return course

def get_template(template_id):
    template = db.session.get(Template, template_id)
    if template is None:
        abort(404)
    return template

# Routes
@app.route('/')
def index():
    courses = Course.query.all()
    return render_template('index.html', courses=courses)

@app.route('/course/<int:course_id>')
def view_course(course_id):
    course = get_course(course_id)
    return render_template('view_course.html', course=course)

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
            new_course = Course(title=title, trimester=int(trimester), code=code, content=content)
            db.session.add(new_course)
            db.session.commit()
            return redirect(url_for('index'))

    return render_template('create_course.html')

@app.route('/create_template', methods=('GET', 'POST'))
def create_template():
    if request.method == 'POST':
        template_name = request.form['name']
        field_names = request.form.getlist('field_name')

        if not template_name:
            flash('Name of template is required!')
        elif not field_names or all(f.strip() == '' for f in field_names):
            flash('At least one field name is required!')
        else:
            for i, fname in enumerate(field_names):
                if fname.strip():
                    new_template = Template(name=template_name, field_name=fname.strip(), field_order=i)
                    db.session.add(new_template)
            db.session.commit()
            return redirect(url_for('index'))

    return render_template('create_template.html')

@app.route('/template/<int:template_id>')
def view_template(template_id):
    template = get_template(template_id)
    return render_template('view_template.html', template=template)

@app.route('/<int:id>/edit', methods=('GET', 'POST'))
def edit_course(id):
    course = get_course(id)

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            course.title = title
            course.content = content
            db.session.commit()
            return redirect(url_for('index'))

    return render_template('edit_course.html', course=course)

@app.route('/<int:id>/edit', methods=('GET', 'POST'))
def edit_template(id):
    template = get_template(id)

    if request.method == 'POST':
        title = request.form['title']
        field_name = request.form['field_name']

        if not title:
            flash('Title is required!')
        else:
            template.title = title
            template.field_name = field_name
            db.session.commit()
            return redirect(url_for('index'))

    return render_template('edit.html', template=template)

@app.route('/<int:id>/delete', methods=('POST',))
def delete(id):
    course = get_course(id)
    db.session.delete(course)
    db.session.commit()
    flash(f'"{course.title}" was successfully deleted!')
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
