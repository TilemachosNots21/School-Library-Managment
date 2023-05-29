from flask import Flask, render_template, request, flash, redirect, url_for, abort, session
from MySQLdb.cursors import DictCursor
from flask_mysqldb import MySQL
from libraryschooldb import db  # initially created by __init__.py, need to be used here
from libraryschooldb.authentication import auth
from libraryschooldb.authentication.forms import LoginForm
from libraryschooldb.authentication.forms import PasswordResetRequestForm
from libraryschooldb.authentication.forms import PasswordResetForm
from libraryschooldb.authentication.forms import RegistrationForm


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        password = form.password.data
        role = None

        # Query the database to find the user
        cursor = db.connection.cursor(DictCursor)
        try:
            cursor.execute("SELECT * FROM AppUser WHERE Username = %s", (username,))  # returns a tuple!!
            user = cursor.fetchone()
            if not user:
                # Check if the user exists in the RegistrationRequest table
                cursor.execute("SELECT * FROM RegistrationRequest WHERE Username = %s", (username,))
                reg_request = cursor.fetchone()
                if reg_request:
                    flash('Your account has not been activated yet.')
                else:
                    flash('No such account exists. Try again')
                return render_template('Login.html', form=form)

            user_id = user['UserID']  # get the useID from the tuple which is in the first position

            # Check if user is an administrator
            cursor.execute("SELECT * FROM Administrator WHERE AdminID = %s", (user_id,))
            if cursor.fetchone():
                role = 'administrator'
            else:
                # Check if user is an operator
                cursor.execute("SELECT * FROM Operator WHERE OperatorID = %s", (user_id,))
                if cursor.fetchone():
                    role = 'operator'
                else:
                    # Check if user is a school user and determine if they are a student or teacher
                    cursor.execute("SELECT * FROM SchoolUser WHERE SchoolUserID = %s", (user_id,))
                    school_user = cursor.fetchone()
                    if school_user:
                        role = school_user['Position']  #  'Teacher' or 'Student'

            # If user exists and password is correct
            if user['Password'] == password:
                # Log in user and redirect to profile page
                session['username'] = username
                session['role'] = role
                session['user_id'] = user_id
                if role == 'administrator':
                    return redirect(url_for('admin.admin_dashboard', role=role, username=username))
                elif role == 'operator':
                    return redirect(url_for('oper.operator_dashboard', role=session.get('role'), username=session.get('username'),user_id= session.get('user_id')))
                elif role == 'Teacher':
                    return redirect(url_for('teacher.teacher_dashboard', role=role, username=username, user_id= user_id ))
                elif role == 'Student':
                    return redirect(url_for('student.student_dashboard', role=role, username=username, user_id= user_id))
            else:
                flash('Incorrect username or password. Try again')

        except Exception as e:
            # if the connection to the database fails, return HTTP response 500
            flash(str(e), "danger")
            print(str(e))
            # abort(500)
        finally:
            cursor.close()

    # If no form submitted or form validation failed
    return render_template('Login.html', form=form)


@auth.route('/request_reset', methods=['GET', 'POST'])
def request_password_reset():
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        cur = db.connection.cursor()
        try:
            cur.execute("SELECT * FROM AppUser WHERE Username = %s AND Email = %s",
                        (form.username.data, form.email.data))
            user = cur.fetchone()
            if user:
                # If user exists, redirect to reset password page
                return redirect(url_for('auth.reset_password', username=form.username.data, email=form.email.data))
            else:
                flash('Username or email does not exist.')
        except Exception as e:
            flash(str(e), "danger")
            print(str(e))
            # abort(500)
        finally:
            cur.close()
            db.connection.commit()
    return render_template('request_reset_password.html', form=form)


@auth.route('/reset_password/<username>/<email>', methods=['GET', 'POST'])
def reset_password(username, email):
    form = PasswordResetForm()
    if form.validate_on_submit():
        cur = db.connection.cursor()
        try:
            # Update password in database
            cur.execute("UPDATE AppUser SET Password = %s WHERE Username = %s AND Email = %s",
                        (form.password.data, username, email))
            db.connection.commit()
            flash('Your password has been updated! You are now able to log in', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            flash(str(e), "danger")
            print(str(e))
            # abort(500)
        finally:
            cur.close()
    return render_template('reset_password.html', form=form)


@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    school_units = []
    cur = db.connection.cursor()
    try:
        cur.execute("SELECT School_Name FROM School_Unit")
        school_units = [row[0] for row in cur.fetchall()]
        if form.validate_on_submit():
            username = form.username.data
            name = form.name.data
            surname = form.surname.data
            birthdate = form.birthdate.data.strftime('%Y-%m-%d')
            email = form.email.data
            password = form.password.data
            schoolunits = form.school_unit.choices
            role = form.role.data
            phoneNumber = None
            if role == 'operator':
                phoneNumber = form.phoneNumber.data

            cur.execute("SELECT Username,Email FROM AppUser WHERE Username = %s OR Email = %s", (username, email,))
            account = cur.fetchone()
            if account:
                flash('Username or email already exists!', 'danger')
            else:
                cur.execute("SELECT SchoolID FROM School_Unit WHERE School_Name = %s", schoolunits)
                school = cur.fetchone()
                cur.execute(
                    "INSERT INTO RegistrationRequest (Username, FirstName, LastName, BirthDate, Email, Password, "
                    "PhoneNumber, School_Unit, Role_type) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (username, name, surname, birthdate, email, password, phoneNumber, school, role))
                flash("Registration request completed.You will be notified when your account is available")
                db.connection.commit()
    except Exception as e:
        db.connection.rollback()
        flash("An error occurred. Please try again.", "danger")
        print(f"Error: {str(e)}")
    finally:
        cur.close()

    return render_template('register_page.html', form=form, schoolUnits=school_units)


@auth.route('/logout')
def logout():
    # Remove user's information from the session
    session.pop('username', None)
    session.pop('role', None)
    flash('You have been logged out.')
    # Redirect to the home page (or any other page you want)
    return redirect(url_for('home.home_page'))
