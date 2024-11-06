import sys
import math
from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from pylive.QtGraphEditor.PanAndZoomGraphicsView import PanAndZoomGraphicsView
from pylive.QtGraphEditor.GraphModel import GraphModel, NodeIndex, EdgeIndex, InletIndex, OutletIndex

from enum import Enum
class PinType(Enum):
	INLET = "INLET"
	OUTLET = "OUTLET"


class PinItem(QGraphicsItem):
	"""Graphics item representing a pin (either inlet or outlet)."""
	def __init__(self, parent_node):
		super().__init__(parent=parent_node)
		assert isinstance(parent_node, NodeItem)
		self.parent_node = parent_node
		self.persistent_index:Optional[QModelIndex]=None
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
		if self.parent_node.isSelected() or state & QStyle.StateFlag.State_MouseOver:
			painter.setBrush(palette.accent().color())
		else:
			painter.setBrush(palette.windowText().color())
		painter.drawEllipse(-self.pin_radius, -self.pin_radius, self.pin_radius * 2, self.pin_radius * 2)

		# # Draw the name
		# painter.setPen(option.palette.light().color())
		# font = QApplication.font()
		# painter.drawText(5, -QFontMetrics(font).descent(), self.name)

	def hoverEnterEvent(self, event):
		self.update()
		self.label.show()

	def hoverLeaveEvent(self, event):
		self.update()
		self.label.hide()

	def itemChange(self, change, value):
		if self.persistent_index and change == QGraphicsItem.GraphicsItemChange.ItemScenePositionHasChanged:
			for edge_item in self.edges:
				edge_item.updatePosition()
		return super().itemChange(change, value)

	def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
		graphview = self.parent_node.parent_graph
		graphview.initiateConnection(pin=self)

	def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
		graphview = self.parent_node.parent_graph
		graphview.moveConnection(graphview.mapFromScene(event.scenePos()))
		# return super().mouseMoveEvent(event)

	def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
		graphview = self.parent_node.parent_graph

		pin = graphview.pinAt(graphview.mapFromScene(event.scenePos()))
		graphview.finishConnection(pin)


class OutletItem(PinItem):
	def destroy(self):
		for edge in self.edges:
			edge.destroy()
		self.edges = []

		self.parent_node.removeOutlet(self)
		self.scene().removeItem(self)
		self.parent_node.updatePinPositions()

class InletItem(PinItem):
	def destroy(self):
		for edge in self.edges:
			edge.destroy()
		self.edges = []

		self.parent_node.removeInlet(self)
		self.scene().removeItem(self)
		self.parent_node.updatePinPositions()

class TextItem(QGraphicsTextItem):
	def __init__(self, text):
		super().__init__(text)
		self.setTextInteractionFlags(Qt.NoTextInteraction)  # Disable interaction by default

		# Center-align the text within the item
		text_option = QTextOption()
		text_option.setAlignment(Qt.AlignCenter)
		self.document().setDefaultTextOption(text_option)

		# Remove the default margins
		self.document().setDocumentMargin(0)

	def sceneEvent(self, event:QEvent)->bool:
		print("event type:", event.type())
		print(QEvent.GraphicsSceneMouseDoubleClick)
		print()
		if event.type() == QEvent.GraphicsSceneMouseDoubleClick:
			self.setTextInteractionFlags(Qt.TextEditorInteraction)

			ret = super().sceneEvent(event)
			# QGraphicsTextItem::sceneevent needs to be processed before
			# the focus
			self.setFocus(Qt.MouseFocusReason)
			return ret

		return super().sceneEvent(event)

	def focusOutEvent(self, event):
		# Disable text editing when focus is lost
		self.setTextInteractionFlags(Qt.NoTextInteraction)
		# Call the base implementation to handle the focus-out event
		super().focusOutEvent(event)

	
class NodeItem(QGraphicsItem):
	"""Graphics item representing a node."""
	def __init__(self, parent_graph:"GraphView"):
		super().__init__(parent=None)
		self.parent_graph = parent_graph
		self.name = "<node>"
		self.script = "<script>"
		self.rect = QRectF(-5, -5, 100, 27)  # Set size of the node box
		self.persistent_node_index:Optional[QPersistentModelIndex] = None
		# Store pins (inlets and outlets)
		self.inlets = []
		self.outlets = []

		# Enable dragging and selecting
		self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
		self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
		self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
		self.setAcceptHoverEvents(True)
		self.setZValue(2)

		self.nameedit = TextItem(self)
		self.nameedit.setPos(0,0)
		self.nameedit.setTextWidth(self.rect.width()-10)


	def destroy(self):
		for inlet in self.inlets:
			inlet.destroy()
		for outlet in self.outlets:
			outlet.destroy()
		self.scene().removeItem(self)

	def addOutlet(self):
		outlet = OutletItem(parent_node=self)
		self.outlets.append(outlet)
		self.updatePinPositions()
		return outlet

	def removeOutlet(self, outlet:OutletItem):
		self.outlets.remove(outlet)
		self.updatePinPositions()

	def addInlet(self):
		inlet = InletItem(parent_node=self)
		self.inlets.append(inlet)
		self.updatePinPositions()
		return inlet

	def removeInlet(self, inlet:InletItem):
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
		if (self.parent_graph.graph_model and
			self.persistent_node_index and
			self.persistent_node_index.isValid()
		):
			match change:
				case QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
					graph:GraphModel = self.parent_graph.graph_model
					node_index = NodeIndex(self.persistent_node_index.model().index(self.persistent_node_index.row(), 0))
					
					new_pos = self.pos()
					posx = int(new_pos.x())
					posy = int(new_pos.y())

					graph.setNode(node_index, {"posx": posx, "posy":posy})

				# case QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
				# 	if nodes_selectionmodel:=self.parent_graph.nodes_selectionmodel:
				# 		graph = self.parent_graph.graph_model
				# 		node_index = graph.nodes.index(self.persistent_node_index.row(), 0)
				# 		if value == 1:
				# 			nodes_selectionmodel.select(node_index, QItemSelectionModel.SelectionFlag.SelectCurrent)
				# 			nodes_selectionmodel.setCurrentIndex(node_index, QItemSelectionModel.SelectionFlag.Current)
				# 		elif value == 0:
				# 			nodes_selectionmodel.select(node_index, QItemSelectionModel.SelectionFlag.Deselect)
				# 	else:
				# 		pass

		return super().itemChange(change, value)


class EdgeItem(QGraphicsLineItem):
	"""Graphics item representing an edge (connection)."""
	GrabThreshold = 15
	def __init__(self, source_pin_item:OutletItem|None, target_pin_item:InletItem|None, parent_graph:"GraphView"):
		super().__init__(parent=None)
		assert source_pin_item is None or isinstance(source_pin_item, OutletItem)
		assert target_pin_item is None or isinstance(target_pin_item, InletItem)
		self._source_pin_item = source_pin_item
		self._target_pin_item = target_pin_item
		self.parent_graph = parent_graph

		if source_pin_item:
			source_pin_item.edges.append(self)
		if target_pin_item:
			target_pin_item.edges.append(self)
		self.persistent_edge_index:Optional[QPersistentModelIndex] = None

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

	def sourcePin(self)->OutletItem|None:
		return self._source_pin_item

	def setSourcePin(self, pin: OutletItem|None):
		assert pin is None or isinstance(pin, OutletItem)

		# add or remove edge to pin edges for position update
		if pin:
			pin.edges.append(self)
		elif self._source_pin_item:
			self._source_pin_item.edges.remove(self)

		self._source_pin_item = pin
		self.updatePosition()

	def targetPin(self):
		return self._target_pin_item

	def setTargetPin(self, pin: InletItem|None):
		assert pin is None or isinstance(pin, InletItem)

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
					edge_index = graph.edges.index(self.persistent_edge_index.row(), 0)
					if value == 1:
						edges_selectionmodel.select(edge_index, QItemSelectionModel.SelectionFlag.Select)
					elif value == 0:
						edges_selectionmodel.select(edge_index, QItemSelectionModel.SelectionFlag.Deselect)
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


class GraphView(PanAndZoomGraphicsView):
	"""A view that displays the node editor."""
	def __init__(self, parent=None):
		super().__init__(parent)

		# Create a scene to hold the node and edge graphics
		scene = QGraphicsScene(self)
		scene.setSceneRect(QRect(-9999//2,-9999//2, 9999, 9999))
		self.setScene(scene)
		self.index_to_item_map = dict()

		self.graph_model = None
		self.nodes_selectionmodel = None
		self.edges_selectionmodel = None

		self.setCacheMode(QGraphicsView.CacheModeFlag.CacheNone)
		self.setInteractive(True)
		self.setRenderHint(QPainter.RenderHint.TextAntialiasing, False)
		self.setRenderHint(QPainter.RenderHint.Antialiasing, False)
		self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)

		# polkaBrush = QBrush()
		# polkaBrush.setColor(QApplication.palette().mid().color())
		# polkaBrush.setStyle(Qt.BrushStyle.Dense7Pattern)
		# self.setBackgroundBrush(polkaBrush)

	def setScene(self, scene:QGraphicsScene|None):
		if self.scene():
			self.scene().selectionChanged.disconnect(self.onSceneSelectionChanged)
		if scene:
			scene.selectionChanged.connect(self.onSceneSelectionChanged)
		super().setScene(scene)

	def onSceneSelectionChanged(self):
		if self.graph_model:
			node_selection = []
			edge_selection = []
			for item in self.scene().selectedItems():
				if isinstance(item, NodeItem):
					if item.persistent_node_index:
						node = self.graph_model.nodes.index(item.persistent_node_index.row(), item.persistent_node_index.column())
						if node:
							node_selection.append(node)
				if isinstance(item, EdgeItem):
					if item.persistent_edge_index:
						edge = self.graph_model.nodes.index(item.persistent_edge_index.row(), item.persistent_edge_index.column())
						if edge:
							edge_selection.append(edge)


			if self.nodes_selectionmodel:
				item_selection = QItemSelection()
				for node in node_selection:
					item_selection.merge(QItemSelection(node, node), QItemSelectionModel.SelectionFlag.Select)
				self.nodes_selectionmodel.select(item_selection, QItemSelectionModel.SelectionFlag.ClearAndSelect)

				if node_selection:
					self.nodes_selectionmodel.setCurrentIndex(node_selection[-1], QItemSelectionModel.SelectionFlag.Current)
				else:
					self.nodes_selectionmodel.setCurrentIndex(QModelIndex(), QItemSelectionModel.SelectionFlag.Clear)

			if self.edges_selectionmodel:
				item_selection = QItemSelection()
				for edge in edge_selection:
					item_selection.merge(QItemSelection(edge, edge), QItemSelectionModel.SelectionFlag.Select)
				self.edges_selectionmodel.select(item_selection, QItemSelectionModel.SelectionFlag.ClearAndSelect)

				if edge_selection:
					self.edges_selectionmodel.setCurrentIndex(edge_selection[-1], QItemSelectionModel.SelectionFlag.Current)
				else:
					self.edges_selectionmodel.setCurrentIndex(QModelIndex(), QItemSelectionModel.SelectionFlag.Clear)


	def pinAt(self, pos:QPoint):
		"""Returns the topmost pin at position pos, which is in viewport coordinates."""
		for item in self.items(pos):
			if isinstance(item, PinItem):
				return item
		return None

	def initiateConnection(self, pin):
		if isinstance(pin, OutletItem):
			self.interactive_edge = EdgeItem(source_pin_item=pin, target_pin_item=None, parent_graph=self)
			self.interactive_edge_start_pin = pin
		elif isinstance(pin, InletItem):
			self.interactive_edge = EdgeItem(source_pin_item=None, target_pin_item=pin, parent_graph=self)
			self.interactive_edge_start_pin = pin
		self.interactive_edge.updatePosition()
		self.scene().addItem(self.interactive_edge)

	def modifyConnection(self, edge:EdgeItem, endpoint:PinType):
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
		if isinstance(self.interactive_edge_start_pin, OutletItem):
			line.setP2(self.mapToScene(pos))
		elif isinstance(self.interactive_edge_start_pin, InletItem):
			line.setP1(self.mapToScene(pos))
		self.interactive_edge.setLine(line)

		# attach free endpoint to closeby pin
		pinUnderMouse = self.pinAt(pos)
		if isinstance(self.interactive_edge_start_pin, OutletItem) and isinstance(pinUnderMouse, InletItem):
			self.interactive_edge.setTargetPin(pinUnderMouse)
			self.interactive_edge.updatePosition()
		elif isinstance(self.interactive_edge_start_pin, InletItem) and isinstance(pinUnderMouse, OutletItem):
			self.interactive_edge.setSourcePin(pinUnderMouse)
			self.interactive_edge.updatePosition()

	def finishConnection(self, pin:PinItem|None):
		assert self.interactive_edge_start_pin
		start_pin:InletItem|OutletItem = self.interactive_edge_start_pin
		end_pin = pin
		persistent_edge_index = self.interactive_edge.persistent_edge_index

		CanConnectPins = (
			isinstance(start_pin, InletItem) 
			and isinstance(end_pin, OutletItem)
		) or (
			isinstance(start_pin, OutletItem) 
			and isinstance(end_pin, InletItem)
		)

		IsEdgeExists = (
			self.graph_model
			and persistent_edge_index
			and persistent_edge_index.isValid()
		)

		if CanConnectPins and end_pin:
			if IsEdgeExists and self.graph_model and persistent_edge_index:
				"""modify edge"""
				edge_index = EdgeIndex(self.graph_model.edges.index(persistent_edge_index.row(), 0))
				if isinstance(end_pin, OutletItem) and end_pin.persistent_index:
					outlet = self.graph_model.outlets.index(end_pin.persistent_index.row(), 0)
					self.graph_model.setEdge(edge_index, {"source": outlet})
				elif isinstance(end_pin, InletItem) and end_pin.persistent_index:
					inlet = self.graph_model.inlets.index(end_pin.persistent_index.row(), 0)
					self.graph_model.setEdge(edge_index, {"target": inlet})
			else:
				"""create edge"""
				inlet_item = end_pin
				outlet_item = start_pin
				if isinstance(end_pin, OutletItem) and isinstance(start_pin, InletItem):
					outlet_item, inlet_item = inlet_item, outlet_item

				if (
					self.graph_model 
					and outlet_item.persistent_index 
					and inlet_item.persistent_index
				):
					self.interactive_edge.destroy()
					self.graph_model.addEdge(outlet=outlet_item.persistent_index, inlet=inlet_item.persistent_index)
				else:
					raise NotImplementedError()
		else:
			if IsEdgeExists:
				"""Delete Edge"""
				if self.graph_model and persistent_edge_index:
					edge_index = EdgeIndex(self.graph_model.edges.index(persistent_edge_index.row(), 0))
					self.graph_model.removeEdges([edge_index])
					return
			else:
				"""remove interactive edge"""
				self.interactive_edge.destroy()

	def setModel(self, graph_model:GraphModel):
		self.graph_model = graph_model
		self.handleNodesInserted(  NodeIndex(), 0, self.graph_model.nodes.rowCount()-1)
		self.handleInletsInserted( InletIndex(), 0, self.graph_model.inlets.rowCount()-1)
		self.handleOutletsInserted(OutletIndex(), 0, self.graph_model.outlets.rowCount()-1)
		self.handleEdgesInserted(  EdgeIndex(), 0, self.graph_model.edges.rowCount()-1)

		self.graph_model.nodes.rowsInserted.connect(self.handleNodesInserted)
		self.graph_model.nodes.dataChanged.connect(self.handleNodesDataChanged)
		self.graph_model.nodes.rowsAboutToBeRemoved.connect(self.handleNodesRemoved)

		self.graph_model.inlets.rowsInserted.connect(self.handleInletsInserted)
		self.graph_model.inlets.dataChanged.connect(self.handleInletsDataChanged)
		self.graph_model.inlets.rowsAboutToBeRemoved.connect(self.handleInletsRemoved)

		self.graph_model.outlets.rowsInserted.connect(self.handleOutletsInserted)
		self.graph_model.outlets.dataChanged.connect(self.handleOutletsDataChanged)
		self.graph_model.outlets.rowsAboutToBeRemoved.connect(self.handleOutletsRemoved)

		self.graph_model.edges.rowsInserted.connect(self.handleEdgesInserted)
		self.graph_model.edges.dataChanged.connect(self.handleEdgesDataChanged)
		self.graph_model.edges.rowsAboutToBeRemoved.connect(self.handleEdgesRemoved)

	def setNodesSelectionModel(self, nodes_selectionmodel:QItemSelectionModel):
		self.nodes_selectionmodel = nodes_selectionmodel
		self.nodes_selectionmodel.selectionChanged.connect(self.handleNodesSelectionChanged)

	def setEdgesSelectionModel(self, edges_selectionmodel:QItemSelectionModel):
		self.edges_selectionmodel = edges_selectionmodel
		self.edges_selectionmodel.selectionChanged.connect(self.handleEdgesSelectionChanged)

		self.zoom_factor=1.2

	@Slot(QItemSelection, QItemSelection)
	def handleNodesSelectionChanged(self, selected:QItemSelection, deselected:QItemSelection):

		self.scene().blockSignals(True)
		for node in [index for index in selected.indexes() if index.column()==0]:
			persistent_node_index = QPersistentModelIndex(node)
			node_item = self.index_to_item_map[persistent_node_index]
			node_item.setSelected(True)

		for node in [index for index in deselected.indexes() if index.column()==0]:
			persistent_node_index = QPersistentModelIndex(node)
			node_item = self.index_to_item_map[persistent_node_index]
			node_item.setSelected(False)
		self.scene().blockSignals(False)

	def handleEdgesSelectionChanged(self, selected:QItemSelection, deselected:QItemSelection):
		self.scene().blockSignals(True)
		for index in [index for index in selected.indexes() if index.column()==0]:
			persistent_index = QPersistentModelIndex(index)
			item = self.index_to_item_map[persistent_index]
			item.setSelected(True)

		for index in [index for index in deselected.indexes() if index.column()==0]:
			persistent_index = QPersistentModelIndex(index)
			item = self.index_to_item_map[persistent_index]
			item.setSelected(False)
		self.scene().blockSignals(False)

	@Slot(QModelIndex, int, int)
	def handleNodesInserted(self, parent:NodeIndex, first:int, last:int):
		if parent.isValid():
			raise NotImplementedError("Subgraphs are not implemented yet!")

		if self.graph_model:
			for row in range(first, last+1):
				# get node and create the gaphics item
				node = NodeIndex(self.graph_model.nodes.index(row, 0))
				node_item = NodeItem(parent_graph=self)
				# self.nodes.append(node_item)
				self.scene().addItem(node_item)

				# map node to graphics item
				persistent_node_index = QPersistentModelIndex(node)
				node_item.persistent_node_index = persistent_node_index
				self.index_to_item_map[persistent_node_index] = node_item

				# update gaphics item
				self.handleNodesDataChanged(node, NodeIndex(node.siblingAtColumn(4)))

	@Slot(QModelIndex, int, int)
	def handleNodesRemoved(self, parent:NodeIndex, first:int, last:int):
		if parent.isValid():
			raise NotImplementedError("Subgraphs are not implemented yet!")

		if self.graph_model:
			for row in range(last, first-1, -1):
				node = self.graph_model.nodes.index(row, 0)
				node_item = self.index_to_item_map[QPersistentModelIndex(node)]
				node_item.destroy()
				del self.index_to_item_map[QPersistentModelIndex(node)]
				# self.nodes.remove(node)
	
	def handleNodesDataChanged(self, topLeft:NodeIndex, bottomRight:NodeIndex, roles=[]):
		if self.graph_model:
			for row in range(topLeft.row(), bottomRight.row()+1):
				graph:GraphModel = self.graph_model
				node_index = NodeIndex(graph.nodes.index(row, 0))
				persistent_node_index = QPersistentModelIndex(node_index)
				node_item:NodeItem = self.index_to_item_map[persistent_node_index]
				new_pos = node_item.pos()
				for col in range(topLeft.column(), bottomRight.column()+1):
					match col:
						case 0:
							pass
						case 1:
							new_name = str(node_index.siblingAtColumn(1).data())
							node_item.name = new_name
							node_item.nameedit.setPlainText(new_name)
							node_item.update()
						case 2:
							"""posx changed"""
							data = node_index.siblingAtColumn(2).data()
							new_pos.setX(int(data))
						case 3:
							"""posy changed"""
							data = node_index.siblingAtColumn(3).data()
							new_pos.setY(int(data))
						case 4:
							"set script"
				if new_pos!=node_item.pos():
					node_item.setPos(new_pos)

	@Slot(QModelIndex, int, int)
	def handleEdgesInserted(self, parent:QModelIndex, first:int, last:int):
		if parent.isValid():
			raise NotImplementedError("Subgraphs are not implemented yet!")

		if self.graph_model:
			for row in range(first, last+1):
				# get edge and create the gaphics item
				graph:GraphModel = self.graph_model
				edge = EdgeIndex(graph.edges.index(row, 0))

				# target_inlet = graph.getEdge(edge)["target"]
				# target_inlet_item = self.index_to_item_map[QPersistentModelIndex(target_inlet)]
				# source_outlet = graph.getEdge(edge)["source"]
				# source_outlet_item = self.index_to_item_map[QPersistentModelIndex(source_outlet)]

				persistent_edge_index = QPersistentModelIndex(edge)
				try:
					edge_item = self.index_to_item_map[persistent_edge_index]
				except KeyError:
					edge_item = EdgeItem(source_pin_item=None, target_pin_item=None, parent_graph=self)
					self.scene().addItem(edge_item)
					edge_item.persistent_edge_index = persistent_edge_index
					self.index_to_item_map[persistent_edge_index] = edge_item

				# update gaphics item
				self.handleEdgesDataChanged(edge, EdgeIndex(edge.siblingAtColumn(2)))

	@Slot(QModelIndex, int, int)
	def handleEdgesRemoved(self, parent:EdgeIndex, first:int, last:int):
		if parent.isValid():
			raise NotImplementedError("Subgraphs are not implemented yet!")

		print("handle edges removed")
		if self.graph_model:
			for row in range(last, first-1, -1):
				edge = EdgeIndex(self.graph_model.edges.index(row, 0))
				persistent_index = QPersistentModelIndex(edge)
				edge_item = self.index_to_item_map[persistent_index]
				edge_item.destroy()
				del self.index_to_item_map[persistent_index]
	
	def handleEdgesDataChanged(self, topLeft:EdgeIndex, bottomRight:EdgeIndex, roles=[]):
		if self.graph_model:
			for row in range(topLeft.row(), bottomRight.row()+1):
				graph:GraphModel = self.graph_model
				edge = graph.edges.index(row, 0)
				persistent_index = QPersistentModelIndex(edge)
				graphics_item = self.index_to_item_map[persistent_index]
				for col in range(topLeft.column(), bottomRight.column()+1):
					match col:
						case 0:
							"""unique id changed"""
							pass
						case 1:
							"""source outlet changed"""
							edge_item:EdgeItem = graphics_item
							edge_index = EdgeIndex(graph.edges.index(persistent_index.row(), 0))
							outlet = graph.getEdge(edge_index, relations=True)["source"]
							if outlet is not None:
								source_pin_item = self.index_to_item_map[QPersistentModelIndex(outlet)]
								edge_item.setSourcePin( source_pin_item )
						case 2:
							"""target inlet changed"""
							edge_item:EdgeItem = graphics_item
							edge_index = EdgeIndex(graph.edges.index(persistent_index.row(), 0))
							inlet = graph.getEdge(edge_index, relations=True)["target"]
							target_pin_item = self.index_to_item_map[QPersistentModelIndex(inlet)]
							edge_item.setTargetPin( target_pin_item )

	@Slot(QModelIndex, int, int)
	def handleOutletsInserted(self, parent:OutletIndex, first:int, last:int):
		if parent.isValid():
			raise ValueError("inlets are flat table, not a tree model")

		if self.graph_model:
			for row in range(first, last+1):
				# get model
				outlet = OutletIndex(self.graph_model.outlets.index(row, 0)) # get the inlet reference
				parent_node = self.graph_model.getOutlet(outlet)["node"] # get the node reference

				# create outlet grtaphics item
				parent_node_item = self.index_to_item_map[QPersistentModelIndex(parent_node)] # get the node graphics item
				outlet_item = parent_node_item.addOutlet()

				# map inlet to graphics item
				persistent_index = QPersistentModelIndex(outlet)
				outlet_item.persistent_index = persistent_index
				self.index_to_item_map[persistent_index] = outlet_item

				# update graphics item
				self.handleOutletsDataChanged(outlet, OutletIndex(outlet.siblingAtColumn(2)))

	@Slot(QModelIndex, int, int)
	def handleOutletsRemoved(self, parent:OutletIndex, first:int, last:int):
		if parent.isValid():
			raise NotImplementedError("Subgraphs are not implemented yet!")

		if self.graph_model:
			for row in range(last, first-1, -1):
				#get model
				outlet = OutletIndex(self.graph_model.outlets.index(row, 0)) # get the inlet reference
				parent_node = self.graph_model.getOutlet(outlet)["node"] # get the node reference

				# remove outlet graphics item
				persistent_index = QPersistentModelIndex(outlet)
				outlet_item = self.index_to_item_map[persistent_index]
				outlet_item.destroy()

				# remove mapping
				del self.index_to_item_map[persistent_index]
	
	def handleOutletsDataChanged(self, topLeft:OutletIndex, bottomRight:OutletIndex, roles=[]):
		if self.graph_model:
			for row in range(topLeft.row(), bottomRight.row()+1):
				graph:GraphModel = self.graph_model
				outlet = OutletIndex(graph.outlets.index(row, 0))
				persistent_index = QPersistentModelIndex(outlet)
				graphics_item = self.index_to_item_map[persistent_index]
				for col in range(topLeft.column(), bottomRight.column()+1):
					match col:
						case 0:
							"""unique id changed"""
							# raise NotImplementedError("Setting the inlet's unique id is not supported!")
							pass
						case 1:
							"""parent node changed"""
							# raise NotImplementedError("Setting the inlet's parent node is not supported!")
							pass
						case 2:
							"""name changed"""
							graphics_item.label.setText(str(outlet.siblingAtColumn(2).data()))

	@Slot(QModelIndex, int, int)
	def handleInletsInserted(self, parent:QModelIndex, first:int, last:int):
		if parent.isValid():
			raise ValueError("inlets are flat table, not a tree model")

		if self.graph_model:
			for row in range(first, last+1):
				# get inlet and create the gaphics item
				graph:GraphModel = self.graph_model
				inlet = InletIndex(graph.inlets.index(row, 0)) # get the inlet reference
				inlet_node = graph.getInlet(inlet)["node"] # get the node reference
				parent_node_item = self.index_to_item_map[QPersistentModelIndex(inlet_node)] # get the node graphics item
				inlet_item = parent_node_item.addInlet()

				# map inlet to graphics item
				persistent_index = QPersistentModelIndex(inlet)
				inlet_item.persistent_index = persistent_index
				self.index_to_item_map[persistent_index] = inlet_item

				# update graphics item and add to scene
				self.handleInletsDataChanged(inlet, inlet.siblingAtColumn(2))

	@Slot(QModelIndex, int, int)
	def handleInletsRemoved(self, parent:QModelIndex, first:int, last:int):
		if parent.isValid():
			raise NotImplementedError("Subgraphs are not implemented yet!")

		if self.graph_model:
			for row in range(last, first-1, -1):
				inlet = self.graph_model.inlets.index(row, 0)
				persistent_index = QPersistentModelIndex(inlet)
				inlet_item = self.index_to_item_map[persistent_index]
				inlet_item.destroy()
				del self.index_to_item_map[persistent_index]

	def handleInletsDataChanged(self, topLeft:QModelIndex, bottomRight:QModelIndex, roles=[]):
		if self.graph_model:
			for row in range(topLeft.row(), bottomRight.row()+1):
				graph:GraphModel = self.graph_model
				inlet = graph.inlets.index(row, 0)
				persistent_index = QPersistentModelIndex(inlet)
				graphics_item:PinItem = self.index_to_item_map[persistent_index]
				for col in range(topLeft.column(), bottomRight.column()+1):
					match col:
						case 0:
							"""unique id changed"""
							pass
						case 1:
							pass
						case 2:
							"""name changed"""
							graphics_item.label.setText( str(inlet.siblingAtColumn(2).data()) )

	
	
	def drawBackground(self, painter: QPainter, rect:QRectF | QRect):
		super().drawBackground(painter, rect);

		def drawGrid(gridStep:int):
			windowRect:QRect = self.rect()
			tl:QPointF = self.mapToScene(windowRect.topLeft())
			br:QPointF = self.mapToScene(windowRect.bottomRight())

			left = math.floor(tl.x() / gridStep - 0.5)
			right = math.floor(br.x() / gridStep + 1.0)
			bottom = math.floor(tl.y() / gridStep - 0.5)
			top = math.floor(br.y() / gridStep + 1.0)

			# vertical lines
			for xi in range(left, right):
				line = QLineF(xi * gridStep, bottom * gridStep, xi * gridStep, top * gridStep);
				painter.drawLine(line)

			# horizontal lines
			for yi in range(bottom, top):
				line = QLineF(left * gridStep, yi * gridStep, right * gridStep, yi * gridStep);
				painter.drawLine(line)

		def drawDots(gridStep:int, radius=2):
			windowRect:QRect = self.rect()
			tl:QPointF = self.mapToScene(windowRect.topLeft())
			br:QPointF = self.mapToScene(windowRect.bottomRight())

			left = math.floor(tl.x() / gridStep - 0.5)
			right = math.floor(br.x() / gridStep + 1.0)
			bottom = math.floor(tl.y() / gridStep - 0.5)
			top = math.floor(br.y() / gridStep + 1.0)

			for xi in range(left, right):
				for yi in range(bottom, top):
					painter.drawEllipse(QPoint(xi*gridStep, yi*gridStep), radius,radius)

		fineGridColor = self.palette().text().color()
		fineGridColor.setAlpha(5)
		pFine = QPen(fineGridColor, 1.0)

		coarseGridColor = self.palette().text().color()
		coarseGridColor.setAlpha(10)
		pCoarse = QPen(coarseGridColor, 1.0)

		# painter.setPen(pFine)
		# drawGrid(10)
		# painter.setPen(pCoarse)
		# drawGrid(100)
		painter.setPen(Qt.PenStyle.NoPen)
		painter.setBrush(coarseGridColor)
		drawDots(20, radius=1)

if __name__ == "__main__":
	from GraphTableView import GraphTableView
	from GraphDetailsView import GraphDetailsView
	class MainWindow(QWidget):
		def __init__(self):
			super().__init__()

			self.setWindowTitle("Graph Viewer Example")
			self.resize(900, 500)

			# Initialize the GraphModel
			self.graph_model = GraphModel()
			self.nodes_selectionmodel = QItemSelectionModel(self.graph_model.nodes)
			self.edges_selectionmodel = QItemSelectionModel(self.graph_model.edges)

			# Add some example nodes and edges
			read_node = self.graph_model.addNode("Read", 10, -100, "Script 1")
			outlet_id = self.graph_model.addOutlet(read_node, "image")
			write_node = self.graph_model.addNode("Write", 20, 100, "Script 2")
			inlet_id = self.graph_model.addInlet(write_node, "image")

			node3_id = self.graph_model.addNode("Preview", -50, 10, "Script 2")
			self.graph_model.addInlet(node3_id, "in")
			self.graph_model.addOutlet(node3_id, "out")
			
			
			self.graph_model.addEdge(outlet_id, inlet_id)

			# Set up the node editor views
			self.graph_table_view = GraphTableView()
			self.graph_table_view.setModel(self.graph_model)
			self.graph_table_view.setNodesSelectionModel(self.nodes_selectionmodel)
			self.graph_table_view.setEdgesSelectionModel(self.edges_selectionmodel)

			self.graph_view = GraphView()
			self.graph_view.setModel(self.graph_model)
			self.graph_view.setNodesSelectionModel(self.nodes_selectionmodel)
			self.graph_view.setEdgesSelectionModel(self.edges_selectionmodel)

			self.graph_details_view = GraphDetailsView()
			self.graph_details_view.setModel(self.graph_model)
			self.graph_details_view.setNodesSelectionModel(self.nodes_selectionmodel)

			
			layout = QHBoxLayout()
			layout.addWidget(self.graph_table_view, 1)
			layout.addWidget(self.graph_view, 1)
			layout.addWidget(self.graph_details_view, 1)
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
