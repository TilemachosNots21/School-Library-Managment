from flask import Flask, render_template, request, flash, redirect, url_for, abort, session
from flask_mysqldb import MySQL
from libraryschooldb import db  # initially created by __init__.py, need to be used here
from libraryschooldb.teacher import teacher


@teacher.route('/login/teacher', methods=['GET', 'POST'])
def teacher_dashboard():
    return render_template('teacher_page.html')
