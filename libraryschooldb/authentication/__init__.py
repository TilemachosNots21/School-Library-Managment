from flask import Blueprint

auth = Blueprint(name='auth', import_name=__name__)

from libraryschooldb.authentication import routes
