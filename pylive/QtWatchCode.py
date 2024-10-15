# TODO
# optionally open a file, and update if file changes
# if script has been modified, and file has changed, ask, to update
# on save, if file has changed ask to override the changed file
# check sublime for policies.

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

class TimeoutException(Exception):
	pass


class WatchCode(QWidget):
	def __init__(self, parent=None):
		super().__init__(parent=parent)
		self.setWindowTitle("WatchCode")

		self.setLayout(QHBoxLayout())

		self.codeeditor = QCodeEditor()
		# self.codeeditor.menuBar()
		self.codeeditor.setPlainText(source)
		self.appwindow = QLabel()
		self.appwindow.setObjectName("PREVIEW_WINDOW_ID")

		self.layout().addWidget(self.codeeditor)
		self.layout().addWidget(self.appwindow)

		# Timer to interrupt execution after 3 seconds
		self.timeout_timer = QTimer()
		self.timeout_timer.setInterval(1000)  # Set a timeout (in ms)
		self.timeout_timer.timeout.connect(self.raise_timeout_exception)

		self.codeeditor.textChanged.connect(self.evaluate)
		self.evaluate()

	def raise_timeout_exception(self):
		# Raise an exception to stop the user's code
		raise TimeoutException()

	def evaluate(self):
		source = self.codeeditor.toPlainText()
		global_vars = globals()
		local_vars = locals()
		self.timeout_timer.start()
		try:
			exec(source, global_vars, local_vars)
		except TimeoutException:
			print("timeout exception")
		except Exception as err:
			print("err")
		finally:
			self.timeout_timer.stop()

if __name__ == "__main__":
	import sys
	import subprocess
	app = QApplication(sys.argv)
	window = WatchCode()
	window.show()
	sys.exit(app.exec())