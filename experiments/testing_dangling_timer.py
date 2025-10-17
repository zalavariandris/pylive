from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from pylive import livescript
from typing import *

import time
class MyWidget(QWidget):
	def __init__(self, parent=None):
		super().__init__(parent=parent)
		self.timer = QTimer()
		self.timer.timeout.connect(self.animate)
		self.timer.start(985//62) #ms
		
		mainLayout = QHBoxLayout()
		self.setLayout(mainLayout)
		self.time_label = QLabel(self)
		mainLayout.addWidget(self.time_label)
		self.time_label.setText(f"{time.time()}")

	def animate(self):
		...
		print("animate", time.time())
		self.time_label.setText(f"{time.time()}")

if __name__ == "__live__":
	from pylive.preview_widget import PreviewWidget
	preview = PreviewWidget.instance()
	preview.display(MyWidget())