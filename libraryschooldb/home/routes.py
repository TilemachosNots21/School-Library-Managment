from flask import Flask, render_template, request, flash, redirect, url_for, abort, session
from flask_mysqldb import MySQL
from MySQLdb.cursors import DictCursor
from libraryschooldb import db
from libraryschooldb.home import home
from libraryschooldb.home.forms import SchoolSearchForm


@home.route('/')
def home_page():
    return render_template('home_page.html')


@home.route('/libraries_list', methods=['GET', 'POST'])
def library_list():
    form = SchoolSearchForm(request.form)
    schools = []
    cursor = db.connection.cursor(DictCursor)

    try:
        query = "SELECT su.School_Name, su.Postal_Address, su.City, su.PhoneNumber, su.Email, su.School_Director, " \
                "CONCAT(au.FirstName, ' ', au.LastName) as OperatorName " \
                "FROM School_Unit su INNER JOIN Operator op ON su.SchoolID = op.SchoolID " \
                "INNER JOIN AppUser au ON op.OperatorID = au.UserID "
        cursor.execute(query)
        schools = cursor.fetchall()
    except Exception as e:
        flash("An error occurred. Please try again.", "danger")
        print(f"Error: {str(e)}")
    finally:
        cursor.close()
        db.connection.commit()

    if request.method == 'POST' and form.validate():
        search_query = form.search_query.data.lower()
        schools = [school for school in schools if search_query in school['School_Name'].lower()]

    return render_template('School_Libraries_List.html', form=form, schools=schools)

