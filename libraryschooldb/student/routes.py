from flask import Flask, render_template, request, flash, redirect, url_for, abort, session
from flask_mysqldb import MySQL
from libraryschooldb import db  # initially created by __init__.py, need to be used here
from libraryschooldb.student import student


@student.route('/login/student', methods=['GET', 'POST'])
def student_dashboard():
    return render_template('student_page.html')

