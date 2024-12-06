from pathlib import Path

class LiveApp:
	def __init__(self, filepath:str):
		self.filepath = filepath

	def run(self):
		self.setUp()

		self.tearDown()

	def setUp(self):
		...

	def tearDown(self):
		...

	def fileChanged(self):
		pass


from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *
class QtLiveApp(LiveApp):
	@override
	def setUp(self):
		app = QApplication()

		app.exec()

	@override
	def tearDown(self):
		pass

import watchfiles
import subprocess
import asyncio
from watchfiles import awatch

from watchfiles import run_process
class TerminalLiveApp(LiveApp):
	def setUp(self):
	    run_process(self.filepath, target=self.fileChanged)
		# subprocess.run(["python", self.filepath])

	def fileChanged(self):
		subprocess.run(["python", self.filepath])

	def tearDown(self):
		...


if __name__ == "__main__":
	script = "C:/dev/src/pylive/script_examples_to_run_live/text_processing.py"
	app = TerminalLiveApp(filepath=script)
	app.run()
	print("exit")