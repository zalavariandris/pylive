from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from pylive import livescript
from typing import *

from pylive.QtGraphEditor.PanAndZoomGraphicsView import PanAndZoomGraphicsView


class GWidget(QGraphicsWidget):
	def setGeometry(self, rect):
		# Called by the layout to assign size and position
		super().setGeometry(rect)
		self._rect = rect

	# def paint(self, painter, option, widget):
	# 	path = self.shape()
	# 	painter.setPen('green')
	# 	painter.drawPath(path)
	# 	# painter.drawRect( QRectF( QPointF(0,0), self._rect.size() ))


class TextWidget(GWidget):
	"""A simple widget that contains a QGraphicsTextItem."""
	def __init__(self, text, parent=None):
		super().__init__(parent)
		self.parent_node = None

		# Create the text item
		self.text_item = QGraphicsTextItem(text, self)
		self.text_item.document().setDocumentMargin(0)
		self.text_item.setTextInteractionFlags(Qt.TextEditorInteraction)
		self.text_item.setAcceptedMouseButtons(Qt.NoButton)  # Transparent to mouse events
		self.text_item.setEnabled(False)

		self._edges = []
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

	def setGeometry(self, rect):
		# Called by the layout to assign size and position
		print("set geo", rect)
		super().setGeometry(rect)
		self._rect = rect


class CircleWidget(GWidget):
	def __init__(self, radius:float, parent=None):
		super().__init__()
		self.circle_item = QGraphicsEllipseItem(QRectF(0,0,radius*2, radius*2), self)
		text_color = self.palette().color(QPalette.Text)
		self.circle_item.setBrush(Qt.NoBrush)
		self.circle_item.setPen(QPen(text_color, 2))

	def sizeHint(self, which, constraint=QSizeF()):
		circle_rect = self.circle_item.rect()
		return circle_rect.size()


class PinWidget(QGraphicsWidget):
	def __init__(self, text):
		super().__init__()
		self.parent_node = None

		# Create the text item
		self.circle_item = CircleWidget(radius=3)
		self.text_widget = TextWidget(text)

		self.main_layout = QGraphicsLinearLayout(Qt.Horizontal)
		self.main_layout.setContentsMargins(0,0,0,0)
		self.main_layout.setSpacing(3)
		
		self.setLayout(self.main_layout)

		self._edges = []
		self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges)

	def itemChange(self, change, value):
		match change:
			case QGraphicsItem.GraphicsItemChange.ItemScenePositionHasChanged:
				for edge_item in self._edges:
					edge_item.updatePosition()
		return super().itemChange(change, value)

	def getConnectionPoint(self):
		return self.circle_item.sceneBoundingRect().center()

	def shape(self):
		shape = QPainterPath()
		shape.addRect( QRectF(self.circle_item.x()-8,0,22,15) )
		return shape

	def boundingRect(self) -> QRectF:
		return self.shape().boundingRect()

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
		for edge in reversed(self.edges):
			edge.destroy()
		self.edges = []

		if self.parent_node:
			self.parent_node.removeOutlet(self)
			self.parent_node.updatePinPositions()
		self.scene().removeItem(self)


class InletWidget(PinWidget):
	def __init__(self, text):
		super().__init__(text)
		self.main_layout.addItem(self.circle_item)
		self.main_layout.addItem(self.text_widget)
		self.main_layout.setAlignment(self.circle_item, Qt.AlignmentFlag.AlignCenter)

	def destroy(self):
		for edge in reversed(self.edges):
			edge.destroy()
		self.edges = []

		if self.parent_node:
			self.parent_node.removeInlet(self)
			self.parent_node.updatePinPositions()
		self.parentNode = None
		self.scene().removeItem(self)


class NodeWidget(QGraphicsWidget):
	"""A widget that holds multiple TextWidgets arranged in a vertical layout."""

	def __init__(self, title="Node", parent=None):
		super().__init__(parent)

		# Enable selection and movement
		self.setFlag(QGraphicsWidget.ItemIsSelectable, True)
		self.setFlag(QGraphicsWidget.ItemIsMovable, True)
		self.setFlag(QGraphicsWidget.ItemIsFocusable, True)

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

	def addInlet(self, inlet:InletWidget):
		self.inlets_layout.addItem(inlet)
		inlet.setParentItem(self)
		self.inlets.append(inlet)

	def addOutlet(self, outlet:OutletWidget):
		self.outlets_layout.addItem(outlet)
		self.outlets_layout.setAlignment(outlet, Qt.AlignRight)
		outlet.parent_node = self
		outlet.setParentItem(self)

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

		painter.setBrush(palette.window())
		# painter.setBrush(Qt.NoBrush)

		pen = QPen(palette.text().color(), 1)
		pen.setCosmetic(True)
		pen.setWidthF(1)
		if state & QStyle.StateFlag.State_Selected:
			pen.setColor(palette.accent().color())
		painter.setPen(pen)

		# painter.setPen(palette.window().color())
		painter.drawRoundedRect(QRectF(QPointF(),self.size()), 3, 3)


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
		self.is_moving_endpoint = False

	def sourceOutlet(self)->OutletWidget|None:
		return self._source_pin_item

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

	def updatePosition(self):
		line = self.line()
		sourcePin = self._source_outlet
		targetPin = self._target_inlet

		def getConnectionPoint(widget):
			try:
				return widget.getConnectionPoint()
			except AttributeError:
				return widget.scenePos() + QPointF(widget.geometry().width()/2, widget.geometry().height()/2)

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
			pass

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

		# Clear parent reference
		self.parent_graph = None

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
		self.interactive_edge_start_pin:PinWidget|None = None
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

	def mousePressEvent(self, event):
		if pin:=self.pinAt(event.scenePos()):
			print(pin)
			self.initiateConnection(pin)

		elif edge:=self.edgeAt(event.scenePos()):
			delta1 = edge.line().p1() - event.scenePos()
			d1 = delta1.manhattanLength()
			delta2 = edge.line().p2() - event.scenePos()
			d2 = delta2.manhattanLength()

			# print("closest end:", closest_pin)

			if d1<d2:
				self.interactive_edge_start_pin = edge._target_inlet
				# self.modifyConnection(edge=self, endpoint=PinType.OUTLET)
			else:
				self.interactive_edge_start_pin = edge._source_outlet
				# self.modifyConnection(edge=self, endpoint=PinType.INLET)

			
			self.interactive_edge = edge
			self.is_dragging_edge = True
		else:
			super().mousePressEvent(event)

	def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
		if self.is_dragging_edge:
			self.moveConnection(event.scenePos())
		else:
			return super().mouseMoveEvent(event)

	def mouseReleaseEvent(self, event):
		"""
		Override mouseReleaseEvent to filter events when the mouse is released in the scene.
		"""
		if self.is_dragging_edge:
			pin = self.pinAt(event.scenePos())
			self.finishConnection(pin)
			self.is_dragging_edge = False
		else:
			return super().mouseReleaseEvent(event)
		
	def initiateConnection(self, pin):
		if isinstance(pin, OutletWidget):
			self.interactive_edge = EdgeWidget(source_outlet=pin, target_inlet=None)
			self.interactive_edge_start_pin = pin
		elif isinstance(pin, InletWidget):
			self.interactive_edge = EdgeWidget(source_outlet=None, target_inlet=pin)
			self.interactive_edge_start_pin = pin
		assert self.interactive_edge
		self.interactive_edge.updatePosition()
		self.addItem(self.interactive_edge)
		self.is_dragging_edge = True

	def moveConnection(self, scenepos:QPointF):
		assert isinstance(scenepos, QPointF), f"got: {scenepos}"
		assert self.interactive_edge

		# move free endpoint
		line = self.interactive_edge.line()
		if isinstance(self.interactive_edge_start_pin, OutletWidget):
			line.setP2(scenepos)
		elif isinstance(self.interactive_edge_start_pin, InletWidget):
			line.setP1(scenepos)
		self.interactive_edge.setLine(line)

		# attach free endpoint to closeby pin
		pinUnderMouse = self.pinAt(scenepos)
		if isinstance(self.interactive_edge_start_pin, OutletWidget) and isinstance(pinUnderMouse, InletWidget):
			self.interactive_edge.setTargetInlet(pinUnderMouse)
			self.interactive_edge.updatePosition()
		elif isinstance(self.interactive_edge_start_pin, InletWidget) and isinstance(pinUnderMouse, OutletWidget):
			self.interactive_edge.setSourceOutlet(pinUnderMouse)
			self.interactive_edge.updatePosition()

	def finishConnection(self, pin:PinWidget|None):
		assert self.interactive_edge_start_pin
		assert self.interactive_edge

		start_pin:PinWidget = self.interactive_edge_start_pin
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
			if isinstance(self.interactive_edge_start_pin, InletWidget):
				outlet = cast(OutletWidget, pin)
				self.interactive_edge.setSourceOutlet(outlet)

			elif isinstance(self.interactive_edge_start_pin, OutletWidget):
				inlet = cast(InletWidget, pin)
				self.interactive_edge.setTargetInlet(inlet)
		else:
			"""remove interactive edge"""
			self.interactive_edge.destroy()

		self.interactive_edge = None
		self.interactive_edge_start_pin = None

	def cancelConnection(self):
		...


if __name__ == "__main__":
	from pylive import livescript
	import sys
	app = QApplication(sys.argv)
	window = QGraphicsView()

	graphscene = GraphScene()
	graphscene.setSceneRect(QRectF(-400, -400, 800, 800))
	window.setScene(graphscene)

	# create node2
	read_text_node = NodeWidget("Read Text")
	outlet = OutletWidget("text out")
	read_text_node.addOutlet(outlet)
	graphscene.addNode(read_text_node)
	read_text_node.moveBy(-200, 0)

	convert_node = NodeWidget("Markdown2Html")
	convert_node.addInlet(InletWidget("Markdown in"))
	convert_node.addOutlet(OutletWidget("HTML out"))
	graphscene.addNode(convert_node)
	convert_node.moveBy(0, -150)

	# create node3
	write_text_node = NodeWidget("Write Text")
	inlet = InletWidget("text in")
	write_text_node.addInlet(inlet)
	graphscene.addNode(write_text_node)
	write_text_node.moveBy(150, 0)

	# create edge1
	edge1 = EdgeWidget(outlet, inlet)
	graphscene.addEdge(edge1)
	
	# scene.addItem(QGraphicsRectItem(0,0,100,100))
	window.show()
	sys.exit(app.exec())
