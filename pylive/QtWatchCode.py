from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from pathlib import Path

from pylive.QCodeEditor import QCodeEditor
from pylive import getWidgetByName
from typing import *


source = """\
from datetime import datetime
from PySide6.QtWidgets import QApplication

display(f"hello{datetime.now()}")
"""



def display(msg:Any):
	if preview_widget := cast(QLabel, getWidgetByName("PREVIEW_WINDOW_ID")):
		preview_widget.setText(f"{msg}")

class WatchCode(QWidget):
	def __init__(self, parent=None):
		super().__init__(parent=parent)
		self.setWindowTitle("WatchCode")

		self.setLayout(QHBoxLayout())

		self.codeeditor = QCodeEditor()
		self.codeeditor.setPlainText(source)
		self.appwindow = QLabel()
		self.appwindow.setObjectName("PREVIEW_WINDOW_ID")

		self.layout().addWidget(self.codeeditor)
		self.layout().addWidget(self.appwindow)


		self.codeeditor.textChanged.connect(self.evaluate)
		self.evaluate()

	def evaluate(self):
		source = self.codeeditor.toPlainText()
		global_vars = globals()
		local_vars = locals()
		exec(source, global_vars, local_vars)

if __name__ == "__main__":
	import sys
	import subprocess
	app = QApplication(sys.argv)
	window = WatchCode()
	window.show()
	sys.exit(app.exec())