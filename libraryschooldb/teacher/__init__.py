from flask import Blueprint

teacher = Blueprint(name='teacher', import_name=__name__ )

from libraryschooldb.teacher import routes
