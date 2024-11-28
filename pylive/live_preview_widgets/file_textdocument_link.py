from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from pathlib import Path


class FileTextDocumentLink(QObject):
	def __init__(self, filepath, document, widget: Optional[QWidget] = None) -> None:
		super().__init__(widget)
		self._widget = widget
		self.filepath = filepath
		self.document = document

		self.watcher = QFileSystemWatcher()
		self.watcher.fileChanged.connect(lambda:
			self.fileChangedEvent(self.filepath))

	def fileChangedEvent(self, path):
		assert path == self.filepath
		assert self.document is not None

		def reload_script():
			# reload the file changed on disk
			assert self.filepath
			with open(self.filepath, 'r') as file:
				data = file.read()
				self.document.setPlainText(data)
				self.document.setModified(False)

		if not self.document.isModified():
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
			msg_box = QMessageBox(self._widget)
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
		if self.document.isModified():
			# prompt user if file has changed
			msg_box = QMessageBox(self._widget)
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
			self.document.setPlainText("")
			self.document.setModified(False)

		return AcceptClose

	def newFile(self):
		self.closeFile()

	def saveFile(self, filepath:str|None=None):
		assert filepath is None or isinstance(filepath, str), f"got:, {filepath}"
		DoSaveAs = self.filepath!=filepath
		if DoSaveAs:
			...
		
		if not self.filepath or filepath:
			choosen_filepath, filter_used = QFileDialog.getSaveFileName(self._widget, 
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
				file.write(self.document.toPlainText())
				self.document.setModified(False)
		except FileNotFoundError:
			pass
		self.watcher.addPath(filepath)
		self.filepath = filepath

	def openFile(self, filepath:str|None=None):
		# close current file
		self.closeFile()

		if not filepath:
			# if not filepath is specified open file doalog
			choosen_filepath, filter_used = QFileDialog.getOpenFileName(self._widget, 
				"Open", ".py", "Python Script (*.py);;Any File (*)")
			filepath = choosen_filepath

		# open filepath
		if not filepath:
			return
		
		try:
			with open(filepath, 'r') as file:
				text = file.read()
				self.document.setPlainText(text)
				self.document.setModified(False)
				self.filepath = filepath

				self.watcher.addPath(filepath)
		except FileNotFoundError:
			pass

		self.filepath = filepath