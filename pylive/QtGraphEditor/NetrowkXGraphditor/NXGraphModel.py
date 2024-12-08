from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

import networkx as nx

from pylive.utils.geo import intersectRayWithRectangle

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


class EdgeWidget(QGraphicsWidget):
	def __init__(self, source_node:QGraphicsWidget, target_node:QGraphicsWidget, parent=None):
		super().__init__(parent=parent)
		self._source_node = source_node
		source_node.geometryChanged.connect(self.updatePosition)
		self._target_node = target_node
		target_node.geometryChanged.connect(self.updatePosition)

		# components
		palette = self.palette()
		textColor = palette.color(QPalette.ColorGroup.All, QPalette.ColorRole.Text)
		# arrow body
		self.body = QGraphicsLineItem(self)
		pen = QPen( QPen(textColor, 1.5) )
		pen.setCapStyle(Qt.FlatCap)
		self.body.setPen(pen)

		# arrow head
		self.headsize=8
		triangle = QPolygonF([
			QPointF(0, 0),
			QPointF(-self.headsize, self.headsize / 2),
			QPointF(-self.headsize, -self.headsize / 2)
		])
		self.arrowhead = QGraphicsPolygonItem(self)  # Add arrowhead as a child
		self.arrowhead.setPolygon(triangle)
		self.arrowhead.setPen(Qt.NoPen)
		self.arrowhead.setBrush(textColor)

		# arrow tail
		self.tailsize=8
		self.arrowtail = QGraphicsEllipseItem(-self.tailsize/2, -self.tailsize/2, self.tailsize, self.tailsize, parent=self)
		self.arrowtail.setPen(Qt.NoPen)
		self.arrowtail.setBrush(textColor)

		#
		self.updatePosition()

	def setSource(self, source_node:QGraphicsWidget):
		if self._source_node:
			self._source_node.geometryChanged.disconnect(self.updatePosition)
		if source_node:
			self._source_node = source_node
			source_node.geometryChanged.connect(self.updatePosition)
		else:
			self._source_node = None
		self.updatePosition()

	def setTarget(self, target_node:QGraphicsWidget):
		if self._target_node:
			self._target_node.geometryChanged.disconnect(self.updatePosition)
		
		if target_node:
			self._target_node = target_node
			target_node.geometryChanged.connect(self.updatePosition)
		else:
			self._target_node = None
		
		self.updatePosition()

	def updatePosition(self):
		if not self._source_node or not self._target_node:
			print("warning: unconnected edges are not yet implemented")

		line = QLineF()
		
		if self._source_node and self._target_node:
			margin = 0
			source_rect = self._source_node.geometry()\
			.adjusted(-margin,-margin,margin,margin)
			target_rect = self._target_node.geometry()\
			.adjusted(-margin,-margin,margin,margin)
			source_center = source_rect.center()
			target_center = target_rect.center()
			direction = target_center-source_center

			if I:=intersectRayWithRectangle(
				origin=(source_center.x(), source_center.y()),
				direction = (direction.x(), direction.y()),
				top = target_rect.top(),
				left = target_rect.left(),
				bottom = target_rect.bottom(),
				right = target_rect.right()):

				line.setP2(QPointF(I[0], I[1]))

			direction = source_center - target_center
			if I:=intersectRayWithRectangle(
				origin=(target_center.x(), target_center.y()),
				direction = (direction.x(), direction.y()),
				top = source_rect.top(),
				left = source_rect.left(),
				bottom = source_rect.bottom(),
				right = source_rect.right()
			):
				line.setP1(QPointF(I[0], I[1]))
		else:

			if self._source_node:
				line.setP1(self._source_node.geometry().center().toPoint())
			if self._target_node:
				line.setP2(self._target_node.geometry().center().toPoint())

		body_line = QLineF(line)
		body_line.setLength(body_line.length()-self.headsize)
		self.body.setLine(body_line)

		
		# # P = QPointF(QPointF(I[0]-normal.x(), I[1]-normal.y()))
		# # body_line.setP2(P)
		# self.body.line().setP2(QPointF())

		# update head and tails
		transform = QTransform()
		transform.translate(line.p2().x(), line.p2().y())
		transform.rotate(-line.angle())
		self.arrowhead.setTransform(transform)

		transform = QTransform()
		transform.translate(line.p1().x(), line.p1().y())
		transform.rotate(-line.angle())
		self.arrowtail.setTransform(transform)



class GraphDelegate(QObject):
	def createNodeWidget(self, graph:NXGraphModel, n:Hashable):
		"""create and bind the widget"""
		widget = StandardNodeWidget()
		widget.label.textChanged.connect(lambda text:
			self.setNodeModelProps(graph, n, widget, label=text))
		return widget

	def setNodeWidgetProps(self, graph:NXGraphModel, n:Hashable, widget:QGraphicsWidget, **props):
		"""update iwdget props from model"""
		if 'label' in props.keys():
			widget.label.document().setPlainText(props['label'])
		
		if 'inlets' in props.keys():
			...

		if 'outlets' in props.keys():
			...

	def setNodeModelProps(self, graph:NXGraphModel, n:Hashable, widget:QGraphicsWidget, **props):
		"""update model props from widget"""
		graph.setNodeProperties(n, **props)

	def createEdgeWidget(self, graph:NXGraphModel, source:QGraphicsWidget, target:QGraphicsWidget):
		widget = EdgeWidget(source, target)

		return widget

	def setEdgeWidgetProps(self, graph:NXGraphModel, e:Tuple[Hashable, Hashable], widget:EdgeWidget, **props):
		...

	def setEdgeModelProps(self, graph:NXGraphModel, e:Tuple[Hashable, Hashable], widget:EdgeWidget, **props):
		...


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
	graph.addNode("A")
	graph.addNode("B")
	graph.addEdge("A", "B")

	window.show()
	app.exec()



