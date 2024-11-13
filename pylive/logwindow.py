"""capture standard output"""
import sys
import io
from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

class CaptureStdOut(QObject):
	messaged = Signal(str)
	def __init__(self, parent: Optional[QObject]=None) -> None:
		super().__init__(parent)
		self.stdout = sys.stdout
		sys.stdout = self

	def write(self, message):
		self.stdout.write(message)
		self.messaged.emit(message)
		self.stdout.flush()  # Ensure the output is written immediately
		
	def flush(self):
		self.stdout.flush()  # Ensure the output is written immediately

class LogWindow(QPlainTextEdit):
	def __init__(self, parent=None):
		super().__init__(parent=parent)
		# Create an in-memory buffer to capture the output
		captured_output = io.StringIO()

		# Redirect stdout to both the original stdout and the in-memory buffer
		self.captured_output = CaptureStdOut(self)
		self.captured_output.messaged.connect(self.appendMessage)

	def appendMessage(self, text:str):
		if "\033c" in text:
			result = text.split("\033c")[-1].strip()
			self.insertPlainText(result)
		else:
			self.insertPlainText(text)
		
		self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

if __name__ == "__self__":
	...