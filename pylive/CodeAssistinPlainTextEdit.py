from typing import *

import sys
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

import rope
from QRopeAssistStringModel import QRopeAssistStringModel


class CodeAssistingPlainTextEdit(QPlainTextEdit):
	def __init__(self, parent=None):
		super().__init__(parent=parent)
		# setup window
		self.setWindowTitle("CodeAssistingPlainTextEdit")
		self.setTabChangesFocus(False)
		self.setWordWrapMode(QTextOption.WrapMode.NoWrap)
		self.resize(850,850)

		# setup textedit
		option = QTextOption()
		# option.setFlags(QTextOption.ShowTabsAndSpaces | QTextOption.ShowLineAndParagraphSeparators)
		self.document().setDefaultTextOption(option)
		self.setFont(QFont("Monospace", 14))
		self.font().setStyleHint(QFont.StyleHint.TypeWriter);
		self.setTabStopDistance(QFontMetricsF(self.font()).horizontalAdvance(' ') * 4)

		# setup completer
		self.rope_project = rope.base.project.Project('.')
		self.proposals_model = QRopeAssistStringModel(self.rope_project)

		self.completer = QCompleter()
		self.completer.setWidget(self)
		self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
		self.completer.activated.connect(self.insert_completion)
		self.completer.setModel(self.proposals_model)

	def keyPressEvent(self, e: QKeyEvent) -> None:
		editor = self
		completer = self.completer

		# If completer popup is open. Give it exclusive use of specific keys
		if completer.popup().isVisible() and e.key() in [
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

		# Update proposals
		self.proposals_model.updateProposals(editor.document().toPlainText(), self.textCursor().position())

		# Show Hide Completer
		if self.proposals_model.stringList():
			popup = completer.popup()
			popup.setCurrentIndex(completer.completionModel().index(0, 0)) # autoselect first proposal

			# show completer under textCursor
			cr = editor.cursorRect()
			cr.setWidth(popup.sizeHintForColumn(0) +
						popup.verticalScrollBar().sizeHint().width())
			completer.complete(cr)
		else:
			completer.popup().hide()

	@Slot()
	def insert_completion(self, completion):
		"""Callback invoked by pressing Tab/Enter in the completion popup
		tail: The text that will be inserted after the selected completion.
		"""
		textCursor = self.textCursor()
		starting_offset = self.proposals_model.starting_offset(editor.document().toPlainText(), textCursor.position())
		textCursor.setPosition(starting_offset, QTextCursor.MoveMode.KeepAnchor)
		textCursor.insertText(completion) 

if __name__ == "__main__":
	app = QApplication(sys.argv)

	# Create the editor and completer
	editor = CodeAssistingPlainTextEdit()
	editor.setWindowTitle("Python Code Editor with Rope Completion (PySide6)")

	editor.show()
	sys.exit(app.exec())
