import subprocess
import os
from flask import Flask, render_template, session, send_file , request, flash, redirect, url_for, abort, session
from MySQLdb.cursors import DictCursor
from flask_mysqldb import MySQL
from werkzeug.utils import secure_filename
from libraryschooldb import db  # initially created by __init__.py, need to be used here
from libraryschooldb.admin import admin
from libraryschooldb.admin.forms import BorrowHistoryForm, SchoolUnitForm


@admin.route('/login/<role>/<username>', methods=['GET', 'POST'])
def admin_dashboard(role, username):
    if session.get('role') != 'administrator':
        flash('Unauthorized access. You must be an admin to view this page.', 'danger')
        return redirect(url_for('home.home_page'))  # or wherever you want to redirect

    return render_template('admin_page.html', role=role, username=username )


@admin.route('/login/admin/total_borrow_history', methods=['GET', 'POST'])
def total_borrow_history():
    if 'username' not in session or session.get('role') != 'administrator':
        flash('Unauthorized access. You must be an admin to view this page.', 'danger')
        return redirect(url_for('home.home_page'))  # or wherever you want to redirect

    form = BorrowHistoryForm()
    loans = []
    if form.validate_on_submit():
        year = form.year.data
        month = form.month.data
        query = "SELECT s.School_Name , Count(B.BorrowID) AS TotalLoans " \
                "FROM School_Unit s " \
                "JOIN SchoolUser su ON s.SchoolID = su.SchoolID " \
                "JOIN Borrow b ON su.SchoolUserID = b.SchoolUserID " \
                "WHERE YEAR(b.Borrow_Date) = %s AND MONTH(b.Borrow_Date) = %s " \
                "GROUP BY s.School_Name"
        try:
            cursor = db.connection.cursor(DictCursor)
            cursor.execute(query, (year, month))
            loans = cursor.fetchall()
        except Exception as e:
            flash(str(e), "danger")
            print(str(e))
            # abort(500)
        finally:
            cursor.close()

    return render_template('Admin_total_borrow_history.html', form=form, loans=loans)


@admin.route('/login/admin/register_school', methods=['GET', 'POST'])
def register_school():
    if 'username' not in session or session.get('role') != 'administrator':
        flash('Unauthorized access. You must be an admin to view this page.', 'danger')
        return redirect(url_for('home.home_page'))  # or wherever you want to redirect

    form = SchoolUnitForm()
    if form.validate_on_submit():
        school_name = form.school_name.data
        address = form.address.data
        city = form.city.data
        phone_number = form.phone_number.data
        email = form.email.data
        director_name = form.director_name.data
        admin_id = session['user_id']

        query = "CALL InsertSchoolUnit(%s,%s,%s,%s,%s,%s)"

        try:
            cursor=db.connection.cursor()
            cursor.execute(query,(school_name,address,city,phone_number,email,director_name,admin_id))
        except Exception as e:
            flash(str(e), "danger")
            print(str(e))
            # abort(500)
        finally:
            cursor.close()
            db.connection.commit()

    flash('The school unit was added successfully.')
    return render_template('register_library.html', form=form)


@admin.route('/login/admin/backup', methods=['GET', 'POST'])
def create_backup():
    if 'username' not in session or session.get('role') != 'administrator':
        flash('Permission denied.')
        return redirect(url_for('home.home_page'))

    if request.method == 'POST':
        try:
            db_user = 'root'
            # db_password = ''
            db_name = 'myschool_library'
            backup_file_path = 'C:/xampp/Data_Bases/MyDatabase/Backup/db_backup.sql'

            command = ['C:/xampp/mysql/bin/mysqldump.exe', '-u', db_user, db_name]
            with open(backup_file_path, 'w') as f:
                proc = subprocess.run(command, stdout=f, stderr=subprocess.PIPE)
                if proc.returncode != 0:
                    flash(f'An error occurred during backup: {proc.stderr.decode()}')

            flash('Backup created successfully.')
            return send_file(backup_file_path, as_attachment=True)

        except subprocess.CalledProcessError:
            flash('Backup creation failed. Please try again.')
        except Exception as e:
            flash(f'An error occurred: {str(e)}')

    return render_template('admin_page.html')


@admin.route("/login/admin/restore", methods=['GET', 'POST'])
def restore_system():
    if 'username' not in session or session.get('role') != 'administrator':
        flash('Permission denied.')
        return redirect(url_for('home.home_page'))

    if request.method == 'POST':
        try:
            db_user = 'root'
            # db_password = ''
            db_name = 'myschool_library'
            backup_dir = 'C:/xampp/Data_Bases/MyDatabase/Backup'

            # Get backup file from form
            backup_file = request.files['backup_file']
            if backup_file:
                filename = secure_filename(backup_file.filename)
                backup_file_path = os.path.join(backup_dir, filename)
                backup_file.save(backup_file_path)

                command = ['C:/xampp/mysql/bin/mysql.exe', '-u', db_user, db_name]
                with open(backup_file_path, 'r') as f:
                    proc = subprocess.run(command, stdin=f, stderr=subprocess.PIPE)
                    if proc.returncode != 0:
                        flash(f'An error occurred during backup: {proc.stderr.decode()}')

                flash('System restored successfully from backup.')
            else:
                flash('No file selected for restoring.')

        except FileNotFoundError:
            flash('Backup file not found. Please upload a valid backup file.')
        except subprocess.CalledProcessError:
            flash('System restore failed. Please try again.')
        except Exception as e:
            flash(f'An error occurred: {str(e)}')

    return render_template('admin_page.html')


@admin.route('/login/admin/approval_of_operator', methods=['GET', 'POST'])
def approve_operator_registrations():
    if 'username' not in session or session.get('role') != 'administrator':
        flash('Permission denied.')
        return redirect(url_for('home.home_page'))
    operator_requests = []
    admin_id = session.get('user_id')
    query = "SELECT FirstName, LastName, Email, PhoneNumber, Username, School_Unit " \
            "FROM RegistrationRequest " \
            "WHERE Role_Type = 'operator' "

    try:
        cursor = db.connection.cursor(DictCursor)
        cursor.execute(query)
        operator_requests = cursor.fetchall()

        if request.method == 'POST':
            username = request.form.get('username')
            action = request.form.get('action')

            if action == 'approve':
                cursor.execute("SELECT * FROM RegistrationRequest WHERE Username = %s", (username,))
                selected_operator = cursor.fetchone()
                school_id = selected_operator['School_Unit']
                cursor.execute("DELETE FROM RegistrationRequest WHERE RequestID = %s",
                               (selected_operator['RequestID'],))
                cursor.execute("SELECT School_Name FROM School_Unit WHERE SchoolId = %s", (school_id,))
                school_name = cursor.fetchone()
                query2 = "CALL InsertOperator(%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                cursor.execute(query2, (selected_operator['FirstName'], selected_operator['LastName'], selected_operator['Email'],selected_operator['Username'], selected_operator['Password'], selected_operator['PhoneNumber'], selected_operator['BirthDate'], admin_id, school_id))
                flash('The request from user {} has been successfully approved.'.format(username), 'success')
                return redirect(url_for('admin.approve_operator_registrations'))
            elif action == 'reject':
                cursor.execute("SELECT RequestID FROM RegistrationRequest WHERE Username = %s", (username,))
                selected_operator = cursor.fetchone()
                cursor.execute("DELETE FROM RegistrationRequest WHERE RequestID = %s",
                               (selected_operator['RequestID'],))
                flash('The request from user {} has been successfully rejected.'.format(username), 'success')
                return redirect(url_for('admin.approve_operator_registrations'))
            else:
                flash('Invalid action.', 'error')
                return redirect(url_for('admin.approve_operator_registrations'))
    except Exception as e:
        flash(str(e), "Error")
    finally:
        cursor.close()
        db.connection.commit()

    return render_template('approve_operator.html', operator_requests=operator_requests)


@admin.route('/book_category_details', methods=['GET', 'POST'])
def book_category_details():
    # Fetch the list of book categories from the database
    cursor = db.connection.cursor(DictCursor)
    cursor.execute("SELECT CategoryName FROM Category")
    categories = [category['CategoryName'] for category in cursor.fetchall()]
    authors = []
    teachers = []

    if request.method == 'POST':
        category_name = request.form['category_name']

        query = """
        SELECT a.FullName AS AuthorName, CONCAT(u.FirstName, ' ', u.LastName) AS TeacherName
        FROM Category c
        JOIN BookCategory bc ON c.CategoryID = bc.CategoryID
        JOIN Book b ON bc.BookID = b.BookID
        JOIN BookAuthor ba ON b.BookID = ba.BookID
        JOIN Author a ON ba.AuthorID = a.AuthorID
        JOIN Borrow br ON b.BookID = br.BookID
        JOIN SchoolUser su ON br.SchoolUserID = su.SchoolUserID
        JOIN AppUser u ON su.SchoolUserID = u.UserID
        WHERE c.CategoryName = %s AND su.Position = 'Teacher' AND br.Borrow_Date >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR);
        """
        cursor.execute(query, (category_name,))
        results = cursor.fetchall()

        print("SQL Query Results:", results)  # Print out the results of the SQL query

        authors = list(set([result['AuthorName'] for result in results]))
        teachers = list(set([result['TeacherName'] for result in results]))

    cursor.close()

    # Render the template with the query results and categories
    return render_template('admin_book_category_details.html', categories=categories, authors=authors, teachers=teachers)


@admin.route('/login/<role>/<username>/young_teachers_books', methods=['GET','POST'])
def young_teachers_books(role, username):
    cursor = db.connection.cursor(DictCursor)
    query = """
    SELECT CONCAT(u.FirstName, ' ', u.LastName) AS TeacherName, COUNT(DISTINCT b.BookID) AS NumberOfBooks
    FROM SchoolUser su
    JOIN AppUser u ON su.SchoolUserID = u.UserID
    JOIN Borrow bo ON su.SchoolUserID = bo.SchoolUserID
    JOIN Book b ON bo.BookID = b.BookID
    WHERE su.Position = 'Teacher' AND YEAR(CURDATE()) - YEAR(u.BirthDate) < 40
    GROUP BY su.SchoolUserID
    ORDER BY NumberOfBooks DESC;
    """
    cursor.execute(query)
    results = cursor.fetchall()
    cursor.close()
    return render_template('admin_young_teachers_books.html', results=results,role=role,username=username)


@admin.route('/login/<role>/<username>/unborrowed_authors', methods=['GET'])
def unborrowed_authors(role,username):
    cursor = db.connection.cursor(DictCursor)
    query = """
    SELECT AuthorName FROM UnborrowedAuthors;
    """
    cursor.execute(query)
    results = cursor.fetchall()

    authors = [result['AuthorName'] for result in results]

    cursor.close()

    return render_template('admin_unborrowed_authors.html', authors=authors, role=role, username=username)


@admin.route('/login/<role>/<username>/operators_loan_count', methods=['GET', 'POST'])
def operators_loan_count(role, username):
    cursor = db.connection.cursor(DictCursor)
    results = []

    if request.method == 'POST':
        selected_year = request.form['year']  # Get the selected year from the form data

        query = """
        SELECT o.OperatorID, CONCAT(u.FirstName, ' ', u.LastName) AS OperatorName, COUNT(b.BorrowID) AS NumberOfLoans
        FROM Operator o
        JOIN AppUser u ON o.OperatorID = u.UserID
        JOIN Borrow b ON o.OperatorID = b.OperatorID
        WHERE YEAR(b.Borrow_Date) = %s
        GROUP BY o.OperatorID
        HAVING NumberOfLoans > 20;
        """
        cursor.execute(query, (selected_year,))
        results = cursor.fetchall()

    cursor.close()

    return render_template('admin_operators_loan_count.html', results=results, role=role,username=username)


@admin.route('/login/<role>/<username>/top_category_pairs', methods=['GET'])
def top_category_pairs(role,username):
    cursor = db.connection.cursor(DictCursor)

    query = """
    SELECT bc1.CategoryID AS Category1, bc2.CategoryID AS Category2, COUNT(*) AS Frequency
    FROM BookCategory bc1
    JOIN BookCategory bc2 ON bc1.BookID = bc2.BookID AND bc1.CategoryID < bc2.CategoryID
    JOIN Borrow b ON bc1.BookID = b.BookID
    GROUP BY bc1.CategoryID, bc2.CategoryID
    ORDER BY Frequency DESC
    LIMIT 3;
    """
    cursor.execute(query)
    results = cursor.fetchall()

    cursor.close()

    return render_template('admin_top_category_pairs.html', results=results, role=role, username=username)


@admin.route('/login/<role>/<username>/authors_with_five_less_books', methods=['GET'])
def authors_with_five_less_books(role,username):
    cursor = db.connection.cursor(DictCursor)

    query = """
    WITH AuthorCounts AS (
      SELECT ba.AuthorID, a.FullName, COUNT(*) AS BookCount
      FROM BookAuthor ba
      JOIN Author a ON ba.AuthorID = a.AuthorID
      GROUP BY ba.AuthorID, A.FullName
    ),
    MaxAuthor AS (
      SELECT MAX(BookCount) AS MaxBooks
      FROM AuthorCounts
    )
    SELECT ac.AuthorID, ac.FullName, ac.BookCount
    FROM AuthorCounts ac, MaxAuthor ma
    WHERE ac.BookCount >= ma.MaxBooks - 5;
    """
    cursor.execute(query)
    results = cursor.fetchall()

    cursor.close()

    return render_template('admin_authors_with_five_less_books.html', results=results, role=role, username=username)



