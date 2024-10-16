from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from PythonSyntaxHighlighter import PythonSyntaxHighlighter

keywords = ["def", "class", "print", "Japan", "Indonesia", "China", "UAE", "America"]

keywords

class QScriptEditor(QPlainTextEdit):
	textChanged = Signal()
	def __init__(self, parent=None):
		super().__init__(parent=parent)
		# setup window
		self.setWindowTitle("CodeEditor")

		# setup textedit
		option = QTextOption()
		# option.setFlags(QTextOption.ShowTabsAndSpaces | QTextOption.ShowLineAndParagraphSeparators)
		self.document().setDefaultTextOption(option)
		self.setTabStopDistance(QFontMetricsF(self.font()).horizontalAdvance(' ') * 4)

		# setup highlighter
		self.highlighter = PythonSyntaxHighlighter(self.document())

	def autoindent(self, e: QKeyEvent):
		if e.key() == Qt.Key_Return:
			# get the current line
			lineno = self.textCursor().blockNumber()
			line_text = self.document().findBlockByNumber(lineno).text()

			# calc current indentations
			indendation = len(line_text) - len(line_text.lstrip(' \t'))

			# run original event
			self.blockSignals(True)
			result = super().keyPressEvent(e)
			self.blockSignals(False)
			# and indent as the previous line
			if line_text.endswith(":"):
				self.insertPlainText("\t"*(indendation+1))
			else:
				self.insertPlainText("\t"*indendation)
			return result
		else:
			return super().keyPressEvent(e)

	def keyPressEvent(self, e: QKeyEvent) -> None:
		return self.autoindent(e)

		

if __name__ == "__main__":
	import sys
	import textwrap
	from datetime import datetime
	app = QApplication(sys.argv)
	editor = QScriptEditor()

	editor.setPlainText(textwrap.dedent("""\
	def main(name: str):
		print(f"hello, {name}")
	"""))
	@editor.textChanged.connect
	def textChanged():
		print("text changed", datetime.now())
	editor.show()
	print(f"{editor.toPlainText()}")
	sys.exit(app.exec())
