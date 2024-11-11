from re import X
import sys
import math
from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from pylive.QtGraphEditor import graphmodel_columnbased
from pylive.QtGraphEditor.PanAndZoomGraphicsView import PanAndZoomGraphicsView
from pylive.QtGraphEditor.graphmodel_columnbased import (
	GraphModel,
	NodeRef, EdgeRef, InletRef, OutletRef,
	NodeAttribute, EdgeAttribute, InletAttribute, OutletAttribute
)

from enum import Enum
class PinType(Enum):
	INLET = "INLET"
	OUTLET = "OUTLET"

class PinItem(QGraphicsItem):
	"""Graphics item representing a pin (either inlet or outlet)."""
	def __init__(self, parent=None):
		super().__init__(parent=parent)
		self.parent_node:'NodeGraphicsItem|None' = None
		self.edges = []

		self.label = QGraphicsSimpleTextItem(parent=self)
		self.label.setBrush(QApplication.palette().text().color())
		self.label.setY(-QFontMetrics(self.label.font()).height())
		self.label.hide()

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

	def destroy(self):
		for edge in self.edges:
			edge.destroy()
		self.edges = []

		if self.parent_node:
			self.parent_node.removeInlet(self)
			self.parent_node.updatePinPositions()
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
		self.setZValue(2)		

	def destroy(self):
		for inlet in self.inlets:
			inlet.destroy()
		for outlet in self.outlets:
			outlet.destroy()
		self.scene().removeItem(self)

	def addOutlet(self, outlet:PinItem):
		outlet.parent_node = self
		outlet.setParentItem(self)
		self.outlets.append(outlet)
		self.updatePinPositions()

	def removeOutlet(self, outlet:PinItem):
		self.outlets.remove(outlet)
		self.updatePinPositions()

	def addInlet(self, inlet:PinItem):
		inlet.parent_node = self
		inlet.setParentItem(self)
		self.inlets.append(inlet)
		self.updatePinPositions()

	def removeInlet(self, inlet:PinItem):
		self.inlets.remove(inlet)
		self.updatePinPositions()

	def mouseDoubleClickEvent(self, event: QMouseEvent):
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

	def updatePinPositions(self, vertical_mode=False):
		"""
		Update the positions of inlets and outlets.
		:param vertical_mode: If True, place inlets on the left and outlets on the right (default).
							  If False, place inlets on the top and outlets on the bottom.
		"""
		offset = 0
		rect_width = self.rect.width()
		rect_height = self.rect.height()

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
			case QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
				self.positionChanged.emit()

		return super().itemChange(change, value)

class OutletView(PinItem):
	def __init__(self, parent=None):
		super().__init__(parent=parent)
		self.persistent_index:Optional[OutletRef]=None


class InletView(PinItem):
	def __init__(self, parent=None):
		super().__init__(parent=parent)
		self.persistent_index:Optional[InletRef]=None


class EditableTextItem(QGraphicsTextItem):
	def __init__(self, text, parent=None):
		super().__init__(text, parent)
		self.setFlag(QGraphicsItem.ItemIsFocusable)  # Allow focus events
		self.setTextInteractionFlags(Qt.NoTextInteraction)  # Initially non-editable
		# self.setFlag(QGraphicsItem.ItemIsSelectable, True)

		# Center-align the text within the item
		text_option = QTextOption()
		text_option.setAlignment(Qt.AlignCenter)
		self.document().setDefaultTextOption(text_option)

		# Remove the default margins
		self.document().setDocumentMargin(0)

	def mouseDoubleClickEvent(self, event):
		# Enable editing on double-click
		"""parent node must manually cal the double click event,
		because an item nor slectable nor movable will not receive press events"""
		self.setTextInteractionFlags(Qt.TextEditorInteraction)
		self.setFocus(Qt.MouseFocusReason)

		click = QGraphicsSceneMouseEvent(QEvent.GraphicsSceneMousePress)
		click.setButton(event.button())
		click.setPos(event.pos())
		self.mousePressEvent(click)
		# super().mouseDoubleClickEvent(event)

	def focusOutEvent(self, event: QFocusEvent):
		# When the item loses focus, disable editing
		self.setTextInteractionFlags(Qt.NoTextInteraction)
		super().focusOutEvent(event)


class EdgeItem(QGraphicsLineItem):
	"""Graphics item representing an edge (connection)."""
	GrabThreshold = 15
	def __init__(self, source_pin_item:OutletView|None, target_pin_item:InletView|None, parent_graph:"GraphView"):
		super().__init__(parent=None)
		assert source_pin_item is None or isinstance(source_pin_item, OutletView)
		assert target_pin_item is None or isinstance(target_pin_item, InletView)
		self._source_pin_item = source_pin_item
		self._target_pin_item = target_pin_item
		self.parent_graph = parent_graph

		if source_pin_item:
			source_pin_item.edges.append(self)
		if target_pin_item:
			target_pin_item.edges.append(self)
		self.persistent_edge_index:Optional[EdgeRef] = None

		self.setPen(QPen(Qt.GlobalColor.black, 2))
		self.updatePosition()

		# Enable selecting
		self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
		self.setAcceptHoverEvents(True)

		self.setZValue(-1)

		#
		self.is_moving_endpoint = False

	def destroy(self):
		if self._source_pin_item:
			self._source_pin_item.edges.remove(self)
		if self._target_pin_item:
			self._target_pin_item.edges.remove(self)
		self.scene().removeItem(self)

	def sourcePin(self)->OutletView|None:
		return self._source_pin_item

	def setSourcePin(self, pin: OutletView|None):
		assert pin is None or isinstance(pin, OutletView)

		# add or remove edge to pin edges for position update
		if pin:
			pin.edges.append(self)
		elif self._source_pin_item:
			self._source_pin_item.edges.remove(self)

		self._source_pin_item = pin
		self.updatePosition()

	def targetPin(self):
		return self._target_pin_item

	def setTargetPin(self, pin: InletView|None):
		assert pin is None or isinstance(pin, InletView)

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

	def itemChange(self, change, value):
		if self.persistent_edge_index and self.persistent_edge_index.isValid():
			if QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
				if self.parent_graph.graph_model and self.parent_graph.edges_selectionmodel:
					edges_selectionmodel = self.parent_graph.edges_selectionmodel
					graph:GraphModel = self.parent_graph.graph_model

					if value == 1:
						edges_selectionmodel.select(self.persistent_edge_index._index, QItemSelectionModel.SelectionFlag.Select)
					elif value == 0:
						edges_selectionmodel.select(self.persistent_edge_index._index, QItemSelectionModel.SelectionFlag.Deselect)
				else:
					pass

		return super().itemChange(change, value)

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


class EdgeView(EdgeItem):
	def __init__(self, source_pin_item:OutletView|None, target_pin_item:InletView|None, parent_graph:"GraphView"):
		super().__init__(source_pin_item, target_pin_item, parent_graph)


class NodeView(NodeGraphicsItem):
	def __init__(self, parent_graph: "GraphView"):
		# model reference
		self.persistent_node_index:Optional[NodeRef] = None
		super().__init__(parent_graph)

		# widgets
		self.nameedit = EditableTextItem(self)
		self.nameedit.setPos(0,0)
		self.nameedit.setTextWidth(self.rect.width()-10)

		# self.nameedit.document().contentsChanged.connect(self.nameChangedEvent)
		# self.positionChanged.connect(self.positionChangedEvent)

	# def nameChangedEvent(self):
	# 	if (self.parent_graph.graph_model and
	# 		self.persistent_node_index and
	# 		self.persistent_node_index.isValid()
	# 	):
	# 		graph:GraphModel = self.parent_graph.graph_model
	# 		node_index = self.persistent_node_index
	# 		new_name = self.nameedit.toPlainText()
	# 		graph.setNodeData(node_index, new_name, NodeAttribute.Name)

	# def positionChangedEvent(self):
	# 	if (self.parent_graph.graph_model and
	# 		self.persistent_node_index and
	# 		self.persistent_node_index.isValid()
	# 	):
	# 		graph:GraphModel = self.parent_graph.graph_model
	# 		node_index = self.persistent_node_index
	# 		new_pos = self.pos()
	# 		graph.setNodeData(node_index, int(new_pos.x()), NodeAttribute.LocationX)
	# 		graph.setNodeData(node_index, int(new_pos.y()), NodeAttribute.LocationY)



# class NodeItemDelegate(QObject):
# 	commitData = Signal(NodeGraphicsItem, NodeRef, list)
# 	def __init__(self, parent: Optional[QObject] = None) -> None:
# 		super().__init__(parent)
# 		# self.commitData.connect(self.setModelData)

# 	def createEditor(self, parent:'GraphView', option:QStyleOptionViewItem , node: NodeRef)->NodeGraphicsItem:
		

# 		return node_item

# 	def setEditorData(self, editor: NodeGraphicsItem, graph:GraphModel, node: NodeRef, attributes: List[NodeAttribute]):





class PinItemDelegate(QObject):
	...


class EdgeItemDelegate(QObject):
	...


class GraphView(PanAndZoomGraphicsView):
	"""A view that displays the node editor."""
	def __init__(self, parent=None):
		super().__init__(parent)

		# Create a scene to hold the node and edge graphics
		scene = QGraphicsScene(self)
		scene.setSceneRect(QRect(-9999//2,-9999//2, 9999, 9999))
		self.setScene(scene)
		self.index_to_item_map:Dict[NodeRef|EdgeRef|InletRef|OutletRef, QGraphicsItem] = dict()

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
		# 		if isinstance(item, EdgeView):
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
			if isinstance(item, PinItem):
				return item
		return None

	def initiateConnection(self, pin):
		if isinstance(pin, OutletView):
			self.interactive_edge = EdgeView(source_pin_item=pin, target_pin_item=None, parent_graph=self)
			self.interactive_edge_start_pin = pin
		elif isinstance(pin, InletView):
			self.interactive_edge = EdgeView(source_pin_item=None, target_pin_item=pin, parent_graph=self)
			self.interactive_edge_start_pin = pin
		self.interactive_edge.updatePosition()
		self.scene().addItem(self.interactive_edge)

	def modifyConnection(self, edge:EdgeView, endpoint:PinType):
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
		if isinstance(self.interactive_edge_start_pin, OutletView):
			line.setP2(self.mapToScene(pos))
		elif isinstance(self.interactive_edge_start_pin, InletView):
			line.setP1(self.mapToScene(pos))
		self.interactive_edge.setLine(line)

		# attach free endpoint to closeby pin
		pinUnderMouse = self.pinAt(pos)
		if isinstance(self.interactive_edge_start_pin, OutletView) and isinstance(pinUnderMouse, InletView):
			self.interactive_edge.setTargetPin(pinUnderMouse)
			self.interactive_edge.updatePosition()
		elif isinstance(self.interactive_edge_start_pin, InletView) and isinstance(pinUnderMouse, OutletView):
			self.interactive_edge.setSourcePin(pinUnderMouse)
			self.interactive_edge.updatePosition()

	def finishConnection(self, pin:PinItem|None):
		assert self.interactive_edge_start_pin
		start_pin:InletView|OutletView = self.interactive_edge_start_pin
		end_pin = pin
		persistent_edge_index = self.interactive_edge.persistent_edge_index

		CanConnectPins = (
			isinstance(start_pin, InletView) 
			and isinstance(end_pin, OutletView)
		) or (
			isinstance(start_pin, OutletView) 
			and isinstance(end_pin, InletView)
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
				if isinstance(end_pin, OutletView) and end_pin.persistent_index:
					outlet = cast(OutletRef, end_pin.persistent_index)
					self.graph_model.setEdgeSource(edge_index, outlet)
				elif isinstance(end_pin, InletView) and end_pin.persistent_index:
					inlet = cast(InletRef, end_pin.persistent_index)
					self.graph_model.setEdgeTarget(edge_index, inlet)
			else:
				"""create edge"""
				inlet_item = cast(InletView, end_pin)
				outlet_item = cast(OutletView, start_pin)
				if isinstance(end_pin, OutletView) and isinstance(start_pin, InletView):
					outlet_item, inlet_item = inlet_item, outlet_item

				if (
					self.graph_model 
					and outlet_item.persistent_index 
					and inlet_item.persistent_index
				):
					self.interactive_edge.destroy()
					outlet:OutletRef = cast(OutletRef, outlet_item.persistent_index)
					inlet:InletRef = cast(InletRef, inlet_item.persistent_index)
					self.graph_model.addEdge(outlet=outlet, inlet=inlet)
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
		self.graph_model.nodesDataChanged.connect(self.handleNodesDataChanged)
		self.graph_model.nodesAboutToBeRemoved.connect(self.handleNodesRemoved)

		self.graph_model.inletsAdded.connect(self.handleInletsAdded)
		self.graph_model.inletsDataChanged.connect(self.handleInletsDataChanged)
		self.graph_model.inletsAboutToBeRemoved.connect(self.handleInletsRemoved)

		self.graph_model.outletsAdded.connect(self.handleOutletsAdded)
		self.graph_model.outletsDataChanged.connect(self.handleOutletsDataChanged)
		self.graph_model.outletsAboutToBeRemoved.connect(self.handleOutletsRemoved)

		self.graph_model.edgesAdded.connect(self.handleEdgesAdded)
		self.graph_model.edgesDataChanged.connect(self.handleEdgesDataChanged)
		self.graph_model.edgesAboutToBeRemoved.connect(self.handleEdgesRemoved)

	@Slot(QModelIndex, int, int)
	def handleNodesAdded(self, nodes:List[NodeRef]):
		if not self.graph_model:
			return

		for node in nodes:
			# create node item
			node_item = NodeView(parent_graph=self)
			self.scene().addItem(node_item)
			node_item.persistent_node_index = node
			self.index_to_item_map[node] = node_item

			# bind events to model
			node_item.nameedit.document().contentsChanged.connect(lambda node=node, node_item=node_item: 
				self.graph_model.setNodeData(node, node_item.nameedit.toPlainText(), NodeAttribute.Name) if self.graph_model else None
			)
			node_item.positionChanged.connect(lambda node=node, node_item=node_item: (
				self.graph_model.blockSignals(True),
				self.graph_model.setNodeData(node, int(node_item.x()), NodeAttribute.LocationX),
				self.graph_model.setNodeData(node, int(node_item.y()), NodeAttribute.LocationY),
				self.graph_model.blockSignals(False),
				self.graph_model.nodesDataChanged.emit([node], [NodeAttribute.LocationX, NodeAttribute.LocationY])
			) if self.graph_model else None )


			# update gaphics item
			self.handleNodesDataChanged([node])
			self.handleInletsAdded(self.graph_model.getNodeInlets(node))
			self.handleOutletsAdded(self.graph_model.getNodeOutlets(node))
	
	def handleNodesDataChanged(self, nodes:List[NodeRef], attributes:List[NodeAttribute]|None=None):
		print("handleNodesDataChanged", nodes, attributes)
		if not self.graph_model:
			return

		if not attributes:
			attributes = [NodeAttribute.Id, NodeAttribute.Name, NodeAttribute.LocationX, NodeAttribute.LocationY]

		for node in nodes:
			node_item = cast(NodeView, self.index_to_item_map[node])
			new_pos = node_item.pos()
			for attribute in attributes:
				match attribute:
					case NodeAttribute.Id:
						pass

					case NodeAttribute.Name:
						new_name = self.graph_model.getNodeData(node, attribute)
						old_name = node_item.nameedit.toPlainText()
						if old_name != new_name:
							node_item.nameedit.setPlainText(new_name)

					case NodeAttribute.LocationX:
						"""posx changed"""
						data = self.graph_model.getNodeData(node, attribute)
						new_pos.setX(int(data))

					case NodeAttribute.LocationY:
						"""posy changed"""
						data = self.graph_model.getNodeData(node, attribute)
						new_pos.setY(int(data))

			if new_pos!=node_item.pos():
				node_item.setPos(new_pos)

	@Slot(QModelIndex, int, int)
	def handleNodesRemoved(self, nodes:List[NodeRef]):
		for node in nodes:
			node_item = cast(NodeView, self.index_to_item_map[node])
			node_item.destroy()
			del self.index_to_item_map[node]

	@Slot(QModelIndex, int, int)
	def handleEdgesAdded(self, edges:List[EdgeRef]):
		if not self.graph_model:
			return

		for edge in edges:
			try:
				edge_item = cast(EdgeView, self.index_to_item_map[edge])
			except KeyError:
				edge_item = EdgeView(source_pin_item=None, target_pin_item=None, parent_graph=self)
				self.scene().addItem(edge_item)
				edge_item.persistent_edge_index = edge
				self.index_to_item_map[edge] = edge_item

			outlet = self.graph_model.getEdgeSource(edge)
			source_pin_item = cast(OutletView, self.index_to_item_map[outlet])
			edge_item.setSourcePin( source_pin_item )

			inlet = self.graph_model.getEdgeTarget(edge)
			target_pin_item = cast(InletView, self.index_to_item_map[inlet])
			edge_item.setTargetPin( target_pin_item )

			# update gaphics item
			self.handleEdgesDataChanged([edge])

	def handleEdgesRemoved(self, edges:List[EdgeRef]):
		for edge in edges:
			edge_item = cast(EdgeView, self.index_to_item_map[edge])
			edge_item.destroy()
			del self.index_to_item_map[edge]
	
	def handleEdgesDataChanged(self, edges:List[EdgeRef], attributes:List[EdgeAttribute]|None=None):
		if not self.graph_model:
			return

		if not attributes:
			attributes = [EdgeAttribute.Id, EdgeAttribute.SourceOutlet, EdgeAttribute.TargetInlet]

		for edge in edges:
			edge_item = cast(EdgeView, self.index_to_item_map[edge])
			for attribute in attributes:
				match attribute:
					case EdgeAttribute.Id:
						"""unique id changed"""
						pass

	def handleOutletsAdded(self, outlets:List[OutletRef]):

		if not self.graph_model:
			return

		for outlet in outlets:

			parent_node = self.graph_model.getOutletOwner(outlet) # get the node reference

			# create outlet graphics item
			parent_node_item = cast(NodeView, self.index_to_item_map[parent_node]) # get the node graphics item
			outlet_item = OutletView()
			parent_node_item.addOutlet(outlet_item)

			# map inlet to graphics item
			outlet_item.persistent_index = outlet
			self.index_to_item_map[outlet] = outlet_item



			# update graphics item
		self.handleOutletsDataChanged(outlets)

	def handleOutletsRemoved(self, outlets:List[OutletRef]):
		if not self.graph_model:
			return

		for outlet in outlets:
			parent_node = self.graph_model.getOutletOwner(outlet) # get the node reference

			# remove outlet graphics item
			outlet_item = cast(OutletView, self.index_to_item_map[outlet])
			outlet_item.destroy()

			# remove mapping
			del self.index_to_item_map[outlet]
	
	def handleOutletsDataChanged(self, outlets:List[OutletRef], attributes:List[OutletAttribute]|None=None):
		if not self.graph_model:
			return

		if not attributes:
			attributes = [OutletAttribute.Id, OutletAttribute.Owner, OutletAttribute.Name]

		for outlet in outlets:
			outlet_item = cast(OutletView, self.index_to_item_map[outlet])
			for attribute in attributes:
				match attribute:
					case OutletAttribute.Id:
						"""unique id changed"""
						pass
					case OutletAttribute.Owner:
						"""parent node changed"""
						pass
					case OutletAttribute.Name:
						"""name changed"""
						new_name = self.graph_model.getOutletData(outlet, attribute)
						if outlet_item.label.text() != new_name:
							outlet_item.label.setText(new_name)

	def handleInletsAdded(self, inlets:List[InletRef]):
		if not self.graph_model:
			return

		for inlet in inlets:
			parent_node = self.graph_model.getInletOwner(inlet) # get the node reference
			parent_node_item = cast(NodeView, self.index_to_item_map[parent_node]) # get the node graphics item
			inlet_item = InletView()
			parent_node_item.addInlet(inlet_item)

			# map inlet to graphics item
			inlet_item.persistent_index = inlet
			self.index_to_item_map[inlet] = inlet_item

			# update graphics item and add to scene
		self.handleInletsDataChanged(inlets)

	@Slot(QModelIndex, int, int)
	def handleInletsRemoved(self, inlets:List[InletRef]):
		if not self.graph_model:
			return

		for inlet in inlets:
			persistent_index = inlet
			inlet_item = cast(InletView, self.index_to_item_map[persistent_index])
			inlet_item.destroy()
			del self.index_to_item_map[persistent_index]

	def handleInletsDataChanged(self, inlets:List[InletRef], attributes:List[InletAttribute]|None=None):
		if not self.graph_model:
			return

		if not attributes:
			attributes = [InletAttribute.Id, InletAttribute.Owner, InletAttribute.Name]

		for inlet in inlets:
			inlet_item = cast(InletView, self.index_to_item_map[inlet])
			for attribute in attributes:
				match attribute:
					case InletAttribute.Id:
						"""unique id changed"""
						pass
					case InletAttribute.Owner:
						"""parent node changed"""
						pass
					case InletAttribute.Name:
						"""name changed"""
						new_name = self.graph_model.getInletData(inlet, attribute)
						if inlet_item.label.text() != new_name:
							inlet_item.label.setText(new_name)

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
			node_item = cast(NodeView, self.index_to_item_map[node])
			node_item.setSelected(True)

		for node in [NodeRef(index, self.graph_model) for index in deselected.indexes() if index.column()==0]:
			node_item = cast(NodeView, self.index_to_item_map[node])
			node_item.setSelected(False)
		self.scene().blockSignals(False)

	def handleEdgesSelectionChanged(self, selected:QItemSelection, deselected:QItemSelection):
		if not self.graph_model:
			return

		self.scene().blockSignals(True)
		for edge in [EdgeRef(index, self.graph_model) for index in selected.indexes() if index.column()==0]:
			item = cast(EdgeView, self.index_to_item_map[edge])
			item.setSelected(True)

		for edge in [EdgeRef(index, self.graph_model) for index in deselected.indexes() if index.column()==0]:
			item = cast(EdgeView, self.index_to_item_map[edge])
			item.setSelected(False)
		self.scene().blockSignals(False)


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
			self.nodes_selectionmodel = QItemSelectionModel(self.graph_model._nodeTable)
			self.edges_selectionmodel = QItemSelectionModel(self.graph_model._edgeTable)

			# Add some example nodes and edges
			read_node = self.graph_model.addNode("Read", 10, -100)
			outlet_id = self.graph_model.addOutlet(read_node, "image")
			write_node = self.graph_model.addNode("Write", 20, 100)
			inlet_id = self.graph_model.addInlet(write_node, "image")

			node3_id = self.graph_model.addNode("Preview", -50, 10)
			self.graph_model.addInlet(node3_id, "in")
			self.graph_model.addOutlet(node3_id, "out")
			
			
			self.graph_model.addEdge(outlet_id, inlet_id)

			# Set up the node editor views

			self.graph_view = GraphView()
			self.graph_view.setModel(self.graph_model)
			self.graph_view.setNodesSelectionModel(self.nodes_selectionmodel)
			self.graph_view.setEdgesSelectionModel(self.edges_selectionmodel)

			self.graph_view2 = GraphView()
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
