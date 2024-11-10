from graphmodel_columnbased import (
	GraphModel,
	NodeAttribute, InletAttribute, OutletAttribute, EdgeAttribute
)

from graphview_columnbased import (
	GraphView
)

from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *


class MindMap(GraphView):
	def __init__(self, parent=None):
		super().__init__(parent)

	def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
		graph = self.model()
		if graph and not self.itemAt(event.position().toPoint()):
			clickpos = self.mapToScene(event.position().toPoint())
			node = graph.addNode("Idea", int(clickpos.x()), int(clickpos.y()))
			graph.addInlet(node, "in")
			graph.addOutlet(node, "out")
		else:
			return super().mouseDoubleClickEvent(event)

class MainWindow(QWidget):
	def __init__(self, parent: Optional[QWidget]=None) -> None:
		super().__init__(parent)

		self.setWindowTitle("MindMap")

		self.model = GraphModel()
		self.graphview = MindMap()
		self.graphview.setModel(self.model)

		mainLayout = QHBoxLayout()
		self.setLayout(mainLayout)
		mainLayout.addWidget(self.graphview)

if __name__ == "__main__":
	import sys
	app = QApplication(sys.argv)
	window = MainWindow()
	window.show()
	sys.exit(app.exec())