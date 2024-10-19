### ScripEditor.py ###
# This is a drop-in replacement for QPlainText, with autoindent, 
# sytax highlighter and an autocomplete for python.
######################

from typing import *

from datetime import date
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from SimplePythonHighlighter import SimplePythonHighlighter

import rope.base.project
from rope.contrib import codeassist

import traceback
class TracebackStackWidget(QLabel):
	def __init__(self, parent=None):
		super().__init__(parent=parent)
		self.setStyleSheet("""QLabel{
			padding: 4px;
			margin-left: 10px;
			border-radius: 3px;
			background: darkred;
			color: white;
		}""")
		# self.setStyleSheet("background: darkgray; color: red;")
		# self.set

		self.setAutoFillBackground(True);
		# self.setPalette(sample_palette);
		# self.setStyleSheet("background: rgba(255,0,0,160); color: red;")
		self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

	def setTextFromTracebackStackSummary(self, summary: traceback.StackSummary):
		raise NotImplementedError

	def setTextFromException(self, exception):
		traceback_text = "".join(traceback.format_exception(exception))
		self.setText(traceback_text)

class TracebackFrameWidget(QLabel):
	def __init__(self, parent=None):
		super().__init__(parent=parent)
		self.setStyleSheet("""QLabel{
			padding: 0px;
			margin-left: 10px;
			border-radius: 3px;
			background: rgba(255,0,0,52);
			color: white;
		}""")
		self.setAutoFillBackground(True);
		self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

class InlineWidget(QLabel):
	def __init__(self, parent=None):
		super().__init__(parent=parent)
		self.setStyleSheet("""QLabel{
			padding: 0px;
			margin-left: 10px;
			border-radius: 3px;
			background: rgba(255,0,0,52);
			color: white;
		}""")
		self.setAutoFillBackground(True);
		self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

	def setTextPosition(self, pos:int):
		pass


class QScriptEditor(QPlainTextEdit):
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
		self.highlighter = SimplePythonHighlighter(self.document())

		# setup completer
		self.rope_project = rope.base.project.Project('.')
		self.completions = QStringListModel(self)
		self.completions.setStringList([])

		self.completer = QCompleter(self.completions)
		self.completer.setWidget(self)
		self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
		self.completer.activated.connect(self.insert_completion)

		self.error_labels = []


	def update_error_labels(self, errors:List[Tuple[int, str]]=[]):
		print("update error labels", datetime.now())
		for lbl in self.error_labels:
			try:
				self.error_labels.remove(lbl)
				lbl.deleteLater()
			except Exception as err:
				print(err)

		for lineno, msg in errors:
			cursor_line = self.textCursor().blockNumber()+1
			if cursor_line == lineno:
				break
			block = self.document().findBlockByLineNumber(lineno-1)
			rect = self.blockBoundingGeometry(block)
			text_without_tabs = block.text().replace("\t", "")
			tabs_count = len(block.text()) - len(text_without_tabs)
			block_text_width = QFontMetrics(self.font()).horizontalAdvance(text_without_tabs)
			block_text_width+=tabs_count*self.tabStopDistance()
			error_label = Inline(parent=self)
			error_label.setTextPosition()
			error_label.move(int(block_text_width), int(rect.top()))
			error_label.setText(msg)
			error_label.show()
			self.error_labels.append(error_label)

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

		### Autoindent ###
		if e.key() == Qt.Key_Return:
			# get the current line
			lineno = self.textCursor().blockNumber()
			line_text = self.document().findBlockByLineNumber(lineno).text()

			# calc current indentations
			indendation = len(line_text) - len(line_text.lstrip(' \t'))

			# run original event
			self.blockSignals(True)
			super().keyPressEvent(e)
			self.blockSignals(False)
			# and indent as the previous line
			if line_text.endswith(":"):
				self.insertPlainText("\t"*(indendation+1))
			elif indendation>0: # if indentation is 0, isnertinh no characters will not emit textChanged signal.
				self.insertPlainText("\t"*indendation)
			else:
				self.textChanged.emit()

		else:
			super().keyPressEvent(e)

		### Insert autocomplete ###
		# print("text:", e.text())
		# get line text under cursor
		textCursor = self.textCursor()
		textCursor.select(QTextCursor.LineUnderCursor)
		lineUnderCursor = textCursor.selectedText()

		textCursor.position()

		if lineUnderCursor.strip() and self.document().characterCount() != old_len:
			try:
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
			except Exception as err:
				print(err)
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
	import random
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
	# @editor.textChanged.connect
	# def textChanged():
	# 	print("text changed", datetime.now())
	editor.show()
	@editor.textChanged.connect
	def update_error_labels():
		lineno = random.randint(1,len(editor.toPlainText().split("\n")))
		editor.update_error_labels([(lineno, f"bad line {lineno}")])
	# print(f"{editor.toPlainText()}")
	sys.exit(app.exec())
