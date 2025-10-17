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
		
	def paintEvent(self, event):
		painter = QPainter(self)

		# Set up the painter (e.g., pen and brush)
		painter.setPen(QPen(QColor("blue"), 3, Qt.SolidLine))
		painter.setBrush(QColor(200, 100, 255))

		# Draw a rectangle
		painter.drawRect(50, 50, 300, 200)

		# Draw a circle
		painter.setPen(QPen(QColor("red"), 2))
		painter.setBrush(QColor(255, 200, 200))
		painter.drawEllipse(100, 100, 100, 100)

		# Draw some text
		painter.setPen(QColor("green"))
		painter.setFont(painter.font())
		painter.drawText(event.rect(), Qt.AlignCenter, "Hello, PySide6!")

if __name__ == "__live__":
	from pylive.preview_widget import PreviewWidget
	preview = PreviewWidget.instance()
	preview.display(MyWidget())

if __name__ == "__main__":
	...

