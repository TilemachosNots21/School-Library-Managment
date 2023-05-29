from flask import Blueprint

student = Blueprint(name='student', import_name=__name__ )

from libraryschooldb.student import routes
