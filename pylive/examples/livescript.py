from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *


from pathlib import Path
from datetime import datetime
import time
import humanize

from pylive.QtScriptEditor.script_edit import ScriptEdit
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
from pylive.examples import livescript
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
		self.watcher.fileChanged.connect(lambda: 
			self.on_file_change(self.filepath)
		)

		# setup from config
		self.loadConfig()
		if self.config()['open_recent_file']:
			if recent:=self.config()['recent']:
				self.openFile(recent[-1])

		# setup menubar
		self.script_edit.document().modificationChanged.connect(
			lambda: self.updateWindowTitle()
		)

		self.main_splitter.addWidget(self.script_edit)

		self.right_panel = QSplitter(Qt.Orientation.Vertical, self)
		self.right_panel.addWidget(self.preview_widget)
		self.right_panel.addWidget(self.log_window)
		self.right_panel.setStretchFactor(0,100)
		self.right_panel.setStretchFactor(1,0)

		self.main_splitter.addWidget(self.right_panel)

		if self.main_splitter.count()>0:
			self.main_splitter.setSizes([
				self.width()//self.main_splitter.count() 
				for i in range(self.main_splitter.count())
			])

		self.setupMenuBar()

		self.preview_widget.hide()
		self.preview_widget.contentChanged.connect(
			lambda: self.preview_widget.show()
		)


		# Set the custom exception handler
		sys.excepthook = self.handle_uncaught_exceptions

	def config(self):

		config = {
			"open_recent_file":False,
			"recent": [],
			"live": True
		}
		config.update(self._config)
		return config


	def saveConfig(self):
		import json
		with open("./livescript.init", 'w') as file:
			file.write(json.dumps(self.config(), indent=2))
			
	def loadConfig(self):
		import json
		try:
			with open("./livescript.init", 'r') as file:
				self._config = json.loads(file.read())
		except FileNotFoundError as err:
			...

	def handle_uncaught_exceptions(self, exc_type, exc_value, exc_tb):
		self.display_exception(exc_value)

	def updateWindowTitle(self):
		filename = Path(self.filepath).name if self.filepath else "untitled"
		modified_mark = '*' if self.script_edit.document().isModified() else ''
		self.setWindowTitle(f"{filename} {modified_mark} - LiveScript")

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
				self.script_edit.linter.underline(e.lineno, text)
			self.log_window.appendError(text)
		else:
			tb = traceback.TracebackException.from_exception(e)
			last_frame = tb.stack[-1]
			if last_frame.lineno:
				self.script_edit.linter.underline(last_frame.lineno, str(e))

			formatted_traceback = ''.join(tb.format())
			text = " ".join([prefix, formatted_traceback, postfix])
			if hasattr(e, 'offset'):
				text+= f" (offset: {e.offset})"
			if hasattr(e, 'start'):
				text+= f" (start: {e.start})"
			self.log_window.appendError(text)

	def evaluate(self):
		CachedSource = getattr(self, '_sourcecode', "").strip()
		CurrentSource = self.script_edit.toPlainText().strip()
		if CurrentSource == CachedSource:
			return

		self._sourcecode = self.script_edit.toPlainText()
		self.preview_widget.clear()
		self.log_window.clear()
		global_vars = self.createContext()

		self.preview_widget.hide()
		self.script_edit.linter.clear()

		try:
			start_time = time.perf_counter()
			the_ast = ast.parse(self._sourcecode, 
				filename="<script>", 
				type_comments=True)
			try:
				compiled = compile(the_ast, 
					filename="<script>", 
					mode="exec")
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
		print("on file change", path)

		def reload_script():
			# reload the file changed on disk
			assert self.filepath
			with open(self.filepath, 'r') as file:
				data = file.read()
				self.script_edit.setPlainText(data)
				self.script_edit.document().setModified(False)

		if not self.script_edit.document().isModified():
			"""
			When the script is not modified in the editor,
			silently reload the file changed on disk!
			"""
			reload_script()
		else:
			"""
			Notify the user that the file haschanged on disk,
			and ask if they want to reload it?
			"""
			msg_box = QMessageBox(self)
			msg_box.setWindowTitle("File has changed on Disk.")
			msg_box.setText("Do you want to reload?")
			msg_box.setIcon(QMessageBox.Icon.Question)
			msg_box.setStandardButtons(
				QMessageBox.StandardButton.Yes |
				QMessageBox.StandardButton.No
			)
			"""
			Temporary block _file change_ signals, to ignore multiple changes
			when the messagebox is already open
			"""
			self.watcher.blockSignals(True) 
			result = msg_box.exec()
			self.watcher.blockSignals(False)

			if result == QMessageBox.StandardButton.Yes:
				reload_script()

	def setupStatusBar(self):
		self.statusbar = QStatusBar()
		self.layout().addWidget(self.statusbar)
		self.statusbar.showMessage("started")
		self.statusbar.setSizePolicy(QSizePolicy.Policy.Expanding,
			QSizePolicy.Policy.Maximum)
		
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
		new_file_action.setShortcut(QKeySequence.StandardKey.New)

		ope_file_action = QAction("Open File", self)
		ope_file_action.triggered.connect(lambda: self.openFile())
		ope_file_action.setShortcut(QKeySequence.StandardKey.Open)

		save_file_action = QAction("Save File", self)
		save_file_action.triggered.connect(lambda: self.saveFile())
		save_file_action.setShortcut(QKeySequence.StandardKey.Save)

		restart_action = QAction("Restart", self)
		restart_action.triggered.connect(lambda: self.restart())
		restart_action.setShortcut(QKeySequence.StandardKey.Refresh)

		file_menu.addAction(new_file_action)
		file_menu.addAction(ope_file_action)
		file_menu.addAction(save_file_action)
		file_menu.addAction(restart_action)
		file_menu.addSeparator()

		for recent in self.config()['recent']:
			open_recent_action = QAction(f"{recent}", self)
			open_recent_action.triggered.connect(
				lambda recent=recent: self.openFile(recent)
			)
			file_menu.addAction(open_recent_action)

		"""Edit menu"""
		edit_menu  = self.menu_bar.addMenu("Edit")
		copy_action = QAction("Copy", self)
		copy_action.triggered.connect(self.script_edit.copy)
		copy_action.setShortcut(QKeySequence.StandardKey.Copy)
		cut_action = QAction("Cut", self)
		cut_action.triggered.connect(self.script_edit.cut)
		cut_action.setShortcut(QKeySequence.StandardKey.Cut)
		paste_action = QAction("Paste", self)
		paste_action.triggered.connect(self.script_edit.paste)
		paste_action.setShortcut(QKeySequence.StandardKey.Paste)
		toggle_comments_action = QAction("toggle comments", self)
		toggle_comments_action.setShortcut("Ctrl+/")
		toggle_comments_action.triggered.connect(self.script_edit.toggleComment)

		edit_menu.addAction(cut_action)
		edit_menu.addAction(paste_action)
		edit_menu.addAction(toggle_comments_action)

		""" View menu """
		view_menu = self.menu_bar.addMenu("View")
		zoom_in_action = QAction("Zoom In", self)
		zoom_in_action.setShortcut(QKeySequence.StandardKey.ZoomIn)
		zoom_in_action.triggered.connect(lambda:
			self.increaseFontSize()
		)
		zoom_out_action = QAction("Zoom Out", self)
		zoom_out_action.triggered.connect(lambda:
			self.decreaseFontSize()
		)
		zoom_out_action.setShortcut(QKeySequence.StandardKey.ZoomOut)

		view_menu.addAction(zoom_in_action)
		view_menu.addAction(zoom_out_action)

		"""Template menu"""
		template_menu  = self.menu_bar.addMenu("Templates")
		insert_template_action = QAction("insert template", self)
		insert_template_action.triggered.connect(lambda: 
			self.script_edit.insertPlainText(TEMPLATE_SCRIPT)
		)

		# Add actions to Edit menu
		template_menu.addAction(insert_template_action)

		self.layout().setMenuBar(self.menu_bar)

	def increaseFontSize(self):
		font = QApplication.font()
		font.setPointSize(font.pointSize()+2)
		QApplication.setFont(font)

	def decreaseFontSize(self):
		font = QApplication.font()
		font.setPointSize(font.pointSize()-2)
		QApplication.setFont(font)

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
			filename = Path(self.filepath).name if self.filepath else "Script"
			msg_box.setText(f"{filename} has been modified, save changes?")
			msg_box.setIcon(QMessageBox.Icon.Warning)
			msg_box.setStandardButtons(
				QMessageBox.StandardButton.Yes | 
				QMessageBox.StandardButton.No | 
				QMessageBox.StandardButton.Cancel
			)
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
			self._config['open_recent_file'] = False

		return AcceptClose

	def newFile(self):
		self.closeFile()

	def saveFile(self, filepath:str|None=None):
		assert filepath is None or isinstance(filepath, str), f"got:, {filepath}"
		DoSaveAs = self.filepath!=filepath
		if DoSaveAs:
			...
		
		if not self.filepath or filepath:
			choosen_filepath, filter_used = QFileDialog.getSaveFileName(self, 
				"Save", ".py", "Python Script (*.py);;Any File (*)")
			if not choosen_filepath:
				return # if no filepath was choosen cancel saving
			filepath = choosen_filepath
		elif self.filepath:
			filepath = self.filepath

		if not filepath:
			return

		""" note
		We must stop watching this file, otherwise it will silently reload the
		script. It reloads silently, because if the document is not modified,
		and the file has been changed, it will silently reload the script.
		"""
		self.watcher.removePath(filepath) 
		try:
			with open(filepath, 'w') as file:
				file.write(self.script_edit.toPlainText())
				self.script_edit.document().setModified(False)
			self._config['recent'].append(filepath)
			self.saveConfig()
		except FileNotFoundError:
			pass
		self.watcher.addPath(filepath)
		self.filepath = filepath
		self.updateWindowTitle()

	def openFile(self, filepath:str|None=None):
		# close current file
		self.closeFile()

		if not filepath:
			# if not filepath is specified open file doalog
			choosen_filepath, filter_used = QFileDialog.getOpenFileName(self, 
				"Open", ".py", "Python Script (*.py);;Any File (*)")
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

				if filepath in self.config()['recent']:
					self._config['recent'] = [path for path
						in self.config()['recent'] 
						if path!=filepath]

				self._config['recent'].append(filepath)
				self._config['open_recent_file'] = True
				self.saveConfig()
				self.watcher.addPath(filepath)
		except FileNotFoundError:
			self._config['recent'].remove(filepath)

		self.filepath = filepath
		self.updateWindowTitle()


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
