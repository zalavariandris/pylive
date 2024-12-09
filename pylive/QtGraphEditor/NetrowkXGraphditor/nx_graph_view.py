from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from standard_graph_delegate import GraphDelegate
from nx_graph_model import NXGraphModel

class NXGraphView(QGraphicsView):
	def __init__(self, parent=None):
		super().__init__(parent=parent)
		scene = QGraphicsScene()
		scene.setSceneRect(QRect(-9999//2,-9999//2, 9999, 9999))
		self.setScene(scene)
		
		self._item_to_widget_map = dict()
		self._widget_to_item_map = dict()
		self._delegate = GraphDelegate()
		self.setGraphModel( NXGraphModel() )
		
	def delegate(self):
		return self._delegate

	def graphModel(self):
		return self._graphmodel

	def setGraphModel(self, graphmodel:NXGraphModel):
		self._graphmodel = graphmodel

		self._graphmodel.nodesAdded.connect(self.handleNodesAdded)
		self._graphmodel.nodesPropertiesChanged.connect(self.handleNodesPropertiesChanged)
		self._graphmodel.edgesAdded.connect(self.handleEdgesAdded)
	
	def handleNodesAdded(self, nodes:List[Hashable]):
		for n in nodes:
			widget = self.delegate().createNodeWidget(self.graphModel(), n)
			self._item_to_widget_map[n]=widget
			self._widget_to_item_map[widget]=n
			self.scene().addItem(widget)

	def handleNodesRemoved(self, nodes:List[Hashable]):
		for n in nodes:
			widget = self._item_to_widget_map[n]
			self.scene().removeItem(widget)
			del self._item_to_widget_map[n]
			del self._widget_to_item_map[widget]

	def handleEdgesAdded(self, edges:List[Tuple[Hashable, Hashable]]):
		for u, v in edges:
			source_node = self._item_to_widget_map[u]
			target_node = self._item_to_widget_map[v]
			print(source_node, target_node)
			widget = self.delegate().createEdgeWidget(self, source_node, target_node)
			widget.setSource(source_node)
			widget.setTarget(target_node)
			self._item_to_widget_map[(u,v)]=widget
			self._widget_to_item_map[widget]=(u,v)
			self.scene().addItem(widget)

	def handleEdgesRemoed(self, edges:List[Tuple[Hashable, Hashable]]):
		for u,v in edges:
			widget = self._item_to_widget_map[(u,v)]
			widget.setSource(None)
			widget.setTarget(None)
			self.scene().removeItem(widget)
			del self._item_to_widget_map[(u, v)]
			del self._widget_to_item_map[widget]

	def handleNodesPropertiesChanged(self, nodesProperies):
		for n, properties in nodesProperies.items():
			widget = self._item_to_widget_map[n]
			self.delegate().setNodeWidgetProps(self, n, widget, **properties)

	def handleEdgesPropertiesChanged(self, edgesProperties):
		for edge, properties in edgesProperties.items():
			widget = self._item_to_widget_map[edge]
			self.delegate().setEdgeWidgetProps(self, edge, widget, **properties)

	def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
		print("doubleclick")
		itemAtMouse = self.itemAt(event.position().toPoint())
		print("itemAtMouse", itemAtMouse)
		if itemAtMouse:
			return super().mouseDoubleClickEvent(event)

		clickpos = self.mapToScene(event.position().toPoint())
		from pylive.utils.unique import make_unique_id
		n = make_unique_id()
		self.graphModel().addNode(n, label="new node")
		widget = self._item_to_widget_map[n]
		widget.setPos(clickpos)


if __name__ == "__main__":
	app = QApplication.instance() or QApplication()
	window = NXGraphView()
	# window.scene().addItem( QGraphicsRectItem(QRect(0,0,100,100)) )
	graph = window.graphModel()
	# graph.addNode("A")
	# graph.addNode("B")
	graph.addEdge("A", "B")

	window.show()
	app.exec()
