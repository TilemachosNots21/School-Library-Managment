from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DateField, RadioField
from wtforms.validators import DataRequired


class SchoolSearchForm(FlaskForm):
    search_query = StringField('Αναζήτηση Βιβλιοθήκης', validators=[DataRequired()])
    submit = SubmitField('Submit')

