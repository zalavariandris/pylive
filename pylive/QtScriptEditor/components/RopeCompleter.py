from typing import *

from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *

from rope.contrib import codeassist
import rope.base.project

from datetime import datetime

class RopeCompleter(QCompleter):
	def __init__(self, rope_project, document: QTextDocument, parent=None):
		super().__init__(parent=parent)
		self.rope_project = rope_project
		self.document = document
		self.proposals_model = QStringListModel([], parent=self)  # Model for proposals
		self.setModel(self.proposals_model)

	def setCompletionPrefix(self, prefix: str) -> None:
		timebegin = datetime.now()
		# Retrieve the entire source code from the document
		source_code = self.document.toPlainText()
		offset = len(prefix)

		# Ensure the prefix is valid
		if not source_code[offset-len(prefix):offset] == prefix:
			raise IndexError("Document does not match the provided prefix")

		# Get proposals from Rope
		try:
			proposals = codeassist.code_assist(self.rope_project, source_code=source_code, offset=offset)
			proposals = codeassist.sorted_proposals(proposals)  # Sorting proposals

			# Update the model of the QCompleter
			self.proposals_model.setStringList([str(proposal.name) for proposal in proposals])
			super().setCompletionPrefix("")
		except Exception as err:
			print(err)
		timeend = datetime.now()
		import humanize
		print("completer took", humanize.naturaldelta(timeend-timebegin, minimum_unit="milliseconds"))


		
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
		# completer = KeywordsCompleter()
		self.rope_project = rope.base.project.Project('.')
		completer = RopeCompleter(self.rope_project, self.document())
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
		# text_cursor.select(QTextCursor.SelectionType.WordUnderCursor)
		# word_under_cursor = text_cursor.selection().toPlainText()

		# Get text until position
		# when using a code completion it actually needs the cursor offset. So this is too much.
		text_cursor.setPosition(0, QTextCursor.MoveMode.KeepAnchor)
		text_until_position = text_cursor.selection().toPlainText()

		self.completer.setCompletionPrefix(text_until_position)

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

	app = QApplication(sys.argv)
	script_edit = CompleterTextEdit()

	script = dedent("""\
	def hello_world():
		print("Hello, World!")
		# This is a comment
		x = 42
		return x
	""")

	with open("../../test_script.py") as file:
		script = file.read()
		
	script_edit.setPlainText(script)
	# show app
	script_edit.show()
	sys.exit(app.exec())