from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from typing import *

class WordCompleter(QCompleter):
	def __init__(self, textedit:QTextEdit, words:List[str]=[]):
		super().__init__(words, parent=textedit)
		self.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
		self.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
		self.text_edit = textedit  # The QTextEdit instance
		self.setWidget(self.text_edit)
		self.activated.connect(self.insertCompletion)

		# Install event filter on the text edit
		self.text_edit.installEventFilter(self)
		self.text_edit.textChanged.connect(lambda: self.updateCompletion())
		# self.popup().installEventFilter(self)
		# self.text_edit.viewport().installEventFilter(self)
		# self.text_edit.viewport().setMouseTracking(True)

	def insertCompletion(self, completion):
		"""
		Inserts the selected completion into the text at the cursor position.
		"""
		tc = self.text_edit.textCursor()
		extra = len(completion) - len(self.completionPrefix())
		tc.movePosition(QTextCursor.MoveOperation.Left)
		tc.movePosition(QTextCursor.MoveOperation.EndOfWord)
		tc.insertText(completion[-extra:])
		self.text_edit.setTextCursor(tc)

	def textUnderCursor(self):
		"""
		Returns the word under the cursor in the QTextEdit.
		"""
		cursor = self.text_edit.textCursor()
		cursor.select(QTextCursor.SelectionType.WordUnderCursor)
		return cursor.selectedText()

	def eventFilter(self, o:QObject, e:QEvent):
		"""
		Filters events for the QTextEdit and the completer popup.
		"""
		if e.type() == QEvent.Type.KeyRelease:
			print(f"text under cursor: '{self.textUnderCursor()}'")

		#superclass already installed an eventfilter on the popup() ListView
		if e.type() == QEvent.Type.KeyPress:
			e = cast(QKeyEvent, e)
			print("currentCompletion:", self.currentCompletion())
			if o is self.text_edit or o is self.popup():
			
				# Handle key events for autocompletion
				if e.key() in {Qt.Key.Key_Enter, Qt.Key.Key_Return} and self.popup().isVisible():
					# Get the currently selected completion from the popup
					current_index = self.popup().currentIndex()
					selected_completion = self.completionModel().data(current_index, Qt.ItemDataRole.DisplayRole)
					if selected_completion:
						success = self.insertCompletion(selected_completion)
					self.popup().hide()
					return True
				elif e.key() == Qt.Key.Key_Escape and self.popup().isVisible():
					print("Escape pressed")
					self.popup().hide()
					return True
				elif e.key() in {Qt.Key.Key_Up, Qt.Key.Key_Down} and self.popup().isVisible():
					# Let the popup handle up/down keys for selection
					return False

		return super().eventFilter(o, e)

	def updateCompletion(self):
		"""
		Updates the completion prefix and shows the popup if necessary.
		"""
		prefix = self.textUnderCursor()
		if prefix and len(prefix) > 0 and prefix != self.currentCompletion():
			self.setCompletionPrefix(prefix)
			popup = self.popup()
			popup.setCurrentIndex(self.completionModel().index(0, 0))

			# Calculate the required width for the popup
			rect = self.text_edit.cursorRect()
			# Get the width needed for the longest completion
			model = self.completionModel()
			max_width = 0
			for i in range(model.rowCount()):
				text = model.data(model.index(i, 0), Qt.ItemDataRole.DisplayRole)
				width = popup.fontMetrics().horizontalAdvance(text)
				max_width = max(max_width, width)
			
			# Add padding for the scrollbar and item margins
			scrollbar_width = popup.verticalScrollBar().sizeHint().width()
			item_margin = 5  # Adjust this value based on your styling
			total_width = max_width + scrollbar_width + 2 * item_margin
			
			# Ensure the popup isn't too narrow or too wide
			min_width = 5
			max_width = self.text_edit.width()
			total_width = max(min_width, min(total_width, max_width))
			
			rect.setWidth(total_width)
			self.complete(rect)
		else:
			self.popup().hide()


class PythonKeywordsCompleter(WordCompleter):
	def __init__(self, textedit:QTextEdit, additional_keywords=[]) -> None:
		keywords_list = [
			"and", "as", "assert", "break", "class", "continue", 
			"def", "del", "elif", "else", "except", "False", 
			"finally", "for", "from", "global", "if", "import", 
			"in", "is", "lambda", "None", "nonlocal", "not", 
			"or", "pass", "raise", "return", "True", "try", 
			"while", "with", "yield"
		]

		builtins_list = [
			"abs", "aiter", "all", "anext", "any", "ascii",
			"bin", "bool", "breakpoint", "bytearray", "bytes",
			"callable", "chr", "classmethod", "compile", "complex",
			"delattr", "dict", "dir", "divmod",
			"enumerate", "eval", "exec",
			"filter", "float", "format", "frozenset",
			"getattr", "globals",
			"hasattr", "hash", "help", "hex",
			"id", "input", "int", "isinstance", "issubclass", "iter",
			"len", "list", "locals",
			"map", "max", "memoryview", "min",
			"next",
			"object", "oct", "open", "ord",
			"pow", "print", "property",
			"range", "repr", "reversed", "round",
			"set", "setattr", "slice", "sorted", "staticmethod", "str", "sum", "super",
			"tuple", "type",
			"vars",
			"zip"
		]
		

		super().__init__(textedit)
		self.setModel(QStringListModel(keywords_list + builtins_list))


if __name__ == "__main__":
	#create app
	app = QApplication([])

	# create completing editor
	editor = QTextEdit()
	completer = PythonKeywordsCompleter(editor, ["apple", "ananas", "banana", "cherry", "date", "elderberry", "fig", "grape", "honeydew", "kiwi", "lemon"])
	editor.setWindowTitle("QTextEdit with Custom Completer")
	editor.resize(600, 400)

	# placeholder
	words = [completer.model().index(row,0).data() for row in range(completer.model().rowCount())]
	editor.setPlaceholderText("Start typing...\n\neg.: " + ", ".join(words))
	
	# show window
	editor.show()

	#run app
	app.exec()
