from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

class ScriptEditor(QPlainTextEdit):
	def __init__(self, parent=None):
		super().__init__(parent)
		