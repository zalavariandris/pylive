import sys
from typing import Optional
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from GraphModel import GraphModel


class InletItem(QGraphicsItem):
	"""Graphics item representing a pin (either inlet or outlet)."""
	def __init__(self, parent_node):
		super().__init__(parent=parent_node)
		self.parent_node = parent_node
		self.name = "<inlet name>"
		self.persistent_inlet_index:Optional[QModelIndex]=None
		self.edges = []

		# Size of the pin and space for the name text
		self.pin_radius = 5
		self.text_margin = 10

		# Font for drawing the name
		self.font = QFont("Arial", 10)

		self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges)

	def boundingRect(self) -> QRectF:
		"""Calculate bounding rect to include both pin and name text."""
		font = QApplication.font()
		text_width = QFontMetrics(font).horizontalAdvance(self.name)
		pin_diameter = self.pin_radius * 2
		fm = QFontMetrics(font)
		height = max(pin_diameter, fm.height()+fm.descent()+5)

		# Bounding rect includes the pin (left side) and text (right side)
		return QRectF(-self.text_margin - pin_diameter, 
					  -height / 2, 
					   10 + text_width + self.text_margin + pin_diameter, 
					   height)

	def paint(self, painter, option, widget=None):
		"""Draw the pin and the name."""
		# Draw pin (ellipse)
		painter.setBrush(Qt.NoBrush)
		painter.setPen(option.palette.light().color())
		painter.drawEllipse(-self.pin_radius, -self.pin_radius, self.pin_radius * 2, self.pin_radius * 2)

		# Draw the name
		painter.setPen(option.palette.light().color())
		font = QApplication.font()
		painter.drawText(5, -QFontMetrics(font).descent(), self.name)

		self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges)

	def itemChange(self, change, value):
		if self.persistent_inlet_index and change == QGraphicsItem.GraphicsItemChange.ItemScenePositionHasChanged:
			for edge_item in self.edges:
				edge_item.updatePosition()
		return super().itemChange(change, value)


class OutletItem(QGraphicsItem):
	"""Graphics item representing a pin (either inlet or outlet)."""
	def __init__(self, parent_node):
		super().__init__(parent=parent_node)
		self.parent_node = parent_node
		self.name = "<outlet name>"
		self.persistent_outlet_index:Optional[QModelIndex]=None
		self.edges = []

		# Size of the pin and space for the name text
		self.pin_radius = 5
		self.text_margin = 10

		self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges)

	def boundingRect(self) -> QRectF:
		"""Calculate bounding rect to include both pin and name text."""
		font = QApplication.font()
		text_width = QFontMetrics(font).horizontalAdvance(self.name)
		pin_diameter = self.pin_radius * 2
		fm = QFontMetrics(font)
		height = max(pin_diameter, fm.height()+fm.descent()+5)

		# Bounding rect includes the pin (left side) and text (right side)
		return QRectF(-self.text_margin - pin_diameter, 
					  -pin_diameter, 
					   5 + text_width + self.text_margin + pin_diameter, 
					   height)

	def paint(self, painter, options, widget=None):
		"""Draw the pin and the name."""
		# Draw pin (ellipse)
		painter.setBrush(Qt.NoBrush)
		painter.setPen(options.palette.light().color())
		painter.drawEllipse(-self.pin_radius, -self.pin_radius, self.pin_radius * 2, self.pin_radius * 2)

		# Draw the name
		painter.setPen(options.palette.light().color())
		font = QApplication.font()
		text_x = -QFontMetrics(font).horizontalAdvance(self.name) - self.text_margin
		painter.drawText(10, 10, self.name)

	def itemChange(self, change, value):
		if self.persistent_outlet_index and change == QGraphicsItem.GraphicsItemChange.ItemScenePositionHasChanged:
			for edge_item in self.edges:
				edge_item.updatePosition()
		return super().itemChange(change, value)


class NodeItem(QGraphicsItem):
	"""Graphics item representing a node."""
	def __init__(self, parent_graph:"GraphView"):
		super().__init__(parent=None)
		self.parent_graph = parent_graph
		self.name = "<node>"
		self.script = "<script>"
		self.rect = QRectF(-10, -10, 100, 30)  # Set size of the node box
		self.persistent_node_index:Optional[QPersistentModelIndex] = None
		# Store pins (inlets and outlets)
		self.inlets = []
		self.outlets = []

		# Enable dragging and selecting
		self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
		self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
		self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)

	def addInlet(self):
		inlet = InletItem(parent_node=self,)
		self.inlets.append(inlet)
		self.updatePinPositions()
		return inlet

	def addOutlet(self):
		outlet = OutletItem(parent_node=self)
		self.outlets.append(outlet)
		self.updatePinPositions()
		return outlet

	def updatePinPositions(self, vertical_mode=False):
		"""
		Update the positions of inlets and outlets.
		:param vertical_mode: If True, place inlets on the left and outlets on the right (default).
							  If False, place inlets on the top and outlets on the bottom.
		"""
		offset = 8
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

		painter.setBrush(option.palette.window())
		painter.setPen(option.palette.midlight().color())
		painter.drawRoundedRect(self.rect, 3,3)

		# Draw the node name text
		painter.setPen(option.palette.text().color())
		painter.drawText(self.rect, Qt.AlignCenter, self.name)

	def itemChange(self, change, value):
		if self.persistent_node_index and change == QGraphicsItem.ItemPositionHasChanged:
			graph = self.parent_graph.graph_model
			node_index = graph.nodes.index(self.persistent_node_index.row(), 0)
			new_pos = self.pos()
			posx = int(new_pos.x())
			posy = int(new_pos.y())
			graph.nodes.blockSignals(True)
			graph.nodes.setData(node_index.siblingAtColumn(2), posx, Qt.ItemDataRole.DisplayRole)
			graph.nodes.setData(node_index.siblingAtColumn(3), posy, Qt.ItemDataRole.DisplayRole)
			graph.nodes.blockSignals(False)
			graph.nodes.dataChanged.emit(node_index.siblingAtColumn(2), node_index.siblingAtColumn(3))
		return super().itemChange(change, value)


class EdgeItem(QGraphicsLineItem):
	"""Graphics item representing an edge (connection)."""
	def __init__(self, source_pin_item, target_pin_item):
		super().__init__(parent=None)
		self.source_pin_item = source_pin_item
		self.target_pin_item = target_pin_item
		source_pin_item.edges.append(self)
		target_pin_item.edges.append(self)
		self.persistent_edge_index:Optional[QPersistentModelIndex] = None

		self.setPen(QPen(Qt.GlobalColor.black, 2))
		self.updatePosition()

	def updatePosition(self):
		line = QLineF(self.source_pin_item.scenePos(), self.target_pin_item.scenePos())
		self.setLine(line)

	def paint(self, painter:QPainter, options:QStyleOptionGraphicsItem, widget=None):
		p1 = self.line().p1()
		p2 = self.line().p2()

		painter.setPen(options.palette.light().color())
		painter.drawLine(self.line())

		# draw plugs
		painter.setBrush(options.palette.text().color())
		painter.setPen(Qt.NoPen)
		r = 3
		painter.drawEllipse(-r+p1.x(), -r+p1.y(), r * 2, r * 2)
		painter.drawEllipse(-r+p2.x(), -r+p2.y(), r * 2, r * 2)


class InfiniteGraphicsView(QGraphicsView):
	def __init__(self, parent=None):
		super().__init__(parent=parent)

		self._scene = QGraphicsScene()
		self._click_pos = None

		self.setDragMode(QGraphicsView.ScrollHandDrag)
		self.setRenderHint(QPainter.Antialiasing)

		# setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
		# setViewportUpdateMode(QGraphicsView.MinimalViewportUpdate)
		self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

		self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

		self.setCacheMode(QGraphicsView.CacheBackground)

	def scale_up(self):
		step = 1.2
		factor = step ** 1.0
		t = self.transform()
		if t.m11() <= 2.0:
			self.scale(factor, factor)

	def scale_down(self):
		step = 1.2
		factor = step ** -1.0
		self.scale(factor, factor)

	def mousePressEvent(self, event: QMouseEvent):
		super().mousePressEvent(event)
		if event.button() == Qt.MouseButton.LeftButton:
			self._click_pos = self.mapToScene(event.pos())

	def mouseMoveEvent(self, event: QMouseEvent):
		super().mouseMoveEvent(event)
		if self._scene.mouseGrabberItem() is None and event.buttons() == Qt.MouseButton.LeftButton:
			# Make sure shift is not being pressed
			if not (event.modifiers() & Qt.ShiftModifier):
				difference = self._click_pos - self.mapToScene(event.position().toPoint())
				self.setSceneRect(self.sceneRect().translated(difference.x(), difference.y()))

	def wheelEvent(self, event: QWheelEvent):
		delta = event.angleDelta()
		if delta.y() == 0:
			event.ignore()
			return

		d = delta.y() / abs(delta.y())
		if d > 0.0:
			self.scale_up()
		else:
			self.scale_down()


class GraphView(InfiniteGraphicsView):
	"""A view that displays the node editor."""
	def __init__(self, parent=None):
		super().__init__(parent)
		self.setRenderHint(QPainter.RenderHint.Antialiasing)

		# Create a scene to hold the node and edge graphics
		scene = QGraphicsScene(self)
		scene.setSceneRect(QRect(-9999/2,-9999/2, 9999, 9999))
		self.setScene(scene)
		self.nodes = []
		self.edges = []
		self.index_to_item_map = dict()

	def setModel(self, graph_model:GraphModel):
		self.graph_model = graph_model
		self.handleNodesInserted(  QModelIndex(), 0, self.graph_model.nodes.rowCount()-1)
		self.handleInletsInserted( QModelIndex(), 0, self.graph_model.inlets.rowCount()-1)
		self.handleOutletsInserted(QModelIndex(), 0, self.graph_model.outlets.rowCount()-1)
		self.handleEdgesInserted(  QModelIndex(), 0, self.graph_model.edges.rowCount()-1)
		self.graph_model.nodes.rowsInserted.connect(self.handleNodesInserted)
		self.graph_model.nodes.dataChanged.connect(self.handleNodesDataChanged)
		self.graph_model.inlets.rowsInserted.connect(self.handleInletsInserted)
		self.graph_model.inlets.dataChanged.connect(self.handleInletsDataChanged)
		self.graph_model.outlets.rowsInserted.connect(self.handleOutletsInserted)
		self.graph_model.outlets.dataChanged.connect(self.handleOutletsDataChanged)

	def addNode(self):
		node_item = NodeItem(parent_graph=self)
		self.nodes.append(node_item)
		self.scene().addItem(node_item)
		return node_item

	def addEdge(self, source_pin_item, target_pin_item):
		edge_item = EdgeItem(source_pin_item, target_pin_item)
		self.edges.append(edge_item)
		self.scene().addItem(edge_item)
		return edge_item

	def handleNodesInserted(self, parent:QModelIndex, first:int, last:int):
		if parent.isValid():
			raise NotImplementedError("Subgraphs are not implemented yet!")

		for row in range(first, last+1):
			# get node and create the gaphics item
			node = self.graph_model.nodes.index(row, 0)
			node_item = self.addNode()

			# map node to graphics item
			persistent_node_index = QPersistentModelIndex(node)
			node_item.persistent_node_index = persistent_node_index
			self.index_to_item_map[persistent_node_index] = node_item

			# update gaphics item
			self.handleNodesDataChanged(node, node.siblingAtColumn(4))
			
	def handleInletsInserted(self, parent:QModelIndex, first:int, last:int):
		if parent.isValid():
			raise ValueError("inlets are flat table, not a tree model")

		for row in range(first, last+1):
			# get inlet and create the gaphics item
			inlet = self.graph_model.inlets.index(row, 0) # get the inlet reference
			inlet_node = self.graph_model.getInlet(inlet)["node"] # get the node reference
			parent_node_item = self.index_to_item_map[QPersistentModelIndex(inlet_node)] # get the node graphics item
			inlet_item = parent_node_item.addInlet()

			# map inlet to graphics item
			persistent_inlet_index = QPersistentModelIndex(inlet)
			inlet_item.persistent_inlet_index = persistent_inlet_index
			self.index_to_item_map[persistent_inlet_index] = inlet_item

			# update graphics item and add to scene
			self.handleInletsDataChanged(inlet, inlet.siblingAtColumn(2))

	def handleOutletsInserted(self, parent:QModelIndex, first:int, last:int):
		if parent.isValid():
			raise ValueError("inlets are flat table, not a tree model")

		for row in range(first, last+1):
			# get inlet and create the gaphics item
			outlet = self.graph_model.outlets.index(row, 0) # get the inlet reference
			outlet_node = self.graph_model.getInlet(outlet)["node"] # get the node reference
			parent_node_item = self.index_to_item_map[QPersistentModelIndex(outlet_node)] # get the node graphics item
			outlet_item = parent_node_item.addOutlet()

			# map inlet to graphics item
			persistent_outlet_index = QPersistentModelIndex(outlet)
			outlet_item.persistent_outlet_index = persistent_outlet_index
			self.index_to_item_map[persistent_outlet_index] = outlet_item

			# update graphics item and add to scene
			self.handleOutletsDataChanged(outlet, outlet.siblingAtColumn(2))

	def handleEdgesInserted(self, parent:QModelIndex, first:int, last:int):
		if parent.isValid():
			raise NotImplementedError("Subgraphs are not implemented yet!")

		for row in range(first, last+1):
			# get node and create the gaphics item
			edge = self.graph_model.edges.index(row, 0)

		
			
			target_inlet = self.graph_model.getEdge(edge)["target"]
			target_inlet_item = self.index_to_item_map[QPersistentModelIndex(target_inlet)]
			source_outlet = self.graph_model.getEdge(edge)["source"]
			source_outlet_item = self.index_to_item_map[QPersistentModelIndex(source_outlet)]
			edge_item = self.addEdge(source_outlet_item, target_inlet_item)

			# map node to graphics item
			persistent_edge_index = QPersistentModelIndex(edge)
			edge_item.persistent_edge_index = persistent_edge_index
			self.index_to_item_map[persistent_edge_index] = edge_item

			# update gaphics item
			self.handleEdgesDataChanged(edge, edge.siblingAtColumn(2))

	def handleNodesDataChanged(self, topLeft:QModelIndex, bottomRight:QModelIndex, roles=[]):
		for row in range(topLeft.row(), bottomRight.row()+1):
			node_index = self.graph_model.nodes.index(row, 0)
			persistent_node_index = QPersistentModelIndex(node_index)
			node_item:NodeItem = self.index_to_item_map[persistent_node_index]
			new_pos = node_item.pos()
			for col in range(topLeft.column(), bottomRight.column()+1):
				match col:
					case 0:
						pass
					case 1:
						node_item.name = str(node_index.siblingAtColumn(1).data())
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

	def handleInletsDataChanged(self, topLeft:QModelIndex, bottomRight:QModelIndex, roles=[]):
		for row in range(topLeft.row(), bottomRight.row()+1):
			inlet = self.graph_model.inlets.index(row, 0)
			persistent_index = QPersistentModelIndex(inlet)
			graphics_item = self.index_to_item_map[persistent_index]
			for col in range(topLeft.column(), bottomRight.column()+1):
				match col:
					case 0:
						"""unique id changed"""
						pass
					case 1:
						pass
					case 2:
						"""name changed"""
						graphics_item.name = str(inlet.siblingAtColumn(2).data())
						graphics_item.update()

	def handleOutletsDataChanged(self, topLeft:QModelIndex, bottomRight:QModelIndex, roles=[]):
		for row in range(topLeft.row(), bottomRight.row()+1):
			outlet = self.graph_model.outlets.index(row, 0)
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
						graphics_item.name = str(outlet.siblingAtColumn(2).data())
						graphics_item.update()

	def handleEdgesDataChanged(self, topLeft:QModelIndex, bottomRight:QModelIndex, roles=[]):
		for row in range(topLeft.row(), bottomRight.row()+1):
			edge = self.graph_model.edges.index(row, 0)
			persistent_index = QPersistentModelIndex(edge)
			graphics_item = self.index_to_item_map[persistent_index]
			for col in range(topLeft.column(), bottomRight.column()+1):
				match col:
					case 0:
						"""unique id changed"""
						pass
					case 1:
						"""source outlet changed"""
						pass
					case 2:
						"""target inlet changed"""
						pass


from GraphTableView import GraphTableView
from GraphDetailsView import GraphDetailsView
class MainWindow(QWidget):
	def __init__(self):
		super().__init__()

		self.setWindowTitle("Graph Viewer Example")
		self.resize(1500, 700)

		# Initialize the GraphModel
		self.graph_model = GraphModel()
		self.nodes_selectionmodel = QItemSelectionModel(self.graph_model.nodes)

		# Add some example nodes and edges
		node1_id = self.graph_model.addNode("Node 1", 10, 100, "Script 1")
		node2_id = self.graph_model.addNode("Node 2", 20, 200, "Script 2")
		outlet_id = self.graph_model.addOutlet(node1_id, "Out1")
		inlet_id = self.graph_model.addInlet(node2_id, "In1")
		self.graph_model.addEdge(outlet_id, inlet_id)

		# Set up the node editor views
		self.graph_table_view = GraphTableView()
		self.graph_table_view.setModel(self.graph_model)
		self.graph_table_view.setNodesSelectionModel(self.nodes_selectionmodel)

		self.graph_view = GraphView()
		self.graph_view.setModel(self.graph_model)
		# self.graph_view.setNodesSelectionModel(self.nodes_selectionmodel)

		self.graph_details_view = GraphDetailsView()
		self.graph_details_view.setModel(self.graph_model)
		self.graph_details_view.setNodesSelectionModel(self.nodes_selectionmodel)
		
		layout = QHBoxLayout()
		layout.addWidget(self.graph_table_view, 1)
		layout.addWidget(self.graph_view, 1)
		layout.addWidget(self.graph_details_view, 1)
		self.setLayout(layout)

if __name__ == "__main__":
	app = QApplication(sys.argv)
	window = MainWindow()
	window.show()
	sys.exit(app.exec())
