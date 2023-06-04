from flask import Blueprint

school_user = Blueprint(name='school_user', import_name=__name__ )

from libraryschooldb.SchoolUsers import routes
