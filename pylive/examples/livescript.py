from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *


from pathlib import Path
from datetime import datetime
import time
import humanize

from pylive.QtScriptEditor.ScriptEdit import ScriptEdit
from typing import *

from io import StringIO
import sys

from pylive.unique import make_unique_id
from pylive.logwindow import LogWindow

import traceback
import ast
import gc

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

		label = QLabel("MyWiddet")
		mainLayout.addWidget(label)

if __name__ == "__live__":
	from pylive.preview_widget import PreviewWidget
	preview = PreviewWidget.instance()
	preview.display(MyWidget())

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

		"""setup UI"""
		mainLayout = QVBoxLayout()
		self.setLayout(mainLayout)
		self.layout().setContentsMargins(0,0,0,0)
		# layout widgets
		self.main_splitter = QSplitter(Qt.Orientation.Horizontal, self)
		mainLayout.addWidget(self.main_splitter)
		self.setupStatusBar()
		
		
		self.script_edit = ScriptEdit()
		self.script_edit.textChanged.connect(lambda: self.evaluate())

		self.preview_widget = PreviewWidget.instance()

		self.log_window = LogWindow()
	
		# setup watch file
		self.filepath = None
		self.watcher = QFileSystemWatcher()
		self.watcher.fileChanged.connect(lambda: self.on_file_change(self.filepath))

		# load config
		self.loadConfig()
		# setup from config
		if recent:=self.config['recent']:
			self.openFile(recent[-1])

		# setup menubar
		self.script_edit.document().modificationChanged.connect(self.updateWindowTitle)
		if not self.filepath:
			self.script_edit.setPlainText(TEMPLATE_SCRIPT)


		self.main_splitter.addWidget(self.script_edit)

		self.right_panel = QSplitter(Qt.Orientation.Vertical, self)
		self.right_panel.addWidget(self.preview_widget)
		self.right_panel.addWidget(self.log_window)
		self.right_panel.setStretchFactor(0,100)
		self.right_panel.setStretchFactor(1,0)

		self.main_splitter.addWidget(self.right_panel)

		if self.main_splitter.count()>0:
			self.main_splitter.setSizes([self.width()//self.main_splitter.count() for i in range(self.main_splitter.count())])

		self.setupMenuBar()

		self.preview_widget.hide()
		self.preview_widget.contentChanged.connect(lambda: self.preview_widget.show())


		# Set the custom exception handler
		sys.excepthook = self.handle_uncaught_exceptions

	def handle_uncaught_exceptions(self, exc_type, exc_value, exc_tb):
		# Extract the line number and other details
		# tb = traceback.extract_tb(exc_tb)
		# last_call = tb[-1]  # The last call in the traceback will be where the exception occurred
		# filename, lineno, funcname, text = last_call

		# # Logging or displaying exception details
		# # print(f"Exception occurred in {filename} at line {lineno}")
		# # print(f"Function: {funcname}")
		# # print(f"Code: {text}")
		
		# # You can also format the exception in a user-friendly way
		# formatted_traceback = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
		# msg = f"Error occurred at {filename} line {lineno}"
		# print(msg)
		# self.script_edit.insertNotification(lineno, f"Error occurred at {filename} line {lineno}")

		self.display_exception(exc_value)



	def updateWindowTitle(self):
		self.setWindowTitle(f"{Path(self.filepath).name if self.filepath else "untitled"} {'*' if self.script_edit.document().isModified() else ''} - LiveScript")

	def createContext(self):
		return {
			'__name__': "__live__",
			'__builtins__': globals()["__builtins__"]
		}

	def display_exception(self, e, prefix="", postfix=""):
		if isinstance(e, SyntaxError):
			text = " ".join([prefix, str(e.msg), postfix])
			if e.lineno:
				text = str(e.msg)
				if hasattr(e, 'offset'):
					text+= f" (offset: {e.offset})"
				if hasattr(e, 'start'):
					text+= f" (start: {e.start})"
				self.script_edit.insertNotification(e.lineno, text)
			self.log_window.appendError(text)
		else:
			tb = traceback.TracebackException.from_exception(e)
			last_frame = tb.stack[-1]
			if last_frame.lineno:
				self.script_edit.insertNotification(last_frame.lineno, str(e))

			formatted_traceback = ''.join(tb.format())
			text = " ".join([prefix, formatted_traceback, postfix])
			if hasattr(e, 'offset'):
				text+= f" (offset: {e.offset})"
			if hasattr(e, 'start'):
				text+= f" (start: {e.start})"
			self.log_window.appendError(text)

	def evaluate(self):
		if hasattr(self, '_sourcecode') and self._sourcecode == self.script_edit.toPlainText().strip():
			return

		self._sourcecode = self.script_edit.toPlainText().strip()
		self.preview_widget.clear()
		self.log_window.clear()
		global_vars = self.createContext()

		self.preview_widget.hide()
		self.script_edit.clearNotifications()
		

		try:
			start_time = time.perf_counter()
			the_ast = ast.parse(self._sourcecode, filename="<script>", type_comments=True)
			try:
				compiled = compile(the_ast, filename="<script>", mode="exec")
				exec(compiled, global_vars)
				end_time = time.perf_counter()
				duration_ms = (end_time - start_time) * 1000
				# self.log_window.appendMessage()
				self.statusbar.showMessage(f"exec took {duration_ms:.3f} ms")
			except SyntaxError as e: #compile syntax error
				self.display_exception(e, prefix="Syntax error while compiling:\n")
			except Exception as e: # compile exception
				self.display_exception(e, prefix="Error while compiling:\n")
		except SyntaxError as e: # parse syntax error
			self.display_exception(e, prefix="Syntax error while parsing:\n")
		except Exception as e:  # parse exception
			self.display_exception(e, prefix="Error while parsing:\n")

		gc.collect()

	def on_file_change(self, path):
		if self.script_edit.document().isModified():
			result = self.prompt_disk_change()
			if result == QMessageBox.StandardButton.Yes:
				pass
			else:
				return

		with open(path, 'r') as file:
			data = file.read()
			self.script_edit.setPlainText(data)
			self.script_edit.document().setModified(False)

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

	def setupStatusBar(self):
		self.statusbar = QStatusBar()
		self.layout().addWidget(self.statusbar)
		self.statusbar.showMessage("started")
		self.statusbar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
		
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
		new_file_action.triggered.connect(lambda: self.newFile())
		new_file_action.setShortcut(QKeySequence(Qt.Key.Key_Control | Qt.Key.Key_N))

		ope_file_action = QAction("Open File", self)
		ope_file_action.triggered.connect(lambda: self.openFile())
		ope_file_action.setShortcut(QKeySequence(Qt.Key.Key_Control | Qt.Key.Key_O))

		save_file_action = QAction("Save File", self)
		save_file_action.triggered.connect(lambda: self.saveFile())
		save_file_action.setShortcut(QKeySequence(Qt.Key.Key_Control | Qt.Key.Key_S))

		restart_action = QAction("Restart", self)
		restart_action.triggered.connect(lambda: self.restart())

		file_menu.addAction(new_file_action)
		file_menu.addAction(ope_file_action)
		file_menu.addAction(save_file_action)
		file_menu.addAction(restart_action)
		file_menu.addSeparator()

		for recent in self.config['recent']:
			open_recent_action = QAction(f"{recent}", self)
			open_recent_action.triggered.connect(lambda recent=recent: self.openFile(recent))
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

	def closeEvent(self, event):
		DoCloseFile = self.closeFile()
		if not DoCloseFile:
			event.ignore()
			return
		event.accept()

	def closeFile(self)->bool:
		AcceptClose = True
		if self.script_edit.document().isModified():
			# prompt user if file has changed
			msg_box = QMessageBox(self)
			msg_box.setWindowTitle("Save changes?")
			msg_box.setText(f"{Path(self.filepath).name if self.filepath else "Script"} has benn modified, save changes?")
			msg_box.setIcon(QMessageBox.Icon.Warning)
			msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel)
			result = msg_box.exec()

			match result:
				case QMessageBox.StandardButton.Yes:
					self.saveFile()
				case QMessageBox.StandardButton.No:
					pass
				case QMessageBox.StandardButton.Cancel:
					AcceptClose = False

		if AcceptClose:
			if self.watcher.files():
				self.watcher.removePaths(self.watcher.files())
			self.filepath = None
			self.script_edit.setPlainText("")
			self.script_edit.document().setModified(False)
			self.updateWindowTitle()

		return AcceptClose

	def newFile(self):
		self.closeFile()

	def saveFile(self, filepath:str|None=None):
		assert filepath is None or isinstance(filepath, str), f"got:, {filepath}"
		DoSaveAs = self.filepath!=filepath
		if DoSaveAs:
			...
		
		if not self.filepath or filepath:
			choosen_filepath, filter_used = QFileDialog.getSaveFileName(self, "Save", ".py", "Python Script (*.py);;Any File (*)")
			if not choosen_filepath:
				return # if no filepath was choosen cancel saving
			filepath = choosen_filepath
		elif self.filepath:
			filepath = self.filepath

		if not filepath:
			return

		self.watcher.blockSignals(True)
		try:
			with open(filepath, 'w') as file:
				file.write(self.script_edit.toPlainText())
				self.script_modified_in_memory = False
			self.config['recent'].append(filepath)
			self.saveConfig()
		except FileNotFoundError:
			pass
		self.watcher.blockSignals(False)
		self.filepath = filepath
		self.updateWindowTitle()

	def openFile(self, filepath:str|None=None):
		# close current file
		self.closeFile()

		if not filepath:
			# if not filepath is specified open file doalog
			choosen_filepath, filter_used = QFileDialog.getOpenFileName(self, "Open", ".py", "Python Script (*.py);;Any File (*)")
			filepath = choosen_filepath

		# open filepath
		if not filepath:
			return
		
		try:
			with open(filepath, 'r') as file:
				text = file.read()
				self.script_edit.setPlainText(text)
				self.script_edit.document().setModified(False)
				self.filepath = filepath

				if filepath in self.config['recent']:
					self.config['recent'] = [path for path in self.config['recent'] if path!=filepath]

				self.config['recent'].append(filepath)
				self.saveConfig()
				self.watcher.addPath(filepath)
		except FileNotFoundError:
			self.config['recent'].remove(filepath)

		self.filepath = filepath
		self.updateWindowTitle()

	def prompt_disk_change(self):
		msg_box = QMessageBox(self)
		msg_box.setWindowTitle("File has changed on Disk.")
		msg_box.setText("Do you want to reload?")
		msg_box.setIcon(QMessageBox.Icon.Question)
		msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
		# temporary block _file change_ signals, to ignore multiple changes when
		# the messagebox is already open
		self.watcher.blockSignals(True) 
		result = msg_box.exec()
		self.watcher.blockSignals(False)
		return result

	def restart(self):
		self.closeFile()
		import sys
		print("argv was",sys.argv)
		print("sys.executable was", sys.executable)
		print("restart now")

		import os
		os.execv(sys.executable, ['python'] + sys.argv)

if __name__ == "__main__":
	import sys
	app = QApplication(sys.argv)
	window = LiveScript()
	window.show()
	sys.exit(app.exec())
