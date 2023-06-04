-- QUERIES

-- Administrator :

-- 3.1.1
SELECT s.School_Name , Count(B.BorrowID) AS TotalLoans
FROM School_Unit s 
JOIN SchoolUser su ON s.SchoolID = su.SchoolID
JOIN Borrow b ON su.SchoolUserID = b.SchoolUserID
WHERE YEAR(b.Borrow_Date) = ? AND MONTH(b.Borrow_Date) = ?          -- The "?" will be specified in the application
GROUP BY s.School_Name; 


-- 3.1.2
SELECT a.FullName AS AuthorName, CONCAT(u.FirstName, ' ', u.LastName) AS TeacherName
FROM Category c
JOIN BookCategory bc ON c.CategoryID = bc.CategoryID
JOIN Book b ON bc.BookID = b.BookID
JOIN BookAuthor ba ON b.BookID = ba.BookID
JOIN Author a ON ba.AuthorID = a.AuthorID
JOIN Borrow br ON b.BookID = br.BookID
JOIN SchoolUser su ON br.SchoolUserID = su.SchoolUserID
JOIN AppUser u ON su.SchoolUserID = u.UserID
WHERE c.CategoryName = ? AND su.Position = 'Teacher' AND br.Borrow_Date >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR);


-- 3.1.3
SELECT CONCAT(u.FirstName, ' ', u.LastName) AS TeacherName, COUNT(DISTINCT b.BookID) AS NumberOfBooks
FROM SchoolUser su
JOIN AppUser u ON su.SchoolUserID = u.UserID
JOIN Borrow bo ON su.SchoolUserID = bo.SchoolUserID
JOIN Book b ON bo.BookID = b.BookID
WHERE su.Position = 'Teacher' AND YEAR(CURDATE()) - YEAR(u.BirthDate) < 40
GROUP BY su.SchoolUserID
ORDER BY NumberOfBooks DESC;


-- 3.1.4
CREATE VIEW UnborrowedAuthors AS
SELECT a.FullName AS AuthorName
FROM Author a
LEFT JOIN BookAuthor ba ON a.AuthorID = ba.AuthorID
LEFT JOIN Book b ON ba.BookID = b.BookID
LEFT JOIN Borrow br ON b.BookID = br.BookID
WHERE br.BorrowID IS NULL;

-- 3.1.5
SELECT o.OperatorID, CONCAT(u.FirstName, ' ', u.LastName) AS OperatorName, COUNT(b.BorrowID) AS NumberOfLoans
FROM Operator o
JOIN AppUser u ON o.OperatorID = u.UserID
JOIN Borrow b ON o.OperatorID = b.OperatorID
WHERE YEAR(b.Borrow_Date) = ?
GROUP BY o.OperatorID
HAVING NumberOfLoans > 20;

-- 3.1.6
SELECT bc1.CategoryID AS Category1, bc2.CategoryID AS Category2, COUNT(*) AS Frequency
FROM BookCategory bc1
JOIN BookCategory bc2 ON bc1.BookID = bc2.BookID AND bc1.CategoryID < bc2.CategoryID
JOIN Borrow b ON bc1.BookID = b.BookID
GROUP BY bc1.CategoryID, bc2.CategoryID
ORDER BY Frequency DESC
LIMIT 3;


-- 3.1.7
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

-- OPERATORS

-- 3.2.1      
SELECT B.Title, GROUP_CONCAT(A.FullName SEPARATOR ', ') AS Authors
FROM Book B 
JOIN BookAuthor BA ON B.BookID = BA.BookID
JOIN Author A ON BA.AuthorID = A.AuthorID
JOIN BookCategory BC ON B.BookID = BC.BookID
JOIN Category C ON BC.CategoryID = C.CategoryID
WHERE B.Title LIKE ? AND A.FullName LIKE ? AND B.SchoolID = ? AND C.CategoryName LIKE ? AND EXISTS (
    SELECT 1 FROM BookCopy BC WHERE BC.BookID = B.BookID
)
GROUP BY B.BookID;


-- 3.2.2     
SELECT su.FirstName, su.LastName, b.BookID, DATEDIFF(CURDATE(), bo.Due_Date) AS Delay_Days
FROM Borrow bo
JOIN SchoolUser su ON bo.SchoolUserID = su.SchoolUserID
JOIN Book b ON bo.BookID = b.BookID
WHERE su.FirstName LIKE ? 
AND su.LastName LIKE ? 
AND bo.Borrow_Status = 'Overdue' 
AND DATEDIFF(CURDATE(), bo.Due_Date) > ? 
;

-- 3.2.3
SELECT SU.FirstName, SU.LastName, C.CategoryName, AVG(R.Likert) as AverageRating
FROM Review R
JOIN SchoolUser SU ON R.SchoolUserID = SU.SchoolUserID
JOIN Book B ON R.BookID = B.BookID
JOIN BookCategory BC ON B.BookID = BC.BookID
JOIN Category C ON BC.CategoryID = C.CategoryID
JOIN Operator O ON R.OperatorID = O.OperatorID
WHERE SU.FirstName LIKE ?
AND SU.LastName LIKE ?
AND C.CategoryName LIKE ?
AND O.OperatorID = ?
GROUP BY SU.FirstName, SU.LastName, C.CategoryName;


-- App User

-- 3.3.1 
SELECT B.Title, A.FullName AS Author, C.CategoryName
FROM Book B
JOIN BookAuthor BA ON B.BookID = BA.BookID
JOIN Author A ON BA.AuthorID = A.AuthorID
JOIN BookCategory BC ON B.BookID = BC.BookID
JOIN Category C ON BC.CategoryID = C.CategoryID
WHERE B.Title LIKE ?
AND A.FullName LIKE ?
AND C.CategoryName LIKE ?
;

-- 3.3.2
SELECT B.Title, Bo.Borrow_Date, Bo.Due_Date
FROM Borrow Bo
JOIN Book B ON Bo.BookID = B.BookID
WHERE Bo.SchoolUserID = ?
;

