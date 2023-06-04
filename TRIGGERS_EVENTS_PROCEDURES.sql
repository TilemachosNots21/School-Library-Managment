-- TRIGGERS


-- Limitation on the number of books that can be borrowed per week by a user:
DELIMITER $$
CREATE TRIGGER check_borrow_limit BEFORE INSERT ON Borrow
FOR EACH ROW
BEGIN
   DECLARE borrow_limit INT;
   DECLARE position VARCHAR(9);
   
   SELECT Position INTO position FROM SchoolUser WHERE SchoolUserID = NEW.SchoolUserID;
   
   IF position = 'Student' THEN
     SET borrow_limit = 2;
   ELSE
     SET borrow_limit = 1;
   END IF;
   
   IF (SELECT COUNT(*) FROM Borrow WHERE SchoolUserID = NEW.SchoolUserID AND WEEK(Borrow_Date) = WEEK(CURRENT_DATE) AND Borrow_Status = 'Accepted' ) >= borrow_limit THEN
      SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'User has reached their borrow limit for the week';
   END IF;
END $$
DELIMITER ;


-- Limitation on the number of books that can be reserved per week by a user:
DELIMITER $$
CREATE TRIGGER check_reservation_limit BEFORE INSERT ON Reservation
FOR EACH ROW
BEGIN
   DECLARE reservation_limit INT;
   DECLARE position VARCHAR(9);
   
   SELECT Position INTO position FROM SchoolUser WHERE SchoolUserID = NEW.SchoolUserID;
   
   IF position = 'Student' THEN
     SET reservation_limit = 2;
   ELSE
     SET reservation_limit = 1;
   END IF;
   
   IF (SELECT COUNT(*) FROM Reservation WHERE SchoolUserID = NEW.SchoolUserID AND WEEK(Submitted_DateTime) = WEEK(CURRENT_TIMESTAMP) AND ReservationStatus = 'Accepted') >= reservation_limit THEN
      SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'User has reached their reservation limit for the week';
   END IF;
END $$
DELIMITER ;



/* 
   Prevent a borrowing attempt if the user has overdue books
   or has already borrowed the same title.
*/

DELIMITER $$
CREATE TRIGGER check_overdue_books BEFORE INSERT ON Borrow
FOR EACH ROW
BEGIN
   IF EXISTS (SELECT 1 
              FROM Borrow b
              WHERE b.SchoolUserID = NEW.SchoolUserID 
              AND (b.Borrow_Status = 'Overdue' OR (b.BookID = NEW.BookID AND b.Borrow_Status = 'Accepted'))) THEN
      SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'User has overdue books or has already borrowed the same title';
   END IF;
END $$
DELIMITER ;

/*
	Prevent a reservation from being made if the user has overdue books
    or has already borrowed the same title.
*/

DELIMITER $$
CREATE TRIGGER check_reservation BEFORE INSERT ON Reservation
FOR EACH ROW
BEGIN
   IF EXISTS (SELECT 1 
              FROM Borrow b
              WHERE b.SchoolUserID = NEW.SchoolUserID 
              AND (b.Borrow_Status = 'Overdue' OR (b.BookID = NEW.BookID AND b.Borrow_Status = 'Accepted'))) THEN
      SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'A reservation cannot be made if a book has not been returned on time or if the same user has already borrowed the title.';
   END IF;
END $$
DELIMITER ;


-- Update acceptance date and set due_reservation_date when a reservation is accepted:
DELIMITER $$
CREATE TRIGGER update_acceptance_date BEFORE UPDATE ON Reservation
FOR EACH ROW
BEGIN
   IF NEW.ReservationStatus = 'Accepted' AND OLD.ReservationStatus = 'Pending' THEN
      UPDATE Reservation SET Acceptance_Date = CURRENT_DATE , Due_Reservation_Date = DATE_ADD(CURRENT_DATE,INTERVAL 1 WEEK)
      WHERE ReservationID = NEW.ReservationID;
   END IF;
END $$
DELIMITER ;

-- Update cancellation date of reservation when cancelled by the user:
DELIMITER $$
CREATE TRIGGER set_cancellation_date BEFORE UPDATE ON Reservation
FOR EACH ROW
BEGIN
   IF NEW.ReservationStatus = 'Cancelled' AND OLD.ReservationStatus IN ('Pending','Accepted') THEN
      SET NEW.Cancelation_Date = CURRENT_DATE;
   END IF;
END$$
DELIMITER ;

-- Update the return date when a book is returned:
DELIMITER $$
CREATE TRIGGER UpdateReturnedDate BEFORE UPDATE ON Borrow
FOR EACH ROW
BEGIN
    IF NEW.Borrow_Status = 'Returned' AND OLD.Borrow_Status != 'Returned' THEN
        SET NEW.Return_Date = CURRENT_DATE();
    END IF;
END $$
DELIMITER ;


/*
	A trigger that updates the date submission of a review 
	if a user wants to change his/her review.
*/

DELIMITER $$
CREATE TRIGGER update_date_submitted BEFORE UPDATE ON Review
FOR EACH ROW
BEGIN
  UPDATE Review SET Date_Submitted = CURDATE() WHERE ReviewID = NEW.ReviewID;
END $$
DELIMITER ;

/*
	Triggers that update the availability of copies of a book in a school unit after a borrowing
*/

DELIMITER $$
CREATE TRIGGER update_availability_of_book_after_borrow AFTER INSERT ON Borrow
FOR EACH ROW
BEGIN
	IF NEW.Borrow_Status = 'Accepted' THEN
		UPDATE BookCopy SET IsAvailable = FALSE , InLibrary = FALSE
		WHERE BookCopyID = NEW.BookCopyID;
	END IF;
END $$
DELIMITER ;

DELIMITER $$
CREATE TRIGGER update_availability_of_returned_book AFTER UPDATE ON Borrow
FOR EACH ROW
BEGIN
	IF NEW.Borrow_Status = 'Returned' THEN
		UPDATE BookCopy SET IsAvailable = TRUE , InLibrary = TRUE
        WHERE BookCopyID = NEW.BookCopyID;
	END IF;
END $$
DELIMITER ;

/*
	A trigger that updates the availability of copies of a book in a school unit after a reservation
*/

DELIMITER $$
CREATE TRIGGER reservation_status_change AFTER UPDATE ON Reservation
FOR EACH ROW
BEGIN
   IF NEW.ReservationStatus = 'Cancelled' AND OLD.ReservationStatus = 'Accepted' THEN
      UPDATE BookCopy
      SET IsAvailable = TRUE
      WHERE BookCopyID = NEW.BookCopyID;
   ELSEIF NEW.ReservationStatus = 'Accepted' AND OLD.ReservationStatus = 'Pending' THEN
      UPDATE BookCopy
      SET IsAvailable = FALSE
      WHERE BookCopyID = NEW.BookCopyID;
   END IF;
END $$
DELIMITER ;

-- When a reservation is completed automatically insert it in the borrow table:
DELIMITER $$
CREATE TRIGGER reservation_completed AFTER UPDATE ON Reservation
FOR EACH ROW
BEGIN
    IF NEW.ReservationStatus = 'Completed' THEN
        INSERT INTO Borrow (SchoolUserID, BookID, BookCopyID, Borrow_Date, Due_Date, Borrow_Status, OperatorID)
        VALUES (NEW.SchoolUserID, NEW.BookID, NEW.BookCopyID, CURRENT_DATE, DATE_ADD(CURRENT_DATE, INTERVAL 1 WEEK), 'Accepted', NEW.OperatorID);
    END IF;
END $$
DELIMITER ;


/*
	Prevent a reservation request if a user has reached the weekly limit:
*/
DELIMITER $$
CREATE TRIGGER prevent_reservation_if_borrow_limits_apply BEFORE INSERT ON Reservation
FOR EACH ROW
BEGIN
   DECLARE reservation_limit INT;
   DECLARE current_borrows INT;
   
   SELECT Position INTO @position FROM SchoolUser WHERE SchoolUserID = NEW.SchoolUserID;
   
   IF @position = 'Student' THEN
     SET reservation_limit = 2;
   ELSE
     SET reservation_limit = 1;
   END IF;

   SELECT COUNT(*) INTO current_borrows FROM Borrow WHERE SchoolUserID = NEW.SchoolUserID AND Borrow_Status = 'Accepted';

   IF current_borrows >= reservation_limit THEN
      SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'User has already borrowed the maximum allowed number of books';
   END IF;
END $$
DELIMITER ;



-- SCEDULED EVENTS    
SET GLOBAL event_scheduler = ON;
/* 
	Schedule to update the status of the borrowed book 
    to overdue when the due date has passed.
*/
DELIMITER $$
CREATE EVENT set_overdue_status ON SCHEDULE EVERY 1 DAY DO
BEGIN
   UPDATE Borrow
   SET Borrow_Status = 'Overdue'
   WHERE Due_Date < CURRENT_DATE AND Borrow_Status = 'Accepted';
END $$
DELIMITER ;

/*
	A schedule to automatically cancel any reservation that exceeds 
    the 1 week interval after the acceptance date.
*/

DELIMITER $$
CREATE EVENT cancel_expired_reservations ON SCHEDULE EVERY 1 DAY 
DO
BEGIN
	UPDATE Reservation
    SET ReservationStatus = 'Cancelled', Cancelation_Date = CURRENT_DATE
    WHERE Acceptance_Date IS NOT NULL AND Due_Reservation_Date < CURRENT_DATE AND
    ReservationStatus = 'Accepted';
END $$
DELIMITER ;



-- PROCEDURES 


-- Insert an Administrator
DELIMITER $$
CREATE PROCEDURE InsertAdministrator(IN pFirstName VARCHAR(45), IN pLastName VARCHAR(45), IN pEmail VARCHAR(50), IN pUsername VARCHAR(80), IN pPassword VARCHAR(100), IN pPhone VARCHAR(15), IN pBirthdate DATE)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        GET DIAGNOSTICS CONDITION 1
        @my_sqlstate = RETURNED_SQLSTATE, @my_errno = MYSQL_ERRNO, @my_text = MESSAGE_TEXT;
        SELECT @my_sqlstate as error_sqlstate, @my_errno as errno, @my_text as error_text;
    END;
    
    START TRANSACTION;

    IF EXISTS (SELECT 1 FROM AppUser WHERE Username = pUsername OR Email = pEmail) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'An user with this username or email already exists.';
    END IF;
    
    IF pPhone IS NULL THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'A phone number must be provided for administrators.';
    ELSEIF EXISTS (SELECT 1 FROM Administrator WHERE PhoneNumber = pPhone) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'An administrator with this phone number already exists.';
    END IF;
    
    SET @age = TIMESTAMPDIFF(YEAR, pBirthdate, CURDATE());
    
    IF @age <= 25 THEN
		SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Age is not valid for an administrator. They must be above 25 years old.';
    END IF;
    
    INSERT INTO AppUser(FirstName, LastName, Email, Username, Password, Birthdate)
    VALUES(pFirstName, pLastName, pEmail, pUsername, pPassword, pBirthdate);
    
    SET @last_id = LAST_INSERT_ID();
    INSERT INTO Administrator(AdminID, PhoneNumber) VALUES(@last_id, pPhone);
    
    COMMIT;
END $$
DELIMITER ;


-- Insert an Operator
DELIMITER $$
CREATE PROCEDURE InsertOperator(IN pFirstName VARCHAR(45), IN pLastName VARCHAR(45), IN pEmail VARCHAR(50), IN pUsername VARCHAR(80), IN pPassword VARCHAR(100), IN pPhone VARCHAR(15), IN pBirthdate DATE, IN p_AdminID INT, IN p_SchoolID INT)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        GET DIAGNOSTICS CONDITION 1
        @my_sqlstate = RETURNED_SQLSTATE, @my_errno = MYSQL_ERRNO, @my_text = MESSAGE_TEXT;
        SELECT @my_sqlstate as error_sqlstate, @my_errno as errno, @my_text as error_text;
    END;
    
    START TRANSACTION;
    
    IF EXISTS (SELECT 1 FROM AppUser WHERE Username = pUsername OR Email = pEmail) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'An user with this username or email already exists.';
    END IF;
    
    IF pPhone IS NULL THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'A phone number must be provided for operators.';
    ELSEIF EXISTS (SELECT 1 FROM Operator WHERE PhoneNumber = pPhone) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'An operator with this phone number already exists.';
    END IF;
    
    SET @age = TIMESTAMPDIFF(YEAR, pBirthdate, CURDATE());
    
    IF @age <= 25 THEN
		SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Age is not valid for an operator. They must be above 25 years old.';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM Administrator WHERE AdminID = p_AdminID ) THEN
		SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'This administrator does not exist.';
	END IF;
        
	IF NOT EXISTS (SELECT 1 FROM School_Unit WHERE SchoolID = p_SchoolID) THEN
		SIGNAL SQLSTATE '45000'
		SET MESSAGE_TEXT = 'The school unit does not exist.';
	END IF;
    
    INSERT INTO AppUser(FirstName, LastName, Email, Username, Password, Birthdate)
    VALUES(pFirstName, pLastName, pEmail, pUsername, pPassword, pBirthdate);
    
    SET @last_id = LAST_INSERT_ID();
    INSERT INTO Operator(OperatorID, PhoneNumber,AdminID,SchoolID) VALUES(@last_id, pPhone,p_AdminID,p_SchoolID);
    
END $$
DELIMITER ;


-- Insert a School user (Teacher or Student)
DELIMITER $$
CREATE PROCEDURE InsertSchoolUser(IN pFirstName VARCHAR(45), IN pLastName VARCHAR(45), IN pEmail VARCHAR(50), IN pUsername VARCHAR(80), IN pPassword VARCHAR(100), IN role_type VARCHAR(20), IN pBirthdate DATE, IN p_SchoolID INT)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        GET DIAGNOSTICS CONDITION 1
        @my_sqlstate = RETURNED_SQLSTATE, @my_errno = MYSQL_ERRNO, @my_text = MESSAGE_TEXT;
        SELECT @my_sqlstate as error_sqlstate, @my_errno as errno, @my_text as error_text;
    END;
    
    START TRANSACTION;
   
   IF EXISTS (SELECT 1 FROM AppUser WHERE Username = pUsername OR Email = pEmail) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'An user with this username or email already exists.';
    END IF;
    
    
	SET @age = TIMESTAMPDIFF(YEAR, pBirthdate, CURDATE());
    IF role_type = 'student' AND (@age < 12 OR @age > 18) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Age is not valid for a student. Students must be between 12 and 18 years old.';
    ELSEIF role_type = 'teacher' AND @age <= 25 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Age is not valid for a teacher. They must be above 25 years old.';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM School_Unit WHERE SchoolID = p_SchoolID) THEN
		SIGNAL SQLSTATE '45000'
		SET MESSAGE_TEXT = 'The school unit does not exist.';
	END IF;
    
    INSERT INTO AppUser(FirstName, LastName, Email, Username, Password, Birthdate)
    VALUES(pFirstName, pLastName, pEmail, pUsername, pPassword, pBirthdate);
    
    SET @last_id = LAST_INSERT_ID();
    
    CASE role_type
        WHEN 'teacher' THEN
            INSERT INTO SchoolUser(SchoolUserID, Position, SchoolID)
            VALUES(@last_id, 'Teacher', p_SchoolID);
        WHEN 'student' THEN
            INSERT INTO SchoolUser(SchoolUserID, Position, SchoolID)
            VALUES(@last_id, 'Student', p_SchoolID);
        ELSE
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Invalid role type.';
    END CASE;
    
    COMMIT;
END $$
DELIMITER ;



-- Update the information of an AppUser
DELIMITER $$
CREATE PROCEDURE UpdateUser(IN p_user_id INT, IN p_username VARCHAR(255), IN p_password VARCHAR(255), IN p_email VARCHAR(255), IN p_phone VARCHAR(15), IN pBirthdate DATE)
BEGIN
    IF EXISTS (SELECT 1 FROM AppUser WHERE UserID != p_user_id AND (Username = p_username OR Email = p_email)) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Username or email already exists.';
    ELSE
        START TRANSACTION;

        -- Calculate age
        SET @age = TIMESTAMPDIFF(YEAR, pBirthdate, CURDATE());

        -- Get role_type based on user_id
        SET @role_type = (
            SELECT
                CASE
                    WHEN EXISTS(SELECT 1 FROM Administrator WHERE AdminID = p_user_id) THEN 'administrator'
                    WHEN EXISTS(SELECT 1 FROM Operator WHERE OperatorID = p_user_id) THEN 'operator'
                    WHEN EXISTS(SELECT 1 FROM SchoolUser WHERE SchoolUserID = p_user_id AND Position = 'Teacher') THEN 'teacher'
                    WHEN EXISTS(SELECT 1 FROM SchoolUser WHERE SchoolUserID = p_user_id AND Position = 'Student') THEN 'student'
                END
        );

        -- Validate age based on role_type
        IF @role_type = 'student' AND (@age < 12 OR @age > 18) THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Age is not valid for a student. Students must be between 12 and 18 years old.';
        ELSEIF @role_type IN ('administrator', 'operator', 'teacher') AND @age <= 25 THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Age is not valid for an administrator, operator, or teacher. They must be above 25 years old.';
        ELSE
            UPDATE AppUser SET Username = p_username, Password = p_password, Email = p_email, Birthdate = pBirthdate WHERE UserID = p_user_id;

            -- Update phone number for Administrator
            IF EXISTS (SELECT 1 FROM Administrator WHERE UserID = p_user_id) THEN
                UPDATE Administrator SET PhoneNumber = p_phone WHERE UserID = p_user_id;
            END IF;

            -- Update phone number for Operator
            IF EXISTS (SELECT 1 FROM Operator WHERE UserID = p_user_id) THEN
                UPDATE Operator SET PhoneNumber = p_phone WHERE UserID = p_user_id;
            END IF;

            COMMIT;
        END IF;
    END IF;
END $$
DELIMITER ;



-- Insert SchoolUnit
DELIMITER $$
CREATE PROCEDURE InsertSchoolUnit(IN pSchoolName VARCHAR(72), IN pPostalAddress VARCHAR(72), IN pCity VARCHAR(45), IN pTelephone VARCHAR(45),IN pEmail VARCHAR(72) ,IN pSchoolDirector VARCHAR(45), IN pAdminID INT)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        GET DIAGNOSTICS CONDITION 1 
        @my_sqlstate = RETURNED_SQLSTATE, @my_errno = MYSQL_ERRNO, @my_text = MESSAGE_TEXT;
        SELECT @my_sqlstate as error_sqlstate, @my_errno as error_errno, @my_text as error_text;
    END;

    START TRANSACTION;
    
    IF NOT EXISTS(SELECT 1 FROM Administrator WHERE AdminID = pAdminID) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'AdminID does not exist.';
    ELSE
        IF EXISTS(SELECT 1 FROM School_Unit WHERE Postal_Address = pPostalAddress OR PhoneNumber = pTelephone OR Email = pEmail) THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'SchoolUnit with given Postal_Address or Telephone or Email already exists.';
        ELSE
            INSERT INTO School_Unit(School_Name, Postal_Address, City, PhoneNumber,Email ,School_Director, AdminID) 
            VALUES(pSchoolName, pPostalAddress, pCity, pTelephone,pEmail ,pSchoolDirector, pAdminID);
        END IF;
    END IF;

    COMMIT;
END $$
DELIMITER ;


-- Insert book copies in a specific school unit

DELIMITER $$
CREATE PROCEDURE InsertBookCopies(IN pBookID INT, IN pSchoolID INT, IN pCopies INT, IN pOperatorID INT)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        GET DIAGNOSTICS CONDITION 1 
        @my_sqlstate = RETURNED_SQLSTATE, @my_errno = MYSQL_ERRNO, @my_text = MESSAGE_TEXT;
        SELECT @my_sqlstate as error_sqlstate, @my_errno as error_errno, @my_text as error_text;
    END;

    -- Validate parameters
    IF NOT EXISTS (SELECT 1 FROM Book WHERE BookID = pBookID) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid BookID.';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM School_Unit WHERE SchoolID = pSchoolID) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid SchoolID.';
    END IF;
    IF pCopies <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid number of copies.';
    END IF;

    START TRANSACTION;

    IF EXISTS (SELECT 1 FROM Operator WHERE OperatorID = pOperatorID AND SchoolID = pSchoolID) THEN
        -- Insert the book copies into the BookCopy table
        WHILE pCopies > 0 DO
            INSERT INTO BookCopy(BookID)
            VALUES(pBookID);
            SET pCopies = pCopies - 1;
        END WHILE;
            
        -- If no errors, commit the transaction
        COMMIT;
    ELSE
        -- If the operator is not associated with the specified school unit, raise an exception
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'The operator is not associated with the specified school unit.';
        ROLLBACK;
    END IF;
END$$
DELIMITER ;


-- Procedure to get a list of books and their ammount in a specific school:
DELIMITER $$
CREATE PROCEDURE get_books_availability(IN pSchoolID INT)
BEGIN
  SELECT b.BookID, b.ISBN, b.Title, a.FullName AS Author, COUNT(bc.BookCopyID) AS AvailableBooks
  FROM Book b
  INNER JOIN BookCopy bc ON b.BookID = bc.BookID
  INNER JOIN BookAuthor ba ON b.BookID = ba.BookID
  INNER JOIN Author a ON ba.AuthorID = a.AuthorID
  WHERE b.SchoolID = pSchoolID
  GROUP BY b.BookID, a.FullName;
END $$
DELIMITER ;


/*-
	Procedure to get the stats of the total ammount of copies of a book, 
    the ammount of the borrowed ones and the ammount that is being reserved (and it is in the library).
*/
DELIMITER $$
CREATE PROCEDURE GetBookCopyStats(IN pBookID INT)
BEGIN
  SELECT 
    b.Title, b.ISBN, COUNT(bc.BookCopyID) AS TotalBookCopies,
    SUM(CASE WHEN bc.InLibrary = FALSE THEN 1 ELSE 0 END) AS BorrowedBookCopies,
    (SELECT COUNT(*) 
      FROM Reservation r 
      JOIN BookCopy bc ON r.BookCopyID = bc.BookCopyID 
      WHERE bc.BookID = pBookID AND r.ReservationStatus = 'Accepted' AND bc.InLibrary = TRUE
    ) AS ReservedBookCopies
  FROM 
    Book b
    LEFT JOIN BookCopy bc ON b.BookID = bc.BookID
  WHERE 
    b.BookID = pBookID;
END$$
DELIMITER ;


-- Procedure to get the pending reservations in order by the requested time:
DELIMITER $$
CREATE PROCEDURE GetPendingReservations(IN pSchoolID INT)
BEGIN
  SELECT r.ReservationID, r.SchoolUserID, r.BookID, r.BookCopyID, r.Submitted_DateTime, 
		r.Acceptance_Date, r.Cancelation_Date, r.ReservationStatus
  FROM Reservation r
  JOIN BookCopy bc ON r.BookCopyID = bc.BookCopyID
  WHERE r.ReservationStatus = 'Pending' AND bc.SchoolID = pSchoolID
  ORDER BY r.BookID ASC, r.Submitted_DateTime ASC;
END$$
DELIMITER ;


-- Procedure to get the borrow history for a specific user in a school unit:
DELIMITER $$
CREATE PROCEDURE GetBorrowHistory(IN p_SchoolUserID INT)
BEGIN
    SELECT Borrow.BorrowID, Borrow.Borrow_Date, Borrow.Due_Date, Borrow.Return_Date, Borrow.Borrow_Status,
           Book.Title, Book.ISBN
    FROM Borrow
    JOIN BookCopy ON Borrow.BookCopyID = BookCopy.BookCopyID
    JOIN Book ON BookCopy.BookID = Book.BookID
    WHERE Borrow.SchoolUserID = p_SchoolUserID;
END $$
DELIMITER ;


-- Procedure to get the reservation history for a specific user in a school unit:
DELIMITER $$
CREATE PROCEDURE GetReservationHistory(IN p_SchoolUserID INT)
BEGIN
    SELECT Reservation.ReservationID, Reservation.Submitted_DateTime, Reservation.Acceptance_Date, Reservation.Due_Reservation_Date, Reservation.Cancelation_Date, Reservation.ReservationStatus,
           Book.Title, Book.ISBN
    FROM Reservation
    JOIN BookCopy ON Reservation.BookCopyID = BookCopy.BookCopyID
    JOIN Book ON BookCopy.BookID = Book.BookID
    WHERE Reservation.SchoolUserID = p_SchoolUserID;
END $$
DELIMITER ;


-- Procedure to get all the reviews submitted by a specific user in a school unit:
DELIMITER $$
CREATE PROCEDURE GetUserReviews(IN p_SchoolUserID INT)
BEGIN
    SELECT Review.ReviewID, Review.Review_text, Review.Likert, Review.Date_Submitted, Review.Approval_Status,
           Book.Title
    FROM Review
    JOIN Book ON Review.BookID = Book.BookID
    WHERE Review.SchoolUserID = p_SchoolUserID;
END $$
DELIMITER ;


-- Search a book based on a given keyword (titlle,author,category etc.)
DELIMITER $$
CREATE PROCEDURE SearchBook(IN p_keyword VARCHAR(60), IN p_school_id INT)
BEGIN
    SELECT DISTINCT Book.* FROM Book
    LEFT JOIN BookAuthor ON Book.BookID = BookAuthor.BookID
    LEFT JOIN Author ON BookAuthor.AuthorID = Author.AuthorID
    LEFT JOIN BookKeywords ON Book.BookID = BookKeywords.BookID
    LEFT JOIN Keywords ON BookKeywords.KeywordID = Keywords.KeywordID
    WHERE (Book.Title LIKE CONCAT('%', p_keyword, '%') 
    OR Author.FullName LIKE CONCAT('%', p_keyword, '%')
    OR Keywords.KeywordText LIKE CONCAT('%', p_keyword, '%')
    OR Book.Publisher LIKE CONCAT('%', p_keyword, '%'))
    AND Book.SchoolID = p_school_id;
END $$
DELIMITER ;

