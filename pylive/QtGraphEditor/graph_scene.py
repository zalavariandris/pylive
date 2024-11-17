from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from pylive import livescript
from typing import *

from pylive.QtGraphEditor.PanAndZoomGraphicsView import PanAndZoomGraphicsView



class TextWidget(QGraphicsWidget):
	"""A simple widget that contains a QGraphicsTextItem."""
	def __init__(self, text, parent=None):
		super().__init__(parent)
		# Create the text item
		self.text_item = QGraphicsTextItem(text, self)
		self.text_item.document().setDocumentMargin(0)
		self.text_item.setTextInteractionFlags(Qt.TextEditorInteraction)
		self.text_item.setAcceptedMouseButtons(Qt.NoButton)  # Transparent to mouse events
		self.text_item.setEnabled(False)

		self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges)
		self.set_line_height(1.1)

	def set_line_height(self, line_height):
		"""Set the line height for the text."""
		cursor = QTextCursor(self.text_item.document())
		cursor.select(QTextCursor.Document)

		# Configure block format
		block_format = QTextBlockFormat()
		block_format.setLineHeight(100, 1)
		cursor.mergeBlockFormat(block_format)

	def sizeHint(self, which, constraint=QSizeF()):
		text_size = QSize(self.text_item.document().size().toSize())
		return text_size


class CircleWidget(QGraphicsWidget):
	def __init__(self, radius:float, parent=None):
		super().__init__()
		self.circle_item = QGraphicsEllipseItem(QRectF(0,0,radius*2, radius*2), self)
		text_color = self.palette().color(QPalette.Text)
		self.circle_item.setBrush(Qt.NoBrush)
		self.circle_item.setPen(QPen(text_color, 1.4))

	def sizeHint(self, which, constraint=QSizeF()):
		circle_rect = self.circle_item.rect()
		return circle_rect.size()


class PinWidget(QGraphicsWidget):
	def __init__(self, text):
		super().__init__()
		self._parent_node = None

		# Create the text item
		self.circle_item = CircleWidget(radius=3)
		self.text_widget = TextWidget(text)
		font = self.text_widget.text_item.document().defaultFont()
		font.setPointSize(6)
		self.text_widget.text_item.document().setDefaultFont(font)

		self.main_layout = QGraphicsLinearLayout(Qt.Horizontal)
		self.main_layout.setContentsMargins(0,0,0,0)
		self.main_layout.setSpacing(3)
		
		self.setLayout(self.main_layout)

		self._edges = []
		self.geometryChanged.connect(self.updateEdges)
		self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges)
		self.setAcceptHoverEvents(True)

	def setHighlight(self, value):
		if value:
			accent_color = self.palette().color(QPalette.ColorRole.Accent)
			self.circle_item.circle_item.setPen(QPen(accent_color, 2))
		else:
			text_color = self.palette().color(QPalette.ColorRole.Text)
			self.circle_item.circle_item.setPen(QPen(text_color, 2))

	

	def updateEdges(self):
		for edge_item in list(self._edges):
			edge_item.updatePosition()

	def itemChange(self, change, value):
		match change:
			case QGraphicsItem.GraphicsItemChange.ItemScenePositionHasChanged:
				self.updateEdges()

		return super().itemChange(change, value)

	def shape(self):
		shape = QPainterPath()
		circle_rect = self.circle_item.rect()
		circle_rect.adjust(-5,-5,5,5)
		circle_rect.translate(self.circle_item.pos())
		shape.addRect( circle_rect )
		return shape

	def boundingRect(self) -> QRectF:
		return self.shape().boundingRect()

	def orientation(self):
		return self._orientation

	def setOrientation(self, orientation:Qt.Orientation):
		print("set orientation", orientation)
		match orientation:
			case Qt.Orientation.Vertical:
				self.main_layout.setOrientation(orientation)
				self.main_layout.removeItem(self.text_widget)
				self.text_widget.hide()
				if isinstance(self, OutletWidget):
					self.text_widget.moveBy(3,+10)
				else:
					self.text_widget.moveBy(3,-13)
				
				self._orientation = orientation

			case Qt.Orientation.Horizontal:
				self.main_layout.setOrientation(orientation)
				if isinstance(self, OutletWidget):
					self.main_layout.insertItem(0, self.text_widget)
				else:
					self.main_layout.addItem(self.text_widget)
				self.text_widget.show()
				self._orientation = orientation
			case _:
				...

		self.updateGeometry()
		self.adjustSize()

	def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent) -> None:
		self.setHighlight(True)
		if self.orientation() == Qt.Orientation.Vertical:
			self.text_widget.show()
		return super().hoverEnterEvent(event)

	def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent) -> None:
		self.setHighlight(False)
		if self.orientation() == Qt.Orientation.Vertical:
			self.text_widget.hide()
		return super().hoverLeaveEvent(event)



	# def paint(self, painter, option, widget):
	# 	painter.setPen('green')
	# 	painter.drawRect(self.boundingRect())
	# 	painter.setPen('cyan')
	# 	painter.drawPath(self.shape())


class OutletWidget(PinWidget):
	def __init__(self, text):
		super().__init__(text)
		self.main_layout.addItem(self.text_widget)
		self.main_layout.addItem(self.circle_item)
		self.main_layout.setAlignment(self.circle_item, Qt.AlignmentFlag.AlignCenter)

	def destroy(self):
		for edge in reversed(self._edges):
			edge.destroy()
		self._edges = []

		if self._parent_node:
			self._parent_node.removeOutlet(self)
			self._parent_node.updatePinPositions()
		self.scene().removeItem(self)


class InletWidget(PinWidget):
	def __init__(self, text):
		super().__init__(text)
		self.main_layout.addItem(self.circle_item)
		self.main_layout.addItem(self.text_widget)
		self.main_layout.setAlignment(self.circle_item, Qt.AlignmentFlag.AlignCenter)

	def destroy(self):
		for edge in reversed(self._edges):
			edge.destroy()
		self._edges = []

		if self._parent_node:
			self._parent_node.removeInlet(self)
			self._parent_node.updatePinPositions()
		self._parent_node = None
		self.scene().removeItem(self)


class NodeWidget(QGraphicsWidget):
	"""A widget that holds multiple TextWidgets arranged in a vertical layout."""

	def __init__(self, title="Node", parent=None):
		super().__init__(parent)

		# Enable selection and movement
		self.setFlag(QGraphicsWidget.ItemIsSelectable, True)
		self.setFlag(QGraphicsWidget.ItemIsMovable, True)
		self.setFlag(QGraphicsWidget.ItemIsFocusable, True)

		self._orientation = Qt.Orientation.Horizontal

		# Create a layout
		self.main_layout = QGraphicsLinearLayout(Qt.Vertical)
		self.main_layout.setContentsMargins(8,3,8,3)
		self.main_layout.setSpacing(0)

		# create heading layout
		self.header = TextWidget(title)
		self.main_layout.addItem(self.header)

		# Create inlets layout
		self.inlets_layout = QGraphicsLinearLayout(Qt.Vertical)
		self.main_layout.addItem(self.inlets_layout)

		# create outlets layout
		self.outlets_layout = QGraphicsLinearLayout(Qt.Vertical)
		self.main_layout.addItem(self.outlets_layout)
		self.main_layout.setAlignment(self.outlets_layout, Qt.AlignmentFlag.AlignRight)

		# Set the layout for the widget
		self.setLayout(self.main_layout)

		# Define the bounding geometry
		# self.setGeometry(QRectF(-75, -59, 150, 100))
		self.inlets = []
		self.outlets = []

	def orientation(self):
		return self._orientation

	def setOrientation(self, orientation:Qt.Orientation):
		match orientation:
			case Qt.Orientation.Vertical:

				# Set orientation for inlets and outlets
				self.inlets_layout.setOrientation(orientation)
				self.outlets_layout.setOrientation(orientation)
				# self.inlets_layout.setMaximumHeight(1)
				# self.outlets_layout.setMaximumHeight(1)

				# Update orientation for child items

				for i in range(self.inlets_layout.count()):
					item = cast(InletWidget, self.inlets_layout.itemAt(i))
					item.setOrientation(orientation)

				for i in range(self.outlets_layout.count()):
					item = cast(OutletWidget, self.outlets_layout.itemAt(i))
					item.setOrientation(orientation)

				 # Clear and reorder main_layout: inlets, header, outlets
				while self.main_layout.count() > 0:
					self.main_layout.removeAt(0)

				self.main_layout.addItem(self.inlets_layout)
				self.main_layout.addItem(self.header)
				self.main_layout.addItem(self.outlets_layout)

				# Align items
				self.main_layout.setAlignment(self.inlets_layout, Qt.AlignmentFlag.AlignCenter)
				self.main_layout.setAlignment(self.outlets_layout, Qt.AlignmentFlag.AlignCenter)

				self._orientation = orientation
			
			case Qt.Orientation.Horizontal:
				# Update orientation for inlets and outlets
				self.inlets_layout.setOrientation(orientation)
				self.outlets_layout.setOrientation(orientation)

				
				

				for i in range(self.inlets_layout.count()):
					item = cast(InletWidget, self.inlets_layout.itemAt(i))
					item.setOrientation(orientation)

				for i in range(self.outlets_layout.count()):
					item = cast(OutletWidget, self.outlets_layout.itemAt(i))
					item.setOrientation(orientation)

				# Clear and reorder main_layout: header, inlets, outlets
				while self.main_layout.count() > 0:
					self.main_layout.removeAt(0)

				self.main_layout.addItem(self.header)
				self.main_layout.addItem(self.inlets_layout)
				self.main_layout.addItem(self.outlets_layout)

				# Align items
				self.main_layout.setAlignment(self.inlets_layout, Qt.AlignmentFlag.AlignLeft)
				self.main_layout.setAlignment(self.outlets_layout, Qt.AlignmentFlag.AlignRight)

				self._orientation = orientation
			case _:
				...

		self.adjustSize()

	def addInlet(self, inlet:InletWidget):
		self.inlets_layout.addItem(inlet)
		inlet.setParentItem(self)
		self.inlets.append(inlet)

	def addOutlet(self, outlet:OutletWidget):
		self.outlets_layout.addItem(outlet)
		self.outlets_layout.setAlignment(outlet, Qt.AlignRight)
		outlet._parent_node = self
		outlet.setParentItem(self)

	def paint(self, painter:QPainter, option:QStyleOptionGraphicsItem, widget=None):
		# Draw the node rectangle
		palette:QPalette = option.palette # type: ignore
		state:QStyle.StateFlag = option.state # type: ignore

		painter.setBrush(palette.window())
		# painter.setBrush(Qt.NoBrush)

		pen = QPen(palette.text().color(), 1)
		pen.setCosmetic(True)
		pen.setWidthF(1)
		if state & QStyle.StateFlag.State_Selected:
			pen.setColor(palette.accent().color())
		painter.setPen(pen)

		# painter.setPen(palette.window().color())
		painter.drawRoundedRect(QRectF(QPointF(), self.size()), 3, 3)


class EdgeWidget(QGraphicsLineItem):
	"""Graphics item representing an edge (connection)."""
	GrabThreshold = 15
	def __init__(self, source_outlet:OutletWidget|None, target_inlet:InletWidget|None):
		super().__init__(parent=None)
		assert source_outlet is None or isinstance(source_outlet, OutletWidget), f"got: {source_outlet}"
		assert target_inlet is None or isinstance(target_inlet, InletWidget), f"got: {target_inlet}"
		self._source_outlet = source_outlet
		self._target_inlet = target_inlet

		if source_outlet:
			source_outlet._edges.append(self)
		if target_inlet:
			target_inlet._edges.append(self)

		self.setPen(QPen(Qt.GlobalColor.black, 2))
		self.updatePosition()

		# Enable selecting
		self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
		self.setAcceptHoverEvents(True)

		self.setZValue(-1)

		#
		self.is_moving_endpoint = False\

		self.GrabThreshold = 10
		self._shape_pen = QPen(Qt.GlobalColor.black, self.GrabThreshold)

	def sourceOutlet(self)->OutletWidget|None:
		return self._source_outlet

	def setSourceOutlet(self, pin: OutletWidget|None):
		assert pin is None or isinstance(pin, OutletWidget), f"got: {pin}"

		# add or remove edge to pin edges for position update
		if pin:
			pin._edges.append(self)
		elif self._source_outlet:
			self._source_outlet._edges.remove(self)

		self._source_outlet = pin
		self.updatePosition()

	def targetInlet(self):
		return self._target_inlet

	def setTargetInlet(self, pin: InletWidget|None):
		assert pin is None or isinstance(pin, InletWidget), f"got: {pin}"

		# add or remove edge to pin edges for position update
		if pin:
			pin._edges.append(self)
		elif self._target_inlet:
			self._target_inlet._edges.remove(self)
		self._target_inlet = pin
		self.updatePosition()


	def shape(self) -> QPainterPath:
		"""Override shape to provide a wider clickable area."""
		
		self._shape_pen.setCosmetic(True)
		path = QPainterPath()
		path.moveTo(self.line().p1())
		path.lineTo(self.line().p2())
		stroker = QPainterPathStroker()
		stroker.setWidth(self.GrabThreshold)
		stroker.setCapStyle(Qt.PenCapStyle.RoundCap)
		stroker.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
		return stroker.createStroke(path)

	def boundingRect(self) -> QRectF:
		"""Override boundingRect to account for the wider collision shape."""
		self._shape_pen = QPen(Qt.GlobalColor.black, self.GrabThreshold)
		extra = (self._shape_pen.width() + self.pen().width()) / 2.0
		p1 = self.line().p1()
		p2 = self.line().p2()
		return QRectF(p1, QSizeF(p2.x() - p1.x(), p2.y() - p1.y())).normalized().adjusted(-extra, -extra, extra, extra)

	def updatePosition(self):
		# assert self._source_outlet and self._target_inlet
		# if not (
		# 	self.scene 
		# 	and self._source_outlet.scene() 
		# 	and self._target_inlet.scene()
		# ):
		# 	return # dont update position if not in scene or the pins are not part of the same scene

		# assert self.scene() == self._source_outlet.scene() == self._target_inlet.scene()


		line = self.line()
		sourcePin = self._source_outlet
		targetPin = self._target_inlet

		def getConnectionPoint(widget):
			# try:
			# 	return widget.getConnectionPoint()
			# except AttributeError:
			return widget.scenePos() + widget.boundingRect().center()

		if sourcePin and targetPin:
			line.setP1( getConnectionPoint(sourcePin) )
			line.setP2( getConnectionPoint(targetPin) )
			self.setLine(line)
		elif sourcePin:
			line.setP1( getConnectionPoint(sourcePin) )
			line.setP2( getConnectionPoint(sourcePin) )
			self.setLine(line)
		elif targetPin:
			line.setP1( getConnectionPoint(targetPin) )
			line.setP2( getConnectionPoint(targetPin) )
			self.setLine(line)
		else:
			return # nothing to update

	def destroy(self):
		# Safely remove from source pin
		if self._source_outlet:
			try:
				self._source_outlet._edges.remove(self)
			except ValueError:
				pass  # Already removed
			self._source_outlet = None

		# Safely remove from target pin
		if self._target_inlet:
			try:
				self._target_inlet._edges.remove(self)
			except ValueError:
				pass  # Already removed
			self._target_inlet = None

		# Safely remove from scene
		if self.scene():
			self.scene().removeItem(self)

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


class GraphScene(QGraphicsScene):
	def __init__(self, parent=None):
		super().__init__(parent)

		# Create a scene to hold the node and edge graphics
		self.setSceneRect(QRect(-9999//2,-9999//2, 9999, 9999))

		self.interactive_edge:EdgeWidget|None = None
		self.interactive_edge_fixed_pin:PinWidget|None = None
		self.interactive_edge_moving_pin:PinWidget|None = None # keep track of original connection
		self.is_dragging_edge = False # indicate that an edge is being moved

	def addNode(self, node: NodeWidget):
		self.addItem(node)

	def addEdge(self, edge: EdgeWidget):
		self.addItem(edge)

	def pinAt(self, pos:QPoint|QPointF)->PinWidget:
		for item in self.items(pos, deviceTransform=QTransform()):
			if isinstance(item, PinWidget):
				return item
		return None

	def nodeAt(self, pos:QPoint|QPointF)->NodeWidget:
		for item in self.items(pos, deviceTransform=QTransform()):
			if isinstance(item, NodeWidget):
				return item
		return None

	def edgeAt(self, pos:QPoint|QPointF)->EdgeWidget:
		for item in self.items(pos, deviceTransform=QTransform()):
			if isinstance(item, EdgeWidget):
				return item
		return None

	def mousePressEvent(self, event)->None:
		self.mousePressScenePos = event.scenePos()

		if pin:=self.pinAt(event.scenePos()):
			print(pin)
			self.initiateConnection(pin)
			event.accept()
			return

		if edge:=self.edgeAt(event.scenePos()):
			delta1 = edge.line().p1() - event.scenePos()
			d1 = delta1.manhattanLength()
			delta2 = edge.line().p2() - event.scenePos()
			d2 = delta2.manhattanLength()

			# print("closest end:", closest_pin)

			if d1<d2:
				self.interactive_edge_fixed_pin = edge._target_inlet
				self.interactive_edge_moving_pin = edge._source_outlet
			else:
				self.interactive_edge_fixed_pin = edge._source_outlet
				self.interactive_edge_moving_pin = edge._target_inlet

			self.interactive_edge = edge
			self.is_dragging_edge = False
			event.accept()
			return
		
		return super().mousePressEvent(event)

	def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
		GrabThreshold = 15
		
		if self.interactive_edge and not self.is_dragging_edge:
			mouseDelta = event.scenePos() - self.mousePressScenePos
			IsThresholdSurpassed = mouseDelta.manhattanLength()>GrabThreshold
			if IsThresholdSurpassed:
				self.is_dragging_edge = True

		if self.is_dragging_edge and self.interactive_edge:
			self.moveConnection(event.scenePos())
			return
		
		return super().mouseMoveEvent(event)

	def mouseReleaseEvent(self, event):
		"""
		Override mouseReleaseEvent to filter events when the mouse is released in the scene.
		"""
		if self.is_dragging_edge:
			pin = self.pinAt(event.scenePos())
			self.finishConnection(pin)

		self.is_dragging_edge = False
		self.interactive_edge_fixed_pin = None
		self.interactive_edge = None
		self.interactive_edge_moving_pin = None

		return super().mouseReleaseEvent(event)
		
	def initiateConnection(self, pin):
		if isinstance(pin, OutletWidget):
			self.interactive_edge = EdgeWidget(source_outlet=pin, target_inlet=None)
			self.interactive_edge_fixed_pin = pin
		elif isinstance(pin, InletWidget):
			self.interactive_edge = EdgeWidget(source_outlet=None, target_inlet=pin)
			self.interactive_edge_fixed_pin = pin
		assert self.interactive_edge
		self.interactive_edge.updatePosition()
		self.addItem(self.interactive_edge)
		self.is_dragging_edge = True

	def moveConnection(self, scenepos:QPointF):
		assert isinstance(scenepos, QPointF), f"got: {scenepos}"
		assert self.interactive_edge

		# move free endpoint
		line = self.interactive_edge.line()
		if isinstance(self.interactive_edge_fixed_pin, OutletWidget):
			line.setP2(scenepos)
		elif isinstance(self.interactive_edge_fixed_pin, InletWidget):
			line.setP1(scenepos)
		self.interactive_edge.setLine(line)

		# attach free endpoint to closeby pin
		pinUnderMouse = self.pinAt(scenepos)

		if current_inlet:=self.interactive_edge.targetInlet():
			current_inlet.setHighlight(False)
		if current_outlet:=self.interactive_edge.sourceOutlet():
			current_outlet.setHighlight(False)

		if isinstance(self.interactive_edge_fixed_pin, OutletWidget) and isinstance(pinUnderMouse, InletWidget):
			
			self.interactive_edge.setTargetInlet(pinUnderMouse)
			pinUnderMouse.setHighlight(True)
			self.interactive_edge.updatePosition()
		elif isinstance(self.interactive_edge_fixed_pin, InletWidget) and isinstance(pinUnderMouse, OutletWidget):
			self.interactive_edge.sourceOutlet().setHighlight(False)
			self.interactive_edge.setSourceOutlet(pinUnderMouse)
			pinUnderMouse.setHighlight(True)
			self.interactive_edge.updatePosition()

	def cancelConnection(self):
		assert self.is_dragging_edge and self.interactive_edge and self.interactive_edge_fixed_pin

		if self.interactive_edge_moving_pin:
			# restore edge pin connections
			if isinstance(self.interactive_edge_moving_pin, InletWidget):
				self.interactive_edge.setTargetInlet(self.interactive_edge_moving_pin)
			if isinstance(self.interactive_edge_moving_pin, OutletWidget):
				self.interactive_edge.setSourceOutlet(self.interactive_edge_moving_pin)
		else:
			self.interactive_edge.destroy()
			#remove cancelled edge creation

	def finishConnection(self, pin:PinWidget|None):
		assert self.interactive_edge_fixed_pin
		assert self.interactive_edge

		start_pin:PinWidget = self.interactive_edge_fixed_pin
		end_pin = pin

		CanConnectPins = (
			isinstance(start_pin, InletWidget) 
			and isinstance(end_pin, OutletWidget)
		) or (
			isinstance(start_pin, OutletWidget) 
			and isinstance(end_pin, InletWidget)
		)

		if CanConnectPins and pin:
			"""establish connection"""
			if isinstance(self.interactive_edge_fixed_pin, InletWidget):
				outlet = cast(OutletWidget, pin)
				self.interactive_edge.setSourceOutlet(outlet)

			elif isinstance(self.interactive_edge_fixed_pin, OutletWidget):
				inlet = cast(InletWidget, pin)
				self.interactive_edge.setTargetInlet(inlet)
		else:
			"""remove interactive edge"""
			self.interactive_edge.destroy()

		self.interactive_edge = None
		self.interactive_edge_fixed_pin = None




if __name__ == "__main__":
	class GraphView(QGraphicsView):
		def __init__(self):
			super().__init__()
			self.setRenderHint(QPainter.RenderHint.Antialiasing)

		def contextMenuEvent(self, event: QContextMenuEvent) -> None:

			# Create the context menu
			context_menu = QMenu(self)
			
			# Add actions to the context menu
			action1 = QAction("delete selection", self)
			context_menu.addAction(action1)
			
			action2 = QAction("create node", self)
			context_menu.addAction(action2)

			action3 = QAction(f"flip orientation", self)
			context_menu.addAction(action3)
			action3.triggered.connect(self.flipOrientation)
			
			# Show the context menu at the position of the mouse event
			context_menu.exec(event.globalPos())

		def flipOrientation(self):
			graphscene = cast(GraphScene, self.scene())
			for item in graphscene.items():
				if isinstance(item, NodeWidget):
					node = cast(NodeWidget, item)
					if node.orientation() == Qt.Vertical:
						node.setOrientation(Qt.Horizontal)
					elif node.orientation() == Qt.Horizontal:
						node.setOrientation(Qt.Vertical)

		def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
			graphscene = cast(GraphScene, self.scene())
			node = NodeWidget("<new node>")
			clickpos = self.mapToScene(event.position().toPoint())
			node.setPos(clickpos)
			graphscene.addNode(node)

			return super().mouseDoubleClickEvent(event)




	from pylive import livescript
	import sys
	app = QApplication(sys.argv)
	window = QWidget()
	mainLayout = QVBoxLayout()
	mainLayout.setContentsMargins(0,0,0,0)
	window.setLayout(mainLayout)
	graphview = GraphView()
	mainLayout.addWidget(graphview)

	graphscene = GraphScene()
	graphscene.setSceneRect(QRectF(-400, -400, 800, 800))
	graphview.setScene(graphscene)

	# Read
	read_text_node = NodeWidget("Read Text")
	outlet = OutletWidget("text out")
	read_text_node.addOutlet(outlet)
	graphscene.addNode(read_text_node)
	read_text_node.moveBy(-70, -70)

	# Convert
	convert_node = NodeWidget("Markdown2Html")
	inlet  =InletWidget("Markdown in")
	convert_node.addInlet(inlet)
	convert_node.addOutlet(OutletWidget("HTML out"))
	graphscene.addNode(convert_node)
	convert_node.moveBy(0, 0)

	# Write
	write_text_node = NodeWidget("Write Text")
	write_text_node.addInlet(InletWidget("text in"))
	graphscene.addNode(write_text_node)
	write_text_node.moveBy(70, 100)

	# create edge1
	edge1 = EdgeWidget(outlet, inlet)
	graphscene.addEdge(edge1)

	
	# scene.addItem(QGraphicsRectItem(0,0,100,100))
	window.show()
	sys.exit(app.exec())
