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


if __name__ == "__main__":
	import sys
	app = QApplication.instance() or QApplication(sys.argv)	

	# initalize your widgets here
	...
	from pylive.preview_widget import PreviewWidget
	widget = MyWidget()
	preview = PreviewWidget.instance()
	preview.display(widget)
	preview.show()

	if not QApplication.startingUp():
	    app.exec()

