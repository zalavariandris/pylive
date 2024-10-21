from typing import *

from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *

from ScriptCursor import ScriptCursor
from PygmentsSyntaxHighlighter import PygmentsSyntaxHighlighter

class ScriptEdit(QPlainTextEdit):
	def __init__(self, parent=None):
		super().__init__(parent)
		""" Setup Textedit """
		######################
		self.setWindowTitle("ScriptTextEdit")
		self.setWordWrapMode(QTextOption.WrapMode.NoWrap)
		self.setTabChangesFocus(False)
		self.setTabStopDistance(QFontMetricsF(self.font()).horizontalAdvance(' ') * 4)

		# set a monospace font
		font = QFont("Operator Mono", 11)
		self.setFont(font)
		self.font().setStyleHint(QFont.StyleHint.TypeWriter);

		# resize window
		width = QFontMetrics(font).horizontalAdvance('O') * 70
		self.resize(width, int(width*4/3))

		""" Setup Syntax Highlighting """
		# # Show whitespace characters
		# option = QTextOption(self.document().defaultTextOption())
		# option.setFlags(QTextOption.Flag.ShowTabsAndSpaces)
		# self.document().setDefaultTextOption(option)
		# WhitespaceHighlighter(self.document())
		PygmentsSyntaxHighlighter(self.document())

		""" Setup autocomplete """
		# completion model
		keywords = [
			'and', 'as', 'assert', 'async', 'await', 'break', 'class', 'continue',
			'def', 'del', 'elif', 'else', 'except', 'False', 'finally', 'for',
			'from', 'global', 'if', 'import', 'in', 'is', 'lambda', 'None', 'nonlocal',
			'not', 'or', 'pass', 'raise', 'return', 'True', 'try', 'while', 'with', 'yield'
		]
		self.completions_model = QStringListModel(keywords)

		# completion view
		self.completer = QCompleter(self.completions_model)
		self.completer.setWidget(self)
		self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
		self.completer.activated.connect(self.insertCompletion)

		""" Setup error widgets """
		# error model
		self.error_messages_model = QStandardItemModel()

		# error view
		self.error_messages_model.rowsInserted.connect(self.onErrorRowsInserted)

	def insertErrorMessage(self, lineno:int, message:str):
		self.error_messages_model.appendRow([QStandardItem(str(lineno)), QStandardItem(message)])

	def onErrorRowsInserted(self, parent: QModelIndex, first: int, last:int):
		# Iterate over each row in the range of inserted rows
		print("rows inserted", first, last)
		for row in range(first, last + 1):
			print("row:", row)
			# Retrieve the line number and message from the model
			lineno = int(self.error_messages_model.data(self.error_messages_model.index(row, 0)))  # Assuming column 0 is line number
			msg = self.error_messages_model.data(self.error_messages_model.index(row, 1))     # Assuming column 1 is message

			# Check if the block corresponding to the line number is valid
			block = self.document().findBlockByLineNumber(lineno - 1)  # Use lineno - 1 for 0-based index

			if not block.isValid():  # Ensure the block is valid
				continue

			# Get the bounding rectangle for the block
			rect = self.blockBoundingGeometry(block)
			text_without_tabs = block.text().replace("\t", "")
			tabs_count = len(block.text()) - len(text_without_tabs)
			block_text_width = QFontMetrics(self.font()).horizontalAdvance(text_without_tabs)
			block_text_width += tabs_count * self.tabStopDistance()

			# Create and position the error label
			error_label = QLabel(parent=self)
			error_label.move(int(block_text_width), int(rect.top()))
			error_label.setText(msg)  # Use the retrieved message
			error_label.show()

			# Store the error label for future reference
			# self.error_labels.append(error_label)

	def setFont(self:Self, font:QFont):
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

		### Insert Text, and Handle text editing features ### 
		# - mulitline -indenting, unindent,
		# - automatic indent of new lines,
		# - and toggle comments for multiple lines
		###############
		cursor = self.textCursor()
		if e.key() == Qt.Key.Key_Tab:
			if cursor.hasSelection() and len(cursor.selection().toPlainText().split("\n")) > 1:
				self.indentSelection()
			else:
				cursor.insertText('\t')
		elif e.key() == Qt.Key.Key_Backtab:  # Shift + Tab
			if cursor.hasSelection() and len(cursor.selection().toPlainText().split("\n")) > 1:
				self.unindentSelection()
		elif e.key() == Qt.Key.Key_Slash and e.modifiers() & Qt.KeyboardModifier.ControlModifier:
			self.toggleCommentSelection()
		elif e.key() == Qt.Key.Key_Return:
			ScriptCursor(self.textCursor()).insertNewLine()
		else:
			super().keyPressEvent(e)

		### UPDATE COMPLETIONS ###
		##########################
		# update proposals
		tc = self.textCursor()
		tc.select(QTextCursor.SelectionType.WordUnderCursor)
		selected_text = tc.selectedText()
		self.completer.setCompletionPrefix(selected_text)

		self.updateCompleterWidget()

	@Slot()
	def updateCompleterWidget(self):
		### Show Hide Completer ###
		###########################
		# get line under cursor
		text_cursor = self.textCursor()
		text_cursor.select(QTextCursor.SelectionType.LineUnderCursor)
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

	def toggleCommentSelection(self):
		cursor = ScriptCursor(self.textCursor())
		cursor.toggleCommentSelection(comment="# ")
		self.setTextCursor(cursor)

	def indentSelection(self):
		cursor = ScriptCursor(self.textCursor())
		cursor.indentSelection()
		self.setTextCursor(cursor)

	def unindentSelection(self):
		cursor = ScriptCursor(self.textCursor())
		cursor.unindentSelection()
		self.setTextCursor(cursor)

	def insertCompletion(self, completion:str):
		tc = self.textCursor()
		tc.select(QTextCursor.SelectionType.WordUnderCursor)
		tc.insertText(completion)

if __name__ == "__main__":
	import sys
	from textwrap import dedent
	from WhitespaceHighlighter import WhitespaceHighlighter

	app = QApplication(sys.argv)
	script_edit = ScriptEdit()


	
	script_edit.setPlainText(dedent("""\
	def hello_world():
		print("Hello, World!")
		# This is a comment
		x = 42
		return x
		
	"""))

	script_edit.insertErrorMessage(2, "placeholder error message at line 2")

	# show app
	script_edit.show()
	sys.exit(app.exec())
