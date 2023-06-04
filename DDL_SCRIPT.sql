create database myschool_library;
use myschool_library;

CREATE TABLE IF NOT EXISTS AppUser( 
UserID INT not null AUTO_INCREMENT,
FirstName VARCHAR(45) not null,
LastName  VARCHAR(45) not null,
BirthDate DATE not null,
Email VARCHAR(80) UNIQUE not null,
Username VARCHAR(80) UNIQUE not null,
Password VARCHAR(100) not null,
PRIMARY KEY (UserID)
);

CREATE TABLE IF NOT EXISTS Administrator(
AdminID INT not null,
PhoneNumber VARCHAR(45) UNIQUE not null,
PRIMARY KEY (AdminID),
FOREIGN KEY (AdminID) REFERENCES AppUser(UserID) on DELETE RESTRICT on UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS School_Unit(
SchoolID INT not null AUTO_INCREMENT,
School_Name VARCHAR(72) UNIQUE not null,
Postal_Address VARCHAR(72) UNIQUE not null,
City VARCHAR(45) not null,
PhoneNumber VARCHAR(45) UNIQUE not null,
Email VARCHAR(80) UNIQUE not null,                   
School_Director VARCHAR(45) not null,
AdminID INT not null,
PRIMARY KEY (SchoolID),
FOREIGN KEY (AdminID) REFERENCES Administrator(AdminID) on DELETE RESTRICT on UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS SchoolUser(
SchoolUserID INT not null,
Position VARCHAR(9) not null check (Position in ('Teacher','Student')),
SchoolID INT not null,
PRIMARY KEY (SchoolUserID),
FOREIGN KEY (SchoolUserID) REFERENCES AppUser(UserID) on DELETE RESTRICT on UPDATE CASCADE,
FOREIGN KEY (SchoolID) REFERENCES School_Unit(SchoolID) on DELETE RESTRICT on UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS Operator(
OperatorID INT not null,
PhoneNumber VARCHAR(45) UNIQUE,
AdminID INT not null,
SchoolID INT not null,
PRIMARY KEY (OperatorID),
FOREIGN KEY (OperatorID) REFERENCES AppUser(UserID) on DELETE RESTRICT on UPDATE CASCADE ,
FOREIGN KEY (AdminID) REFERENCES Administrator(AdminID) on DELETE RESTRICT on UPDATE CASCADE ,
FOREIGN KEY (SchoolID) REFERENCES School_Unit(SchoolID) on DELETE RESTRICT on UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS Book(
BookID INT not null AUTO_INCREMENT,
ISBN VARCHAR(17) not null,  
Title VARCHAR(60) not null,
Publisher VARCHAR(45),
Number_of_pages INT not null,
Summary TEXT not null,
Image varchar(300) not null,                        -- Link for the image
language VARCHAR(45) not null,
OperatorID INT not null,
SchoolID INT not null,
PRIMARY KEY (BookID),
FOREIGN KEY (OperatorID) REFERENCES Operator(OperatorID) on DELETE RESTRICT on UPDATE CASCADE,
FOREIGN KEY (SchoolID) REFERENCES School_Unit(SchoolID) on DELETE RESTRICT on UPDATE CASCADE,
CONSTRAINT UNIQUE (ISBN,SchoolID)
);

CREATE TABLE IF NOT EXISTS BookCopy(
BookCopyID INT not null AUTO_INCREMENT,
BookID INT not null,
InLibrary BOOLEAN not null DEFAULT TRUE,
IsAvailable BOOLEAN not null DEFAULT TRUE,
PRIMARY KEY (BookCopyID,BookID), 
FOREIGN KEY (BookID) REFERENCES Book(BookID) on DELETE RESTRICT on UPDATE CASCADE,
CONSTRAINT not_in_library_and_available CHECK ( NOT (InLibrary = FALSE AND IsAvailable = TRUE))
);

CREATE TABLE IF NOT EXISTS Category(
CategoryID INT not null AUTO_INCREMENT,
CategoryName VARCHAR(45) not null,
PRIMARY KEY (CategoryID)
);

CREATE TABLE IF NOT EXISTS Author(
AuthorID INT not null AUTO_INCREMENT,
FullName VARCHAR(90) not null,
PRIMARY KEY (AuthorID)
);

CREATE TABLE IF NOT EXISTS Keywords(
KeywordID INT not null auto_increment,
KeywordText VARCHAR(60) not null,
PRIMARY KEY (KeywordID)
);

CREATE TABLE IF NOT EXISTS BookCategory(
BookID INT not null,
CategoryID INT not null,
PRIMARY KEY (BookID,CategoryID),
FOREIGN KEY (BookID) REFERENCES Book(BookID) on DELETE RESTRICT on UPDATE CASCADE,
FOREIGN KEY (CategoryID) REFERENCES Category(CategoryID) on DELETE RESTRICT on UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS BookAuthor(
BookID INT not null,
AuthorID INT not null,
PRIMARY KEY (BookID,AuthorID),
FOREIGN KEY (BookID) REFERENCES Book(BookID) on DELETE RESTRICT on UPDATE CASCADE,
FOREIGN KEY (AuthorID) REFERENCES Author(AuthorID) on DELETE RESTRICT on UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS BookKeywords(
BookID INT not null,
KeywordID INT not null,
PRIMARY KEY (BookID,KeywordID),
FOREIGN KEY (BookID) REFERENCES Book(BookID) on DELETE RESTRICT on UPDATE CASCADE,
FOREIGN KEY (KeywordID) REFERENCES Keywords(KeywordID) on DELETE RESTRICT on UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS Borrow(
BorrowID INT not null AUTO_INCREMENT,
SchoolUserID INT not null,
BookID INT not null,         
BookCopyID INT not null,
Borrow_Date DATE not null DEFAULT (CURRENT_DATE),
Due_Date DATE not null DEFAULT (DATE_ADD(CURRENT_DATE,INTERVAL 1 WEEK)),
Return_Date DATE,                                                                                                                    
Borrow_Status VARCHAR(12) not null DEFAULT 'Accepted' CHECK (Borrow_Status in ('Accepted','Overdue','Lost','Returned')),
OperatorID INT not null,
PRIMARY KEY (BorrowID, SchoolUserID, BookID),
FOREIGN KEY (SchoolUserID) REFERENCES SchoolUser(SchoolUserID) on DELETE RESTRICT on UPDATE CASCADE,
FOREIGN KEY (BookID) REFERENCES Book(BookID) on DELETE RESTRICT on UPDATE CASCADE,
FOREIGN KEY (BookCopyID) REFERENCES BookCopy(BookCopyID) on DELETE RESTRICT on UPDATE CASCADE ,
FOREIGN KEY (OperatorID) REFERENCES Operator(OperatorID) on DELETE RESTRICT on UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS Reservation(
ReservationID INT not null AUTO_INCREMENT,
SchoolUserID INT not null,
BookID INT not null,
BookCopyID INT,
Submitted_DateTime DATETIME not null DEFAULT (CURRENT_TIMESTAMP),
Acceptance_Date DATE,
Due_Reservation_Date DATE,
Cancelation_Date DATE CHECK (Cancelation_Date >= Acceptance_Date),
ReservationStatus VARCHAR(12) not null DEFAULT 'Pending' CHECK (ReservationStatus in ('Pending','Cancelled','Accepted','Completed')),
OperatorID INT not null,
PRIMARY KEY (ReservationID, SchoolUserID, BookID),
FOREIGN KEY (SchoolUserID) REFERENCES SchoolUser(SchoolUserID) on DELETE RESTRICT on UPDATE CASCADE,
FOREIGN KEY (BookID) REFERENCES Book(BookID) on DELETE RESTRICT on UPDATE CASCADE,
FOREIGN KEY (BookCopyID) REFERENCES BookCopy(BookCopyID) on DELETE RESTRICT on UPDATE CASCADE,
FOREIGN KEY (OperatorID) REFERENCES Operator(OperatorID) on DELETE RESTRICT on UPDATE CASCADE
);
  
CREATE TABLE IF NOT EXISTS Review(
ReviewID INT not null AUTO_INCREMENT,
SchoolUserID INT not null,
BookID INT not null,
Review_text TEXT,
Likert INT not null DEFAULT 0 CHECK ( Likert BETWEEN 1 AND 5),
Date_Submitted DATETIME not null DEFAULT CURRENT_TIMESTAMP,
Approval_Status VARCHAR(45) not null DEFAULT 'Pending' CHECK (Approval_Status in ( 'Pending','Approved','Rejected')) ,
OperatorID INT not null,
PRIMARY KEY ( ReviewID, SchoolUserID, BookID ),
FOREIGN KEY (SchoolUserID) REFERENCES SchoolUser(SchoolUserID) on DELETE RESTRICT on UPDATE CASCADE,
FOREIGN KEY (BookID) REFERENCES Book(BookID) on DELETE RESTRICT on UPDATE CASCADE,
FOREIGN KEY (OperatorID) REFERENCES Operator(OperatorID) on DELETE RESTRICT on UPDATE CASCADE,
CONSTRAINT unique_review_per_book_by_user  UNIQUE (BookID, SchoolUserID)    
);

CREATE TABLE IF NOT EXISTS RegistrationRequest(
RequestID INT not null AUTO_INCREMENT,
FirstName VARCHAR(45) not null,
LastName  VARCHAR(45) not null,
BirthDate DATE not null,
Email VARCHAR(80) UNIQUE not null,
PhoneNumber VARCHAR(45) UNIQUE,
Username VARCHAR(80) UNIQUE not null,
Password VARCHAR(100) not null,
School_Unit INT not null,
Role_Type VARCHAR(20) not null CHECK (Role_Type in ('operator','student','teacher') ),
PRIMARY KEY (RequestID)
);


-- INDEXES

CREATE INDEX idx_login ON AppUser(Username,Password);
CREATE INDEX idx_schooluserInfo ON SchoolUser(SchoolID,SchoolUserID,Position);
CREATE INDEX idx_book_title_School ON Book(BookID,Title,SchoolID);
CREATE INDEX idx_category ON Category(CategoryName);
CREATE INDEX idx_borrow ON Borrow(SchoolUserID, Borrow_Date, BorrowID, BookID);
CREATE INDEX idx_review  ON Review(SchoolUserID, BookID, OperatorID);

