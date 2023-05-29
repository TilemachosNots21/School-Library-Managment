from flask import Flask, render_template, request, flash, redirect, url_for, abort, session
from MySQLdb.cursors import DictCursor
from flask_mysqldb import MySQL
from libraryschooldb import db  # initially created by __init__.py, need to be used here
from libraryschooldb.oper import operator
from libraryschooldb.oper.forms import InsertBookForm, BookSearchForm, EditBookForm


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
            if form.genre_leverage.data:
                genre_name = form.new_genre.data
                cursor.execute('SELECT * FROM Category WHERE CategoryName = %s;', [genre_name])
                if not cursor.fetchone():
                    cursor.execute('INSERT INTO Category (CategoryName) VALUES (%s);', [genre_name])
                    db.connection.commit()
                    genre = cursor.lastrowid
                else:
                    genre = cursor.fetchone()['CategoryID']
            else:
                genre = form.genres.data

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

            cursor.execute('INSERT INTO BookCategory(BookID, CategoryID) VALUES(%s, %s);', [book_id, genre])

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


def fetch_books(cursor, school_id):
    cursor.execute("SELECT BookID, Title, ISBN, Publisher "
                   "FROM Book "
                   "WHERE SchoolID = %s", (school_id,))
    return cursor.fetchall()


def fetch_categories(cursor, book_ids):
    cursor.execute(
        "SELECT BookID, GROUP_CONCAT(CategoryName SEPARATOR ',') AS Categories"
        "FROM BookCategory Bc INNER JOIN Category C ON Bc.CategoryID = C.CategoryID "
        "WHERE BookID IN (%s) "
        "GROUP BY BookID",(book_ids,))
    return cursor.fetchall()


def fetch_keywords(cursor, book_ids):
    cursor.execute(
        "SELECT BookID, GROUP_CONCAT(KeywordText SEPARATOR ', ') AS Keywords "
        "FROM BookKeywords Bk INNER JOIN Keywords K ON Bk.KeywordID = K.KeywordID "
        "WHERE BookID IN (%s) "
        "GROUP BY BookID",(book_ids,))
    return cursor.fetchall()


def fetch_copies(cursor, book_ids):
    cursor.execute("SELECT BookID, COUNT(*) AS TotalCopies FROM BookCopy WHERE BookID IN (%s) GROUP BY BookID",
                   (book_ids,))
    return cursor.fetchall()


def fetch_search_books(cursor, search_term, school_id):
    cursor.callproc('SearchBook', [search_term, school_id])
    return cursor.fetchall()


def book_data_combined(books_in_school, categories, keywords, copies):
    book_list = []
    for book in books_in_school:
        book_dict = {'BookID': book['BookID'], 'Title': book['Title'], 'ISBN': book['ISBN'],
                     'Publisher': book['Publisher'], 'Categories': '', 'Keywords': '', 'TotalCopies': ''}

        # Add additional data to the dictionary
        for category in categories:
            if category['BookID'] == book['BookID']:
                book_dict['Categories'] = category['Categories']
                break

        for keyword in keywords:
            if keyword['BookID'] == book['BookID']:
                book_dict['Keywords'] = keyword['Keywords']
                break

        for copy in copies:
            if copy['BookID'] == book['BookID']:
                book_dict['TotalCopies'] = copy['TotalCopies']
                break

        book_list.append(book_dict)
    return book_list


@operator.route('/login/<role>/<user_id>/<username>/books_list', methods=['GET', 'POST'])
def book_list(role, user_id, username):
    form = BookSearchForm()
    operator_id = session.get('user_id')
    cursor = db.connection.cursor(DictCursor)
    books_list = []

    # Get the school_ID of the operator:
    cursor.execute("SELECT SchoolID FROM Operator WHERE OperatorID = %s", (operator_id,))
    school_id = cursor.fetchone()['SchoolID']

    try:
        if form.validate_on_submit():
            search_term = form.search.data
            books_in_school = fetch_search_books(cursor, search_term, school_id)
        else:
            books_in_school = fetch_books(cursor, school_id)

        book_ids = tuple(book['BookID'] for book in books_in_school)

        categories = fetch_categories(cursor, book_ids)
        keywords = fetch_keywords(cursor, book_ids)
        copies = fetch_copies(cursor, book_ids)

        books_list = book_data_combined(books_in_school, categories, keywords, copies)
    except Exception as e:
        flash(str(e), "danger")

    return render_template('oper_books_list.html', form=form, role=role, user_id=user_id, username=username, books_list=books_list)


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



