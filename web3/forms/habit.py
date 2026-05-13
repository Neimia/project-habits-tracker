from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, DateField
from wtforms.validators import DataRequired, Length
from flask_wtf.file import FileField, FileAllowed, FileRequired


class AddHabitForm(FlaskForm):
    name = StringField('название', validators=[DataRequired(), Length(min=1, max=100)])
    description = TextAreaField('описание')
    submit = SubmitField('добавить')


class CheckHabitForm(FlaskForm):
    check_date = DateField('дата', validators=[DataRequired()])
    submit = SubmitField('отметить')


class ImportHabitsForm(FlaskForm):
    db_file = FileField('файл базы данных (.db)', validators=[
        FileRequired(),
        FileAllowed(['db'], 'только .db файлы')
    ])
    submit = SubmitField('импортировать')