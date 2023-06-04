from flask_wtf import FlaskForm
from wtforms import validators, SubmitField, SelectField, StringField, IntegerField, TextAreaField, Form, FieldList, \
    FormField, BooleanField, SelectMultipleField
from wtforms.validators import DataRequired, NumberRange, ValidationError


class AtLeastOneGenre(ValidationError):

    def __call__(self, form, field):
        genres = form.genres.data
        new_genre = form.new_genre.data
        # Check if at least one genre has been selected or input
        if not genres and not new_genre:
            raise ValidationError("Please select at least one genre or enter a new one.")


class InsertBookForm(FlaskForm):
    title = StringField('Τίτλος', validators=[DataRequired()])
    publisher = StringField('Εκδότης', validators=[DataRequired()])
    isbn = StringField('ISBN', validators=[DataRequired()])
    authors = FieldList(StringField('Συγγραφέας/είς'), min_entries=1, validators=[DataRequired()])
    number_of_pages = IntegerField('Αριθμός Σελίδων', validators=[DataRequired(), NumberRange(min=1)])
    description = TextAreaField('Περιγραφή')
    number_of_copies = IntegerField('Διαθέσιμα Αντίτυπα', validators=[DataRequired(),NumberRange(min=1)])
    image_url = StringField('Εικόνα', [validators.URL(message='Must be a valid URL'), ])
    genres = SelectMultipleField('Είδος/Κατηγορία', choices=[], validators=[AtLeastOneGenre()])
    new_genre = StringField('Νέο είδος/κατηγορία')
    language = SelectField('Γλώσσα', choices=[('0', '-'), ('1', 'Ελληνικά'), ('2', 'Αγγλικά'), ('3', 'Γερμανικά'), ('4', 'Γαλλικά')], validators=[DataRequired()])
    keywords = FieldList(StringField('Λέξεις Κλειδιά'), min_entries=1, validators=[DataRequired()])
    submit = SubmitField('Εισαγωγή Βιβλίου')


class BookSearchForm(FlaskForm):
    search = StringField('Αναζήτηση', validators=[DataRequired()])
    submit = SubmitField('Υποβολή')


class EditBookForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    isbn = StringField('ISBN', validators=[DataRequired()])
    publisher = StringField('Publisher', validators=[DataRequired()])
    authors = TextAreaField('Authors')  # This assumes authors are entered as comma-separated values in a textarea
    categories = TextAreaField('Categories')  # Same assumption for categories
    keywords = TextAreaField('Keywords')  # Same assumption for keywords
    available_copies = StringField('Available Copies', validators=[DataRequired()])
    submit = SubmitField('Update')

