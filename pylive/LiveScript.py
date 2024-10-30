local_vars = locals() # capture default local variables

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


class PreviewWidget(QWidget):
	def __init__(self, parent: Optional[QWidget]=None) -> None:
		super().__init__(parent=parent)
		self.setObjectName("PREVIEW_WINDOW_ID")
		self.statusLabel = QLabel()
		self.previewFrame = QWidget()
		self.previewFrame.setLayout(QVBoxLayout())

		self.loggingLabel = QLabel()

		self.setLayout(QVBoxLayout())
		self.layout().addWidget(self.previewFrame)
		self.layout().addWidget(self.loggingLabel)

	def display(self, data:Any):
		match data:
			case str():
				self.previewFrame.layout().addWidget(QLabel(data))
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
		#
		global global_vars
		global local_vars

		old_stdout = sys.stdout # route standard output
		sys.stdout = mystdout = StringIO()

		# clear output
		print("\033c") # clear text
		try:
			start_time = time.perf_counter()
			# compiled = compile(source, "<string>", mode="exec")
			exec(source, globals(), local_vars)
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
		self.app_widget = PreviewWidget()
		self.script_edit.textChanged.connect(lambda: self.app_widget.evaluate(self.script_edit.toPlainText()))

		self.setLayout(QVBoxLayout())
		self.layout().addWidget(self.splitter)
		self.splitter.addWidget(self.script_edit)
		self.splitter.addWidget(self.app_widget)
		self.splitter.setSizes([self.width()//2,self.width()//2])

	def setAppWidget(self):
		pass

	def setScript(self, text:str):
		self.script_edit.setPlainText(text)

if __name__ == "__main__":
	import sys
	import subprocess
	app = QApplication(sys.argv)
	window = QLiveScript()
	# from textwrap import dedent, indent
	# initial_script = dedent("""\
	# from PySide6.QtGui import *
	# from PySide6.QtCore import *
	# from PySide6.QtWidgets import *
	# from typing import *
	# from pylive.utils import getWidgetByName
	# window = cast(QLabel, getWidgetByName("PREVIEW_WINDOW_ID"))
	# import numpy as np

	# import sys

	# def show_python_version():
	# 	print(sys.platform)
	# 	print(sys.executable)
		
	# show_python_version()

	# # prin text to the widget by simply use the built in print.
	# # the snadard out i redirected to the preview widget
	# print("you can simply print to this widget")

	# # Create a random image with shape (height, width, channels)
	# def random_image():
	# 	height, width = 256, 256  # You can adjust the size
	# 	img = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)

	# 	# Convert to QImage
	# 	return QImage(img.data, width, height, 3 * width, QImage.Format_RGB888)

	# pix = QPixmap()
	# pix.convertFromImage(random_image())
	# window.display(pix)

	# class MyWidget(QLabel):
	# 	def __init__(self, parent=None):
	# 		super().__init__(parent=parent)
	# 		self.setText("This is my custom Widget")


	# window.display(MyWidget())
	# """)

	# window.setScript(initial_script)

	# with open("./test_script.py", 'r') as file:
	# 	window.setScript(file.read())

	window.show()
	sys.exit(app.exec())

