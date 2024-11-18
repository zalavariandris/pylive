from re import X
import sys
import math
from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from pylive.QtGraphEditor.PanAndZoomGraphicsView import PanAndZoomGraphicsView
from pylive.QtGraphEditor.graphmodel_databased import (
	GraphModel,
	NodeRef, EdgeRef, InletRef, OutletRef,
)

from enum import Enum


class EditableTextItem(QGraphicsTextItem):
	def __init__(self, text, parent=None):
		super().__init__(text, parent)
		self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable)  # Allow focus events
		self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)  # Initially non-editable
		# self.setFlag(QGraphicsItem.ItemIsSelectable, True)

		# Center-align the text within the item
		text_option = QTextOption()
		text_option.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.document().setDefaultTextOption(text_option)

		# Remove the default margins
		self.document().setDocumentMargin(0)

	def mouseDoubleClickEvent(self, event):
		# Enable editing on double-click
		"""parent node must manually cal the double click event,
		because an item nor slectable nor movable will not receive press events"""
		self.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
		self.setFocus(Qt.FocusReason.MouseFocusReason)

		click = QGraphicsSceneMouseEvent(QEvent.Type.GraphicsSceneMousePress)
		click.setButton(event.button())
		click.setPos(event.pos())
		self.mousePressEvent(click)
		# super().mouseDoubleClickEvent(event)

	def focusOutEvent(self, event: QFocusEvent):
		# When the item loses focus, disable editing
		self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
		super().focusOutEvent(event)

class PinType(Enum):
	INLET = "INLET"
	OUTLET = "OUTLET"

class PinGraphicsItem(QGraphicsItem):
	"""Graphics item representing a pin (either inlet or outlet)."""
	def __init__(self, parent=None):
		super().__init__(parent=parent)
		self.parent_node:'NodeGraphicsItem|None' = None
		self.edges = []

		self.label = QGraphicsSimpleTextItem(parent=self)
		self.label.setBrush(QApplication.palette().text().color())
		self.label.setY(-QFontMetrics(self.label.font()).height()-5)
		self.label.hide()
		self.label.setZValue(2)

		# Size of the pin and space for the name text
		self.pin_radius = 4
		self.text_margin = 10

		# Font for drawing the name
		self.font = QFont("Arial", 10)

		self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges)
		self.setAcceptHoverEvents(True)

	def boundingRect(self) -> QRectF:
		# Bounding rect includes the pin (left side) and text (right side)
		return QRectF(-self.pin_radius, 
					  -self.pin_radius, 
					   self.pin_radius*2, 
					   self.pin_radius*2).adjusted(-4,-4,8,8)

	def paint(self, painter, option:QStyleOptionGraphicsItem, widget=None):
		"""Draw the pin and the name."""
		# Draw pin (ellipse)
		# painter.setBrush(Qt.NoBrush)
		palette:QPalette = option.palette # type: ignore
		state:QStyle.StateFlag = option.state # type: ignore
		painter.setPen(QPen(palette.base().color(), 3))
		if self.parent_node and self.parent_node.isSelected() or state & QStyle.StateFlag.State_MouseOver:
			painter.setBrush(palette.accent().color())
		else:
			painter.setBrush(palette.windowText().color())
		painter.drawEllipse(-self.pin_radius, -self.pin_radius, self.pin_radius * 2, self.pin_radius * 2)

	def hoverEnterEvent(self, event):
		self.update()
		self.label.show()

	def hoverLeaveEvent(self, event):
		self.update()
		self.label.hide()

	def itemChange(self, change, value):
		match change:
			case QGraphicsItem.GraphicsItemChange.ItemScenePositionHasChanged:
				for edge_item in self.edges:
					edge_item.updatePosition()
		return super().itemChange(change, value)

	def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
		if self.parent_node:
			graphview = self.parent_node.parent_graph
			graphview.initiateConnection(pin=self)

	def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
		if self.parent_node:
			graphview = self.parent_node.parent_graph
			graphview.moveConnection(graphview.mapFromScene(event.scenePos()))
			# return super().mouseMoveEvent(event)

	def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
		if self.parent_node:
			graphview = self.parent_node.parent_graph
			pin = graphview.pinAt(graphview.mapFromScene(event.scenePos()))
			graphview.finishConnection(pin)



class OutletGraphicsItem(PinGraphicsItem):
	def destroy(self):
		for edge in reversed(self.edges):
			edge.destroy()
		self.edges = []

		if self.parent_node:
			self.parent_node.removeOutlet(self)
			self.parent_node.updatePinPositions()
		self.scene().removeItem(self)


class InletGraphicsItem(PinGraphicsItem):
	def destroy(self):
		for edge in reversed(self.edges):
			edge.destroy()
		self.edges = []

		if self.parent_node:
			self.parent_node.removeInlet(self)
			self.parent_node.updatePinPositions()
		self.parentNode = None
		self.scene().removeItem(self)


class NodeGraphicsItem(QGraphicsObject):
	"""Graphics item representing a node."""
	positionChanged = Signal()
	def __init__(self, parent_graph:"GraphView"):
		# QObject.__init__(self, parent=None)
		super().__init__(parent=None)
		

		self.parent_graph = parent_graph
		self.rect = QRectF(-5, -5, 100, 27)  # Set size of the node box
		
		# Store pins (inlets and outlets)
		self.inlets = []
		self.outlets = []

		# Enable dragging and selecting
		self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
		self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
		self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
		self.setAcceptHoverEvents(True)

		self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges)

	def destroy(self):
		while self.inlets:
			self.inlets[0].destroy() # Always remove first

		while self.outlets:
			self.outlets[0].destroy() # Always remove first
		
		self.scene().removeItem(self)

	def addOutlet(self, outlet:PinGraphicsItem):
		outlet.parent_node = self
		outlet.setParentItem(self)
		self.outlets.append(outlet)
		self.updatePinPositions()

	def removeOutlet(self, outlet:PinGraphicsItem):
		self.outlets.remove(outlet)
		self.updatePinPositions()

	def addInlet(self, inlet:PinGraphicsItem):
		inlet.parent_node = self
		inlet.setParentItem(self)
		self.inlets.append(inlet)
		self.updatePinPositions()

	def removeInlet(self, inlet:PinGraphicsItem):
		self.inlets.remove(inlet)
		self.updatePinPositions()

	def updatePinPositions(self, vertical_mode=False):
		"""
		Update the positions of inlets and outlets.
		:param vertical_mode: If True, place inlets on the left and outlets on the right (default).
							  If False, place inlets on the top and outlets on the bottom.
		"""
		offset = 0
		rect_width = self.rect.width()
		rect_height = self.rect.height()

		# adjust pin positions
		if vertical_mode:
			# Place inlets on the left side and outlets on the right side
			num_inlets = len(self.inlets)
			inlet_spacing = rect_height / (num_inlets + 1)  # Spacing for vertical alignment

			for i, inlet in enumerate(self.inlets):
				inlet_y_pos = self.rect.top() + (i + 1) * inlet_spacing  # Distribute vertically
				inlet.setPos(self.rect.left() - offset, inlet_y_pos)  # Position on left edge
			
			num_outlets = len(self.outlets)
			outlet_spacing = rect_height / (num_outlets + 1)  # Spacing for vertical alignment

			for i, outlet in enumerate(self.outlets):
				outlet_y_pos = self.rect.top() + (i + 1) * outlet_spacing  # Distribute vertically
				outlet.setPos(self.rect.right() + offset, outlet_y_pos)  # Position on right edge
		else:
			# Place inlets on the top side and outlets on the bottom side
			num_inlets = len(self.inlets)
			inlet_spacing = rect_width / (num_inlets + 1)  # Spacing for horizontal alignment

			for i, inlet in enumerate(self.inlets):
				inlet_x_pos = self.rect.left() + (i + 1) * inlet_spacing  # Distribute horizontally
				inlet.setPos(inlet_x_pos, self.rect.top() - offset)  # Position on top edge

			num_outlets = len(self.outlets)
			outlet_spacing = rect_width / (num_outlets + 1)  # Spacing for horizontal alignment

			for i, outlet in enumerate(self.outlets):
				outlet_x_pos = self.rect.left() + (i + 1) * outlet_spacing  # Distribute horizontally
				outlet.setPos(outlet_x_pos, self.rect.bottom() + offset)  # Position on bottom edge

	def boundingRect(self) -> QRectF:
		return self.rect

	def paint(self, painter:QPainter, option:QStyleOptionGraphicsItem, widget=None):
		# option.direction
		# option.fontMetrics
		# option.palette
		# option.rect
		# option.state
		# option.styleObject
		# option.levelOfDetailFromTransform


		# Draw the node rectangle
		palette:QPalette = option.palette # type: ignore
		state:QStyle.StateFlag = option.state # type: ignore

		painter.setBrush(palette.base())
		# painter.setBrush(Qt.NoBrush)

		pen = QPen(palette.text().color(), 1)
		pen.setCosmetic(True)
		pen.setWidthF(1)
		if state & QStyle.StateFlag.State_Selected:
			pen.setColor(palette.accent().color())
		painter.setPen(pen)

		# painter.setPen(palette.window().color())

		painter.drawRoundedRect(self.rect.adjusted(-0.5, -0.5, 0, 0), 3, 3)

		# painter.setBrush(palette.window())
		# painter.drawRect(QRect(0,0,80,10))

		# Draw the node name text
		# painter.setPen(palette.text().color())
		# painter.drawText(self.rect, Qt.AlignmentFlag.AlignCenter, self.name)

	def itemChange(self, change, value):
		match change:
			case QGraphicsItem.GraphicsItemChange.ItemScenePositionHasChanged:
				self.positionChanged.emit()

		return super().itemChange(change, value)




class EdgeGraphicsItem(QGraphicsLineItem):
	"""Graphics item representing an edge (connection)."""
	GrabThreshold = 15
	def __init__(self, source_pin_item:OutletGraphicsItem|None, target_pin_item:InletGraphicsItem|None, parent_graph:"GraphView"):
		super().__init__(parent=None)
		assert source_pin_item is None or isinstance(source_pin_item, OutletGraphicsItem)
		assert target_pin_item is None or isinstance(target_pin_item, InletGraphicsItem)
		self._source_pin_item = source_pin_item
		self._target_pin_item = target_pin_item
		self.parent_graph = parent_graph

		if source_pin_item:
			source_pin_item.edges.append(self)
		if target_pin_item:
			target_pin_item.edges.append(self)

		self.setPen(QPen(Qt.GlobalColor.black, 2))
		self.updatePosition()

		# Enable selecting
		self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
		self.setAcceptHoverEvents(True)

		self.setZValue(-1)

		#
		self.is_moving_endpoint = False

	def destroy(self):
		# Safely remove from source pin
		if self._source_pin_item:
			try:
				self._source_pin_item.edges.remove(self)
			except ValueError:
				pass  # Already removed
			self._source_pin_item = None

		# Safely remove from target pin
		if self._target_pin_item:
			try:
				self._target_pin_item.edges.remove(self)
			except ValueError:
				pass  # Already removed
			self._target_pin_item = None

		# Clear parent reference
		self.parent_graph = None

		# Safely remove from scene
		if self.scene():
			self.scene().removeItem(self)

	def sourcePin(self)->OutletGraphicsItem|None:
		return self._source_pin_item

	def setSourcePin(self, pin: OutletGraphicsItem|None):
		assert pin is None or isinstance(pin, OutletGraphicsItem)

		# add or remove edge to pin edges for position update
		if pin:
			pin.edges.append(self)
		elif self._source_pin_item:
			self._source_pin_item.edges.remove(self)

		self._source_pin_item = pin
		self.updatePosition()

	def targetPin(self):
		return self._target_pin_item

	def setTargetPin(self, pin: InletGraphicsItem|None):
		assert pin is None or isinstance(pin, InletGraphicsItem)

		# add or remove edge to pin edges for position update
		if pin:
			pin.edges.append(self)
		elif self._target_pin_item:
			self._target_pin_item.edges.remove(self)
		self._target_pin_item = pin
		self.updatePosition()

	def updatePosition(self):
		line = self.line()
		sourcePin = self.sourcePin()
		targetPin = self.targetPin()
		if sourcePin and targetPin:
			line.setP1(sourcePin.scenePos())
			line.setP2(targetPin.scenePos())
			self.setLine(line)
		elif sourcePin:
			line.setP1(sourcePin.scenePos())
			line.setP2(sourcePin.scenePos())
			self.setLine(line)
		elif targetPin:
			line.setP1(targetPin.scenePos())
			line.setP2(targetPin.scenePos())
			self.setLine(line)
		else:
			pass

	def paint(self, painter:QPainter, option:QStyleOptionGraphicsItem, widget=None):
		p1 = self.line().p1()
		p2 = self.line().p2()

		palette:QPalette = option.palette # type: ignore
		state:QStyle.StateFlag = option.state # type: ignore
		pen = QPen(palette.text().color(), 2)
		pen.setCosmetic(True)
		pen.setWidthF(1)
		if state & (QStyle.StateFlag.State_Selected | QStyle.StateFlag.State_MouseOver):
			pen.setColor(palette.accent().color())
		painter.setPen(pen)

		# painter.setPen(options.palette.light().color())
		painter.drawLine(self.line())

	def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
		self.mousePressScenePos = event.scenePos()
		self.is_moving_endpoint = False
		return super().mousePressEvent(event)

	def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
		graphview = self.parent_graph
		mousePressScenePos:QPointF = cast(QPointF, self.mousePressScenePos)
		mouseDelta = event.scenePos() - mousePressScenePos
		IsThresholdSurpassed = mouseDelta.manhattanLength()>self.GrabThreshold
		if not self.is_moving_endpoint and IsThresholdSurpassed:
			self.is_moving_endpoint = True
			delta1 = self.line().p1() - event.scenePos()
			d1 = delta1.manhattanLength()
			delta2 = self.line().p2() - event.scenePos()
			d2 = delta2.manhattanLength()
			if d1<d2:
				graphview.modifyConnection(edge=self, endpoint=PinType.OUTLET)
			else:
				graphview.modifyConnection(edge=self, endpoint=PinType.INLET)

		if self.is_moving_endpoint:
			graphview.moveConnection(graphview.mapFromScene(event.scenePos()))
		else:
			return super().mouseMoveEvent(event)

	def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
		if self.is_moving_endpoint:
			self.is_moving_endpoint = False
			self.mousePressScenePos = None
			graphview = self.parent_graph
			pin = graphview.pinAt(graphview.mapFromScene(event.scenePos()))
			graphview.finishConnection(pin)
		else:
			return super().mouseReleaseEvent(event)


class GraphView(PanAndZoomGraphicsView):
	"""A view that displays the node editor."""
	def __init__(self, parent=None):
		super().__init__(parent)

		# Create a scene to hold the node and edge graphics
		scene = QGraphicsScene(self)
		scene.setSceneRect(QRect(-9999//2,-9999//2, 9999, 9999))
		self.setScene(scene)

		self.index_to_item_map:Dict[NodeRef|EdgeRef|InletRef|OutletRef, QGraphicsItem] = dict()
		self.item_to_index_map:Dict[QGraphicsItem, NodeRef|EdgeRef|InletRef|OutletRef] = dict()

		self.graph_model = None
		self.nodes_selectionmodel = None
		self.edges_selectionmodel = None

		# self.delegate = NodeItemDelegate(self)

	def setScene(self, scene:QGraphicsScene|None):
		if self.scene():
			self.scene().selectionChanged.disconnect(self.onSceneSelectionChanged)
		if scene:
			scene.selectionChanged.connect(self.onSceneSelectionChanged)
		super().setScene(scene)

	def onSceneSelectionChanged(self):
		...
		# if self.graph_model:
		# 	node_selection = []
		# 	edge_selection = []
		# 	for item in self.scene().selectedItems():
		# 		if isinstance(item, NodeView):
		# 			if item.persistent_node_index:
		# 				node = item.persistent_node_index
		# 				if node:
		# 					node_selection.append(node)
		# 		if isinstance(item, EdgeGraphicsItem):
		# 			if item.persistent_edge_index:
		# 				edge = item.persistent_edge_index
		# 				if edge:
		# 					edge_selection.append(edge)

		# 	if self.nodes_selectionmodel:
		# 		item_selection = QItemSelection()
		# 		for node in node_selection:
		# 			item_selection.merge(QItemSelection(node, node), QItemSelectionModel.SelectionFlag.Select)
		# 		self.nodes_selectionmodel.select(item_selection, QItemSelectionModel.SelectionFlag.ClearAndSelect)

		# 		if node_selection:
		# 			self.nodes_selectionmodel.setCurrentIndex(node_selection[-1], QItemSelectionModel.SelectionFlag.Current)
		# 		else:
		# 			self.nodes_selectionmodel.setCurrentIndex(QModelIndex(), QItemSelectionModel.SelectionFlag.Clear)

		# 	if self.edges_selectionmodel:
		# 		item_selection = QItemSelection()
		# 		for edge in edge_selection:
		# 			item_selection.merge(QItemSelection(edge, edge), QItemSelectionModel.SelectionFlag.Select)
		# 		self.edges_selectionmodel.select(item_selection, QItemSelectionModel.SelectionFlag.ClearAndSelect)

		# 		if edge_selection:
		# 			self.edges_selectionmodel.setCurrentIndex(edge_selection[-1], QItemSelectionModel.SelectionFlag.Current)
		# 		else:
		# 			self.edges_selectionmodel.setCurrentIndex(QModelIndex(), QItemSelectionModel.SelectionFlag.Clear)

	def pinAt(self, pos:QPoint):
		"""Returns the topmost pin at position pos, which is in viewport coordinates."""
		for item in self.items(pos):
			if isinstance(item, PinGraphicsItem):
				return item
		return None

	def initiateConnection(self, pin):
		if isinstance(pin, OutletGraphicsItem):
			self.interactive_edge = EdgeGraphicsItem(source_pin_item=pin, target_pin_item=None, parent_graph=self)
			self.interactive_edge_start_pin = pin
		elif isinstance(pin, InletGraphicsItem):
			self.interactive_edge = EdgeGraphicsItem(source_pin_item=None, target_pin_item=pin, parent_graph=self)
			self.interactive_edge_start_pin = pin
		self.interactive_edge.updatePosition()
		self.scene().addItem(self.interactive_edge)

	def modifyConnection(self, edge:EdgeGraphicsItem, endpoint:PinType):
		print("modify connection", endpoint)
		if endpoint == PinType.OUTLET:
			self.interactive_edge = edge
			self.interactive_edge_start_pin = edge.targetPin()
		elif endpoint == PinType.INLET:
			self.interactive_edge = edge
			self.interactive_edge_start_pin = edge.sourcePin()
		else:
			raise ValueError(f"Invalid endpoint, got: {endpoint}")

	def moveConnection(self, pos:QPoint):
		assert isinstance(pos, QPoint), f"got: {pos}"
		# move free endpoint
		line = self.interactive_edge.line()
		if isinstance(self.interactive_edge_start_pin, OutletGraphicsItem):
			line.setP2(self.mapToScene(pos))
		elif isinstance(self.interactive_edge_start_pin, InletGraphicsItem):
			line.setP1(self.mapToScene(pos))
		self.interactive_edge.setLine(line)

		# attach free endpoint to closeby pin
		pinUnderMouse = self.pinAt(pos)
		if isinstance(self.interactive_edge_start_pin, OutletGraphicsItem) and isinstance(pinUnderMouse, InletGraphicsItem):
			self.interactive_edge.setTargetPin(pinUnderMouse)
			self.interactive_edge.updatePosition()
		elif isinstance(self.interactive_edge_start_pin, InletGraphicsItem) and isinstance(pinUnderMouse, OutletGraphicsItem):
			self.interactive_edge.setSourcePin(pinUnderMouse)
			self.interactive_edge.updatePosition()

	def finishConnection(self, pin:PinGraphicsItem|None):
		assert self.interactive_edge_start_pin
		start_pin:InletGraphicsItem|OutletGraphicsItem = self.interactive_edge_start_pin
		end_pin = pin
		persistent_edge_index = cast(EdgeRef|None, self.item_to_index_map.get(self.interactive_edge))

		CanConnectPins = (
			isinstance(start_pin, InletGraphicsItem) 
			and isinstance(end_pin, OutletGraphicsItem)
		) or (
			isinstance(start_pin, OutletGraphicsItem) 
			and isinstance(end_pin, InletGraphicsItem)
		)

		IsEdgeExists = (
			self.graph_model
			and persistent_edge_index
			and persistent_edge_index.isValid()
		)

		if CanConnectPins and end_pin:
			if IsEdgeExists and self.graph_model and persistent_edge_index:
				"""modify edge"""
				edge_index:EdgeRef = persistent_edge_index
				self.graph_model.removeEdges([edge_index])

				if isinstance(end_pin, OutletGraphicsItem) and isinstance(start_pin, InletGraphicsItem):
					outlet = cast(OutletRef, self.item_to_index_map[end_pin])
					inlet = cast(InletRef, self.item_to_index_map[start_pin])
					self.graph_model.addEdge(outlet, inlet)

				elif isinstance(end_pin, InletGraphicsItem) and isinstance(start_pin, OutletGraphicsItem):
					outlet = cast(OutletRef, self.item_to_index_map[start_pin])
					inlet = cast(InletRef, self.item_to_index_map[end_pin])
					self.graph_model.addEdge(outlet, inlet)

				else:
					raise ValueError(f"Can't connect {end_pin} to {start_pin}")

			else:
				"""create edge"""
				inlet_item = cast(InletGraphicsItem, end_pin)
				outlet_item = cast(OutletGraphicsItem, start_pin)
				if isinstance(end_pin, OutletGraphicsItem) and isinstance(start_pin, InletGraphicsItem):
					outlet_item, inlet_item = inlet_item, outlet_item

				if (
					self.graph_model 
					and self.item_to_index_map[outlet_item] 
					and self.item_to_index_map[inlet_item]
				):
					self.interactive_edge.destroy()
					outlet:OutletRef = cast(OutletRef, self.item_to_index_map[outlet_item])
					inlet:InletRef = cast(InletRef, self.item_to_index_map[inlet_item])
					self.graph_model.addEdge(outlet, inlet)
				else:
					raise NotImplementedError()
		else:
			if IsEdgeExists:
				"""Delete Edge"""
				if self.graph_model and persistent_edge_index:
					self.graph_model.removeEdges([persistent_edge_index])
					return
			else:
				"""remove interactive edge"""
				self.interactive_edge.destroy()

	def model(self)->GraphModel|None:
		return self.graph_model

	def setModel(self, graph_model:GraphModel):
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

	@Slot(QModelIndex, int, int)
	def handleNodesAdded(self, nodes:Iterable[NodeRef]):
		if not self.graph_model:
			return

		for node in nodes:
			# create node item
			node_item = self.nodeFactory(node)

			self.index_to_item_map[node] = node_item
			self.item_to_index_map[node_item] = node


			# update gaphics item
			self.handleNodesPropertiesChanged([node])
			self.handleInletsAdded(self.graph_model.getNodeInlets(node))
			self.handleOutletsAdded(self.graph_model.getNodeOutlets(node))

			# add item to view
			self.scene().addItem(node_item)

	def nodeFactory(self, node:NodeRef)->QGraphicsItem:
		return NodeGraphicsItem(self)

	# def onNodePropertyChange(self, node:NodeRef, node_item:QGraphicsItem, properties:List[str]|None):
	# 	raise NotImplementedError("subclasses must implement onNodePropertyChange")

	# def onNodeEditorChange(self, node:NodeRef, node_item:QGraphicsItem, properties:List[str]|None):
	# 	raise NotImplementedError("subclasses must implement onNodeEditorChange")

	@Slot(QModelIndex, int, int)
	def handleNodesRemoved(self, nodes:Iterable[NodeRef]):
		for node in nodes:
			node_item = cast(NodeGraphicsItem, self.index_to_item_map[node])
			node_item.destroy()
			del self.index_to_item_map[node]
			del self.item_to_index_map[node_item]

	@Slot(QModelIndex, int, int)
	def handleEdgesAdded(self, edges:Iterable[EdgeRef]):
		if not self.graph_model:
			return

		for edge in edges:
			try:
				edge_item = cast(EdgeGraphicsItem, self.index_to_item_map[edge])
			except KeyError:
				edge_item = EdgeGraphicsItem(source_pin_item=None, target_pin_item=None, parent_graph=self)
				self.scene().addItem(edge_item)
				self.item_to_index_map[edge_item] = edge
				self.index_to_item_map[edge] = edge_item

			outlet = self.graph_model.getEdgeSource(edge)
			source_pin_item = cast(OutletGraphicsItem, self.index_to_item_map[outlet])
			edge_item.setSourcePin( source_pin_item )

			inlet = self.graph_model.getEdgeTarget(edge)
			target_pin_item = cast(InletGraphicsItem, self.index_to_item_map[inlet])
			edge_item.setTargetPin( target_pin_item )

			# update gaphics item
			self.handleEdgesPropertiesChanged([edge])

	def handleEdgesRemoved(self, edges:Iterable[EdgeRef]):
		assert all(isinstance(edge, EdgeRef) for edge in edges), f"got: {edges}"
		for edge in edges:
			edge_item = cast(EdgeGraphicsItem, self.index_to_item_map[edge])
			edge_item.destroy()
			del self.index_to_item_map[edge]
			del self.item_to_index_map[edge_item]

	def handleOutletsAdded(self, outlets:Iterable[OutletRef]):
		if not self.graph_model:
			return

		for outlet in outlets:
			parent_node = self.graph_model.getOutletOwner(outlet) # get the node reference

			# create outlet graphics item
			parent_node_item = cast(NodeGraphicsItem, self.index_to_item_map[parent_node]) # get the node graphics item
			outlet_item = OutletGraphicsItem()
			parent_node_item.addOutlet(outlet_item)

			# map inlet to graphics item
			self.item_to_index_map[outlet_item] = outlet
			self.index_to_item_map[outlet] = outlet_item

			# update graphics item
		self.handleOutletsPropertiesChanged(outlets)

	def handleOutletsRemoved(self, outlets:Iterable[OutletRef]):
		if not self.graph_model:
			return

		for outlet in outlets:
			parent_node = self.graph_model.getOutletOwner(outlet) # get the node reference

			# remove outlet graphics item
			outlet_item = cast(OutletGraphicsItem, self.index_to_item_map[outlet])
			outlet_item.destroy()

			# remove mapping
			del self.index_to_item_map[outlet]
			del self.item_to_index_map[outlet_item]

	def handleInletsAdded(self, inlets:Iterable[InletRef]):
		if not self.graph_model:
			return

		for inlet in inlets:
			parent_node = self.graph_model.getInletOwner(inlet) # get the node reference
			parent_node_item = cast(NodeGraphicsItem, self.index_to_item_map[parent_node]) # get the node graphics item
			inlet_item = InletGraphicsItem()
			parent_node_item.addInlet(inlet_item)

			# map inlet to graphics item
			self.item_to_index_map[inlet_item] = inlet
			self.index_to_item_map[inlet] = inlet_item

			# update graphics item and add to scene
			print("handle inlets added", inlet)
		self.handleInletsPropertiesChanged(inlets)

	@Slot(QModelIndex, int, int)
	def handleInletsRemoved(self, inlets:Iterable[InletRef]):
		if not self.graph_model:
			return

		for inlet in inlets:
			persistent_index = inlet
			inlet_item = cast(InletGraphicsItem, self.index_to_item_map[persistent_index])
			inlet_item.destroy()
			del self.index_to_item_map[persistent_index]
			del self.item_to_index_map[inlet_item]

	# Handle Properties
	def handleNodesPropertiesChanged(self, nodes:List[NodeRef], properties:List[str]=None):
		graph = self.model()
		if not graph:
			return

		# TODO: HANDLE ALL PROPERTIES CHANGED !!!!!!!!
		for node in nodes:
			node_item = cast(NodeGraphicsItem, self.index_to_item_map[node])
			self.onNodePropertyChange(node, node_item, properties)

	def handleEdgesPropertiesChanged(self, edges:Iterable[EdgeRef], properties:List[str]|None=None):
		if not self.graph_model:
			return

		for edge in edges:
			edge_item = cast(EdgeGraphicsItem, self.index_to_item_map[edge])
			... #TODO: 

	def handleOutletsPropertiesChanged(self, outlets:Iterable[OutletRef], properties:List[str]|None=None):
		if not self.graph_model:
			return

		# TODO: HANDLE ALL PROPERTIES CHANGED !!!!!!!!
		# this is probably shoudl be an abstract method,
		# and implement it in the standard, example versions

		for outlet in outlets:
			outlet_item = cast(OutletGraphicsItem, self.index_to_item_map[outlet])
			if not properties or "name" in properties:
				new_name = self.graph_model.getOutletProperty(outlet, "name")
				if outlet_item.label.text() != new_name:
					outlet_item.label.setText(new_name)

	def handleInletsPropertiesChanged(self, inlets:Iterable[InletRef], properties:List[str]|None=None):
		if not self.graph_model:
			return

		# TODO: HANDLE ALL PROPERTIES CHANGED !!!!!!!!
		# this is probably shoudl be an abstract method,
		# and implement it in the standard, example versions

		for inlet in inlets:
			inlet_item = cast(InletGraphicsItem, self.index_to_item_map[inlet])
			if not properties or 'name' in properties: 
				new_name = self.graph_model.getInletProperty(inlet, 'name')
				if inlet_item.label.text() != new_name:
					inlet_item.label.setText(new_name)

	# Selection
	def setNodesSelectionModel(self, nodes_selectionmodel:QItemSelectionModel):
		self.nodes_selectionmodel = nodes_selectionmodel
		self.nodes_selectionmodel.selectionChanged.connect(self.handleNodesSelectionChanged)

	def setEdgesSelectionModel(self, edges_selectionmodel:QItemSelectionModel):
		self.edges_selectionmodel = edges_selectionmodel
		self.edges_selectionmodel.selectionChanged.connect(self.handleEdgesSelectionChanged)

	@Slot(QItemSelection, QItemSelection)
	def handleNodesSelectionChanged(self, selected:QItemSelection, deselected:QItemSelection):
		if not self.graph_model:
			return

		self.scene().blockSignals(True)
		for node in [NodeRef(index, self.graph_model) for index in selected.indexes() if index.column()==0]:
			node_item = cast(NodeGraphicsItem, self.index_to_item_map[node])
			node_item.setSelected(True)

		for node in [NodeRef(index, self.graph_model) for index in deselected.indexes() if index.column()==0]:
			node_item = cast(NodeGraphicsItem, self.index_to_item_map[node])
			node_item.setSelected(False)
		self.scene().blockSignals(False)

	def handleEdgesSelectionChanged(self, selected:QItemSelection, deselected:QItemSelection):
		if not self.graph_model:
			return

		self.scene().blockSignals(True)
		for edge in [EdgeRef(index, self.graph_model) for index in selected.indexes() if index.column()==0]:
			item = cast(EdgeGraphicsItem, self.index_to_item_map[edge])
			item.setSelected(True)

		for edge in [EdgeRef(index, self.graph_model) for index in deselected.indexes() if index.column()==0]:
			item = cast(EdgeGraphicsItem, self.index_to_item_map[edge])
			item.setSelected(False)
		self.scene().blockSignals(False)


class StandardNodeItem(NodeGraphicsItem):
		def __init__(self, parent_graph: "GraphView"):
			# model reference
			# self.persistent_node_index:Optional[NodeRef] = None
			super().__init__(parent_graph)

			# # widgets
			self.nameedit = EditableTextItem(self)
			self.nameedit.setPos(0,0)
			self.nameedit.setTextWidth(self.rect.width()-10)

		def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent):
			# Enable editing subitems on double-click
			"""parent node must manually cal the double click event,
			because an item nor slectable nor movable will not receive press events"""

			# Check if double-click is within the text item’s bounding box
			if self.nameedit.contains(self.mapFromScene(event.scenePos())):
				# Forward the event to nameedit if clicked inside it
				self.nameedit.mouseDoubleClickEvent(event)
			else:
				print("NodeItem->mouseDoubleClickEvent")
				super().mouseDoubleClickEvent(event)
			

class StandardGraphView(GraphView):
	@override
	def nodeFactory(self, node:NodeRef)->QGraphicsItem:
		node_item = StandardNodeItem(parent_graph=self)
		
		node_item.nameedit.document().contentsChanged.connect(lambda: (
			self.model().setNodeProperty(node, name=node_item.nameedit.toPlainText())
		) if self.model() else None)

		node_item.positionChanged.connect(lambda: (
			self.model().blockSignals(True),
			self.model().setNodeProperty(node, posx=int(node_item.x())),
			self.model().setNodeProperty(node, posy=int(node_item.y())),
			self.model().blockSignals(False),
			self.model().nodesPropertyChanged.emit([node], ['posx', 'posy'])
		) if self.model() else None)

		return node_item

	@override
	def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
		graph = self.model()
		if not graph or self.itemAt(event.position().toPoint()):
			return super().mouseDoubleClickEvent(event)

		clickpos = self.mapToScene(event.position().toPoint())
		node = graph.addNode(name="new node", posx=int(clickpos.x()), posy=int(clickpos.y()))
		graph.addInlet(node, name="in")
		graph.addOutlet(node, name="out")

	@override
	def handleNodesPropertiesChanged(self, nodes: List[NodeRef], properties: List[str] = None):
		graph = self.model()
		for node in nodes:
			node_item = cast(StandardNodeItem, self.index_to_item_map[node])
			if not graph:
				return

			if not properties or 'name' in properties:
				new_expression = graph.getNodeProperty(node, 'name')
				old_expression = node_item.nameedit.toPlainText()
				if new_expression != old_expression:
					node_item.nameedit.setPlainText(new_expression)

			if not properties or 'posx' in properties or 'posy' in properties:
				x = int(graph.getNodeProperty(node, 'posx'))
				y = int(graph.getNodeProperty(node, 'posy'))
				node_item.setPos(x,y)

if __name__ == "__main__":
	from tableview_columnbased import GraphTableView
	from detailsview_columnbased import GraphDetailsView

	class MainWindow(QWidget):
		def __init__(self):
			super().__init__()

			self.setWindowTitle("Graph Viewer Example")
			self.resize(900, 500)

			# Initialize the GraphModel
			self.graph_model = GraphModel()

			# Add some example nodes and edges
			read_node = self.graph_model.addNode(name="Read", posx=10, posy=-100)
			outlet_id = self.graph_model.addOutlet(read_node, name="image")
			write_node = self.graph_model.addNode(name="Write", posx=20, posy=100)
			inlet_id = self.graph_model.addInlet(write_node, name="image")

			node3_id = self.graph_model.addNode(name="Preview", posx=-50, posy=10)
			self.graph_model.addInlet(node3_id, name="in")
			self.graph_model.addOutlet(node3_id, name="out")
			
			
			self.graph_model.addEdge(outlet_id, inlet_id)

			# Set up the node editor views

			self.graph_view = StandardGraphView()
			self.graph_view.setModel(self.graph_model)
			# self.graph_view.setNodesSelectionModel(self.nodes_selectionmodel)
			# self.graph_view.setEdgesSelectionModel(self.edges_selectionmodel)

			self.graph_view2 = StandardGraphView()
			self.graph_view2.setModel(self.graph_model)


			layout = QHBoxLayout()
			layout.addWidget(self.graph_view, 1)
			layout.addWidget(self.graph_view2, 1)
			self.setLayout(layout)

			self.menubar = QMenuBar()
			self.color_mode_action = QAction("switch color mode")
			self.color_mode_action.setCheckable(True)
			self.color_mode_action.triggered.connect(self.toggleColorMode)
			self.menubar.addAction(self.color_mode_action)
			self.layout().setMenuBar(self.menubar)

		def toggleColorMode(self):
			from pylive.ColorModeSwitcher import light_color_scheme, dark_color_scheme, QPaletteFromJson
			if self.color_mode_action.isChecked():
				dark_palette = QPaletteFromJson(light_color_scheme)
				QApplication.setPalette(dark_palette)
				self.graph_view.setPalette(dark_palette)
				items = self.graph_view.scene().items()
				self.graph_view.update()
				for item in items:
					item.update(self.graph_view.sceneRect())
				self.graph_view.viewport().update()
				self.graph_view.scene().update(self.graph_view.sceneRect())
				self.graph_view.update()

			else:
				light_palette = QPaletteFromJson(dark_color_scheme)
				QApplication.setPalette(light_palette)
				self.graph_view.setPalette(light_palette)
				items = self.graph_view.scene().items()
				for item in items:
					item.update(self.graph_view.sceneRect())
				self.graph_view.viewport().update()
				self.graph_view.scene().update(self.graph_view.sceneRect())
				self.graph_view.update()

	app = QApplication(sys.argv)
	window = MainWindow()
	window.show()
	sys.exit(app.exec())
