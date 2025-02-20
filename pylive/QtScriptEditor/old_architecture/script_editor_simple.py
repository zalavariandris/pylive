from typing import *

from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *

from pylive.QtScriptEditor.components.pygments_syntax_highlighter import PygmentsSyntaxHighlighter
from pylive.QtScriptEditor.components.textedit_number_editor import TextEditNumberEditor
from pylive.QtScriptEditor.old_architecture.KeywordsCompleter_OLD import KeywordsCompleter
import rope.base.project
from pylive.QtScriptEditor.components.script_cursor import ScriptCursor


class LineNumberArea(QWidget):
	def __init__(self, codeEditor: 'ScriptEdit') -> None:
		super().__init__(codeEditor)
		self.codeEditor = codeEditor


	def paintEvent(self, event:QPaintEvent):
		self.codeEditor.lineNumberAreaPaintEvent(event)


class ScriptEdit(QPlainTextEdit):
	def __init__(self, parent=None):
		super().__init__(parent)
		""" Setup Textedit """
		######################
		self.setupTextEdit()
		self.highlighter = PygmentsSyntaxHighlighter(self.document())

		""" Autocomplete """
		completer = KeywordsCompleter()
		self.setCompleter(completer)

		""" Inline Notifications """
		self.setupInlineNotifications()
		self.number_editor = TextEditNumberEditor(self)

		""" Line numbers """
		self.lineNumberArea = LineNumberArea(self)
		def onBlockCountChanged(newBlockCount:int):
			self.updateLineNumberAreaWidth(newBlockCount)
		self.blockCountChanged.connect(onBlockCountChanged)

		def onUpdateRequest(rect:QRect, dy:int):
			if dy:
				self.lineNumberArea.scroll(0, dy)
			else:
				self.lineNumberArea.update(
					0, 
					rect.y(), 
					self.lineNumberArea.width(), 
					rect.height()
				)
			if rect.contains(self.viewport().rect()):
				self.updateLineNumberAreaWidth(0)

		self.updateRequest.connect(onUpdateRequest)
		self.updateLineNumberAreaWidth(0)

		self.installEventFilter(self)

	def setupTextEdit(self):
		self.setWindowTitle("ScriptTextEdit")
		self.setWordWrapMode(QTextOption.WrapMode.NoWrap)
		self.setTabChangesFocus(False)
		self.setTabStopDistance(QFontMetricsF(self.font()).horizontalAdvance(' ') * 4)

		# set a monospace font
		font = self.font()

		font.setFamilies(["monospace", "Operator Mono Book"])
		font.setPointSize(10)
		font.setWeight(QFont.Weight.Medium)
		font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
		self.setFont(font)
		
		# # show whitespace
		# options = QTextOption()
		# options.setFlags(QTextOption.ShowTabsAndSpaces)
		# self.document().setDefaultTextOption(options)

		# resize window
		width = QFontMetrics(font).horizontalAdvance('O') * 70
		self.resize(width, int(width*4/3))

	def setFont(self, font:QFont):
		super().setFont(font)
		# set tab width to 4 spaces
		self.setTabStopDistance(QFontMetricsF(self.font()).horizontalAdvance(' ') * 4)
		
	### Completer Support ###
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
		print("toggle toggleCompleterVisibility")
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

	### Inline Notifications ###
	def setupInlineNotifications(self):
		""" Setup error widgets """
		# error model
		self.notifications_model = QStandardItemModel()
		self.notifications_labels = []

		# error view
		self.notifications_model.rowsInserted.connect(self.handleNotificationsInserted)
		self.notifications_model.rowsRemoved.connect(self.handleNotificationsRemoved)

	def insertNotification(self, lineno:int, message:str, type:str="info"):
		import html
		self.notifications_model.appendRow([
			QStandardItem(message), 
			QStandardItem(type), 
			QStandardItem(str(lineno))
		])

	def showException(self, e:Exception, prefix="", postfix=""):
		import traceback
		if isinstance(e, SyntaxError):
			text = " ".join([prefix, str(e.msg), postfix])
			if e.lineno:
				text = str(e.msg)
				if hasattr(e, 'offset'):
					text+= f" (offset: {e.offset})"
				if hasattr(e, 'start'):
					text+= f" (start: {e.start})"
				self.insertNotification(e.lineno, text)
		else:
			tb = traceback.TracebackException.from_exception(e)
			last_frame = tb.stack[-1]
			if last_frame.lineno:
				self.insertNotification(last_frame.lineno, str(e))

			formatted_traceback = ''.join(tb.format())
			text = " ".join([prefix, formatted_traceback, postfix])
			if hasattr(e, 'offset'):
				text+= f" (offset: {e.offset})"
			if hasattr(e, 'start'):
				text+= f" (start: {e.start})"

	def clearNotifications(self):
		self.notifications_model.clear()

	@Slot()
	def handleNotificationsInserted(self, parent: QModelIndex, first: int, last:int):
		# Iterate over each row in the range of inserted rows
		for row in range(first, last + 1):
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
			notification_label = QLabel(parent=self.viewport())
			notification_label.setText(f"{message}")  # Use the retrieved message
			notification_label.setFont(self.font())
			notification_label.setAlignment(Qt.AlignmentFlag.AlignBaseline)

			# error_palette = QPalette()
			# error_palette.setColor(QPalette.ColorRole.Window, QColor(200,20,20,180))
			# error_palette.setColor(QPalette.ColorRole.WindowText, error_palette.color(QPalette.ColorRole.PlaceholderText))

			notification_label.setAutoFillBackground(True)
			# notification_label.setPalette(error_palette)
			notification_label.setStyleSheet("""QLabel{
				padding: 0 2;
				border-radius: 3;
				background-color:rgba(200,0,0,100);
				maring: 0;
				color: rgba(255,255,255,220);
			}""")
			notification_label.setWindowOpacity(0.5)

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
			# Check if the row index is within the bounds of the notifications_labels list
			if row < len(self.notifications_labels):
				notification_label = self.notifications_labels[row]
				notification_label.deleteLater()  # Safely remove the label from the GUI
				
				# Remove the label from the list of notifications
				del self.notifications_labels[row]

	### Event handling ###
	def keyPressEvent(self, e: QKeyEvent) -> None:
		### Completer ###
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

		### Script Text Editing features ### 
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

	### Script Cursor support ###
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

	### Line Numbers ###
	def lineNumberAreaPaintEvent(self, event:QPaintEvent):
		painter = QPainter(self.lineNumberArea);
		# painter.fillRect(event.rect(), Qt.lightGray)
		palette = self.palette()
		text_color = palette.color(QPalette.ColorRole.PlaceholderText)

		block = self.firstVisibleBlock()
		block_number = block.blockNumber()
		top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
		bottom = top + round(self.blockBoundingRect(block).height())

		while block.isValid() and top <= event.rect().bottom():
			if block.isVisible() and bottom >= event.rect().top():
				number = str(block_number + 1)
				painter.setPen(text_color)
				painter.drawText(0, top, self.lineNumberArea.width(), self.fontMetrics().height(),
								 Qt.AlignRight, number)
			
			block = block.next()
			top = bottom
			bottom = top + round(self.blockBoundingRect(block).height())
			block_number += 1

	def lineNumberAreaWidth(self):
		digits = 1;
		line_count = max(1, self.blockCount())
		while line_count >= 10:
			line_count /= 10
			digits+=1


		space = 3 + self.fontMetrics().horizontalAdvance('9') * digits;

		return space;

	@Slot(int)
	def updateLineNumberAreaWidth(self, newBlockCount:int):
		self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

	def resizeEvent(self, e: QResizeEvent) -> None:
		super().resizeEvent(e)
		cr = self.contentsRect()
		self.lineNumberArea.setGeometry(QRect(
			cr.left(), 
			cr.top(), 
			self.lineNumberAreaWidth(), 
			cr.height())
		)

if __name__ == "__main__":
	import sys
	from textwrap import dedent
	# from components.WhitespaceHighlighter import WhitespaceHighlighter
	import ast

	app = QApplication(sys.argv)
	script_edit = ScriptEdit()

	script_edit.setPlainText(dedent("""\
	def hello_world():
		print("Hello, World!"
		# This is a comment
		x = 42
		return x

	1
	2
	3
	4
	5
	6
	7
	9
	10
	11
	12
	13
	14
	"""))

	def updateNotifications():
		script_edit.clearNotifications()
		try:
			source = script_edit.toPlainText()
			ast.parse(source)
		except SyntaxError as e:
			script_edit.showException(e)
		except Exception as e:
			script_edit.showException(e)

	script_edit.textChanged.connect(updateNotifications)

	# show app
	script_edit.show()
	updateNotifications()

	sys.exit(app.exec())
