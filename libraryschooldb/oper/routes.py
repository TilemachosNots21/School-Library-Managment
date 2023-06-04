from flask import Flask, render_template, request, flash, redirect, url_for, abort, session
from MySQLdb.cursors import DictCursor
from flask_mysqldb import MySQL
from libraryschooldb import db  # initially created by __init__.py, need to be used here
from libraryschooldb.oper import operator
from libraryschooldb.oper.forms import InsertBookForm, BookSearchForm, EditBookForm , SearchBooksForm, SearchBorrowersForm, SearchRatingsForm


@operator.route('/login/<role>/<user_id>/<username>', methods=['GET', 'POST'])
def operator_dashboard(role,user_id,username):
    return render_template('operator_page.html',role=role,user_id=user_id,username=username)


@operator.route('/login/<role>/<user_id>/<username>/insert_book', methods=['GET', 'POST'])
def insert_book(role, user_id, username):
    form = InsertBookForm()
    cursor = db.connection.cursor(DictCursor)

    try:
        cursor.execute('SELECT * FROM Category;')
        categories = cursor.fetchall()
        form.genres.choices = [(row['CategoryID'], row['CategoryName']) for row in categories]

        if form.validate_on_submit():
            # Allow multiple genres to be selected.
            genre_ids = []
            genre_ids.extend(form.genres.data)

            if form.new_genre.data:
                new_genre_name = form.new_genre.data
                cursor.execute('SELECT * FROM Category WHERE CategoryName = %s;', [new_genre_name])
                genre_row = cursor.fetchone()
                if not genre_row:
                    cursor.execute('INSERT INTO Category (CategoryName) VALUES (%s);', [new_genre_name])
                    db.connection.commit()
                    new_genre_id = cursor.lastrowid
                else:
                    new_genre_id = genre_row['CategoryID']
                genre_ids.append(new_genre_id)

            isbn = form.isbn.data
            title = form.title.data
            publisher = form.publisher.data
            number_of_pages = form.number_of_pages.data
            summary = form.description.data
            image = form.image_url.data
            language = form.language.data
            number_of_copies = form.number_of_copies.data
            authors = form.authors.data
            keywords = form.keywords.data

            cursor.execute('SELECT SchoolID FROM Operator WHERE OperatorID = %s;', [user_id])
            school_id = cursor.fetchone()['SchoolID']

            cursor.execute('INSERT INTO Book(ISBN, Title, Publisher, Number_of_pages, Summary, Image, language, '
                           'OperatorID, SchoolID) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s);',
                           [isbn, title, publisher, number_of_pages, summary, image, language, user_id, school_id])

            book_id = cursor.lastrowid

            for genre_id in genre_ids:
                cursor.execute('INSERT INTO BookCategory(BookID, CategoryID) VALUES(%s, %s);', [book_id, genre_id])

            for author in authors:
                cursor.execute('SELECT * FROM Author WHERE FullName = %s;', [author])
                author_row = cursor.fetchone()
                if not author_row:
                    cursor.execute('INSERT INTO Author(FullName) VALUES (%s);', [author])
                    db.connection.commit()
                    author_id = cursor.lastrowid
                else:
                    author_id = author_row['AuthorID']

                cursor.execute('INSERT INTO BookAuthor(BookID, AuthorID) VALUES(%s, %s);', [book_id, author_id])

            for keyword in keywords:
                cursor.execute('SELECT * FROM Keywords WHERE KeywordText = %s;', [keyword])
                keyword_row = cursor.fetchone()
                if not keyword_row:
                    cursor.execute('INSERT INTO Keywords(KeywordText) VALUES (%s);', [keyword])
                    db.connection.commit()
                    keyword_id = cursor.lastrowid
                else:
                    keyword_id = keyword_row['KeywordID']

                cursor.execute('INSERT INTO BookKeywords(BookID, KeywordID) VALUES(%s, %s);', [book_id, keyword_id])

            # Call the InsertBookCopies procedure to insert book copies
            cursor.callproc('InsertBookCopies', [book_id, school_id, number_of_copies, user_id])

            db.connection.commit()

            flash('Book successfully inserted!', 'success')
            return redirect(url_for('operator.insert_book', role=role, user_id=user_id, username=username))
        else:
            return render_template('insert_book.html', form=form, role=role, user_id=user_id, username=username,
                                   categories=categories)

    except Exception as e:
        print(str(e))
        db.connection.rollback()
        flash('An error occurred. Please try again.', 'error')

    return render_template('insert_book.html', form=form, role=role, user_id=user_id, username=username, categories=categories)


@operator.route('/login/<role>/<user_id>/<username>/books_list', methods=['GET', 'POST'])
def book_list(role, user_id, username):
    form = BookSearchForm()
    operator_id = session.get('user_id')
    cursor = db.connection.cursor(DictCursor)
    books_list = []

    # Get the school_ID of the operator:
    cursor.execute("SELECT SchoolID FROM Operator WHERE OperatorID = %s", (operator_id,))
    school_id = cursor.fetchone()['SchoolID']

    if form.validate_on_submit():
        search_term = form.search.data
        cursor.callproc('SearchBook', [search_term, school_id])
        books_in_school = cursor.fetchall()
    else:
        cursor.execute("SELECT B.BookID, B.Title, B.ISBN, B.Publisher, B.Image, "
                       "GROUP_CONCAT(A.FullName SEPARATOR ', ') AS Authors "
                       "FROM Book AS B "
                       "INNER JOIN BookAuthor AS BA ON B.BookID = BA.BookID "
                       "INNER JOIN Author AS A ON BA.AuthorID = A.AuthorID "
                       "WHERE B.SchoolID = %s "
                       "GROUP BY B.BookID", (school_id,))
        books_in_school = cursor.fetchall()

    book_ids = tuple(book['BookID'] for book in books_in_school)

    cursor.execute(
        "SELECT BookID, GROUP_CONCAT(CategoryName SEPARATOR ',') AS Categories "
        "FROM BookCategory Bc INNER JOIN Category C ON Bc.CategoryID = C.CategoryID "
        "WHERE BookID IN %s "
        "GROUP BY BookID", (book_ids,))
    categories = cursor.fetchall()

    cursor.execute(
        "SELECT BookID, GROUP_CONCAT(KeywordText SEPARATOR ', ') AS Keywords "
        "FROM BookKeywords Bk INNER JOIN Keywords K ON Bk.KeywordID = K.KeywordID "
        "WHERE BookID IN %s "
        "GROUP BY BookID", (book_ids,))
    keywords = cursor.fetchall()

    cursor.execute("SELECT BookID, COUNT(*) AS TotalCopies FROM BookCopy WHERE BookID IN %s GROUP BY BookID",
                   (book_ids,))
    copies = cursor.fetchall()

    book_list = []
    for book_data in books_in_school:
        book_dict = {
            'BookID': book_data['BookID'],
            'Title': book_data['Title'],
            'ISBN': book_data['ISBN'],
            'Publisher': book_data['Publisher'],
            'Authors': book_data['Authors'],
            'Categories': '',
            'Keywords': '',
            'TotalCopies': '',
            'Image': book_data['Image']
        }

        for category in categories:
            if category['BookID'] == book_data['BookID']:
                book_dict['Categories'] = category['Categories']
                break

        for keyword in keywords:
            if keyword['BookID'] == book_data['BookID']:
                book_dict['Keywords'] = keyword['Keywords']
                break

        for copy in copies:
            if copy['BookID'] == book_data['BookID']:
                book_dict['TotalCopies'] = copy['TotalCopies']
                break

        book_list.append(book_dict)

    return render_template('oper_books_list.html', form=form, role=role, user_id=user_id, username=username,
                           books_list=book_list)



@operator.route('/login/<role>/<user_id>/<username>/edit_book/<book_id>', methods=['GET', 'POST'])
def edit_book(role,user_id,username,book_id):
    form = EditBookForm()
    cursor = db.connection.cursor(DictCursor)

    if request.method == 'POST':
        if form.validate_on_submit():
            new_authors = set([author.strip() for author in form.authors.data.split(",")])

            # Fetch current authors
            cursor.execute("""
                SELECT FullName FROM Author 
                INNER JOIN BookAuthor ON Author.AuthorID = BookAuthor.AuthorID 
                WHERE BookAuthor.BookID = %s
                """, (book_id,))
            current_authors = set([author['FullName'] for author in cursor.fetchall()])

            # Find authors to insert and to delete
            authors_to_insert = new_authors - current_authors
            authors_to_delete = current_authors - new_authors

            # For each author to insert, check if exists in `Author` table
            for author_name in authors_to_insert:
                cursor.execute("SELECT AuthorID FROM Author WHERE FullName = %s", (author_name,))
                author = cursor.fetchone()
                if author:
                    # If exists, only insert into `BookAuthor` table
                    cursor.execute("INSERT INTO BookAuthor(BookID, AuthorID) VALUES(%s, %s)", (book_id, author['AuthorID']))
                else:
                    # If not exists, insert into `Author` table and then `BookAuthor` table
                    cursor.execute("INSERT INTO Author(FullName) VALUES(%s)", (author_name,))
                    author_id = cursor.lastrowid
                    cursor.execute("INSERT INTO BookAuthor(BookID, AuthorID) VALUES(%s, %s)", (book_id, author_id))

            # For each author to delete, delete from `BookAuthor` table
            for author_name in authors_to_delete:
                cursor.execute("DELETE BookAuthor FROM BookAuthor "
                               "JOIN Author ON BookAuthor.AuthorID = Author.AuthorID "
                               "WHERE BookAuthor.BookID = %s AND Author.FullName = %s", (book_id, author_name))

            # Here, similar steps should be performed for `categories` and `keywords`

            # Fetch the current number of copies
            cursor.execute("SELECT COUNT(*) as Count FROM BookCopy WHERE BookID = %s", (book_id,))
            current_copies = cursor.fetchone()['Count']

            new_copies = form.available_copies.data
            if new_copies > current_copies:
                copies_to_insert = new_copies - current_copies

                # Insert new copies
                cursor.callproc('InsertBookCopies', [book_id, copies_to_insert])
                cursor.execute("SELECT * FROM InsertBookCopies_Result")
                result = cursor.fetchone()
                if result and result['Status'] == 'Error':
                    flash('An error occurred while inserting new copies.', 'danger')

            db.connection.commit()
            flash('Book successfully updated!', 'success')
        else:
            flash('Please correct the errors in the form.', 'danger')

    elif request.method == 'GET':
        cursor.execute("""
            SELECT Book.BookID, Book.Title, Book.ISBN, Book.Publisher,
            GROUP_CONCAT(DISTINCT Author.FullName) as Authors,
            GROUP_CONCAT(DISTINCT Category.CategoryName) as Categories,
            GROUP_CONCAT(DISTINCT Keyword.KeywordText) as Keywords,
            COUNT(DISTINCT BookCopy.CopyID) as Copies
            FROM Book
            LEFT JOIN BookAuthor ON Book.BookID = BookAuthor.BookID
            LEFT JOIN Author ON BookAuthor.AuthorID = Author.AuthorID
            LEFT JOIN BookCategory ON Book.BookID = BookCategory.BookID
            LEFT JOIN Category ON BookCategory.CategoryID = Category.CategoryID
            LEFT JOIN BookKeyword ON Book.BookID = BookKeyword.BookID
            LEFT JOIN Keyword ON BookKeyword.KeywordID = Keyword.KeywordID
            LEFT JOIN BookCopy ON Book.BookID = BookCopy.BookID
            WHERE Book.BookID = %s
            GROUP BY Book.BookID
            """, (book_id,))
        book = cursor.fetchone()

        if book:
            form.title.data = book['Title']
            form.isbn.data = book['ISBN']
            form.publisher.data = book['Publisher']
            form.authors.data = book['Authors']
            form.categories.data = book['Categories']
            form.keywords.data = book['Keywords']
            form.copies.data = book['Copies']

    return render_template('edit_book.html', form=form, book_id=book_id, user_id=user_id,role=role,username=username)


@operator.route('/login/<role>/<user_id>/<username>/delete_book/<book_id>', methods=['POST'])
def delete_book(role, user_id, username, book_id):
    cursor = db.connection.cursor()

    try:
        # Delete book copies
        cursor.execute('DELETE FROM BookCopy WHERE BookID = %s;', (book_id,))

        # Delete book-category relationships
        cursor.execute('DELETE FROM BookCategory WHERE BookID = %s;', (book_id,))

        # Delete book-author relationships
        cursor.execute('DELETE FROM BookAuthor WHERE BookID = %s;', (book_id,))

        # Delete book-keyword relationships
        cursor.execute('DELETE FROM BookKeywords WHERE BookID = %s;', (book_id,))

        # Delete book
        cursor.execute('DELETE FROM Book WHERE BookID = %s;', (book_id,))

        db.connection.commit()

        flash('Book successfully deleted!', 'success')
    except Exception as e:
        db.connection.rollback()
        flash('An error occurred. Please try again.', 'error')

    return redirect(url_for('oper.book_list', role=role, user_id=user_id, username=username))


@operator.route('/login/<role>/<user_id>/<username>/approve_registration', methods=['GET', 'POST'])
def approve_school_user_registrations(role, user_id, username):
    if 'username' not in session or session.get('role') != 'operator':
        flash('Permission denied.')
        return redirect(url_for('home.home_page'))

    try:
        cursor = db.connection.cursor(DictCursor)
        cursor.execute("SELECT SchoolID From Operator WHERE OperatorID = %s", (session['user_id'],))
        school_id = cursor.fetchone()['SchoolID']

        query = "SELECT FirstName, LastName, Email, Username, Role_Type " \
                "FROM RegistrationRequest " \
                "WHERE (Role_Type = 'student' OR Role_Type = 'teacher') AND School_Unit = %s"
        cursor.execute(query, (school_id,))
        school_user_requests = cursor.fetchall()

        if request.method == 'POST':
            username = request.form.get('username')
            action = request.form.get('action')

            if action == 'approve':
                cursor.execute("SELECT * FROM RegistrationRequest WHERE Username = %s", (username,))
                selected_user = cursor.fetchone()
                cursor.execute("DELETE FROM RegistrationRequest WHERE RequestID = %s",
                               (selected_user['RequestID'],))
                cursor.execute("SELECT School_Name FROM School_Unit WHERE SchoolID = %s", (school_id,))
                school_name = cursor.fetchone()['School_Name']
                query2 = "CALL InsertSchoolUser(%s, %s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(query2, (selected_user['FirstName'], selected_user['LastName'], selected_user['Email'],
                                        selected_user['Username'], selected_user['Password'], selected_user['Role_Type'],
                                        selected_user['BirthDate'], school_id))
                flash('The request from user {} has been successfully approved.'.format(username), 'success')
                return redirect(url_for('oper.approve_school_user_registrations', role=role, user_id=user_id, username=username))
            elif action == 'reject':
                cursor.execute("SELECT RequestID FROM RegistrationRequest WHERE Username = %s", (username,))
                selected_user = cursor.fetchone()
                cursor.execute("DELETE FROM RegistrationRequest WHERE RequestID = %s",
                               (selected_user['RequestID'],))
                flash('The request from user {} has been successfully rejected.'.format(username), 'success')
                return redirect(url_for('oper.approve_school_user_registrations', role=role, user_id=user_id, username=username))
            else:
                flash('Invalid action.', 'error')
                return redirect(url_for('oper.approve_school_user_registrations', role=role, user_id=user_id, username=username))
    except Exception as e:
        flash(str(e), "error")
    finally:
        cursor.close()
        db.connection.commit()

    return render_template('approve_school_user.html', role=role, user_id=user_id, username=username, school_user_requests=school_user_requests)


@operator.route('/login/<role>/<user_id>/<username>/show_users', methods=['GET', 'POST'])
def show_users(role,user_id,username):
    if 'username' not in session or session.get('role') != 'operator':
        flash('Permission denied.')
        return redirect(url_for('home.home_page'))

    try:
        cursor = db.connection.cursor(DictCursor)
        cursor.execute("SELECT SchoolID From Operator WHERE OperatorID = %s", (session['user_id'],))
        school_id = cursor.fetchone()['SchoolID']

        query = "SELECT Au.FirstName, Au.LastName, Au.Email, Au.Username, Su.Position " \
                "FROM AppUser Au INNER JOIN SchoolUser Su ON Au.UserID = Su.SchoolUserID  " \
                "WHERE Su.SchoolID = %s"
        cursor.execute(query, (school_id,))
        school_users = cursor.fetchall()

        if request.method == 'POST':
            username = request.form.get('username')
            action = request.form.get('action')

            cursor.execute("SELECT UserID FROM AppUser WHERE Username = %s", (username,))
            selected_user = cursor.fetchone()
            cursor.execute("DELETE FROM AppUser WHERE UserID = %s",
                               (selected_user['UserID'],))
            flash('User {} has been successfully suspended (deleted).'.format(username), 'success')
            return redirect(url_for('oper.show_users', role=role, user_id=user_id, username=username))

    except Exception as e:
        flash(str(e), "error")
    finally:
        cursor.close()
        db.connection.commit()

    return render_template('show_school_users.html',role=role,user_id=user_id,username=username,school_users=school_users)


@operator.route('/login/<role>/<user_id>/<username>/show_reservations', methods=['GET', 'POST'])
def reservations_handling(role, user_id, username):
    if 'username' not in session or session.get('role') != 'operator':
        flash('Permission denied.')
        return redirect(url_for('home.home_page'))

    try:
        cursor = db.connection.cursor(DictCursor)
        cursor.execute("SELECT SchoolID FROM Operator WHERE OperatorID = %s", (session['user_id'],))
        school_id = cursor.fetchone()['SchoolID']

        reservations = []

        if request.method == 'POST':
            reservation_type = request.form.get('reservation_type')
            time_period = request.form.get('time_period')
            action = request.form.get('action')
            reservation_id = request.form.get('reservation_id')

            query = "SELECT r.ReservationID, r.Submitted_DateTime AS BorrowDate, r.Acceptance_Date AS ReturnDate, r.ReservationStatus AS Status, au.Username, bk.Title AS BookTitle FROM Reservation r " \
                    "JOIN AppUser au ON r.SchoolUserID = au.UserID " \
                    "JOIN Book bk ON r.BookID = bk.BookID " \
                    "WHERE r.SchoolUserID IN (SELECT SchoolUserID FROM SchoolUser WHERE SchoolID = %s)"

            if reservation_type != "all":
                query += f" AND r.ReservationStatus = {reservation_type}"

            if time_period:
                query += f" AND r.Submitted_DateTime >= DATE_SUB(CURRENT_DATE, INTERVAL {time_period} DAY)"

            cursor.execute(query, (school_id,))
            rows = cursor.fetchall()

            reservations = [
                {"ReservationID": row['ReservationID'], "Username": row['Username'], "BookTitle": row['Title'],
                 "BorrowDate": row['Submitted_DateTime'], "ReturnDate": row['Acceptance_Date'],
                 "Status": row['ReservationStatus']} for row in rows]

            if action and reservation_id:
                if action == 'accept':
                    cursor.execute("UPDATE Reservation SET ReservationStatus = 'Accepted' WHERE ReservationID = %s",
                                   (reservation_id,))
                elif action == 'reject':
                    cursor.execute("UPDATE Reservation SET ReservationStatus = 'Cancelled' WHERE ReservationID = %s",
                                   (reservation_id,))

            for reservation in reservations:
                if reservation['Status'] == 'Pending':
                    reservation['Status'] = 'Εκκρεμείς'
                elif reservation['Status'] == 'Accepted':
                    reservation['Status'] = 'Αποδεκτές'
                elif reservation['Status'] == 'Completed':
                    reservation['Status'] = 'Ολοκληρωμένες'
                elif reservation['Status'] == 'Cancelled':
                    reservation['Status'] = 'Ακυρωμένες'
                else:
                    reservation['Status'] = 'Άγνωστο'

        elif request.method == 'GET':
            query = "SELECT r.ReservationID, r.Submitted_DateTime AS BorrowDate, r.Acceptance_Date AS ReturnDate, r.ReservationStatus AS Status, au.Username, bk.Title AS BookTitle FROM Reservation r " \
                    "JOIN AppUser au ON r.SchoolUserID = au.UserID " \
                    "JOIN Book bk ON r.BookID = bk.BookID " \
                    "WHERE r.SchoolUserID IN (SELECT SchoolUserID FROM SchoolUser WHERE SchoolID = %s)"
            cursor.execute(query, (school_id,))
            rows = cursor.fetchall()
            reservations = [{"ReservationID": row[0], "Username": row[1], "BookTitle": row[2],
                             "BorrowDate": row[3], "ReturnDate": row[4], "Status": row[5]} for row in rows]

            for reservation in reservations:
                if reservation['Status'] == 'Pending':
                    reservation['Status'] = 'Εκκρεμείς'
                elif reservation['Status'] == 'Accepted':
                    reservation['Status'] = 'Αποδεκτές'
                elif reservation['Status'] == 'Completed':
                    reservation['Status'] = 'Ολοκληρωμένες'
                elif reservation['Status'] == 'Cancelled':
                    reservation['Status'] = 'Ακυρωμένες'
                else:
                    reservation['Status'] = 'Άγνωστο'

    except Exception as e:
        flash(str(e), "error")
        print("Error executing SQL query:", e)
    finally:
        cursor.close()
        db.connection.commit()

    return render_template('Reservations_operator.html', role=role, user_id=user_id, username=username,
                           reservations=reservations)


@operator.route('/login/<role>/<user_id>/<username>/show_borrowings', methods=['GET', 'POST'])
def borrowings_handling(role, user_id, username):
    if 'username' not in session or session.get('role') != 'operator':
        flash('Permission denied.')
        return redirect(url_for('home.home_page'))

    borrowings = []

    try:
        cursor = db.connection.cursor(DictCursor)
        cursor.execute("SELECT SchoolID FROM Operator WHERE OperatorID = %s", (session['user_id'],))
        school_id = cursor.fetchone()['SchoolID']

        if request.method == 'POST':
            time_period = request.form.get('time_period')

            if time_period == 'all':
                query = "SELECT b.BorrowID, au.Username, bk.Title, bk.ISBN, b.BookCopyID, b.Borrow_Date, b.Due_Date, b.Return_Date, b.Borrow_Status " \
                        "FROM Borrow b " \
                        "JOIN AppUser au ON b.SchoolUserID = au.UserID " \
                        "JOIN Book bk ON b.BookID = bk.BookID " \
                        "WHERE b.BookCopyID IN (SELECT BookCopyID FROM BookCopy WHERE SchoolID = %s)"
                cursor.execute(query, (school_id,))
            else:
                query = "SELECT b.BorrowID, au.Username, bk.Title, bk.ISBN, b.BookCopyID, b.Borrow_Date, b.Due_Date, b.Return_Date, b.Borrow_Status " \
                        "FROM Borrow b " \
                        "JOIN AppUser au ON b.SchoolUserID = au.UserID " \
                        "JOIN Book bk ON b.BookID = bk.BookID " \
                        "WHERE b.BookCopyID IN (SELECT BookCopyID FROM BookCopy WHERE SchoolID = %s) " \
                        "AND b.Borrow_Date >= DATE_SUB(CURRENT_DATE, INTERVAL %s DAY)"
                cursor.execute(query, (school_id, time_period))
        else:
            query = "SELECT b.BorrowID, au.Username, bk.Title, bk.ISBN, b.BookCopyID, b.Borrow_Date, b.Due_Date, b.Return_Date, b.Borrow_Status " \
                    "FROM Borrow b " \
                    "JOIN AppUser au ON b.SchoolUserID = au.UserID " \
                    "JOIN Book bk ON b.BookID = bk.BookID " \
                    "WHERE b.BookCopyID IN (SELECT BookCopyID FROM BookCopy WHERE SchoolID = %s)"
            cursor.execute(query, (school_id,))

        borrowings = cursor.fetchall()

    except Exception as e:
        flash(str(e), "error")
    finally:
        cursor.close()
        db.connection.commit()

    return render_template('borrowings_handling.html', role=role, user_id=user_id, username=username, borrowings=borrowings)


@operator.route('/login/<role>/<user_id>/<username>/search_books', methods=['GET', 'POST'])
def search_books(role,user_id,username):
    form = SearchBooksForm()
    if form.validate_on_submit():
        title = '%' + form.title.data + '%'  # Adding '%' to use the LIKE operator
        author = '%' + form.author.data + '%'
        category = '%' + form.category.data + '%'

        # Get the School ID of the operator (assuming you have a way to get the current operator's ID)
        operator_id = session['user_id']
        cursor = db.connection.cursor(DictCursor)
        cursor.execute("SELECT SchoolID FROM Operator WHERE OperatorID = %s", [operator_id])
        school_id = cursor.fetchone()['SchoolID']

        query = """
        SELECT B.Title, GROUP_CONCAT(A.FullName SEPARATOR ', ') AS Authors
        FROM Book B 
        JOIN BookAuthor BA ON B.BookID = BA.BookID
        JOIN Author A ON BA.AuthorID = A.AuthorID
        JOIN BookCategory BC ON B.BookID = BC.BookID
        JOIN Category C ON BC.CategoryID = C.CategoryID
        WHERE B.Title LIKE %s AND A.FullName LIKE %s AND B.SchoolID = %s AND C.CategoryName LIKE %s AND EXISTS (
            SELECT 1 FROM BookCopy BC WHERE BC.BookID = B.BookID )
        GROUP BY B.BookID;
        """
        cursor.execute(query, [title, author, school_id, category])
        results = cursor.fetchall()
        for result in results:
            result['Authors'] = result['Authors'].split(', ')
        cursor.close()

        return render_template('operator_search_books.html', form=form, results=results,role=role,username=username,user_id=user_id)

    return render_template('operator_search_books.html', form=form, role=role,username=username,user_id=user_id)


@operator.route('/login/<role>/<user_id>/<username>/search_borrowers', methods=['GET', 'POST'])
def search_borrowers(role, user_id, username):
    form = SearchBorrowersForm()
    if form.validate_on_submit():
        first_name = '%' + form.first_name.data + '%'
        last_name = '%' + form.last_name.data + '%'
        delay_days = form.delay_days.data

        query = """
        SELECT su.FirstName, su.LastName, b.BookID, DATEDIFF(CURDATE(), bo.Due_Date) AS DelayDays
        FROM Borrow bo
        JOIN SchoolUser su ON bo.SchoolUserID = su.SchoolUserID
        JOIN Book b ON bo.BookID = b.BookID
        WHERE su.FirstName LIKE %s
        AND su.LastName LIKE %s
        AND bo.Borrow_Status = 'Overdue'
        AND DATEDIFF(CURDATE(), bo.Due_Date) > %s
        """
        cursor = db.connection.cursor(DictCursor)
        cursor.execute(query, [first_name, last_name, delay_days])
        results = cursor.fetchall()
        cursor.close()

        return render_template('operator_search_borrowers.html', form=form, results=results, role=role, username=username, user_id=user_id)

    return render_template('operator_search_borrowers.html', form=form, role=role, username=username, user_id=user_id)


@operator.route('/login/<role>/<user_id>/<username>/search_ratings', methods=['GET', 'POST'])
def search_ratings(role, user_id, username):
    form = SearchRatingsForm()
    if form.validate_on_submit():
        first_name = '%' + form.first_name.data + '%'
        last_name = '%' + form.last_name.data + '%'
        category = '%' + form.category.data + '%'

        operator_id = session['user_id']

        query = """
        SELECT SU.FirstName, SU.LastName, C.CategoryName, AVG(R.Likert) AS AverageRating
        FROM Review R
        JOIN SchoolUser SU ON R.SchoolUserID = SU.SchoolUserID
        JOIN Book B ON R.BookID = B.BookID
        JOIN BookCategory BC ON B.BookID = BC.BookID
        JOIN Category C ON BC.CategoryID = C.CategoryID
        JOIN Operator O ON R.OperatorID = O.OperatorID
        WHERE SU.FirstName LIKE %s
        AND SU.LastName LIKE %s
        AND C.CategoryName LIKE %s
        AND O.OperatorID = %s
        GROUP BY SU.FirstName, SU.LastName, C.CategoryName
        """
        cursor = db.connection.cursor(DictCursor)
        cursor.execute(query, [first_name, last_name, category, operator_id])
        results = cursor.fetchall()
        cursor.close()

        return render_template('operator_search_ratings.html', form=form, results=results, role=role, username=username, user_id=user_id)

    return render_template('operator_search_ratings.html', form=form, role=role, username=username, user_id=user_id)




