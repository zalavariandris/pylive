import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QPlainTextEdit, QVBoxLayout, QWidget
from PySide6.QtGui import QColor, QSyntaxHighlighter, QTextCharFormat, QFont, QTextCursor
from PySide6.QtCore import QRegularExpression, QTimer


from ui import MainWindow

if __name__ == "__main__":
	app = QApplication(sys.argv)
	window = MainWindow(project="examples")	
	window.show()
	sys.exit(app.exec())
