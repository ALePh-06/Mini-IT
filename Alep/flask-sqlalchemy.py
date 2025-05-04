from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# Setup the database URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mydatabase.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Import your models
from database import *

@app.route('/submit/<team_id>', methods=['GET', 'POST'])
def submit_proposal(team_id):
    # Get the team and lecturer based on the team_id
    team = Team.query.filter_by(team_id=team_id).first()
    if not team:
        return "Team not found", 404

    # Fetch the submission template fields for the team
    template_fields = SubmissionTemplate.query.filter_by(team_id=team_id).order_by(SubmissionTemplate.field_order).all()

    if request.method == 'POST':
        # Create a new submission object
        submission = Submission(
            team_id=team_id,
            lecturer_id=team.lecturer_id,
            title=request.form['title']
        )
        db.session.add(submission)
        db.session.commit()

        # Loop through all the template fields and save the student's answers
        for field in template_fields:
            field_value = request.form.get(field.field_name)  # Get the answer for this field
            submission_field = SubmissionField(
                submission_id=submission.id,
                field_name=field.field_name,
                field_value=field_value
            )
            db.session.add(submission_field)

        db.session.commit()

        return redirect(url_for('submission_success', submission_id=submission.id))

    return render_template('submit_proposal.html', team=team, fields=template_fields)

@app.route('/submission_success/<int:submission_id>')
def submission_success(submission_id):
    # Fetch the submission based on ID to confirm success
    submission = Submission.query.get(submission_id)
    if not submission:
        return "Submission not found", 404
    return f"Submission {submission.title} was successful!"

if __name__ == '__main__':
    app.run(debug=True)