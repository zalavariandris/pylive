# TODO
# optionally open a file, and update if file changes
# if script has been modified, and file has changed, ask, to update
# on save, if file has changed ask to override the changed file
# check sublime for policies.

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from pathlib import Path

from pylive.QScriptEditor import QScriptEditor
from pylive.utils import getWidgetByName
from typing import *


initial_script = """\
from datetime import datetime
from pylive.QtLiveScript import display

display(f"hello{datetime.now()}")
"""

def display(msg:Any):
	if preview_widget := cast(QLabel, getWidgetByName("PREVIEW_WINDOW_ID")):
		preview_widget.setText(f"{msg}")

class QLiveScript(QWidget):
	def __init__(self, parent=None):
		super().__init__(parent=parent)
	
		# setup panel
		self.setWindowTitle("QLiveScript")
		self.resize(800,400)
		self.setLayout(QHBoxLayout())

		# setup UI
		self.setupMenuBar()

		self.scripteditor = QScriptEditor()
		self.scripteditor.setPlainText(initial_script)
		self.filepath:str|None = None # keep track of the actual file exist on disk
		self.preview_label = QLabel()
		self.preview_label.setObjectName("PREVIEW_WINDOW_ID")

		# bind ui
		self.scripteditor.textChanged.connect(self.evaluate)
		@self.scripteditor.textChanged.connect
		def set_script_modified():
			self.script_modified_in_memory = True

		self.watcher = QFileSystemWatcher()
		self.watcher.fileChanged.connect(self.on_file_change)

		self.script_modified_in_memory = False

		# layout widgets
		self.layout().addWidget(self.scripteditor, 1)
		self.layout().addWidget(self.preview_label, 1)

		# evaluate on start
		self.evaluate()

	def prompt_disk_change(self):
		msg_box = QMessageBox(self)
		msg_box.setWindowTitle("File has changed on Disk.")
		msg_box.setText("Do you want to reload?")
		msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
		# temporary block _file change_ signals, to ignore multiple changes when
		# the messagebox is already open
		self.watcher.blockSignals(True) 
		result = msg_box.exec()
		self.watcher.blockSignals(False)
		return result

	def on_file_change(self, path):
		if self.script_modified_in_memory:
			result = self.prompt_disk_change()
			if result == QMessageBox.Yes:
				pass
			else:
				return

		with open(path, 'r') as file:
			data = file.read()
			self.scripteditor.setPlainText(data)
			self.script_modified_in_memory = False

	def openFile(self, filepath:str):
		self.watcher.removePaths(self.watcher.files())
		self.watcher.addPath(filepath)
		with open(filepath, 'r') as file:
			data = file.read()
			self.scripteditor.setPlainText(data)
			self.script_modified_in_memory = False
			self.filepath = filepath
			self.setWindowTitle(f"{self.filepath} - WatchCode")

	def saveFile(self, filepath:str):
		print("saving file", filepath)
		with open(filepath, 'w') as file:
			file.write(self.scripteditor.toPlainText())
			self.script_modified_in_memory = False
		self.filepath = filepath

	def setupMenuBar(self):
		self.menu_bar = QMenuBar()
		file_menu  = self.menu_bar.addMenu("File")
		# Add actions to the File menu
		open_action = QAction("Open", self)
		open_action.triggered.connect(self.open)
		save_action = QAction("Save", self)
		save_action.triggered.connect(self.save)

		# Add actions to File menu
		file_menu.addAction(open_action)
		file_menu.addAction(save_action)

		self.layout().setMenuBar(self.menu_bar)

	def open(self):
		if self.filepath:
			msg_box = QMessageBox(self)
			msg_box.setWindowTitle("Save changes?")
			msg_box.setText("File has been modified, save changes?")
			msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
			# temporary block _file change_ signals, to ignore multiple changes when
			# the messagebox is already open
			self.watcher.blockSignals(True) 
			result = msg_box.exec()
			if result == QMessageBox.Yes:
				self.save()
			self.watcher.blockSignals(False)

		filename, filter_used = QFileDialog.getOpenFileName(self, "Open", ".py", "Python Script (*.py);;Any File (*)")
		if filename != '':
			self.openFile(filename)

	def save(self):
		if self.filepath:
			self.saveFile(self.filepath)
		else:
			filename, filter_used = QFileDialog.getSaveFileName(self, "Save", ".py", "Python Script (*.py);;Any File (*)")
			if filename != '':
				self.saveFile(filename)



	def evaluate(self):
		source = self.scripteditor.toPlainText()
		global_vars = globals()
		local_vars = locals()
		try:
			exec(source, global_vars, local_vars)
		except Exception as err:
			print("err")
		finally:
			pass

if __name__ == "__main__":
	import sys
	import subprocess
	app = QApplication(sys.argv)
	window = QLiveScript()
	# window.openFile("./script_test_file.py")
	window.show()
	sys.exit(app.exec())