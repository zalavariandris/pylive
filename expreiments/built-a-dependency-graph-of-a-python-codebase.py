"""
resources: https://www.python.org/success-stories/building-a-dependency-graph-of-our-python-codebase/


given a source python file, visualize import dependencies
"""
from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

import networkx as nx
from pylive.QtGraphEditor.dag_graph_graphics_scene import DAGScene, NodeWidget
from pylive.QtGraphEditor.graphmodel_databased import EdgeRef, GraphModel, InletRef, NodeRef, OutletRef


class NXGraphModel(GraphModel):
	def __init__(self, nxgraph, parent=None):
		super().__init__(parent=parent)
		self.G = nxgraph


class NXGraphView(QGraphicsView):
	def __init__(self, parent=None):
		super().__init__(parent=parent)
		self.setWindowTitle("NXGraphView")
		self.graph_scene = DAGScene()

		# scene widget
		self.setScene(self.graph_scene)

		# source model
		self.graph_model:Optional[GraphModel] = None
		self.nodes_selectionmodel = None
		self.edges_selectionmodel = None

		# items<->model mapping
		self._item_to_widget_map:Dict[NodeRef|EdgeRef|InletRef|OutletRef, QGraphicsItem] = dict()
		self._widget_to_item_map:Dict[QGraphicsItem, NodeRef|EdgeRef|InletRef|OutletRef] = dict()
		# self.delegate = NodeItemDelegate(self)

	def setItemWidget(self, item:NodeRef|EdgeRef|InletRef|OutletRef, widget:QGraphicsItem):
		"""Sets the given widget on the given graph item (node, edge inlet or outlet ref),
		passing the ownership of the widget to the viewport"""
		self._item_to_widget_map[item] = widget
		self._widget_to_item_map[widget] = item

	def itemWidget(self, item:NodeRef|EdgeRef|InletRef|OutletRef)->QGraphicsItem:
		"""returns the widget for the noderef"""
		return self._item_to_widget_map[item]

	def widgetItem(self, widget:QGraphicsItem)->NodeRef|EdgeRef|InletRef|OutletRef:
		return cast(NodeRef, self._widget_to_item_map[widget])

	def setModel(self, graph_model:NXGraphModel):
		self.graph_model = graph_model
		self.handleNodesAdded(  self.graph_model.getNodes())
		self.handleEdgesAdded(  self.graph_model.getEdges())

		self.graph_model.nodesAdded.connect(self.handleNodesAdded)
		self.graph_model.nodesPropertyChanged.connect(self.handleNodesPropertiesChanged)
		self.graph_model.nodesAboutToBeRemoved.connect(self.handleNodesRemoved)

		self.graph_model.inletsAdded.connect(self.handleInletsAdded)
		self.graph_model.inletsPropertyChanged.connect(self.handleInletsPropertiesChanged)
		self.graph_model.inletsAboutToBeRemoved.connect(self.handleInletsRemoved)

		self.graph_model.outletsAdded.connect(self.handleOutletsAdded)
		self.graph_model.outletsPropertyChanged.connect(self.handleOutletsPropertiesChanged)
		self.graph_model.outletsAboutToBeRemoved.connect(self.handleOutletsRemoved)

		self.graph_model.edgesAdded.connect(self.handleEdgesAdded)
		self.graph_model.edgesPropertyChanged.connect(self.handleEdgesPropertiesChanged)
		self.graph_model.edgesAboutToBeRemoved.connect(self.handleEdgesRemoved)

	def handleNodesAdded(self, nodes:Iterable[NodeRef]):
		for node in nodes:
			widget = NodeWidget()
			self.graph_scene.addNode(widget)
			self.setNodeWidget(node, widget)

	def handleNodesPropertiesChanged(self, nodes:List[NodeRef], properties:List[str]=None):
		...

	def handleNodesRemoved(self, nodes:Iterable[NodeRef]):
		...

	def handleEdgesAdded(self, edges:Iterable[EdgeRef]):
		...

	def handleEdgesPropertiesChanged(self, edges:List[EdgeRef], properties:List[str]=None):
		...

	def handleEdgesRemoved(self, edge:Iterable[EdgeRef]):
		...

	def handleInletsAdded(self, inlets:Iterable[InletRef]):
		...

	def handleInletsPropertiesChanged(self, inlets:List[InletRef], properties:List[str]=None):
		...

	def handleInletsRemoved(self, inlets:Iterable[InletRef]):
		...

	def handleOutletsAdded(self, outlets:Iterable[OutletRef]):
		...

	def handleOutletsPropertiesChanged(self, outlets:List[OutletRef], properties:List[str]=None):
		...

	def handleOutletsRemoved(self, outlets:Iterable[OutletRef]):
		...


if __name__ == "__main__":
	import sys
	app = QApplication(sys.argv)

	G = nx.DiGraph()
	graphmodel = NXGraphModel(G)
	graphview = NXGraphView()
	graphview.setModel(graphmodel)
	
	# show window
	graphview.show()
	sys.exit(app.exec())
