
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
		""" Font """
		font = self.font()
		font.setFamilies(["monospace", "Operator Mono Book"])
		font.setPointSize(10)
		font.setWeight(QFont.Weight.Medium)
		font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
		self.setFont(font)

		""" Syntax Highlighter """
		options = QTextOption()
		options.setFlags(QTextOption.Flag.ShowTabsAndSpaces)
		self.document().setDefaultTextOption(options)
		self.highlighter = PygmentsSyntaxHighlighter(self.document())

		### TextEdit Behaviour ###
		self.setWordWrapMode(QTextOption.WrapMode.NoWrap)
		self.setTabChangesFocus(False)
		self.setTabStopDistance(QFontMetricsF(self.font()).horizontalAdvance(' ') * 4)

		""" Autocomplete """
		self.rope_project = rope.base.project.Project('.')
		self.completer = RopeCompleter(self, self.rope_project)

		""" Setup Textedit """
		self.setWindowTitle("ScriptTextEdit")
		width = QFontMetrics(font).horizontalAdvance('O') * 70
		self.resize(width, int(width*4/3))

		""" edit numbers """
		self.number_editor = TextEditNumberEditor(self)

		""" script editor behaviour """
		self.installEventFilter(self)

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
					cursor.insertText('\t')
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
				cursor.insertNewLine()
				return True

		return super().eventFilter(o, e)


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

	
	window = QWidget()
	mainLayout = QVBoxLayout()
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
