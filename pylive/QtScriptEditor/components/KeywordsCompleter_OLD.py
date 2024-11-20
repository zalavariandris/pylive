from typing import *

from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *

class WordsCompleter(QCompleter):
	def __init__(self, words):

		# completion model
		self.completions_model = QStringListModel(words)
		super().__init__(self.completions_model)

		# completion view
		self.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)


class KeywordsCompleter(QCompleter):
	def __init__(self):

		# completion model
		keywords = [
			'and', 'as', 'assert', 'async', 'await', 'break', 'class', 'continue',
			'def', 'del', 'elif', 'else', 'except', 'False', 'finally', 'for',
			'from', 'global', 'if', 'import', 'in', 'is', 'lambda', 'None', 'nonlocal',
			'not', 'or', 'pass', 'raise', 'return', 'True', 'try', 'while', 'with', 'yield'
		]
		self.completions_model = QStringListModel(keywords)
		super().__init__(self.completions_model)

		# completion view
		self.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

		
class CompleterTextEdit(QPlainTextEdit):
	def __init__(self, parent=None):
		super().__init__(parent)
		""" Setup Textedit """
		######################
		self.setupTextEdit()
		self.setupAutocomplete()

	def setupTextEdit(self):
		self.setWindowTitle("ScriptTextEdit")
		self.setWordWrapMode(QTextOption.WrapMode.NoWrap)
		self.setTabChangesFocus(False)
		self.setTabStopDistance(QFontMetricsF(self.font()).horizontalAdvance(' ') * 4)

		# set a monospace font
		font = QFont("Operator Mono", 11)
		self.setFont(font)
		self.font().setStyleHint(QFont.StyleHint.TypeWriter)

		# resize window
		width = QFontMetrics(font).horizontalAdvance('O') * 70
		self.resize(width, int(width*4/3))

	def setupAutocomplete(self):
		""" Setup autocomplete """
		keywords = [
			"apple", "ananas" "banana", "cherry", "date", "elderberry", "fig", "grape", "honeydew", "kiwi", "lemon",
			'and', 'as', 'assert', 'async', 'await', 'break', 'class', 'continue',
			'def', 'del', 'elif', 'else', 'except', 'False', 'finally', 'for',
			'from', 'global', 'if', 'import', 'in', 'is', 'lambda', 'None', 'nonlocal',
			'not', 'or', 'pass', 'raise', 'return', 'True', 'try', 'while', 'with', 'yield'
		]
		completer = WordsCompleter(keywords)
		self.setCompleter(completer)
		
	def setCompleter(self, completer:QCompleter):
		completer.setWidget(self)
		completer.activated.connect(self.insertCompletion)
		self.cursorPositionChanged.connect(self.refreshCompleterPrefix)
		self.textChanged.connect(self.refreshCompleterPrefix)
		completer.completionModel().modelReset.connect(self.toggleCompleterVisibility)
		self.completer = completer

	@Slot()
	def insertCompletion(self, completion:str):
		tc = self.textCursor()
		tc.select(QTextCursor.SelectionType.WordUnderCursor)
		tc.insertText(completion)

	@Slot()
	def refreshCompleterPrefix(self):
		text_cursor = self.textCursor()
		# # Get word under cursor
		# # when using a simple QCompleter it needs a word instead of the whole text
		text_cursor.select(QTextCursor.SelectionType.WordUnderCursor)
		word_under_cursor = text_cursor.selection().toPlainText()

		self.completer.setCompletionPrefix(word_under_cursor)

	@Slot()
	def toggleCompleterVisibility(self):
		### Show Hide Completer ###
		###########################
		# get line under cursor
		text_cursor = self.textCursor()
		if text_cursor.hasSelection():
			self.completer.popup().hide()
			return

		# text_cursor.select(QTextCursor.SelectionType.LineUnderCursor)
		text_cursor.movePosition(QTextCursor.MoveOperation.StartOfLine, QTextCursor.MoveMode.KeepAnchor)
		line_under_cursor = text_cursor.selection().toPlainText()

		completionModel = self.completer.completionModel()
		current_proposals = [completionModel.data(completionModel.index(i, 0)) for i in range(completionModel.rowCount())]
		if len(line_under_cursor.strip())>0 and line_under_cursor[-1].isalnum() and current_proposals:
			popup = self.completer.popup()
			
			# show completer under textCursor
			cr = self.cursorRect()
			cr.setWidth(popup.sizeHintForColumn(0) +
						popup.verticalScrollBar().sizeHint().width())
			self.completer.complete(cr)
			# Ensure the model and popup are fully ready before setting the index
			def set_first_index():
				popup.setCurrentIndex(completionModel.index(0, 0))

			QTimer.singleShot(0, set_first_index)  # Defer setting the index

		else:
			self.completer.popup().hide()

	def setFont(self, font:QFont):
		super().setFont(font)
		self.setTabStopDistance(QFontMetricsF(self.font()).horizontalAdvance(' ') * 4)

	def keyPressEvent(self, e: QKeyEvent) -> None:
		### Handle autocomplete ###
		###########################
		# If completer popup is open. Give it exclusive use of specific keys
		if self.completer.popup().isVisible() and e.key() in [
			# Navigate popup
			Qt.Key.Key_Up,
			Qt.Key.Key_Down,
			# Accept completion
			Qt.Key.Key_Enter,
			Qt.Key.Key_Return,
			Qt.Key.Key_Tab,
			Qt.Key.Key_Backtab,
		]:
			e.ignore()
			return

		super().keyPressEvent(e)


if __name__ == "__main__":
	import sys
	from textwrap import dedent
	from pylive.logwindow import LogWindow
	app = QApplication(sys.argv)
	script_edit = CompleterTextEdit()

	script = dedent("""\
	def hello_world():
		print("Hello, World!")
		# This is a comment
		x = 42
		return x
	""")
		
	script_edit.setPlainText(script)

	# show app
	window = QWidget()
	window.setWindowTitle("RopeCompleter")
	layout = QVBoxLayout()
	layout.addWidget(script_edit)
	logwindow = LogWindow()
	layout.addWidget(logwindow)
	window.setLayout(layout)
	window.show()
	sys.exit(app.exec())