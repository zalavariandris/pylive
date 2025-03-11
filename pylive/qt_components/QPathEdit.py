from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from pathlib import Path
class QPathEdit(QLineEdit):
	def __init__(self, 
		contents:str="", 
		parent:QWidget|None=None
	):
		super().__init__(contents, parent=parent)
		self.setClearButtonEnabled(True)
		dir_pixmap = self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon)
		action = self.addAction(dir_pixmap, QLineEdit.ActionPosition.TrailingPosition)
		action.triggered.connect(self.open)

	def open(self):
		selected, selected_filter = QFileDialog.getOpenFileName(self)
		self.setText(str(selected))

		## todo: conider imlementing
		# - validator
		# - autocomplete

	def path(self)->Path:
		return Path(self.text())

	def setPath(self, path:Path|str):
		self.setText(str(path))

if __name__ == "__main__":
	app = QApplication()
	window = QWidget()
	main_layout = QVBoxLayout()
	window.setLayout(main_layout)
	path_edit = QPathEdit()

	main_layout.addWidget(path_edit)
	window.show()
	app.exec()