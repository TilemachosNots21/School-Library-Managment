from flask import Flask
from flask_mysqldb import MySQL


app = Flask(__name__)
app.debug = True

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'myschool_library'
app.config["SECRET_KEY"] = '1234'


db = MySQL(app)

from libraryschooldb.home import home
from libraryschooldb.authentication import auth
from libraryschooldb.admin import admin
from libraryschooldb.oper import operator
from libraryschooldb.SchoolUsers import school_user
app.register_blueprint(home)
app.register_blueprint(auth)
app.register_blueprint(admin)
app.register_blueprint(operator)
app.register_blueprint(school_user)
