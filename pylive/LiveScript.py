from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from pathlib import Path
from datetime import datetime
import time
import humanize

from pylive.QtScriptEditor.ScriptEdit import ScriptEdit
from pylive.utils import getWidgetByName
from typing import *

from io import StringIO
import sys

def display(msg:Any):
	if preview_widget := cast(QLabel, getWidgetByName("PREVIEW_WINDOW_ID")):
		preview_widget.setText(f"{msg}")


class PreviewWidget(QLabel):
	def __init__(self, parent: Optional[QWidget]=None) -> None:
		super().__init__(parent=parent)
		self.setObjectName("PREVIEW_WINDOW_ID")
		self.setLayout(QVBoxLayout())

	def evaluate(self, source:str):
		global_vars = globals()
		local_vars = locals()

		old_stdout = sys.stdout
		sys.stdout = mystdout = StringIO()
		print("\033c")
		try:
			start_time = time.perf_counter()
			exec(source, global_vars, local_vars)
			end_time = time.perf_counter()
			duration_ms = (end_time - start_time) * 1000
			print(f"exec took {duration_ms:.3f} ms")

		except Exception as err:
			print(err)

		finally:
			sys.stdout = old_stdout
		message = mystdout.getvalue()

		if "\033c" in message:
			result = message.split("\033c")[-1].strip()
			self.setText(result)
		else:
			self.setText(self.text()+"\n"+message)
		pass

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
		self.splitter = QSplitter(self)
		self.script_edit = ScriptEdit()
		self.preview_widget = PreviewWidget()
		self.script_edit.textChanged.connect(lambda: self.preview_widget.evaluate(self.script_edit.toPlainText()))

		self.setLayout(QVBoxLayout())
		self.layout().addWidget(self.splitter)
		self.splitter.addWidget(self.script_edit)
		self.splitter.addWidget(self.preview_widget)
		self.splitter.setSizes([self.width()//2,self.width()//2])

	def setScript(self, text:str):
		self.script_edit.setPlainText(text)

if __name__ == "__main__":
	import sys
	import subprocess
	app = QApplication(sys.argv)
	window = QLiveScript()
	from textwrap import dedent, indent
	initial_script = dedent("""\
	from typing import *
	from pylive.utils import getWidgetByName
	label = cast(QLabel, getWidgetByName("PREVIEW_WINDOW_ID"))
	import numpy as np

	# prin text to the widget by simply use the built in print.
	# the snadard out i redirected to the preview widget
	print("you can simply print to this widget")

	# lets create a random image
	pix = QPixmap()
	img = QImage()
	pix.convertFromImage(img)
	""")

	window.setScript(initial_script)

	# with open("./test_script.py", 'r') as file:
	# 	window.setScript(file.read())

	window.show()
	sys.exit(app.exec())