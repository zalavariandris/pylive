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
		self.timer.start(1000) #ms

	def animate(self):
		print("animate", time.time())

if __name__ == "__live__":
	from pylive.preview_widget import PreviewWidget
	preview = PreviewWidget.instance()
	preview.display(MyWidget())
