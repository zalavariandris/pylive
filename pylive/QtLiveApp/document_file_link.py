from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from pathlib import Path

# TODO Replace with DocumentFileLink
class DocumentFileLink(QObject):
	filepathChanged = Signal() # emit when a file opened
	def __init__(self, document, filepath=None, parent:Optional[QObject]=None) -> None:
		super().__init__(parent=parent)
		self._filepath: Optional[str] = filepath
		self._document:QTextDocument = document
		self.watcher = QFileSystemWatcher()
		self.watcher.fileChanged.connect(lambda:
			self.onFileChanged(self._filepath))

		self.setFileFilter(".py")
		self.setFileSelectFilter("Python Script (*.py);;Any File (*)")

	def onFileChanged(self, path):
		assert path == self._filepath
		assert self._document is not None

		def reload_script():
			# reload the file changed on disk
			assert self._filepath
			with open(self._filepath, 'r') as file:
				data = file.read()
				self._document.setPlainText(data)
				self._document.setModified(False)

		if not self._document.isModified():
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
			msg_box = QMessageBox(self.parentWidget())
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

	def closeFile(self)->bool:
		AcceptClose = True
		if self._document.isModified():
			# prompt user if file has changed
			msg_box = QMessageBox(parent=self.parentWidget())
			msg_box.setWindowTitle("Save changes?")
			filename = Path(self._filepath).name if self._filepath else "Script"
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
			self._filepath = None
			self._document.setPlainText("")
			self._document.setModified(False)

		return AcceptClose

	def parentWidget(self)->QWidget|None:
		parent = self.parent()
		if isinstance( parent, QWidget ):
			return parent
		else:
			return None

	def setFileFilter(self, file_filter:str):
		self._file_filter = file_filter

	def fileFilter(self):
		"""default: '.py'"""
		return self._file_filter

	def setFileSelectFilter(self, select_filter:str):
		"""default: "Python Script (*.py);;Any File (*)"""
		self._select_filter = select_filter

	def fileSelectFilter(self):
		"""default: "Python Script (*.py);;Any File (*)"""
		return self._select_filter

	def filepath(self):
		return self._filepath

	def saveFile(self, filepath:str|None=None):
		assert filepath is None or isinstance(filepath, str), f"got:, {filepath}"
		DoSaveAs = self._filepath!=filepath

		if DoSaveAs:
			...
		
		if not self._filepath or filepath:
			choosen_filepath, filter_used = QFileDialog.getSaveFileName(self.parentWidget(), 
				"Save", self.fileFilter(), self.fileSelectFilter())
			if not choosen_filepath:
				return # if no filepath was choosen cancel saving
			filepath = choosen_filepath
		elif self._filepath:
			filepath = self._filepath

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
				file.write(self._document.toPlainText())
				self._document.setModified(False)
		except FileNotFoundError:
			pass
		self.watcher.addPath(filepath)
		self._filepath = filepath

	def openFile(self, filepath:str|None=None):
		# close current file
		self.closeFile()

		if not filepath:
			# if not filepath is specified open file doalog
			choosen_filepath, filter_used = QFileDialog.getOpenFileName(self.parentWidget(), 
				"Open", self.fileFilter(), self.fileSelectFilter())
			filepath = choosen_filepath

		# open filepath
		if not filepath:
			return
		
		try:
			with open(filepath, 'r') as file:
				text = file.read()
				self._document.setPlainText(text)
				self._document.setModified(False)
				self._filepath = filepath

				self.watcher.addPath(filepath)
		except FileNotFoundError:
			pass

		self._filepath = filepath
		self.filepathChanged.emit()

	def createFileMenu(self):
		new_file_action = QAction("New File", self)
		new_file_action.triggered.connect(lambda: self.closeFile())
		new_file_action.setShortcut(QKeySequence.StandardKey.New)

		open_file_action = QAction("Open File", self)
		open_file_action.triggered.connect(lambda: self.openFile())
		open_file_action.setShortcut(QKeySequence.StandardKey.Open)

		save_file_action = QAction("Save File", self)
		save_file_action.triggered.connect(lambda: self.saveFile())
		save_file_action.setShortcut(QKeySequence.StandardKey.Save)

		filemenu = QMenu("File")
		filemenu.addAction(new_file_action)
		filemenu.addAction(open_file_action)
		filemenu.addAction(save_file_action)
		return filemenu


if __name__ == "__main__":
	import sys
	app = QApplication(sys.argv)

	class Window(QWidget):
		def __init__(self, parent: Optional[QWidget]=None) -> None:
			super().__init__(parent)

			self.setWindowTitle("FileLink example")

			layout = QHBoxLayout()
			self.setLayout(layout)
			self.document = QTextDocument()
			self.document.setDocumentLayout(QPlainTextDocumentLayout(self.document))

			editor = QPlainTextEdit()
			editor.setDocument(self.document)
			def setup_textedit(textedit):
				textedit.setWindowTitle("ScriptTextEdit")
				textedit.setWordWrapMode(QTextOption.WrapMode.NoWrap)
				textedit.setTabChangesFocus(False)
				font = textedit.font()
				font.setFamilies(["monospace"])
				font.setStyleHint(QFont.StyleHint.TypeWriter);
				font.setPointSize(12)
				font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
				textedit.setFont(font)
				textedit.setTabStopDistance(QFontMetricsF(textedit.font()).horizontalAdvance(' ') * 4)
			setup_textedit(editor)

			layout.addWidget(editor)

			self.fileLink = DocumentFileLink(self.document, parent=self)
			self.fileLink.openFile("C:/dev/src/pylive/script_examples_to_run_live/glcanvas_widget_with_moderngl.py")

			self.document.modificationChanged.connect(self.updateWindowTitle)
			self.updateWindowTitle()

			self.setupMenuBar()

		def setupMenuBar(self):
			menubar = QMenuBar(self)
			menubar.setStyleSheet("""
				QMenuBar::item {
					padding: 0px 8px;  /* Adjust padding for the normal state */
				}
				QMenuBar::item:selected {  /* Hover state */
					padding: 0px 0px;  /* Ensure the same padding applies to the hover state */
				}
			""")

			"""File menu"""
			filemenu = self.fileLink.createFileMenu()

			menubar.addMenu(filemenu)
			layout = self.layout()
			layout.setMenuBar(menubar)

		def updateWindowTitle(self):
			file_title = "untitled"
			if self.fileLink.filepath:
				file_title = Path(self.fileLink.filepath).name

			modified_mark = ""
			if self.document.isModified():
				modified_mark = "*"

			self.setWindowTitle(f"{file_title} {modified_mark} - FileLink")

		def closeEvent(self, event):
			DoCloseFile = self.fileLink.closeFile()
			if not DoCloseFile:
				event.ignore()
				return

			event.accept()




	window = Window()
	window.show()

	# launch QApp
	sys.exit(app.exec())