from graphmodel_columnbased import (
	GraphModel,
	NodeAttribute, InletAttribute,
	NodeRef, OutletAttribute, EdgeAttribute
)

from graphview_columnbased import (
	NodeGraphicsItem, GraphView, StandardGraphView, StandardNodeItem,
	EditableTextItem
)

from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *


class MindNodeItem(NodeGraphicsItem):
		def __init__(self, parent_graph: "GraphView"):
			# model reference
			# self.persistent_node_index:Optional[NodeRef] = None
			super().__init__(parent_graph)

			# widgets
			self.nameedit = EditableTextItem(self)
			self.nameedit.setPos(0,0)
			self.nameedit.setTextWidth(self.rect.width()-10)
			

class MindGraphView(GraphView):
	def nodeFactory(self, node:NodeRef)->QGraphicsItem:
		node_item = MindNodeItem(parent_graph=self)
		
		node_item.nameedit.document().contentsChanged.connect(lambda: 
			self.onNodeEditorChange(node, node_item, [NodeAttribute.Name])
		)

		node_item.positionChanged.connect(lambda: 
			self.onNodeEditorChange(node, node_item, [NodeAttribute.LocationX, NodeAttribute.LocationY])
		)

		return node_item

	def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
		graph = self.model()
		if graph and not self.itemAt(event.position().toPoint()):
			clickpos = self.mapToScene(event.position().toPoint())
			node = graph.addNode("Idea", int(clickpos.x()), int(clickpos.y()))
			graph.setNodeData(node, "# title", "title")
			graph.setNodeData(node, "<body>", "body")
			graph.addInlet(node, "in")
			graph.addOutlet(node, "out")
		else:
			return super().mouseDoubleClickEvent(event)

	def onNodeDataChange(self, node:NodeRef, node_item:QGraphicsItem, attributes:List[NodeAttribute|str]):
		print("node data changed", attributes)
		graph = self.model()
		node_item = cast(MindNodeItem, node_item)
		if not graph:
			return

		if 'body' in attributes:
			new_name = node.graph().getNodeData(node, 'body')
			old_name = node_item.nameedit.toPlainText()
			if old_name != new_name:
				node_item.nameedit.setPlainText(new_name)

		if NodeAttribute.LocationX in attributes or NodeAttribute.LocationY in attributes:
			x = int(node.graph().getNodeData(node, NodeAttribute.LocationX))
			y = int(node.graph().getNodeData(node, NodeAttribute.LocationY))
			node_item.setPos(x,y)

	def onNodeEditorChange(self, node:NodeRef, node_item:QGraphicsItem, attributes:List[NodeAttribute|str]):
		graph = self.model()
		node_item = cast(MindNodeItem, self.index_to_item_map[node])
		if not graph:
			return

		if "body" in attributes:
			graph.setNodeData(node, node_item.nameedit.toPlainText(), 'body')

		if NodeAttribute.LocationX in attributes or NodeAttribute.LocationY in attributes:
			graph.blockSignals(True)
			graph.setNodeData(node, int(node_item.x()), NodeAttribute.LocationX)
			graph.setNodeData(node, int(node_item.y()), NodeAttribute.LocationY)
			graph.blockSignals(False)
			graph.nodesDataChanged.emit([node], [NodeAttribute.LocationX, NodeAttribute.LocationY])

class MainWindow(QWidget):
	def __init__(self, parent: Optional[QWidget]=None) -> None:
		super().__init__(parent)

		self.setWindowTitle("MindGraphView")

		self.model = GraphModel()
		self.model.setNodeAttributeLabels(["title", "body"])

		self.graphview = MindGraphView()
		self.graphview.setModel(self.model)
		self.graphview2 = MindGraphView()
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