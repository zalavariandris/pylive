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

# def display(msg:Any):
# 	if preview_widget := cast(QLabel, getWidgetByName("PREVIEW_WINDOW_ID")):
# 		preview_widget.setText(f"{msg}")
from textwrap import dedent
initial_script = dedent("""\
	from pylive.utils import getWidgetByName
	import numpy as np
	def random_image(width=8, height=8):
		img = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
		# Convert to QImage
		return QImage(img.data, width, height, 3 * width, QImage.Format_RGB888)

	app_widget = getWidgetByName("PREVIEW_WINDOW_ID")
	app_widget.display( random_image(128, 128) )
	mylabel = QLabel()
	mylabel.setText("hello")
	app_widget.display(mylabel)
	print("hello")
""")

class AppWidget(QWidget):
	def __init__(self, parent: Optional[QWidget]=None) -> None:
		super().__init__(parent=parent)
		self.setObjectName("PREVIEW_WINDOW_ID")
		self.statusLabel = QLabel()

		self.previewFrame = QWidget()
		
		self.previewFrame.setLayout(QVBoxLayout())
		self.previewFrame.layout().setContentsMargins(0,0,0,0)

		self.previewScrollArea = QScrollArea()
		self.previewScrollArea.setContentsMargins(0,0,0,0)
		self.previewScrollArea.setWidget(self.previewFrame)
		self.previewScrollArea.setWidgetResizable(True)

		self.loggingLabel = QLabel()
		self.loggingScrollArea = QScrollArea()
		self.loggingScrollArea.setWidget(self.loggingLabel)
		self.loggingScrollArea.setWidgetResizable(True)
		self.loggingScrollArea.setContentsMargins(0,0,0,0)

		self.setLayout(QVBoxLayout())
		self.layout().setContentsMargins(0,0,0,0)
		self.layout().addWidget(self.previewScrollArea, 1)
		self.layout().addWidget(self.loggingScrollArea, 0)

	def display(self, data:Any):
		match data:
			case str():
				self.previewFrame.layout().addWidget(QLabel(data))
			case QImage():
				pixlabel = QLabel()
				pixmap = QPixmap()
				pixmap.convertFromImage(data)
				pixlabel.setPixmap(pixmap)
				self.previewFrame.layout().addWidget(pixlabel)
			case QPixmap():
				pixlabel = QLabel()
				pixlabel.setPixmap(data)
				self.previewFrame.layout().addWidget(pixlabel)
			case QWidget():
				self.previewFrame.layout().addWidget(data)
			case _:
				self.previewFrame.layout().addWidget(QLabel(str(data)))


	def clear(self):
		layout = self.previewFrame.layout()
		for i in reversed(range(layout.count())): 
			layout.itemAt(i).widget().deleteLater()

	def evaluate(self, source:str):
		self.clear()

		old_stdout = sys.stdout # route standard output
		sys.stdout = mystdout = StringIO()

		# clear output
		print("\033c") # clear text
		try:
			start_time = time.perf_counter()
			# compiled = compile(source, "<string>", mode="exec")
			exec(source, globals(), globals())
			end_time = time.perf_counter()
			duration_ms = (end_time - start_time) * 1000

			print(f"exec took {duration_ms:.3f} ms")

		except Exception as err:
			print(err)
		finally:
			sys.stdout = old_stdout # restore standard output

		# display message on the logging label
		message = mystdout.getvalue()
		if "\033c" in message:
			result = message.split("\033c")[-1].strip()
			self.loggingLabel.setText(result)
		else:
			self.loggingLabel.setText(self.loggingLabel.text()+"\n"+message)

import traceback
import sys
import os
class LiveScript(QWidget):
	def __init__(self, parent=None):
		super().__init__(parent=parent)
	
		# setup panel
		self.setWindowTitle("LiveScript")
		self.resize(1240,600)
		self.setLayout(QHBoxLayout())
		self.layout().setContentsMargins(0,0,0,0)

		"""setup UI"""
		self.splitter = QSplitter(self)
		self.script_edit = ScriptEdit()
		self.app_widget = AppWidget()

		self.script_edit.textChanged.connect(lambda: self.app_widget.evaluate(self.script_edit.toPlainText()))

		self.setLayout(QVBoxLayout())
		self.layout().addWidget(self.splitter)

		self.splitter.addWidget(self.script_edit)
		self.splitter.addWidget(self.app_widget)
		self.splitter.setSizes([self.width()//2,self.width()//2])

		self.setScript(initial_script)

	def setAppWidget(self):
		pass

	def setScript(self, text:str):
		self.script_edit.setPlainText(text)

if __name__ == "__main__":
	import sys
	import subprocess
	app = QApplication(sys.argv)
	window = LiveScript()

	window.setScript(initial_script)

	# with open("./test_script.py", 'r') as file:
	# 	window.setScript(file.read())

	window.show()
	sys.exit(app.exec())
