CREATE DATABASE IF NOT EXISTS booknest CHARACTER SET utf8mb4;
USE booknest;
DROP TABLE IF EXISTS sale_items, sales, books, categories, users;
CREATE TABLE users(id INT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(40) UNIQUE NOT NULL, password VARCHAR(255) NOT NULL, role ENUM('admin','staff') NOT NULL);
CREATE TABLE categories(id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(60) UNIQUE NOT NULL, tagline VARCHAR(80));
CREATE TABLE books(id INT AUTO_INCREMENT PRIMARY KEY, title VARCHAR(150) NOT NULL, author VARCHAR(100) NOT NULL,
  category_id INT NOT NULL, isbn VARCHAR(13) UNIQUE NOT NULL, price DECIMAL(10,2) NOT NULL CHECK(price>=0),
  stock INT NOT NULL CHECK(stock>=0), reorder_level INT NOT NULL DEFAULT 5, rating DECIMAL(2,1) DEFAULT 4.5, blurb TEXT,
  FOREIGN KEY(category_id) REFERENCES categories(id));
CREATE TABLE sales(id INT AUTO_INCREMENT PRIMARY KEY, sold_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, customer VARCHAR(80), user_id INT NULL,
  subtotal DECIMAL(10,2), discount DECIMAL(10,2), tax DECIMAL(10,2), total DECIMAL(10,2), FOREIGN KEY(user_id) REFERENCES users(id));
CREATE TABLE sale_items(id INT AUTO_INCREMENT PRIMARY KEY, sale_id INT NOT NULL, book_id INT NOT NULL, qty INT NOT NULL CHECK(qty>0), price DECIMAL(10,2) NOT NULL,
  FOREIGN KEY(sale_id) REFERENCES sales(id), FOREIGN KEY(book_id) REFERENCES books(id));
INSERT INTO categories(name,tagline) VALUES('Programming','Code your way up'),('Fiction','Get lost in a story'),('Finance','Grow your money'),('Self-Help','Become your best'),('Science','Question everything'),('History','Learn from the past');
INSERT INTO books(title,author,category_id,isbn,price,stock,reorder_level,rating,blurb) VALUES
('Python Crash Course','Eric Matthes',1,'9781593279288',599,12,5,4.8,'A fast-paced, project-based introduction to programming with Python.'),
('Learning Python','Mark Lutz',1,'9781449355739',899,3,5,4.5,'The definitive deep-dive into the Python language, cover to cover.'),
('Fluent Python','Luciano Ramalho',1,'9781492056355',1099,8,5,4.9,'Write idiomatic, effective Python by mastering its best features.'),
('Database System Concepts','Silberschatz',1,'9780078022159',950,6,4,4.4,'The classic text on relational design, SQL and transactions.'),
('The Alchemist','Paulo Coelho',2,'9780062315007',299,21,6,4.7,'A shepherd boy follows his dream across the desert to find his treasure.'),
('To Kill a Mockingbird','Harper Lee',2,'9780061120084',399,14,5,4.8,'A timeless story of justice and innocence in the American South.'),
('The Kite Runner','Khaled Hosseini',2,'9781594631931',449,9,5,4.6,'A haunting tale of friendship, betrayal and redemption.'),
('Rich Dad Poor Dad','Robert Kiyosaki',3,'9781612680194',350,2,5,4.3,'What the rich teach their kids about money that the poor do not.'),
('The Psychology of Money','Morgan Housel',3,'9780857197689',399,18,6,4.8,'Timeless lessons on wealth, greed and happiness.'),
('Atomic Habits','James Clear',4,'9780735211292',499,25,8,4.9,'Tiny changes, remarkable results: an easy way to build good habits.'),
('Deep Work','Cal Newport',4,'9781455586691',450,11,5,4.5,'Rules for focused success in a distracted world.'),
('A Brief History of Time','Stephen Hawking',5,'9780553380163',380,10,5,4.7,'From the Big Bang to black holes, explained for everyone.'),
('Cosmos','Carl Sagan',5,'9780345539434',520,7,4,4.8,'A personal voyage through the universe and our place in it.'),
('Sapiens','Yuval Noah Harari',6,'9780062316097',599,16,6,4.7,'A brief history of humankind, from apes to AI.'),
('Discovery of India','Jawaharlal Nehru',6,'9780143031031',425,5,5,4.5,'A sweeping portrait of India across thousands of years.'),
('Guns, Germs and Steel','Jared Diamond',6,'9780393317558',560,4,5,4.4,'The fates of human societies, explained.');
