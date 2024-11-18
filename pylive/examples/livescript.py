from typing import *
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

from pylive.utils import getWidgetByName
from pylive.unique import make_unique_id
from pylive.logwindow import LogWindow

import traceback

# def display(data:Any):
# 	"""TODO: 
# 	Use PreviewWidget.current()
# 	current does not seem to work, probably because
# 	the PreviewWidget is redifined when imported in the live script?
# 	"""

# 	from pylive.utils import getWidgetByName
# 	preview_widget = cast(PreviewWidget, getWidgetByName('PREVIEW_WINDOW_ID'))
# 	preview_widget.display(data)

# def clear():
# 	"""TODO: 
# 	Use PreviewWidget.current()
# 	current does not seem to work, probably because
# 	the PreviewWidget is redifined when imported in the live script?
# 	"""

# 	from pylive.utils import getWidgetByName
# 	preview_widget = cast(PreviewWidget, getWidgetByName('PREVIEW_WINDOW_ID'))
# 	preview_widget.clear()

from textwrap import dedent
TEMPLATE_SCRIPT = dedent("""\
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from pylive import livescript
from typing import *

print("Hello World")

class MyWidget(QWidget):
	def __init__(self, parent=None):
		super().__init__(parent=parent)
		mainLayout = QVBoxLayout()
		self.setLayout(mainLayout)

		label = QLabel("MyWidget")
		mainLayout.addWidget(label)

if __name__ == "__live__":
	from pylive.preview_widget import PreviewWidget
	preview = PreviewWidget.instance()
	preview.display("hello")

if __name__ == "__main__":
	...

""")

from pylive.preview_widget import PreviewWidget


class LiveScript(QWidget):
	def __init__(self, parent=None):
		super().__init__(parent=parent)
	
		# setup panel
		self.setWindowTitle("LiveScript")
		self.resize(1240,800)
		self.setLayout(QHBoxLayout())
		self.layout().setContentsMargins(0,0,0,0)

		"""setup UI"""
		self.script_edit = ScriptEdit()
		self.script_edit.textChanged.connect(lambda: self.evaluate())

		self.preview_widget = PreviewWidget.instance()
		self.preview_widget.contentChanged.connect(lambda: self.setPreviewCollapse(False))
		self.log_window = LogWindow()

		"""setup layout"""
		left_panel = QSplitter(Qt.Orientation.Vertical, self)
		left_panel.addWidget(self.script_edit)
		left_panel.addWidget(self.log_window)

		self.splitter = QSplitter(Qt.Orientation.Horizontal, self)
		self.splitter.addWidget(left_panel)
		self.splitter.addWidget(self.preview_widget)
		self.splitter.setSizes([self.width()//self.splitter.count() for i in range(self.splitter.count())])
		self.setPreviewCollapse(True)

		self.setLayout(QVBoxLayout())
		self.layout().addWidget(self.splitter)
		

		# setup watch file
		self.filepath = None

		def setScriptModified():
			self.script_modified_in_memory = True

		self.watcher = QFileSystemWatcher()
		self.watcher.fileChanged.connect(lambda: self.on_file_change(self.filepath))
		self.script_modified_in_memory = False
		self.script_edit.textChanged.connect(setScriptModified)

		# load config
		self.loadConfig()
		# setup from config
		if recent:=self.config['recent']:
			self.openFile(recent[-1])

		# setup menubar
		self.setupMenuBar()

		if not self.filepath:
			self.script_edit.blockSignals(True)
			self.script_edit.setPlainText(TEMPLATE_SCRIPT)
			self.script_edit.blockSignals(False)

	def setPreviewCollapse(self, collapse:bool):
		idx = self.splitter.indexOf(self.preview_widget)
		assert idx>=0

		if collapse:
			sizes = self.splitter.sizes()
			sizes[idx] = 0
			self.splitter.setSizes(sizes)
		else:
			count = self.splitter.count()
			sizes = self.splitter.sizes()
			total_width = sum(size for size in sizes)
			
			sizes[idx] = int(total_width/(count-1))
			self.splitter.setSizes(sizes)

	def createContext(self):
		return {
			'__name__': "__live__",
			'__builtins__': globals()["__builtins__"]
		}

	def evaluate(self):
		source = self.script_edit.toPlainText()
		self.preview_widget.clear()
		self.log_window.clear()
		global_vars = self.createContext()
		self.setPreviewCollapse(True)

		try:
			start_time = time.perf_counter()
			compiled = compile(source, "__main__", mode="exec")
			exec(compiled, global_vars)
			end_time = time.perf_counter()
			duration_ms = (end_time - start_time) * 1000
			print(f"exec took {duration_ms:.3f} ms")

		except Exception as e:
			tb = traceback.TracebackException.from_exception(e)
			self.log_window.appendMessage(''.join(tb.format()))
			# print("ERROR:", )  # Produces a nicely formatted traceback as a string
		finally:
			...

	def on_file_change(self, path):
		if self.script_modified_in_memory:
			result = self.prompt_disk_change()
			if result == QMessageBox.StandardButton.Yes:
				pass
			else:
				return

		with open(path, 'r') as file:
			data = file.read()
			self.script_edit.setPlainText(data)
			self.script_modified_in_memory = False

	def saveConfig(self):
		import json
		with open("./livescript.init", 'w') as file:
			file.write(json.dumps(self.config, indent=2))
			
	def loadConfig(self):
		import json
		try:
			with open("./livescript.init", 'r') as file:
				self.config = json.loads(file.read())
		except FileNotFoundError as err:
			self.config = {
				"recent": [],
				"live": True
			}
		
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

		"""File menu"""
		file_menu  = self.menu_bar.addMenu("File")
		new_file_action = QAction("New File", self)
		new_file_action.triggered.connect(self.newFile)
		new_file_action.setShortcut(QKeySequence(Qt.Key.Key_Control | Qt.Key.Key_N))

		ope_file_action = QAction("Open File", self)
		ope_file_action.triggered.connect(self.openFile)
		ope_file_action.setShortcut(QKeySequence(Qt.Key.Key_Control | Qt.Key.Key_O))

		save_file_action = QAction("Save File", self)
		save_file_action.triggered.connect(self.saveFile)
		save_file_action.setShortcut(QKeySequence(Qt.Key.Key_Control | Qt.Key.Key_S))

		file_menu.addAction(new_file_action)
		file_menu.addAction(ope_file_action)
		file_menu.addAction(save_file_action)
		file_menu.addSeparator()

		for recent in self.config['recent']:
			open_recent_action = QAction(f"{recent}", self)
			open_recent_action.triggered.connect(lambda path=recent: self.openFile(path))
			file_menu.addAction(open_recent_action)

		"""Edit menu"""
		edit_menu  = self.menu_bar.addMenu("Edit")
		copy_action = QAction("Copy", self)
		copy_action.triggered.connect(self.script_edit.copy)
		copy_action.setShortcut(QKeySequence(Qt.Key.Key_Control | Qt.Key.Key_C))
		cut_action = QAction("Cut", self)
		cut_action.triggered.connect(self.script_edit.cut)
		cut_action.setShortcut(QKeySequence(Qt.Key.Key_Control | Qt.Key.Key_X))
		paste_action = QAction("Paste", self)
		paste_action.triggered.connect(self.script_edit.paste)
		paste_action.setShortcut(QKeySequence(Qt.Key.Key_Control | Qt.Key.Key_V))
		toggle_comments_action = QAction("toggle comments", self)
		toggle_comments_action.setShortcut(QKeySequence(Qt.Key.Key_Control | Qt.Key.Key_Slash))
		toggle_comments_action.triggered.connect(self.script_edit.toggleCommentSelection)

		# Add actions to Edit menu
		edit_menu.addAction(cut_action)
		edit_menu.addAction(paste_action)
		edit_menu.addAction(toggle_comments_action)

		"""Template menu"""
		template_menu  = self.menu_bar.addMenu("Templates")
		insert_template_action = QAction("insert template", self)
		insert_template_action.triggered.connect(lambda: self.script_edit.insertPlainText(TEMPLATE_SCRIPT))

		# Add actions to Edit menu
		template_menu.addAction(insert_template_action)

		self.layout().setMenuBar(self.menu_bar)

	def setScript(self, script:str):
		self.script_edit.setPlainText(script)

	def closeEvent(self, event):
		DoCloseFile = self.closeFile()
		if not DoCloseFile:
			event.ignore()
			return
		event.accept()

	def closeFile(self)->bool:
		if self.script_modified_in_memory:
			# prompt user if file has changed
			msg_box = QMessageBox(self)
			msg_box.setWindowTitle("Save changes?")
			msg_box.setText(f"{Path(self.filepath).name if self.filepath else 'New file'} has been modified, save changes?") 
			msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel)
			result = msg_box.exec()

			match result:
				case QMessageBox.StandardButton.Yes:
					self.saveFile()
					if self.watcher.files():
						self.watcher.removePaths(self.watcher.files())
					return True
				case QMessageBox.StandardButton.No:
					if self.watcher.files():
						self.watcher.removePaths(self.watcher.files())
					return True
				case QMessageBox.StandardButton.Cancel:
					return False
		return True

	def newFile(self):
		self.closeFile()

	def saveFile(self, filepath:str|None=None):
		DoSaveAs = self.filepath!=filepath
		if DoSaveAs:
			...
		
		if not self.filepath or filepath:
			choosen_filepath, filter_used = QFileDialog.getSaveFileName(self, "Save", ".py", "Python Script (*.py);;Any File (*)")
			if not choosen_filepath:
				return # if no filepath was chossen cancel saving
			filepath = choosen_filepath

		print("saving file", filepath)
		self.watcher.blockSignals(True)
		with open(filepath, 'w') as file:
			file.write(self.script_edit.toPlainText())
			self.script_modified_in_memory = False
		self.watcher.blockSignals(False)
		self.filepath = filepath

	def openFile(self, filepath:str):
		if not filepath:
			# if not filepath is specified open file doalog
			choosen_filepath, filter_used = QFileDialog.getOpenFileName(self, "Open", ".py", "Python Script (*.py);;Any File (*)")
			
			# if nothing is selected in the dialog, abort file opening
			if choosen_filepath != '':
				return # abort opening a file

			# us dialog filepath from now on
			filepath = choosen_filepath

		self.closeFile()
		
		
		try:
			with open(filepath, 'r') as file:
				text = file.read()
				self.setScript(text)
				self.script_modified_in_memory = False
				self.filepath = filepath
				self.setWindowTitle(f"{self.filepath} - WatchCode")

				if filepath in self.config['recent']:
					self.config['recent'] = [path for path in self.config['recent'] if path!=filepath]

				self.config['recent'].append(filepath)
				self.saveConfig()
				self.watcher.addPath(filepath)
		except FileNotFoundError:
			self.config['recent'].remove(filepath)

	def prompt_disk_change(self):
		msg_box = QMessageBox(self)
		msg_box.setWindowTitle("File has changed on Disk.")
		msg_box.setText("Do you want to reload?")
		msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
		# temporary block _file change_ signals, to ignore multiple changes when
		# the messagebox is already open
		self.watcher.blockSignals(True) 
		result = msg_box.exec()
		self.watcher.blockSignals(False)
		return result

if __name__ == "__main__":
	import sys
	app = QApplication(sys.argv)
	window = LiveScript()
	window.show()
	print("before exec")
	sys.exit(app.exec())
