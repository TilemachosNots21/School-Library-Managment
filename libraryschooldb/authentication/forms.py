from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DateField, RadioField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo


# when passed as a parameter to a template, an object of this class will be rendered as a regular HTML form
# with the additional restrictions specified for each field


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(message="Username required")])
    password = PasswordField('Password', validators=[DataRequired(message="Password required")])
    submit = SubmitField('Login')


class PasswordResetRequestForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(message="Username required")])
    email = StringField('Email', validators=[DataRequired(message="Email required")])
    submit = SubmitField('Request Password Reset')


class PasswordResetForm(FlaskForm):
    password = PasswordField('New Password',validators=[DataRequired()])
    password_confirm = PasswordField('Confirm Password', validators=[DataRequired(message="Confirm your password"), EqualTo('password')])
    submit = SubmitField('Reset Password')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    surname = StringField('Surname', validators=[DataRequired()])
    birthdate = DateField('Birthdate', format='%Y-%m-%d', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    phoneNumber = StringField('PhoneNumber', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    school_unit = SelectField('School Unit', choices= [] , validators=[DataRequired()])
    role = RadioField('Role', choices=[('operator','Υπεύθυνος Βιβλιοθήκης'),('teacher','Εκπαιδευτικός'), ('student', 'Μαθητής')], validators=[DataRequired()])
    submit = SubmitField('Submit')
