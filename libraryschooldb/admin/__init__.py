from flask import Blueprint

admin = Blueprint(name='admin', import_name=__name__)

from libraryschooldb.admin import routes
