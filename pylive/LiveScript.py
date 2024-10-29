from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from pathlib import Path
from datetime import datetime

from pylive.QtScriptEditor.ScriptEdit import ScriptEdit
from pylive.utils import getWidgetByName
from typing import *

from io import StringIO
import sys

def display(msg:Any):
	if preview_widget := cast(QLabel, getWidgetByName("PREVIEW_WINDOW_ID")):
		preview_widget.setText(f"{msg}")

import traceback
import sys
import os
class QLiveScript(QWidget):
	def __init__(self, parent=None):
		super().__init__(parent=parent)
	
		# setup panel
		self.setWindowTitle("QLiveScript")
		self.resize(1240,600)
		self.setLayout(QHBoxLayout())
		self.layout().setContentsMargins(0,0,0,0)

		"""setup UI"""
		self.script_edit = ScriptEdit()

		self.setLayout(QVBoxLayout())
		self.layout().addWidget(self.script_edit)

	def setScript(self, text:str):
		self.script_edit.setPlainText(text)

if __name__ == "__main__":
	import sys
	import subprocess
	app = QApplication(sys.argv)
	window = QLiveScript()
	from textwrap import dedent, indent
	initial_script = dedent("""\
	from datetime import datetime
	from pylive.QtLiveScript import display

	display(f"hello{datetime.now()}")

	a
	""")

	with open("./test_script.py", 'r') as file:
		window.setScript(file.read())

	# window.openFile("./test_script.py")
	window.show()
	sys.exit(app.exec())