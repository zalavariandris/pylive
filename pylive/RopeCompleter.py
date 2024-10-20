from typing import *

import sys
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

import rope.base.project
from rope.base import libutils
import rope.base.project
from rope.contrib import codeassist


class CodeCompleter(QCompleter):
	def __init__(self, *args, **kwargs):
		self.completions = QStringListModel()
		self.completions.setStringList([])
		super(CodeCompleter, self).__init__(self.completions)
		# setup rope for autocomplet proposals

class ScriptEditor(QPlainTextEdit):
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
		self.setFont(QFont("Monospace", 14))
		self.font().setStyleHint(QFont.TypeWriter);
		self.setTabStopDistance(QFontMetricsF(self.font()).horizontalAdvance(' ') * 4)

		# setup completer
		self.rope_project = rope.base.project.Project('.')
		

		self.completer = CodeCompleter()
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
				self.completer.model().setStringList([proposal.name for proposal in proposals])
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
	app = QApplication(sys.argv)

	# Create the editor and completer
	editor = ScriptEditor()
	editor.setWindowTitle("Python Code Editor with Rope Completion (PySide6)")

	editor.show()
	sys.exit(app.exec())
