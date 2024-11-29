from textwrap import dedent
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from typing import *
import jedi
from traitlets.utils import text  # Import the Jedi library

from pylive.QtScriptEditor.components.textedit_completer import TextEditCompleter


class JediCompleter(TextEditCompleter):
	def __init__(self, textedit: QTextEdit | QPlainTextEdit):
		super().__init__(textedit)
		self.hint_label = QLineEdit()  # Label for showing argument hints
		self.hint_label.setParent(textedit)
		self.hint_label.setReadOnly(True)
		self.hint_label.setFrame(False)
		# self.hint_label.setStyleSheet("background-color: #FFFFCC; padding: 4px;")
		self.hint_label.hide()  # Initially hidden

	@override
	def requestCompletions(self):
		textedit = cast(QPlainTextEdit, self.widget())
		source_code = textedit.toPlainText()
		cursor = QTextCursor(textedit.textCursor())
		
		# Get the line and column for Jedi
		line = cursor.blockNumber() + 1  # PySide6 line numbers are 0-based
		column = cursor.columnNumber()  # Current position within the line

		cursor.movePosition(QTextCursor.MoveOperation.StartOfLine, QTextCursor.MoveMode.KeepAnchor)
		line_text = cursor.selectedText()
		
		script = jedi.Script(code=source_code, path="<string>")
		if self.showArgumentHints(script, line, column):
			return

		if line_text.split(" ")[-1].isidentifier() or line_text.endswith("."):
			try:
				# Use Jedi to get completions
				script = jedi.Script(code=source_code, path="<string>")
				completions = script.complete(line=line, column=column)
				context = script.get_context(line=line, column=column)
				script.infer(line=line, column=column)
				script.help()

				# Update proposals in the model
				string_list_model = cast(QStringListModel, self.model())
				string_list_model.setStringList([completion.name for completion in completions])

				# Show function signature hints if inside a function call
				

			except Exception as e:
				print(f"Error in requestCompletions: {e}")
				string_list_model = cast(QStringListModel, self.model())
				string_list_model.setStringList([])
				self.hint_label.hide()

	def showArgumentHints(self, script: jedi.Script, line: int, column: int)->bool:
		try:
			call_signatures = script.get_signatures(line=line, column=column)
			if call_signatures:
				# Jedi returns a list of signatures; we'll use the first one
				signature = call_signatures[0]
				func_name = signature.name
				params = ", ".join([f"{param.name}" for param in signature.params])

				# Format and display the hint
				hint_text = f"{func_name}({params})"
				self.hint_label.setText(hint_text)

				# Position the hint near the cursor
				cursor_rect = self.widget().cursorRect()
				global_pos = self.widget().mapToGlobal(cursor_rect.bottomLeft())
				self.hint_label.move(global_pos)
				self.hint_label.adjustSize()
				self.hint_label.show()
				return True
			else:
				self.hint_label.hide()
				return False
		except Exception as e:
			print(f"Error in showArgumentHints: {e}")
			self.hint_label.hide()
			return False

	@override
	def insertCompletion(self, completion):
		"""
		Inserts the selected completion into the text at the cursor position.
		"""
		textedit = cast(QPlainTextEdit, self.widget())	
		tc = textedit.textCursor()
		tc.select(QTextCursor.SelectionType.WordUnderCursor)
		extra = len(completion) - len(tc.selectedText())
		tc.movePosition(QTextCursor.MoveOperation.Left)
		tc.movePosition(QTextCursor.MoveOperation.EndOfWord)
		tc.insertText(completion[-extra:])
		textedit.setTextCursor(tc)


if __name__ == "__main__":
	def hello(x:int):
		pass

	# Create app
	app = QApplication([])

	window = QWidget()
	mainLayout = QHBoxLayout()
	window.setLayout(mainLayout)

	# Create completing editor
	editor = QTextEdit()
	editor.setTabStopDistance(editor.fontMetrics().horizontalAdvance(' ')*4)
	mainLayout.addWidget(editor)
	completer = JediCompleter(editor)
	editor.setWindowTitle("QTextEdit with a non-blocking Jedi Assist Completer")
	editor.resize(800, 800)

	editor.setPlainText(dedent("""\
	class Dog:
		def __init__(self, name, height=1):
			self.name = name
			self.height = height

	mydog = Dog("buksi")
	"""))

	# COMPLETER INFO
	label = QTextEdit()
	label.setReadOnly(True)
	label.setText("jedi info at x,y")
	mainLayout.addWidget(label)

	def update_completion_info():
		source_code = editor.toPlainText()
		cursor = editor.textCursor()
		line = cursor.blockNumber() + 1  # PySide6 line numbers are 0-based
		column = cursor.columnNumber()  # Current position within the line
		script = jedi.Script(code=source_code, path="<string>")
		# completions = script.complete(line=line, column=column)
		context = script.get_context(line=line, column=column)
		signatures = script.get_signatures(line=line, column=column)
		the_help = script.help(line=line, column=column)
		infer = script.infer(line=line, column=column)


		label.setText(dedent(f"""\
		Jedi info at {line} {column}
		
		help: {the_help}
		context: {context}
		signatures: {signatures}
		infer: {infer}
		"""))


	editor.cursorPositionChanged.connect(lambda: update_completion_info())

	# Placeholder
	words = [completer.model().index(row, 0).data() for row in range(completer.model().rowCount())]
	editor.setPlaceholderText("Start typing...\n\neg.: " + ", ".join(words))

	# Show window
	window.show()

	# Run app
	app.exec()
