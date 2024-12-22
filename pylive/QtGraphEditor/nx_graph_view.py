from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import * 

from pylive.QtGraphEditor.nx_graph_model import NXGraphModel
from pylive.QtGraphEditor.nx_graph_selection_model import NXGraphSelectionModel
from pylive.QtGraphEditor.dag_graph_graphics_scene import DAGScene

class NXGraphView(QGraphicsView):
	def __init__(self, parent:QWidget|None=None):
		super().__init__(parent=parent)
		self.graphScene = DAGScene()
		self.setScene(self.graphScene)
		self._model:NXGraphModel|None = None
		self._selectionModel:NXGraphSelectionModel|None = None

	def setModel(self, model:NXGraphModel):
		self._model = model

	def setSelectionModel(self, selectionModel:NXGraphSelectionModel):
		self._selectionModel = selectionModel

class NXInspectorView(QWidget):
	def __init__(self, parent:QWidget|None=None):
		super().__init__(parent=parent)
		self._model:NXGraphModel|None = None
		self._selectionModel:NXGraphSelectionModel|None = None

	def setModel(self, model:NXGraphModel):
		self._model = model

	def setSelectionModel(self, selectionModel:NXGraphSelectionModel):
		self._selectionModel = selectionModel

if __name__ == "__main__":
	class NXWindow(QWidget):
		def __init__(self, parent: QWidget|None=None) -> None:
			super().__init__(parent)
			self.setWindowTitle("NX Graph Editor")
			self.model = NXGraphModel()
			self.selectionmodel = NXGraphSelectionModel()
			self.graphview = NXGraphView()
			self.graphview.setModel(self.model)
			self.inspector = NXInspectorView()
			self.inspector.setModel(self.model)

			mainLayout = QVBoxLayout()
			splitter = QSplitter()
			mainLayout.addWidget(splitter)
			splitter.addWidget(self.graphview)
			splitter.addWidget(self.inspector)
			splitter.setSizes([splitter.width()//splitter.count() for _ in range(splitter.count())])
			self.setLayout(mainLayout)

	app = QApplication()
	window = NXWindow()
	window.show()
	app.exec()