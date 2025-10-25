from flask_wtf import FlaskForm
from wtforms import (DateField, FloatField, SelectField, SelectMultipleField,
                     StringField, SubmitField, TextAreaField)
from wtforms.validators import DataRequired, Optional


class TaskForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    description = TextAreaField("Description", validators=[Optional()])
    due_date = DateField("Due date", validators=[Optional()])
    priority = SelectField(
        "Priority",
        choices=[("Low", "Low"), ("Normal", "Normal"), ("High", "High")],
        default="Normal",
    )
    estimated_hours = FloatField("Estimated hours", validators=[Optional()])
    assignees = SelectMultipleField("Assign Users", coerce=int, validators=[Optional()])
    dependencies = SelectMultipleField(
        "Depends on", coerce=int, validators=[Optional()]
    )
    submit = SubmitField("Create Task")


class UpdateStatusForm(FlaskForm):
    status = SelectField(
        "Status",
        choices=[
            ("To Do", "To Do"),
            ("In Progress", "In Progress"),
            ("Completed", "Completed"),
        ],
    )
    submit = SubmitField("Update")


class CommentForm(FlaskForm):
    body = TextAreaField("Comment", validators=[DataRequired()])
    submit = SubmitField("Add Comment")
