from typing import *

from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *

from components.ScriptCursor import ScriptCursor
from components.PygmentsSyntaxHighlighter import PygmentsSyntaxHighlighter

class ScriptEdit(QPlainTextEdit):
	def __init__(self, parent=None):
		super().__init__(parent)
		""" Setup Textedit """
		######################
		self.setupTextEdit()
		self.setupSyntaxHighlighting()
		self.setupAutocomplete()
		self.setupInlineNotifications()

	def setupTextEdit(self):
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

	def setupSyntaxHighlighting(self):
		""" Setup Syntax Highlighting """
		# # Show whitespace characters
		# option = QTextOption(self.document().defaultTextOption())
		# option.setFlags(QTextOption.Flag.ShowTabsAndSpaces)
		# self.document().setDefaultTextOption(option)
		# WhitespaceHighlighter(self.document())
		PygmentsSyntaxHighlighter(self.document())

	def setupAutocomplete(self):
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

		# update completer based on text and cursor position
		self.cursorPositionChanged.connect(self.refreshCompleterPrefix)
		self.textChanged.connect(self.refreshCompleterPrefix)

		self.completer.completionModel().modelReset.connect(self.toggleCompleterVisibility)

	@Slot()
	def insertCompletion(self, completion:str):
		tc = self.textCursor()
		tc.select(QTextCursor.SelectionType.WordUnderCursor)
		tc.insertText(completion)

	@Slot()
	def refreshCompleterPrefix(self):
		tc = self.textCursor()
		tc.select(QTextCursor.SelectionType.WordUnderCursor)
		selected_text = tc.selectedText()

		self.completer.setCompletionPrefix(selected_text)
		# self.updateCompleterWidget()

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

	def setupInlineNotifications(self):
		""" Setup error widgets """
		# error model
		self.notifications_model = QStandardItemModel()
		self.notifications_labels = []

		# error view
		self.notifications_model.rowsInserted.connect(self.handleNotificationsInserted)
		self.notifications_model.rowsRemoved.connect(self.handleNotificationsRemoved)

	def insertNotification(self, lineno:int, message:str, type:str="info"):
		self.notifications_model.appendRow([
			QStandardItem(message), 
			QStandardItem(type), 
			QStandardItem(str(lineno))
		])

	def clearNotifications(self):
		self.notifications_model.clear()

	@Slot()
	def handleNotificationsInserted(self, parent: QModelIndex, first: int, last:int):
		# Iterate over each row in the range of inserted rows
		print("rows inserted", first, last)
		for row in range(first, last + 1):
			print("row:", row)
			# Retrieve the notification data
			index = self.notifications_model.index(row, 0)
			message = index.siblingAtColumn(0).data()
			type = index.siblingAtColumn(1).data()
			lineno = int( index.siblingAtColumn(2).data() )
			
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

			# Get font metrics to align with the text baseline
			font_metrics = QFontMetrics(self.font())
			ascent = font_metrics.ascent()
			descent = font_metrics.descent()

			# Create and position the notification label
			notification_label = QLabel(parent=self)
			notification_label.setText(f"{message}, line: {lineno}")  # Use the retrieved message
			notification_label.setFont(self.font())
			notification_label.setAlignment(Qt.AlignmentFlag.AlignBaseline)

			error_palette = QPalette()
			error_palette.setColor(QPalette.ColorRole.Window, QColor(255,0,0,180))
			error_palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)

			notification_label.setAutoFillBackground(True)
			notification_label.setPalette(error_palette)
			# notification_label.setStyleSheet("""QLabel{
			# 	padding: 0 2;
			# 	border-radius: 3;
			# 	background-color:rgba(200,0,0,200);
			# 	maring: 0;
			# 	color: white;
			# }""")

			# Calculate the x position with a little padding
			notification_x = int(rect.left() + block_text_width+5)
			notification_y = int(rect.bottom() - ascent+1)
			notification_label.move(notification_x, notification_y)  # Adjust x and y position
			notification_label.show()

			# Store the notification label for future reference
			self.notifications_labels.insert(row, notification_label)

	def handleNotificationsRemoved(self, parent: QModelIndex, first: int, last: int):
		
		# Iterate over each row in the range of removed rows in reverse order
		for row in reversed(range(first, last + 1)):  # Go backwards to avoid index shifting		
			print("notifications removed", row)
			# Check if the row index is within the bounds of the notifications_labels list
			if row < len(self.notifications_labels):
				notification_label = self.notifications_labels[row]
				notification_label.deleteLater()  # Safely remove the label from the GUI
				
				# Remove the label from the list of notifications
				del self.notifications_labels[row]

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
		# self.updateCompleterPrefix()


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

if __name__ == "__main__":
	import sys
	from textwrap import dedent
	from components.WhitespaceHighlighter import WhitespaceHighlighter

	app = QApplication(sys.argv)
	script_edit = ScriptEdit()

	script_edit.setPlainText(dedent("""\
	def hello_world():
		print("Hello, World!")
		# This is a comment
		x = 42
		return x
	"""))

	# show app
	script_edit.show()
	script_edit.insertNotification(2, "placeholder error message")
	script_edit.insertNotification(3, "msg 2")
	script_edit.clearNotifications()
	script_edit.insertNotification(5, "new placeholder error message")
	sys.exit(app.exec())
