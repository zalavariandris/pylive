
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from typing import *

# components
from pylive.QtScriptEditor.components.pygments_syntax_highlighter import PygmentsSyntaxHighlighter
from pylive.QtScriptEditor.components.simple_python_highlighter import SimplePythonHighlighter
from pylive.QtScriptEditor.components.script_cursor import ScriptCursor
from pylive.QtScriptEditor.components.textedit_number_editor import TextEditNumberEditor

# code assist
import rope.base.project
from rope.contrib import codeassist
from pylive.QtScriptEditor.components.rope_completer_for_textedit import RopeCompleter


class ScriptEdit(QPlainTextEdit):
	def __init__(self, parent=None):
		super().__init__(parent)
		### Font###
		font = self.font()
		font.setFamilies(["monospace", "Operator Mono Book"])
		font.setPointSize(10)
		font.setWeight(QFont.Weight.Medium)
		font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
		self.setFont(font)

		### TextEdit Behaviour ###
		self.setWordWrapMode(QTextOption.WrapMode.NoWrap)
		self.setTabChangesFocus(False)
		self._indent_using_spaces = True
		self._tabsize = 4
		self.setTabSize(4)
		
		### script typing behaviour ###
		self.installEventFilter(self)

		""" Syntax Highlighter """
		options = self.document().defaultTextOption()
		options.setFlags(QTextOption.Flag.ShowTabsAndSpaces)
		self.document().setDefaultTextOption(options)
		self.highlighter = PygmentsSyntaxHighlighter(self.document())

		### Autocomplete ###
		self.rope_project = rope.base.project.Project('.')
		self.completer = RopeCompleter(self, self.rope_project)

		### Setup Textedit ###
		self.setWindowTitle("ScriptTextEdit")
		width = QFontMetrics(font).horizontalAdvance('O') * 70
		self.resize(width, int(width*4/3))

		### edit numbers###
		self.number_editor = TextEditNumberEditor(self)

		### Notification sysyem ###
		self.setupInlineNotifications()

	def indentUsingSpaces(self):
		return self._indent_using_spaces

	def setIndentUsingSpaces(self, indentUsingSpaces:bool):
		self._indent_using_spaces = indentUsingSpaces

	def tabSize(self):
		return self._tabsize

	def setTabSize(self, tabsize:int):
		print("setTabSize", tabsize)
		self._tabsize = tabsize
		self.setTabStopDistance(
			self.fontMetrics().horizontalAdvance(' ') * tabsize
		)
	
	def convertIndentationToTabs(self):
		text = self.toPlainText()
		text = text.replace(" "*self.tabSize(), "\t")
		self.setPlainText(text)

	def convertIndentationToSpaces(self):
		text = self.toPlainText()
		text = text.replace("\t", " "*self.tabSize())
		self.setPlainText(text)

	def toggleComment(self):
		cursor = ScriptCursor(self.textCursor())
		cursor.toggleCommentSelection(comment="# ")
		self.setTextCursor(cursor)

	def indent(self):
		cursor = ScriptCursor(self.textCursor())
		cursor.indentSelection()
		self.setTextCursor(cursor)

	def unindent(self):
		cursor = ScriptCursor(self.textCursor())
		cursor.unindentSelection()
		self.setTextCursor(cursor)
		
	"""Script Cursor"""
	def eventFilter(self, o: QObject, e: QEvent) -> bool: #type: ignore
		if e.type() == QEvent.Type.KeyPress:
			cursor = ScriptCursor(self.textCursor())
			e = cast(QKeyEvent, e)
			editor = self
			if e.key() == Qt.Key.Key_Tab:
				if cursor.hasSelection() and len(cursor.selection().toPlainText().split("\n")) > 1:
					cursor.indentSelection()
					editor.setTextCursor(cursor)
					return True

				else:
					if self.indentUsingSpaces():
						cursor.insertText(" "*self.tabSize())
					else:
						cursor.insertText("\t")
					return True

			elif e.key() == Qt.Key.Key_Backtab:  # Shift + Tab
				if cursor.hasSelection() and len(cursor.selection().toPlainText().split("\n")) > 1:
					cursor.unindentSelection()
					editor.setTextCursor(cursor)
					return True

			elif e.key() == Qt.Key.Key_Slash and e.modifiers() & Qt.KeyboardModifier.ControlModifier:
				cursor.toggleCommentSelection(comment="# ")
				editor.setTextCursor(cursor)
				return True

			elif e.key() == Qt.Key.Key_Return:
				cursor.insertNewLine(indentation=" "*self.tabSize() if self.indentUsingSpaces() else "\t")
				return True

		return super().eventFilter(o, e)

	### Inline Notifications ###
	def setupInlineNotifications(self):
		""" Setup error widgets """
		# error model
		self.notifications_model = QStandardItemModel()
		self.notifications_labels = []

		# error view
		self.notifications_model.rowsInserted.connect(self.handleNotificationsInserted)
		self.notifications_model.rowsRemoved.connect(self.handleNotificationsRemoved)

	def insertNotification(self, lineno:int, message:str, level:Literal["info", "warning", "error"]="info"):
		import html
		self.notifications_model.appendRow([
			QStandardItem(message), 
			QStandardItem(level), 
			QStandardItem(str(lineno))
		])

	def showException(self, e:Exception, prefix="", postfix=""):
		import traceback
		if isinstance(e, SyntaxError):
			text = " ".join([prefix, str(e.msg), postfix])
			if e.lineno:
				text = str(e.msg)
				if offset:=getattr(e, 'offset', None):
					text+= f" (offset: {offset})"
				if start:=getattr(e, 'start', None):
					text+= f" (start: {start})"
				self.insertNotification(e.lineno, text)
		else:
			tb = traceback.TracebackException.from_exception(e)
			last_frame = tb.stack[-1]
			if last_frame.lineno:
				self.insertNotification(last_frame.lineno, str(e), level="error")

			formatted_traceback = ''.join(tb.format())
			text = " ".join([prefix, formatted_traceback, postfix])
			if offset:=getattr(e, 'offset', None):
				text+= f" (offset: {offset})"
			if start:=getattr(e, 'start', None):
				text+= f" (start: {start})"

	def clearNotifications(self):
		self.notifications_model.clear()

	def handleNotificationsInserted(self, parent: QModelIndex, first: int, last:int):
		# Iterate over each row in the range of inserted rows
		for row in range(first, last + 1):
			# Retrieve the notification data
			index = self.notifications_model.index(row, 0)
			message = index.siblingAtColumn(0).data()
			level = index.siblingAtColumn(1).data()
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
			match level:
				case "info":
					level_color = 'rgba(0,0,200,100)'
				case "warning":
					level_color = 'rgba(200,200,0,100)'
				case "error":
					level_color = 'rgba(200,0,0,100)'
				case _:
					level_color = 'rgba(0,0,200,100)'
	
			notification_label.setStyleSheet("""\
				padding: 0 2;
				border-radius: 3;
				background-color: {level_color};
				margin: 0;
				color: rgba(255,255,255,220);
			""".format(level_color=level_color))
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


def main():
	from pylive.thread_pool_tracker import ThreadPoolCounterWidget
	app = QApplication([])
	editor = ScriptEdit()
	from textwrap import dedent
	editor.setPlainText(dedent("""\
	def hello_world():
		print("Hello, World!")
		# This is a comment
		x = 42
		return x
	"""))

	def validate_script(script:str):
		import ast
		try:
			editor.clearNotifications()
			ast.parse(script)
		except SyntaxError as e:
			editor.showException(e)
		except Exception as e:
			editor.showException(e)

	editor.textChanged.connect(lambda: validate_script(editor.toPlainText()))

	window = QWidget()
	menuBar = QMenuBar(window)	
	def create_action(label:str, callback:Callable|None=None):
		action = QAction(label)
		if callback:
			action.triggered.connect(lambda: callback())
		else:
			action.setEnabled(False)
		return action

	def create_menu(label:str, actions:List[QAction]):
		menu = QMenu(label)
		for action in actions:
			action.setParent(menu)
			menu.addAction(action)
		return menu

	edit_menu = create_menu("Edit", [
		create_action("Toggle Comment", 
		lambda: editor.toggleComment()),
		create_action("Indent", 
		lambda: editor.indent()),
		create_action("Unindent", 
		lambda: editor.unindent()),
	])
	menuBar.addMenu(edit_menu)

	indentation_menu = create_menu("Indentation", 
		[
			create_action(
				"Convert Indentation to Tabs", 
				lambda: editor.convertIndentationToTabs()
			),
			create_action(
				"Convert Indentation to Spaces", 
				lambda: editor.convertIndentationToSpaces()
			),
			create_action("Guess from text (not implemented yet)")
		]+[create_action(
			f"TabWidth: {i}",
			lambda i=i: editor.setTabSize(i)
		) for i in range(1,9)]
	)
	menuBar.addMenu(indentation_menu)

	
	mainLayout = QVBoxLayout()
	mainLayout.setMenuBar(menuBar)
	mainLayout.setContentsMargins(0,0,0,0)
	window.setLayout(mainLayout)
	mainLayout.addWidget(editor)
	mainLayout.addWidget(ThreadPoolCounterWidget())
	window.setWindowTitle("QTextEdit with Non-Blocking Rope Assist Completer")
	window.resize(600, 400)
	window.show()

	app.exec()


if __name__ == "__main__":
	main()