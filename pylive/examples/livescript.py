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

def display(data:Any):
	"""TODO: 
	Use PreviewWidget.current()
	current does not seem to work, probably because
	the PreviewWidget is redifined when imported in the live script?
	"""

	from pylive.utils import getWidgetByName
	preview_widget = cast(PreviewWidget, getWidgetByName('PREVIEW_WINDOW_ID'))
	preview_widget.display(data)

def clear():
	"""TODO: 
	Use PreviewWidget.current()
	current does not seem to work, probably because
	the PreviewWidget is redifined when imported in the live script?
	"""

	from pylive.utils import getWidgetByName
	preview_widget = cast(PreviewWidget, getWidgetByName('PREVIEW_WINDOW_ID'))
	preview_widget.clear()

class PreviewWidget(QWidget):
	_stack = []

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

		mainLayout = QVBoxLayout()
		self.setLayout(mainLayout)
		mainLayout.setContentsMargins(0,0,0,0)
		mainLayout.addWidget(self.previewScrollArea, 1)

	@classmethod
	def current(cls):
		return getWidgetByName(cls._stack[-1])

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

	def createContext(self):
		return {
			'__name__': "__main__",
			'__builtins__': globals()["__builtins__"]
		}

	def evaluate(self, source:str):
		self.clear()
		
		global_vars = self.createContext()

		# clear output
		print("\033c") # clear text
		PreviewWidget._stack.append(self.objectName())
		try:
			
			start_time = time.perf_counter()
			
			compiled = compile(source, "__main__", mode="exec")
			exec(compiled, global_vars)
			end_time = time.perf_counter()
			duration_ms = (end_time - start_time) * 1000

			print(f"exec took {duration_ms:.3f} ms")

		except Exception as err:
			print(err)
		finally:
			...
		PreviewWidget._stack.pop()

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
		self.preview_widget = PreviewWidget()
		self.logWindow = LogWindow()
		self.script_edit.textChanged.connect(lambda: self.preview_widget.evaluate(self.script_edit.toPlainText()))

		"""setup layout"""
		left_panel = QSplitter(Qt.Orientation.Vertical, self)
		left_panel.addWidget(self.script_edit)
		left_panel.addWidget(self.logWindow)

		self.splitter = QSplitter(Qt.Orientation.Horizontal, self)
		self.splitter.addWidget(left_panel)
		self.splitter.addWidget(self.preview_widget)
		self.splitter.setSizes([self.width()//self.splitter.count() for i in range(self.splitter.count())])

		self.setLayout(QVBoxLayout())
		self.layout().addWidget(self.splitter)
		

		# setup watch file
		self.filepath = None
		def on_file_change(self, path):
			if self.script_modified_in_memory:
				result = self.prompt_disk_change()
				if result == QMessageBox.StandardButton.Yes:
					pass
				else:
					return

			with open(path, 'r') as file:
				data = file.read()
				self.scripteditor.setPlainText(data)
				self.script_modified_in_memory = False

		def setScriptModified():
			self.script_modified_in_memory = True

		self.watcher = QFileSystemWatcher()
		self.watcher.fileChanged.connect(on_file_change)
		self.script_modified_in_memory = False
		self.script_edit.textChanged.connect(setScriptModified)

		# load config
		self.loadConfig()

		# setup menubar
		self.setupMenuBar()

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

		# setup from config
		if recent:=self.config['recent']:
			self.openFile(recent[-1])
		
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

		"""setup file menu"""
		file_menu  = self.menu_bar.addMenu("File")
		open_action = QAction("Open", self)
		open_action.triggered.connect(self.open)
		open_action.setShortcut(QKeySequence(Qt.Key.Key_Control | Qt.Key.Key_O))
		save_action = QAction("Save", self)
		save_action.triggered.connect(self.save)
		save_action.setShortcut(QKeySequence(Qt.Key.Key_Control | Qt.Key.Key_S))

		file_menu.addAction(open_action)
		file_menu.addAction(save_action)
		file_menu.addSeparator()

		print(self.config)
		for recent in self.config['recent']:
			open_recent_action = QAction(f"{recent}", self)
			open_recent_action.triggered.connect(lambda path=recent: self.openFile(path))
			file_menu.addAction(open_recent_action)

		"""setup edit menu"""
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

		# Add actions to File menu
		edit_menu.addAction(cut_action)
		edit_menu.addAction(paste_action)
		edit_menu.addAction(toggle_comments_action)

		self.layout().setMenuBar(self.menu_bar)

	def setScript(self, script:str):
		self.script_edit.setPlainText(script)

	def closeEvent(self, event):
		if self.script_modified_in_memory and self.filepath:
			msg_box = QMessageBox(self)
			msg_box.setWindowTitle("Save changes?")
			msg_box.setText(f"{Path(self.filepath).name} has been modified, save changes?") 
			msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel)
			result = msg_box.exec()

			
			if result == QMessageBox.StandardButton.Yes:
				self.save()
			elif result == QMessageBox.StandardButton.Cancel:
				event.ignore()

	def openFile(self, filepath:str):
		print("opening file", filepath)
		self.watcher.removePaths(self.watcher.files())
		self.watcher.addPath(filepath)
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

	def saveFile(self, filepath:str):
		print("saving file", filepath)
		with open(filepath, 'w') as file:
			file.write(self.script_edit.toPlainText())
			self.script_modified_in_memory = False
		self.filepath = filepath

	def open(self):
		if self.filepath:
			msg_box = QMessageBox(self)
			msg_box.setWindowTitle("Save changes?")
			msg_box.setText("File has been modified, save changes?")
			msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
			# temporary block _file change_ signals, to ignore multiple changes when
			# the messagebox is already open
			self.watcher.blockSignals(True) 
			result = msg_box.exec()
			if result == QMessageBox.StandardButton.Yes:
				self.save()
			self.watcher.blockSignals(False)

		filename, filter_used = QFileDialog.getOpenFileName(self, "Open", ".py", "Python Script (*.py);;Any File (*)")
		if filename != '':
			self.openFile(filename)

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

	def save(self):
		if self.filepath:
			self.saveFile(self.filepath)
		else:
			filename, filter_used = QFileDialog.getSaveFileName(self, "Save", ".py", "Python Script (*.py);;Any File (*)")
			if filename != '':
				self.saveFile(filename)


if __name__ == "__main__":
	from textwrap import dedent
	import pylive
	import sys
	import subprocess
	app = QApplication(sys.argv)
	window = LiveScript()

	# window.setScript(dedent("""\
	# 	from PySide6.QtGui import *
	# 	from PySide6.QtCore import *
	# 	from PySide6.QtWidgets import *
	# 	import numpy as np
	# 	def random_image(width=8, height=8):
	# 		img = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
	# 		# Convert to QImage
	# 		return QImage(img.data, width, height, 3 * width, QImage.Format_RGB888)

	# 	from pylive import livescript
	# 	livescript.display("HELLO")
	# """))

	# with open("./test_script.py", 'r') as file:
	# 	window.setScript(file.read())

	window.show()
	sys.exit(app.exec())
