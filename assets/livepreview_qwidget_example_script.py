from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

class MyWidget(QWidget):
	def __init__(self, parent=None):
		super().__init__(parent=parent)
		self.setLayout(QVBoxLayout())
		self.layout().addWidget(QLabel("my widget"))


