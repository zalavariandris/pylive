from graphmodel_columnbased import (
	GraphModel,
	NodeAttribute, InletAttribute,
	NodeRef, OutletAttribute, EdgeAttribute
)

from graphview_columnbased import (
	StandardGraphView, StandardNodeItem,
	EditableTextItem
)

from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *


class MindMap(StandardGraphView):
	def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
		graph = self.model()
		if graph and not self.itemAt(event.position().toPoint()):
			clickpos = self.mapToScene(event.position().toPoint())
			node = graph.addNode("Idea", int(clickpos.x()), int(clickpos.y()))
			graph.addInlet(node, "in")
			graph.addOutlet(node, "out")
		else:
			return super().mouseDoubleClickEvent(event)

	def nodeFactory(self, node: NodeRef) -> QGraphicsItem:
		node_item = super().nodeFactory(node)
		scriptedit = EditableTextItem(node_item)
		node_item.scriptedit = scriptedit
		scriptedit.setPos(0,30)
		scriptedit.setTextWidth(node_item.rect.width()-10)

		scriptedit.setPlainText("#Script")
		scriptedit.document().contentsChanged.connect(lambda: 
			self.onNodeEditorChange(node, node_item, ["script"])
		)
		return node_item

	def onNodeDataChange(self, node:NodeRef, node_item:QGraphicsItem, attributes:List[NodeAttribute|str]):
		graph = self.model()
		node_item = cast(StandardNodeItem, self.index_to_item_map[node])
		if not graph:
			return
		super().onNodeDataChange(node, node_item, attributes)

	def onNodeEditorChange(self, node:NodeRef, node_item:QGraphicsItem, attributes:List[NodeAttribute|str]):
		super().onNodeEditorChange(node, node_item, attributes)
		graph = self.model()
		node_item = cast(StandardNodeItem, self.index_to_item_map[node])
		if not graph:
			return

class MainWindow(QWidget):
	def __init__(self, parent: Optional[QWidget]=None) -> None:
		super().__init__(parent)

		self.setWindowTitle("MindMap")

		self.model = GraphModel()
		self.graphview = MindMap()
		self.graphview.setModel(self.model)
		self.graphview2 = MindMap()
		self.graphview2.setModel(self.model)

		mainLayout = QHBoxLayout()
		self.setLayout(mainLayout)
		mainLayout.addWidget(self.graphview)
		mainLayout.addWidget(self.graphview2)

if __name__ == "__main__":
	import sys
	app = QApplication(sys.argv)
	window = MainWindow()
	window.show()
	sys.exit(app.exec())