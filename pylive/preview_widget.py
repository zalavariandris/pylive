from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

class SingletonException(Exception):
	...

class PreviewWidget(QWidget):
	_instance: Optional['PreviewWidget'] = None
	contentChanged = Signal()

	@staticmethod
	def instance() -> 'PreviewWidget':
		"""
		Factory method to get the singleton instance of PreviewWidget.
		"""
		if PreviewWidget._instance is None:
			# Create the instance if it doesn't exist
			PreviewWidget._instance = PreviewWidget.__new__(PreviewWidget)
			PreviewWidget._instance._setupUI()
		return PreviewWidget._instance

	def __init__(self, parent: Optional[QWidget] = None) -> None:
		"""
		Disable direct instantiation. Use instance() method instead.
		"""
		raise SingletonException("Singleon can cannot be instantiated directly. Use the 'instance()' static method!")

	def _setupUI(self) -> None:
		"""
		Initialize the instance. Called only once by the factory method.
		"""
		QWidget.__init__(self, parent=None)
		self.setObjectName("PREVIEW_WINDOW_ID")
		self.statusLabel = QLabel()

		self.previewFrame = QWidget()
		self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

		self.previewFrame.setLayout(QVBoxLayout())
		self.previewFrame.layout().setContentsMargins(0, 0, 0, 0)

		self.previewScrollArea = QScrollArea()
		self.previewScrollArea.setContentsMargins(0, 0, 0, 0)
		self.previewScrollArea.setWidget(self.previewFrame)
		self.previewScrollArea.setWidgetResizable(True)

		mainLayout = QVBoxLayout()
		self.setLayout(mainLayout)
		mainLayout.setContentsMargins(0, 0, 0, 0)
		mainLayout.addWidget(self.previewScrollArea, 1)

	def display(self, data:Any):
		match data:
			case str():
				self.previewFrame.layout().addWidget(QLabel(data))
			case QImage():
				pixlabel = QLabel()
				pixmap = QPixmap()
				pixmap.convertFromImage(data)
				pixlabel.setPixmap(pixmap)
				self.previewFrame.layout().addWidget(pixlabel)
			case QPixmap():
				pixlabel = QLabel()
				pixlabel.setPixmap(data)
				self.previewFrame.layout().addWidget(pixlabel)
			case QWidget():
				self.previewFrame.layout().addWidget(data)
			case _:
				self.previewFrame.layout().addWidget(QLabel(str(data)))

		self.contentChanged.emit()

	def clear(self):
		layout = self.previewFrame.layout()
		for i in reversed(range(layout.count())): 
			layout.itemAt(i).widget().deleteLater()

		self.contentChanged.emit()


if __name__ == "__main__":
	from pylive import livescript
	import sys
	app = QApplication(sys.argv)
	window = QWidget()
	window.setWindowTitle("demonstrate PreviewWidget.instance()")
	layout = QHBoxLayout()
	window.setLayout(layout)
	layout.addWidget(QLabel("left pane"))
	layout.addWidget( PreviewWidget.instance() )
	window.show()
	sys.exit(app.exec())