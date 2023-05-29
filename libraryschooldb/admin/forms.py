import calendar
import datetime
from flask_wtf import FlaskForm
from wtforms import SubmitField, SelectField, StringField, IntegerField
from wtforms.validators import DataRequired


class BorrowHistoryForm(FlaskForm):
    year = SelectField('Χρονιά',
                       choices=[(r, r) for r in range(2013, datetime.datetime.now().year + 1)],
                       validators=[DataRequired()])
    month = SelectField('Μήνας',
                        choices=[(i, name) for i, name in enumerate(calendar.month_name) if i > 0],
                        validators=[DataRequired()])
    submit = SubmitField('Υποβολή')


class SchoolUnitForm(FlaskForm):
    school_name = StringField('Ονομασία Σχολείου', validators=[DataRequired()])
    address = StringField('Διεύθυνση', validators=[DataRequired()])
    city = StringField('Πόλη', validators=[DataRequired()])
    phone_number = IntegerField('Τηλέφωνο', validators=[DataRequired()])
    email = StringField('E-mail', validators=[DataRequired()])
    director_name = StringField('Ονοματεπώνυμο Δ/ντη Σχολείου', validators=[DataRequired()])
    submit = SubmitField('Εγγραφή')

