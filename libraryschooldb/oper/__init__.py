from flask import Blueprint

operator = Blueprint(name='oper', import_name=__name__)

from libraryschooldb.oper import routes
