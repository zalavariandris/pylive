from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *

def indent_text(text, indent="    "):
	lines = text.split("\n")
	indented_lines = []
	for i, line in enumerate(lines):
		indented_lines.append(indent+line)

	return "\n".join(indented_lines)


def unindent_text(text, indent="    "):
	lines = text.split("\n")
	unindented_lines = []
	for i, line in enumerate(lines):
		if line.startswith(indent):
			unindented_lines.append(line[len(indent):])
		else:
			unindented_lines.append(line)
	return "\n".join(unindented_lines)

from textwrap import dedent
def toggle_comment(text, comment="# "):
	lines = dedent(text).split("\n")
	common_indent = text.split("\n")[0][:-len(lines[0])]

	#
	
	if all(line.startswith(comment) for line in lines):
		uncommented_lines = []
		for i, line in enumerate(lines):
			uncommented_lines.append(common_indent + line[len(comment):])
		return "\n".join(uncommented_lines)
	else:
		commented_lines = []
		for i, line in enumerate(lines):
			commented_lines.append(common_indent + comment + line)
		return "\n".join(commented_lines)


class ScriptCursor(QTextCursor):
	def __init__(self, source:None|QTextDocument|QTextFrame|QTextBlock|QTextCursor=None):
		if source:
			super().__init__(source)
		else:
			super().__init__()

	def toggleCommentSelection(self, comment="# "):
		print("toggle comment selection")
		atBlockStart = self.atBlockStart()
		anchor = self.anchor()
		position = self.position()
		start = self.selectionStart()
		end = self.selectionEnd()

		if self.hasSelection() and len(self.selection().toPlainText().split("\n")) > 1:
			self.beginEditBlock()

			# extend selection to lines
			self.setPosition(start, QTextCursor.MoveMode.MoveAnchor)
			self.movePosition(QTextCursor.MoveOperation.StartOfLine, QTextCursor.MoveMode.MoveAnchor)
			self.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
			self.movePosition(QTextCursor.MoveOperation.EndOfLine, QTextCursor.MoveMode.KeepAnchor)
			lines_start = self.selectionStart()
			lines_end = self.selectionEnd()
			startOffset = start - lines_start
			endOffset = end - lines_end

			# Replace the selected text with the indented text
			text = self.selection().toPlainText()
			

			commented_text = toggle_comment(text, comment="# ")
			self.insertText(commented_text)

			# Calculate the new start and end positions after insert
			if len(commented_text) > len(text):
				new_start = lines_start + len(comment) + startOffset if not atBlockStart else lines_start
				new_end = lines_start + len(commented_text) + endOffset
			else:
				new_start = lines_start - len(text.split("\n")[0]) + len(commented_text.split("\n")[0]) + startOffset if not atBlockStart else lines_start
				new_end = lines_start + len(commented_text) + endOffset

			if anchor<position:
				self.setPosition(new_start, QTextCursor.MoveMode.MoveAnchor)
				self.setPosition(new_end, QTextCursor.MoveMode.KeepAnchor)
			else:
				self.setPosition(new_end, QTextCursor.MoveMode.MoveAnchor)
				self.setPosition(new_start, QTextCursor.MoveMode.KeepAnchor)
			self.endEditBlock()

	def indentSelection(self, indentation="\t"):
		atBlockStart = self.atBlockStart()
		anchor = self.anchor()
		position = self.position()
		start = self.selectionStart()
		end = self.selectionEnd()

		if self.hasSelection() and len(self.selection().toPlainText().split("\n")) > 1:
			self.beginEditBlock()

			# extend selection to lines
			self.setPosition(start, QTextCursor.MoveMode.MoveAnchor)
			self.movePosition(QTextCursor.MoveOperation.StartOfLine, QTextCursor.MoveMode.MoveAnchor)
			self.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
			self.movePosition(QTextCursor.MoveOperation.EndOfLine, QTextCursor.MoveMode.KeepAnchor)
			lines_start = self.selectionStart()
			lines_end = self.selectionEnd()
			startOffset = start - lines_start
			endOffset = end - lines_end

			# Replace the selected text with the indented text
			text = self.selection().toPlainText()
			

			indented_text = indent_text(text)
			self.insertText(indented_text)

			# Calculate the new start and end positions after indentation
			new_start = lines_start + len(indentation) + startOffset if not atBlockStart else lines_start  # +4 for added indentation
			new_end = lines_start + len(indented_text) + endOffset

			if anchor<position:
				self.setPosition(new_start, QTextCursor.MoveMode.MoveAnchor)
				self.setPosition(new_end, QTextCursor.MoveMode.KeepAnchor)
			else:
				self.setPosition(new_end, QTextCursor.MoveMode.MoveAnchor)
				self.setPosition(new_start, QTextCursor.MoveMode.KeepAnchor)
			self.endEditBlock()
			# textEdit.setTextCursor(cursor)  # Set the cursor to the modified one

	def unindentSelection(self, indentation="\t"):
		atBlockStart = self.atBlockStart()
		anchor = self.anchor()
		position = self.position()
		start = self.selectionStart()
		end = self.selectionEnd()

		if self.hasSelection() and len(self.selection().toPlainText().split("\n")) > 1:
			self.beginEditBlock()

			# extend selection to lines
			self.setPosition(start, QTextCursor.MoveMode.MoveAnchor)
			self.movePosition(QTextCursor.MoveOperation.StartOfLine, QTextCursor.MoveMode.MoveAnchor)
			self.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
			self.movePosition(QTextCursor.MoveOperation.EndOfLine, QTextCursor.MoveMode.KeepAnchor)
			lines_start = self.selectionStart()
			lines_end = self.selectionEnd()
			startOffset = start - lines_start
			endOffset = end - lines_end

			# Replace the selected text with the indented text
			text = self.selection().toPlainText()
			lines = text.split("\n")

			unindented_text = unindent_text(text)
			self.insertText(unindented_text)

			# Calculate the new start and end positions after indentation
			new_start = lines_start - len(text.split("\n")[0]) + len(unindented_text.split("\n")[0]) + startOffset if not atBlockStart else lines_start
			new_end = lines_start + len(unindented_text) + endOffset

			if anchor<position:
				self.setPosition(new_start, QTextCursor.MoveMode.MoveAnchor)
				self.setPosition(new_end, QTextCursor.MoveMode.KeepAnchor)
			else:
				self.setPosition(new_end, QTextCursor.MoveMode.MoveAnchor)
				self.setPosition(new_start, QTextCursor.MoveMode.KeepAnchor)
			self.endEditBlock()
			# self.setTextCursor(cursor)  # Set the cursor to the modified one

class IndentablePlainTextEdit(QPlainTextEdit):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.setWindowTitle("IndentablePlainTextEdit")
		self.setTabChangesFocus(False)
		self.setWordWrapMode(QTextOption.WrapMode.NoWrap)
		self.resize(850, 850)

		self.setFont(QFont("Operator Mono", 10))
		self.setTabStopDistance(QFontMetricsF(self.font()).horizontalAdvance(' ') * 4)

		self.indent_spaces = '    '  # Set indent spaces here

	def scriptCursor(self) -> ScriptCursor:
		return ScriptCursor(super().textCursor())

	def keyPressEvent(self, e: QKeyEvent) -> None:
		cursor = self.textCursor()
		if e.key() == Qt.Key_Tab:
			if cursor.hasSelection() and len(cursor.selection().toPlainText().split("\n")) > 1:
				self.indentSelection()
			else:
				cursor.insertText('\t')
		elif e.key() == Qt.Key_Backtab:  # Shift + Tab
			if cursor.hasSelection() and len(cursor.selection().toPlainText().split("\n")) > 1:
				self.unindentSelection()
		elif e.key() == Qt.Key_Slash and e.modifiers() & Qt.ControlModifier:
			self.toggleCommentSelection()
		else:
			super().keyPressEvent(e)

	def textCursor(self) -> QTextCursor:
		 return QTextCursor(super().textCursor())

	def toggleCommentSelection(self):
		cursor = self.scriptCursor()
		cursor.toggleCommentSelection(comment="# ")
		self.setTextCursor(cursor)

	def indentSelection(self):
		cursor = self.scriptCursor()
		cursor.indentSelection()
		self.setTextCursor(cursor)

	def unindentSelection(self):
		cursor = self.scriptCursor()
		cursor.unindentSelection()
		self.setTextCursor(cursor)

if __name__ == "__main__":
	import sys
	import textwrap
	from datetime import datetime
	import random
	app = QApplication(sys.argv)
	window = IndentablePlainTextEdit()

	window.setPlainText(textwrap.dedent("""\
	class Person:
	def __init__(self, name:str):
		self.name = name

	def say(self):
		print(self.name)

	peti = Person()
	"""))
	window.show()
	sys.exit(app.exec())
