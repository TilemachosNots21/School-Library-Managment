from flask import Flask, render_template, request, flash, redirect, url_for, abort, session
from flask_mysqldb import MySQL
from MySQLdb.cursors import DictCursor
from libraryschooldb import db  # initially created by __init__.py, need to be used here
from libraryschooldb.SchoolUsers import school_user


@school_user.route('/login/SchoolUser/<role>/<username>/<user_id>', methods=['GET', 'POST'])
def school_user_dashboard(role,username,user_id):

    return render_template('School_user_page.html',role=role,username=username,user_id=user_id)


@school_user.route('/login/SchoolUser/<role>/<username>/<user_id>/borrowed_books', methods=['GET'])
def borrowed_books(role,username,user_id):
    Schooluser_id = session['user_id']

    query = """
    SELECT B.Title, Bo.Borrow_Date as BorrowDate, Bo.Due_Date as DueDate
    FROM Borrow Bo
    JOIN Book B ON Bo.BookID = B.BookID
    WHERE Bo.SchoolUserID = %s
    """
    cursor = db.connection.cursor(DictCursor)
    cursor.execute(query, [Schooluser_id])
    results = cursor.fetchall()
    cursor.close()

    return render_template('schooluser_borrowed_books.html', results=results,role=role,username=username,user_id=user_id)




