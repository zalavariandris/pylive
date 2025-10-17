import sys
from PySide6.QtCore import Qt
from PySide6.QtSql import QSqlDatabase, QSqlTableModel, QSqlRelationalTableModel, QSqlRelation, QSqlQuery, QSqlRelationalDelegate
from PySide6.QtWidgets import QApplication, QTableView, QVBoxLayout, QWidget, QPushButton, QLineEdit, QHBoxLayout

class RelationalDatabaseApp(QWidget):
    def __init__(self):
        super().__init__()

        # Create and open SQLite database in memory
        self.db = QSqlDatabase.addDatabase("QSQLITE")
        self.db.setDatabaseName(":memory:")

        if not self.db.open():
            print("Error: Cannot open database")
            return

        self._create_tables()

        # Create models for the tables
        self.authors_model = QSqlRelationalTableModel(self, self.db)
        self.authors_model.setTable("authors")
        self.authors_model.select()

        self.books_model = QSqlRelationalTableModel(self, self.db)
        self.books_model.setTable("books")
        # self.books_model.setRelation(2, QSqlRelation("authors", "id", "name"))
        self.books_model.setRelation(self.books_model.fieldIndex('author_id'), QSqlRelation('authors', 'id', 'name'))
        self.books_model.select()

        # Set QSqlRelationalDelegate for the 'author_id' column
        self.books_view = QTableView()
        self.books_view.setModel(self.books_model)
        self.books_view.setItemDelegate(QSqlRelationalDelegate(self.books_view))

        # Create table views for displaying the data
        self.authors_view = QTableView()
        self.authors_view.setModel(self.authors_model)

        # Layout setup
        layout = QVBoxLayout()
        layout.addWidget(self.authors_view)
        layout.addWidget(self.books_view)

        # Add buttons for adding/removing books and authors
        self.add_book_button = QPushButton("Add Book")
        self.add_book_button.clicked.connect(self.add_book)
        
        self.remove_book_button = QPushButton("Remove Book")
        self.remove_book_button.clicked.connect(self.remove_book)

        self.add_author_button = QPushButton("Add Author")
        self.add_author_button.clicked.connect(self.add_author)

        self.remove_author_button = QPushButton("Remove Author")
        self.remove_author_button.clicked.connect(self.remove_author)

        layout.addWidget(self.add_book_button)
        layout.addWidget(self.remove_book_button)
        
        layout.addWidget(self.add_author_button)
        layout.addWidget(self.remove_author_button)

        self.setLayout(layout)
        self.setWindowTitle("Relational Database Example")
        self.resize(800, 600)

        # Input fields for book and author
        self.book_title_input = QLineEdit(self)
        self.book_title_input.setPlaceholderText("Enter Book Title")
        layout.addWidget(self.book_title_input)

        self.author_name_input = QLineEdit(self)
        self.author_name_input.setPlaceholderText("Enter Author Name")
        layout.addWidget(self.author_name_input)

    def _create_tables(self):
        # Create authors and books tables in memory
        queries = [
            """CREATE TABLE authors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT
            )""",
            """CREATE TABLE books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                author_id INTEGER,
                FOREIGN KEY(author_id) REFERENCES authors(id)
            )"""
        ]
        
        # Create QSqlQuery object to execute queries
        query = QSqlQuery(self.db)
        for sql in queries:
            if not query.exec(sql):
                print(f"Error creating tables: {query.lastError().text()}")
                return

        # Insert some sample data
        if not query.exec("INSERT INTO authors (name) VALUES ('Author A')"):
            print(f"Error inserting data into authors: {query.lastError().text()}")

        if not query.exec("INSERT INTO authors (name) VALUES ('Author B')"):
            print(f"Error inserting data into authors: {query.lastError().text()}")

        if not query.exec("INSERT INTO books (title, author_id) VALUES ('Book 1', 1)"):
            print(f"Error inserting data into books: {query.lastError().text()}")

        if not query.exec("INSERT INTO books (title, author_id) VALUES ('Book 2', 2)"):
            print(f"Error inserting data into books: {query.lastError().text()}")

    def add_book(self):
        # Add a book with a specified title and author
        title = self.book_title_input.text()
        author_name = self.author_name_input.text()

        # First, find the author ID based on the name
        query = QSqlQuery(self.db)
        query.prepare("SELECT id FROM authors WHERE name = :name")
        query.bindValue(":name", author_name)
        if not query.exec():
            print(f"Error querying authors: {query.lastError().text()}")
            return

        if query.next():
            author_id = query.value(0)
            query.prepare("INSERT INTO books (title, author_id) VALUES (:title, :author_id)")
            query.bindValue(":title", title)
            query.bindValue(":author_id", author_id)
            if query.exec():
                self.books_model.select()  # Refresh the books model
            else:
                print(f"Error inserting book: {query.lastError().text()}")
        else:
            print("Author not found!")

    def remove_book(self):
        # Remove a book based on the selected row in the books view
        selected_rows = self.books_view.selectionModel().selectedRows()
        if selected_rows:
            book_id = self.books_model.record(selected_rows[0].row()).value("id")
            query = QSqlQuery(self.db)
            query.prepare("DELETE FROM books WHERE id = :id")
            query.bindValue(":id", book_id)
            if query.exec():
                self.books_model.select()  # Refresh the books model
            else:
                print(f"Error removing book: {query.lastError().text()}")

    def add_author(self):
        # Get the author name from input
        author_name = self.author_name_input.text()
        if author_name:
            query = QSqlQuery(self.db)
            query.prepare("INSERT INTO authors (name) VALUES (:name)")
            query.bindValue(":name", author_name)
            
            if query.exec():
                # Refresh the authors model to show the new author
                self.authors_model.select()  # Refresh authors model
                
                # Trigger the reset of the books model to update the dropdown in the view
                self.books_model.beginResetModel()
                self.books_model.endResetModel()
            else:
                print(f"Error adding author: {query.lastError().text()}")
        else:
            print("Author name cannot be empty!")


    def remove_author(self):
        # Remove an author and their associated books
        author_name = self.author_name_input.text()
        if author_name:
            # First, remove all books by this author
            query = QSqlQuery(self.db)
            query.prepare("DELETE FROM books WHERE author_id IN (SELECT id FROM authors WHERE name = :name)")
            query.bindValue(":name", author_name)
            if query.exec():
                # Now remove the author
                query.prepare("DELETE FROM authors WHERE name = :name")
                if query.exec():
                    self.authors_model.select()  # Refresh the authors model
                    self.books_model.select()  # Refresh the books model
                else:
                    print(f"Error removing author: {query.lastError().text()}")
            else:
                print(f"Error removing books for author: {query.lastError().text()}")
        else:
            print("Author name cannot be empty!")

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = RelationalDatabaseApp()
    window.show()

    sys.exit(app.exec())
