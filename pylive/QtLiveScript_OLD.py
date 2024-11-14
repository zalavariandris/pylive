# TODO
# optionally open a file, and update if file changes
# if script has been modified, and file has changed, ask, to update
# on save, if file has changed ask to override the changed file
# check sublime for policies.

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
		self.scripteditor = ScriptEdit()

		self.filepath:str|None = None # keep track of the actual file exist on disk

		self.right_pane = QWidget()
		self.right_pane.setLayout(QGridLayout())

		self.preview_label = QLabel()
		self.preview_label.setObjectName("PREVIEW_WINDOW_ID")
		

		self.exception_panel = QWidget()
		self.exception_panel.setLayout(QVBoxLayout())
		
		self.right_pane.layout().addWidget(self.preview_label, 0, 0)

		# setup menubar
		self.setupMenuBar()

		# bind ui
		
		@self.scripteditor.textChanged.connect
		def on_text_changed():
			print("text changed")
			self.evaluate()

		@self.scripteditor.textChanged.connect
		def set_script_modified():
			self.script_modified_in_memory = True

		self.watcher = QFileSystemWatcher()
		self.watcher.fileChanged.connect(self.on_file_change)
		self.script_modified_in_memory = False

		# layout widgets
		self.layout().addWidget(self.scripteditor, 1)
		self.layout().addWidget(self.right_pane, 1)

		# evaluate on start
		self.evaluate()

	def closeEvent(self, event):
		if self.script_modified_in_memory:
			msg_box = QMessageBox(self)
			result = msg_box.exec()
			if result == QMessageBox.Yes:
				self.save()

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
		print("opening file", filepath)
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
		self.menu_bar.setStyleSheet("""
			QMenuBar::item {
				padding: 0px 8px;  /* Adjust padding for the normal state */
			}
			QMenuBar::item:selected {  /* Hover state */
				padding: 0px 0px;  /* Ensure the same padding applies to the hover state */
			}
		""")

		file_menu  = self.menu_bar.addMenu("File")
		# Add actions to the File menu
		open_action = QAction("Open", self)
		open_action.triggered.connect(self.open)
		open_action.setShortcut(QKeySequence(Qt.CTRL | Qt.Key_O))
		save_action = QAction("Save", self)
		save_action.triggered.connect(self.save)
		save_action.setShortcut(QKeySequence(Qt.CTRL | Qt.Key_S))

		# Add actions to File menu
		file_menu.addAction(open_action)
		file_menu.addAction(save_action)

		edit_menu  = self.menu_bar.addMenu("Edit")
		# Add actions to the File menu
		copy_action = QAction("Copy", self)
		copy_action.triggered.connect(self.scripteditor.copy)
		copy_action.setShortcut(QKeySequence(Qt.CTRL | Qt.Key_C))
		cut_action = QAction("Cut", self)
		cut_action.triggered.connect(self.scripteditor.cut)
		cut_action.setShortcut(QKeySequence(Qt.CTRL | Qt.Key_X))
		paste_action = QAction("Paste", self)
		paste_action.triggered.connect(self.scripteditor.paste)
		paste_action.setShortcut(QKeySequence(Qt.CTRL | Qt.Key_V))
		toggle_comments_action = QAction("toggle comments", self)
		toggle_comments_action.setShortcut(QKeySequence(Qt.CTRL | Qt.Key_Slash))
		toggle_comments_action.triggered.connect(self.toggle_comment)

		# Add actions to File menu
		edit_menu.addAction(cut_action)
		edit_menu.addAction(paste_action)
		edit_menu.addAction(toggle_comments_action)

		self.layout().setMenuBar(self.menu_bar)

	def toggle_comment(self):
		print("toggle_comment")
		from textwrap import dedent, indent

		def toggle_comment(txt):
			original_lines = txt.split("\n")
			original_first_line = original_lines[0]
			txt = dedent(txt)
			lines = txt.split("\n")
			first_line = lines[0]
			common_indent = original_first_line[:-len(first_line)]
			lines_with_comment = [f"#{line}" for line in txt.split("\n")]
			txt = "\n".join(lines_with_comment)
			txt = indent(txt, common_indent)
			

			return txt

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

		self.error_labels_data = []
		try:
			old_stdout = sys.stdout
			sys.stdout = mystdout = StringIO()
			timebegin = datetime.now()
			# exec(source, global_vars, local_vars)
			timeend = datetime.now()
			print("exec time:", timeend, timebegin)
			sys.stdout = old_stdout
			message = mystdout.getvalue()

			if "\033c" in message:
				result = message.split("\033c")[-1].strip()
				self.preview_label.setText(result)
			else:
				self.preview_label.setText(self.preview_label.text()+"\n"+message)
			
		except Exception as err:
			print("update exceptions")
			
		finally:
			pass

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
	""")

	window.openFile("./test_script.py")
	window.show()
	sys.exit(app.exec())