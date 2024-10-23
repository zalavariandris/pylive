from typing import *

from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *

class KeywordsCompleter(QCompleter):
	def __init__(self):

		# completion model
		keywords = [
			'and', 'as', 'assert', 'async', 'await', 'break', 'class', 'continue',
			'def', 'del', 'elif', 'else', 'except', 'False', 'finally', 'for',
			'from', 'global', 'if', 'import', 'in', 'is', 'lambda', 'None', 'nonlocal',
			'not', 'or', 'pass', 'raise', 'return', 'True', 'try', 'while', 'with', 'yield'
		]
		self.completions_model = QStringListModel(keywords)
		super().__init__(self.completions_model)

		# completion view
		self.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)


		# update completer based on text and cursor position