from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length


class RegisterForm(FlaskForm):
    username = StringField('логин', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('пароль', validators=[DataRequired(), Length(min=4)])
    password_again = PasswordField('повтор пароля', validators=[DataRequired()])
    submit = SubmitField('зарегистрироваться')


class LoginForm(FlaskForm):
    username = StringField('логин', validators=[DataRequired()])
    password = PasswordField('пароль', validators=[DataRequired()])
    remember_me = BooleanField('запомнить меня')
    submit = SubmitField('войти')