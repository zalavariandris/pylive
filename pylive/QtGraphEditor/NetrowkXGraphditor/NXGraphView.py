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
from pylive.QtGraphEditor.graphview_databased import EditableTextItem, InletGraphicsItem




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
		if not self.graph_model:
			return

		for node in nodes:		
			# Create Node Widget TODO: move to a delegate
			widget =  MyNodeWidget()
			widget.nameedit.document().contentsChanged.connect(lambda model=self.graph_model: 
				model.setNodeProperty(node, 
					name=widget.nameedit.toPlainText()
				)
			)

			widget.geometryChanged.connect(lambda model=self.graph_model: 
				model.setNodeProperty(node, 
					posx=int(widget.x()), 
					posy=int(widget.y())
				)
			)

			# add to scebne
			self.graph_scene.addNode(widget)

			# set item widget
			self._item_to_widget_map[node] = widget
			self._widget_to_item_map[widget] = node

			# update graphics item
			self.handleNodesPropertiesChanged([node], properties=['name'])
			self.handleInletsAdded(self.graph_model.getNodeInlets(node))
			self.handleOutletsAdded(self.graph_model.getNodeOutlets(node))

	def handleNodesPropertiesChanged(self, nodes:List[NodeRef], properties:List[str]):
		if not self.graph_model:
			return

		for node in nodes:
			widget = cast(MyNodeWidget, self._item_to_widget_map[node])
			# Set Editor Properties TODO: move to delegate
			if 'name' in properties:
				new_name = self.graph_model.getNodeProperty(node, 'name')
				old_name = widget.nameedit.toPlainText()

			if 'posx' in properties or 'posy' in properties:
				x = int(self.graph_model.getNodeProperty(node, 'posx'))
				y = int(self.graph_model.getNodeProperty(node, 'posy'))
				widget.setPos(x,y)

	def handleNodesRemoved(self, nodes:Iterable[NodeRef]):
		if not self.graph_model:
			return

		for node in nodes:
			assert len([inlet for inlet in self.graph_model.getNodeInlets(node)])==0
			assert len([outlet for outlet in self.graph_model.getNodeOutlets(node)])==0

			widget = self._item_to_widget_map[node]
			self.graph_scene.removeNodes([widget])

			del self._item_to_widget_map[node]
			del self._widget_to_item_map[widget]

	def handleEdgesAdded(self, edges:Iterable[EdgeRef]):
		if not self.graph_model:
			return

		for edge in edges:
			try:
				widget:EdgeWidgetProtocol = self.index_to_item_map[edge]
			except KeyError:
				# Create Edge Widget: TODO move to a delegate
				widget = MyEdgeWidget()
				self.scene().addItem(widget)
				self._widget_to_item_map[widget] = edge
				self._item_to_widget_map[edge] = widget

			outlet = self.graph_model.getEdgeSource(edge)
			inlet = self.graph_model.getEdgeTarget(edge)

			source_pin_item = cast(ConnectableWidgetProtocol, self._item_to_widget_map[outlet])
			widget.setSourcePin(source_pin_item)
			target_pin_item = cast(ConnectableWidgetProtocol, self._item_to_widget_map[outlet])
			widget.setTargetPin(target_pin_item)








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
	G.add_edge("a", "b")
	graphmodel = NXGraphModel(G)
	graphview = NXGraphView()
	graphview.setModel(graphmodel)
	
	# show window
	graphview.show()
	sys.exit(app.exec())
