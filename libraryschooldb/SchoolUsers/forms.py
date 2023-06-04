from flask_wtf import FlaskForm
from wtforms import validators, SubmitField, SelectField, StringField, IntegerField, TextAreaField, Form, FieldList, \
    FormField, BooleanField, SelectMultipleField
from wtforms.validators import DataRequired, NumberRange, ValidationError


class SearchRatingsForm(FlaskForm):
    first_name = StringField('First Name', [validators.optional()])
    last_name = StringField('Last Name', [validators.optional()])
    category = StringField('Category', [validators.optional()])
    submit = SubmitField('Search')
