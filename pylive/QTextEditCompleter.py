import sys
from typing import *
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

from datetime import datetime
class QTextEditCompleter(QCompleter):
	def __init__(self, completions:QStringListModel|List[str]|None=None, parent=None):
		if completions:
			super().__init__(completions, parent=parent)
		else:
			super().__init__(parent=parent)
		self.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
		self.setCaseSensitivity(Qt.CaseInsensitive)

	def eventFilter(self, o, e):
		
		if e.type() == QEvent.KeyPress:
			print("filter", o, datetime.now())


			completer = self

		
			# If completer popup is open. Give it exclusive use of specific keys
			if self.popup().isVisible() and e.key() in [
				# Navigate popup
				Qt.Key.Key_Up,
				Qt.Key.Key_Down,
				# Accept completion
				Qt.Key.Key_Enter,
				Qt.Key.Key_Return,
				Qt.Key.Key_Tab,
				Qt.Key.Key_Backtab,
			]:
				
				return super().eventFilter(o, e)

			# super().keyPressEvent(e)
			# Show Hide Completer
			print(self.completionModel())
			completions = [self.completionModel().index(row, 0).data() for row in range( self.completionModel().rowCount() )]
			print("completions", completions)
			if completions:
				popup = self.popup()
				popup.setCurrentIndex(self.completionModel().index(0, 0)) # autoselect first proposal

				# show completer under textCursor
				cr = self.widget().cursorRect()
				cr.setWidth(popup.sizeHintForColumn(0) +
							popup.verticalScrollBar().sizeHint().width())
				completer.complete(cr)
			else:
				self.popup().hide()


	def insertCompletion(self, completion):
		print("insertCompletion")
		"""Insert the selected completion into the text edit."""
		cursor = self.widget().textCursor()
		if not completion:
			return

		# Get the current position of the cursor
		cursor_position = cursor.position()

		# Get the text before the cursor
		text_before_cursor = self.widget().toPlainText()[:cursor_position]

		# Split the text to find the last word
		last_space_index = text_before_cursor.rfind(' ')
		if last_space_index == -1:
			# No spaces found; insert directly at the start
			new_text = completion
		else:
			# Insert the completion after the last space
			new_text = text_before_cursor[:last_space_index + 1] + completion

		# Replace the current text with the new text
		self.widget().setPlainText(new_text)

		# Move the cursor to the end of the new text
		cursor.setPosition(len(new_text))
		self.widget().setTextCursor(cursor)

	def setCompletionPrefix(self, prefix):
		"""Override to update the completion list based on the prefix."""
		super().setCompletionPrefix(prefix)
		if self.completionCount() > 0:
			self.popup().show()
		else:
			self.popup().hide()




if __name__ == "__main__":
	keywords = [
		'and', 'as', 'assert', 'async', 'await', 'break', 'class', 'continue',
		'def', 'del', 'elif', 'else', 'except', 'False', 'finally', 'for',
		'from', 'global', 'if', 'import', 'in', 'is', 'lambda', 'None', 'nonlocal',
		'not', 'or', 'pass', 'raise', 'return', 'True', 'try', 'while', 'with', 'yield'
	]
	app = QApplication(sys.argv)
	textedit = QPlainTextEdit()
	completer = QTextEditCompleter()
	completer.setModel(QStringListModel(keywords))
	completer.setWidget(textedit)
	completer.installEventFilter(textedit)
	textedit.textChanged.connect(lambda: completer.setCompletionPrefix(textedit.toPlainText().split(" ")[-1]))
	textedit.show()
	app.exec()
