import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QPlainTextEdit, QVBoxLayout, QWidget
from PySide6.QtGui import QColor, QSyntaxHighlighter, QTextCharFormat, QFont, QTextCursor
from PySide6.QtCore import QRegularExpression, QTimer


from ui import AppEditor

if __name__ == "__main__":
	app = QApplication(sys.argv)
	window = AppEditor(project="examples")	
	window.show()
	sys.exit(app.exec())
