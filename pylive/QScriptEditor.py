### ScripEditor.py ###
# This is a drop-in replacement for QPlainText, with autoindent, 
# sytax highlighter and an autocomplete for python.
######################


from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from PythonSyntaxHighlighter import PythonSyntaxHighlighter

import rope.base.project
from rope.contrib import codeassist

keywords = ["def", "class", "print", "Japan", "Indonesia", "China", "UAE", "America"]

class QScriptEditor(QPlainTextEdit):
	textChanged = Signal()
	def __init__(self, parent=None):
		super().__init__(parent=parent)
		# setup window
		self.setWindowTitle("ScriptEditor")
		self.setTabChangesFocus(False)
		self.setWordWrapMode(QTextOption.WrapMode.NoWrap)
		self.resize(850,850)

		# setup textedit
		option = QTextOption()
		# option.setFlags(QTextOption.ShowTabsAndSpaces | QTextOption.ShowLineAndParagraphSeparators)
		self.document().setDefaultTextOption(option)
		self.setFont(QFont("Operator Mono", 10))
		self.setTabStopDistance(QFontMetricsF(self.font()).horizontalAdvance(' ') * 4)

		# setup highlighter
		self.highlighter = PythonSyntaxHighlighter(self.document())

		# setup completer
		self.rope_project = rope.base.project.Project('.')
		self.completions = QStringListModel(self)
		self.completions.setStringList([])

		self.completer = QCompleter(self.completions, self)
		self.completer.setWidget(self)
		self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
		self.completer.activated.connect(self.insert_completion)

	def keyPressEvent(self, e: QKeyEvent) -> None:
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

		# # Fall back to tabChangesFocus (should be off in QPlainTextEdit props)
		# if e.key() == Qt.Key_Tab:  # type: ignore[attr-defined]
		# 	e.ignore()  # Prevent QPlainTextEdit from entering literal Tab
		# 	return
		# elif e.key() == Qt.Key_Backtab:  # type: ignore[attr-defined]
		# 	e.ignore()  # Prevent QPlainTextEdit from blocking Backtab
		# 	return

		old_len = self.document().characterCount()

		### Audtindent ###
		if e.key() == Qt.Key_Return:
			# get the current line
			lineno = self.textCursor().blockNumber()
			line_text = self.document().findBlockByNumber(lineno).text()

			# calc current indentations
			indendation = len(line_text) - len(line_text.lstrip(' \t'))

			# run original event
			self.blockSignals(True)
			super().keyPressEvent(e)
			self.blockSignals(False)
			# and indent as the previous line
			if line_text.endswith(":"):
				self.insertPlainText("\t"*(indendation+1))
			else:
				self.insertPlainText("\t"*indendation)
		else:
			super().keyPressEvent(e)

		### Insert autocomplete ###
		print("text:", e.text())
		# get line text under cursor
		textCursor = self.textCursor()
		textCursor.select(QTextCursor.LineUnderCursor)
		lineUnderCursor = textCursor.selectedText()

		if lineUnderCursor.strip() and self.document().characterCount() != old_len:
			proposals = codeassist.code_assist(self.rope_project, self.document().toPlainText(), self.textCursor().position())
			proposals = codeassist.sorted_proposals(proposals) # Sorting proposals; for changing the order see pydoc
			# print(proposals)
			self.completions.setStringList([proposal.name for proposal in proposals])
			# Where to insert the completions
			self.starting_offset = codeassist.starting_offset(self.document().toPlainText(), self.textCursor().position())

			if proposals:
				popup = self.completer.popup()
				popup.setCurrentIndex(self.completer.completionModel().index(0, 0))
				cr = self.cursorRect()
				cr.setWidth(popup.sizeHintForColumn(0) +
							popup.verticalScrollBar().sizeHint().width())
				self.completer.complete(cr)
			else:
				self.completer.popup().hide()
		elif self.completer.popup().isVisible():
			self.completer.popup().hide()  # Fix "popup hangs around" bug

	@Slot()
	def insert_completion(self, completion, completion_tail=""):
		"""Callback invoked by pressing Tab/Enter in the completion popup
		tail: The text that will be inserted after the selected completion.
		"""
		textCursor = self.textCursor()
		textCursor.setPosition(self.starting_offset, QTextCursor.KeepAnchor)
		textCursor.insertText(completion + completion_tail) 
		

if __name__ == "__main__":
	import sys
	import textwrap
	from datetime import datetime
	app = QApplication(sys.argv)
	editor = QScriptEditor()

	editor.setPlainText(textwrap.dedent("""\
	class Person:
		def __init__(self, name:str):
			self.name = name

		def say(self):
			print(self.name)

	peti = Person()

	"""))
	@editor.textChanged.connect
	def textChanged():
		print("text changed", datetime.now())
	editor.show()
	print(f"{editor.toPlainText()}")
	sys.exit(app.exec())
