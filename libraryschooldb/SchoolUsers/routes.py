from flask import Flask, render_template, request, flash, redirect, url_for, abort, session
from flask_mysqldb import MySQL
from libraryschooldb import db  # initially created by __init__.py, need to be used here
from libraryschooldb.SchoolUsers import school_user


@school_user.route('/login/SchoolUser/<role>/<username>/<user_id>', methods=['GET', 'POST'])
def school_user_dashboard(role,username,user_id):

    return render_template('School_user_page.html',role=role,username=username,user_id=user_id)
