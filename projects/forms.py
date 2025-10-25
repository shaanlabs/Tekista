from flask_wtf import FlaskForm
from wtforms import (DateField, SelectMultipleField, StringField, SubmitField,
                     TextAreaField)
from wtforms.validators import DataRequired, Optional


class ProjectForm(FlaskForm):
	title = StringField('Title', validators=[DataRequired()])
	description = TextAreaField('Description', validators=[Optional()])
	deadline = DateField('Deadline', validators=[Optional()])
	users = SelectMultipleField('Assign Users', coerce=int, validators=[Optional()])
	submit = SubmitField('Create Project')
