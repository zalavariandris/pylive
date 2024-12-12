from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

import networkx as nx

from pylive.utils.geo import intersect_ray_with_rectangle

class NXGraphModel(QObject):
	nodesAdded = Signal(list) #List[Tuple[Hashable, Hashable]]
	nodesAboutToBeRemoved = Signal(list) #List[Tuple[Hashable, Hashable]]
	nodesPropertiesChanged = Signal(dict) # Dict[Hashable, Dict[str, Any]]
	nodesRemoved = Signal(list)

	edgesAdded = Signal(list) #List[Tuple[Hashable, Hashable]]
	edgesAboutToBeRemoved = Signal(list) #List[Tuple[Hashable, Hashable]]
	edgesPropertiesChanged = Signal(dict) # Dict[Hashable, Dict[str, Any]]
	edgesRemoved = Signal(list)

	def __init__(self, G:nx.DiGraph=nx.DiGraph(), parent=None):
		super().__init__(parent=parent)
		self.G = G

		for n in self.G.nodes:
			node = self.addNode(name=n)
			self.addInlet(node, "in")
			self.addOutlet(node, "out")

		for e in self.G.edges:
			u, v = e
			
			self.addEdge(u, v)

	def patch(self, G:nx.DiGraph):
		...
		raise NotImplementedError("Not yet implemented")

	def __del__(self):
		self.G = None
		# self.nodesAdded.disconnect()
		# self.nodesAboutToBeRemoved.disconnect()
		# self.nodesPropertyChanged.disconnect()
		# self.nodesRemoved.disconnect()
		# self.edgesAdded.disconnect()
		# self.edgesAboutToBeRemoved.disconnect()
		# self.edgesPropertyChanged.disconnect()
		# self.edgesRemoved.disconnect()

	def addNode(self, n:Hashable, / , **props):
		print("add node", n)
		self.G.add_node(n, **props)
		self.nodesAdded.emit([n])
		self.nodesPropertiesChanged.emit({n:props})

	def addEdge(self, u:Hashable, v:Hashable, / , **props):

		if u not in self.G.nodes:
			self.addNode(u)
		if v not in self.G.nodes:
			self.addNode(v)

		self.G.add_edge(u, v, **props)
		self.edgesAdded.emit([(u, v)])

	def remove_node(self, n:Hashable):
		self.nodesAboutToBeRemoved.emit([n])
		self.G.remove_node(n)

	def remove_edge(self, u:Hashable, v:Hashable):
		self.edgesAboutToBeRemoved.emit([(u,v)])
		self.G.remove_edge( u,v )

	def setNodeProperties(self, n:Hashable, /, **props):
		# change guard TODO: find removed props
		change = {}
		for key, val in props.items():
			if key not in self.G.nodes[n] or val != self.G.nodes[n][key]:
				change[key] = val
		nx.set_node_attributes(self.G, {n: change})
		self.nodesPropertiesChanged.emit({n: change})

	def getNodeProperty(self, n:Hashable, name, /):
		return self.G.nodes[n][name]

	def setEdgeProperties(self, u:Hashable, v:Hashable, /, **props):
		nx.set_edge_attributes(self.G, {(u,v): props})
		self.nodesPropertiesChanged.emit([n], list(props.keys()) )

	def getEdgeProperty(self, u:Hashable, v:Hashable, prop, /):
		return self.G.edge[u, v][prop]

from pylive.QtGraphEditor.editable_text_item import EditableTextItem


class StandardNodeWidget(QGraphicsWidget):
	def __init__(self, parent=None):
		super().__init__(parent=parent)
		self.setGeometry(QRect(0,0,100,26))
		# Enable dragging and selecting
		self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
		self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
		self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
		self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges)
		self.setAcceptHoverEvents(True)

		self.label = EditableTextItem(parent=self)
		self.label.setPos(5,5)
		self.label.setTextWidth(self.geometry().width()-10)
		self.label.setText("Hello")

	def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent):
		# Enable editing subitems on double-click
		"""parent node must manually cal the double click event,
		because an item nor slectable nor movable will not receive press events"""

		# Check if double-click is within the text item’s bounding box
		if self.label.contains(self.mapFromScene(event.scenePos())):
			# Forward the event to label if clicked inside it
			self.label.mouseDoubleClickEvent(event)
		else:
			print("NodeItem->mouseDoubleClickEvent")
			super().mouseDoubleClickEvent(event)

	def paint(self, painter:QPainter, option:QStyleOptionGraphicsItem, widget=None):
		# option.direction
		# option.fontMetrics
		# option.palette
		# option.rect
		# option.state
		# option.styleObject
		# option.levelOfDetailFromTransform


		# Draw the node rectangle
		palette:QPalette = option.palette #type: ignore
		state:QStyle.StateFlag = option.state # type: ignore

		painter.setBrush(palette.base())
		# painter.setBrush(Qt.NoBrush)

		pen = QPen(palette.text().color(), 1)
		pen.setCosmetic(True)
		pen.setWidthF(2)
		if state & QStyle.StateFlag.State_Selected:
			pen.setColor(palette.accent().color())
		painter.setPen(pen)
		painter.drawRoundedRect(0.5,0.5, self.geometry().width(), self.geometry().height(), 3,3)






