import sys
from typing import Optional
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from InfiniteGraphicsView import InfiniteGraphicsView
from GraphModel import GraphModel

class PinItem(QGraphicsItem):
	"""Graphics item representing a pin (either inlet or outlet)."""
	def __init__(self, parent_node):
		super().__init__(parent=parent_node)
		self.parent_node = parent_node
		self.persistent_index:Optional[QModelIndex]=None
		self.edges = []

		self.label = QGraphicsSimpleTextItem(parent=self)

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

	def paint(self, painter, option, widget=None):
		"""Draw the pin and the name."""
		# Draw pin (ellipse)
		# painter.setBrush(Qt.NoBrush)
		painter.setPen(QPen(option.palette.base().color(), 3))
		if option.state & QStyle.StateFlag.State_MouseOver:
			painter.setBrush(option.palette.accent().color())
		else:
			painter.setBrush(option.palette.windowText().color())
		painter.drawEllipse(-self.pin_radius, -self.pin_radius, self.pin_radius * 2, self.pin_radius * 2)

		# # Draw the name
		# painter.setPen(option.palette.light().color())
		# font = QApplication.font()
		# painter.drawText(5, -QFontMetrics(font).descent(), self.name)

	def hoverEnterEvent(self, event):
		print("enter")
		self.update()

	def hoverExitEvent(self, event):
		print("exit")
		self.update()

	def itemChange(self, change, value):
		if self.persistent_index and change == QGraphicsItem.GraphicsItemChange.ItemScenePositionHasChanged:
			for edge_item in self.edges:
				edge_item.updatePosition()
		return super().itemChange(change, value)

	def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
		graphview = self.parent_node.parent_graph
		graphview.initiateConnect(pin=self)
		# return super().mousePressEvent(event)

	# def hoverMoveEvent(self, event):
	# 	print("mouse hover move")
	# 	# return super().hoverMoveEvent(event)

	def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
		graphview = self.parent_node.parent_graph
		graphview.moveConnection(event.scenePos())
		# return super().mouseMoveEvent(event)

	def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
		graphview = self.parent_node.parent_graph
		graphview.establishConnection()
		# return super().mouseReleaseEvent(event)

	
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
		self.setAcceptHoverEvents(True)

		self.setZValue(2)

	def addInlet(self):
		inlet = PinItem(parent_node=self,)
		self.inlets.append(inlet)
		self.updatePinPositions()
		return inlet

	def addOutlet(self):
		outlet = PinItem(parent_node=self)
		self.outlets.append(outlet)
		self.updatePinPositions()
		return outlet

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
		palette:QPalette = option.palette
		state:QStyle.StateFlag = option.state

		painter.setBrush(palette.base())
		# painter.setBrush(Qt.NoBrush)

		if state & QStyle.StateFlag.State_Selected:
			# Use a highlight color for the border when selected
			painter.setPen(palette.accent().color())
		else:
			# Use the midlight color for the border when not selected
			painter.setPen(palette.text().color())

		# painter.setPen(palette.window().color())
		painter.drawRoundedRect(self.rect, 3,3)

		# Draw the node name text
		# painter.setPen(palette.text().color())
		painter.drawText(self.rect, Qt.AlignmentFlag.AlignCenter, self.name)

	def itemChange(self, change, value):
		if (self.parent_graph.graph_model and
			self.persistent_node_index and
			self.persistent_node_index.isValid()
		):
			match change:
				case QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
					graph:GraphModel = self.parent_graph.graph_model
					node_index = graph.nodes.index(self.persistent_node_index.row(), 0)
					new_pos = self.pos()
					posx = int(new_pos.x())
					posy = int(new_pos.y())
					graph.nodes.blockSignals(True)
					graph.nodes.setData(node_index.siblingAtColumn(2), posx, Qt.ItemDataRole.DisplayRole)
					graph.nodes.setData(node_index.siblingAtColumn(3), posy, Qt.ItemDataRole.DisplayRole)
					graph.nodes.blockSignals(False)
					graph.nodes.dataChanged.emit(node_index.siblingAtColumn(2), node_index.siblingAtColumn(3))
				case QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
					if nodes_selectionmodel:=self.parent_graph.nodes_selectionmodel:
						graph = self.parent_graph.graph_model
						node_index = graph.nodes.index(self.persistent_node_index.row(), 0)
						if value == 1:
							nodes_selectionmodel.select(node_index, QItemSelectionModel.SelectionFlag.Select)
						elif value == 0:
							nodes_selectionmodel.select(node_index, QItemSelectionModel.SelectionFlag.Deselect)
					else:
						pass

		return super().itemChange(change, value)


class EdgeItem(QGraphicsLineItem):
	"""Graphics item representing an edge (connection)."""
	def __init__(self, source_pin_item, target_pin_item, parent_graph:"GraphView"):
		super().__init__(parent=None)
		self.source_pin_item = source_pin_item
		self.target_pin_item = target_pin_item
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

	def updatePosition(self):
		line = self.line()
		if self.source_pin_item:
			line.setP1(self.source_pin_item.scenePos())
		if self.target_pin_item:
			line.setP2(self.target_pin_item.scenePos())
		if self.source_pin_item or self.target_pin_item:
			self.setLine(line)

	def paint(self, painter:QPainter, option:QStyleOptionGraphicsItem, widget=None):
		p1 = self.line().p1()
		p2 = self.line().p2()

		palette:QPalette = option.palette
		state:QStyle.StateFlag = option.state
		if state & QStyle.StateFlag.State_Selected:
			# Use a highlight color for the border when selected
			painter.setPen(QPen(palette.highlight().color(), 3))
		else:
			# Use the midlight color for the border when not selected
			painter.setPen(QPen(palette.midlight().color(), 2))
		# painter.setPen(options.palette.light().color())
		painter.drawLine(self.line())

		# # draw plugs
		# painter.setBrush(palette.text().color())
		# painter.setPen(Qt.PenStyle.NoPen)
		# r = 1

		# painter.drawEllipse(p1, r * 2, r * 2)
		# painter.drawEllipse(p2, r * 2, r * 2)

	def itemChange(self, change, value):
		if self.persistent_edge_index and self.persistent_edge_index.isValid():
			if QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
				if self.parent_graph.edges_selectionmodel:
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


class GraphView(QGraphicsView):
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

		self.graph_model = None
		self.nodes_selectionmodel = None
		self.edges_selectionmodel = None

		polkaBrush = QBrush()
		polkaBrush.setColor(QApplication.palette().mid().color())
		polkaBrush.setStyle(Qt.BrushStyle.Dense7Pattern)
		self.setBackgroundBrush(polkaBrush)

	def initiateConnect(self, pin):
		self.potential_edge = EdgeItem(source_pin_item=pin, target_pin_item=None, parent_graph=self)
		line = self.potential_edge.line()
		line.setP2(pin.pos())
		self.potential_edge.setLine(line)
		self.scene().addItem(self.potential_edge)
		print("initiateConnect")

	def moveConnection(self, scene_pos):
		line = self.potential_edge.line()
		line.setP2(scene_pos)
		self.potential_edge.setLine(line)

		items = self.items(self.mapFromScene(scene_pos))
		for item in items:
			if isinstance(item, PinItem) and item!=self.potential_edge.source_pin_item:
				self.potential_edge.target_pin_item = item
				self.potential_edge.updatePosition()
				break
		# item = self.scene().itemAt(scene_pos.toPoint())
		# print("item under mouse:", items)

	def establishConnection(self):
		# remove the dummy edge
		self.scene().removeItem(self.potential_edge)
		if not (self.potential_edge.source_pin_item and self.potential_edge.target_pin_item):
			return
		# get connected pins
		inlet = self.potential_edge.source_pin_item.persistent_index
		outlet = self.potential_edge.target_pin_item.persistent_index

		# connect model
		if inlet.model() == outlet.model():
			# bad pins were selected
			return

		if inlet.model() == self.graph_model.outlets: 
			# pins are swapped
			inlet, outlet = outlet, inlet

		outlet = self.graph_model.outlets.index(outlet.row(), 0)
		inlet = self.graph_model.inlets.index(inlet.row(), 0)
		self.graph_model.addEdge(outlet, inlet)

	def setModel(self, graph_model:GraphModel):
		self.graph_model = graph_model
		self.handleNodesInserted(  QModelIndex(), 0, self.graph_model.nodes.rowCount()-1)
		self.handleInletsInserted( QModelIndex(), 0, self.graph_model.inlets.rowCount()-1)
		self.handleOutletsInserted(QModelIndex(), 0, self.graph_model.outlets.rowCount()-1)
		self.handleEdgesInserted(  QModelIndex(), 0, self.graph_model.edges.rowCount()-1)

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

	def handleNodesSelectionChanged(self, selected:QItemSelection, deselected:QItemSelection):
		for node in [index for index in selected.indexes() if index.column()==0]:
			persistent_node_index = QPersistentModelIndex(node)
			node_item = self.index_to_item_map[persistent_node_index]
			node_item.setSelected(True)

		for node in [index for index in deselected.indexes() if index.column()==0]:
			persistent_node_index = QPersistentModelIndex(node)
			node_item = self.index_to_item_map[persistent_node_index]
			node_item.setSelected(False)

	def handleEdgesSelectionChanged(self, selected:QItemSelection, deselected:QItemSelection):
		for index in [index for index in selected.indexes() if index.column()==0]:
			persistent_index = QPersistentModelIndex(index)
			item = self.index_to_item_map[persistent_index]
			item.setSelected(True)

		for index in [index for index in deselected.indexes() if index.column()==0]:
			persistent_index = QPersistentModelIndex(index)
			item = self.index_to_item_map[persistent_index]
			item.setSelected(False)

	def addNode(self):
		node_item = NodeItem(parent_graph=self)
		self.nodes.append(node_item)
		self.scene().addItem(node_item)
		return node_item

	def addEdge(self, source_pin_item, target_pin_item):
		edge_item = EdgeItem(source_pin_item, target_pin_item, parent_graph=self)
		self.edges.append(edge_item)
		self.scene().addItem(edge_item)
		return edge_item

	def handleNodesInserted(self, parent:QModelIndex, first:int, last:int):
		if parent.isValid():
			raise NotImplementedError("Subgraphs are not implemented yet!")

		for row in range(first, last+1):
			# get node and create the gaphics item
			graph:GraphModel = self.graph_model
			node = graph.nodes.index(row, 0)
			node_item = self.addNode()

			# map node to graphics item
			persistent_node_index = QPersistentModelIndex(node)
			node_item.persistent_node_index = persistent_node_index
			self.index_to_item_map[persistent_node_index] = node_item

			# update gaphics item
			self.handleNodesDataChanged(node, node.siblingAtColumn(4))
	
	def handleOutletsRemoved(self, parent:QModelIndex, first:int, last:int):
		if parent.isValid():
			raise NotImplementedError("Subgraphs are not implemented yet!")

		for row in range(last, first-1, -1):
			outlet = self.graph_model.outlets.index(row, 0)
			persistent_index = QPersistentModelIndex(outlet)
			outlet_item = self.index_to_item_map[persistent_index]
			self.scene().removeItem(outlet_item)
			del self.index_to_item_map[persistent_index]

	def handleInletsRemoved(self, parent:QModelIndex, first:int, last:int):
		if parent.isValid():
			raise NotImplementedError("Subgraphs are not implemented yet!")

		for row in range(last, first-1, -1):
			inlet = self.graph_model.inlets.index(row, 0)
			persistent_index = QPersistentModelIndex(inlet)
			inlet_item = self.index_to_item_map[persistent_index]
			self.scene().removeItem(inlet_item)
			del self.index_to_item_map[persistent_index]

	def handleNodesRemoved(self, parent:QModelIndex, first:int, last:int):
		if parent.isValid():
			raise NotImplementedError("Subgraphs are not implemented yet!")

		for row in range(last, first-1, -1):
			node = self.graph_model.nodes.index(row, 0)
			node_item = self.index_to_item_map[QPersistentModelIndex(node)]
			self.scene().removeItem(node_item)
			del self.index_to_item_map[QPersistentModelIndex(node)]

	def handleEdgesRemoved(self, parent:QModelIndex, first:int, last:int):
		if parent.isValid():
			raise NotImplementedError("Subgraphs are not implemented yet!")

		for row in range(last, first-1, -1):
			edge = self.graph_model.edges.index(row, 0)
			persistent_index = QPersistentModelIndex(edge)
			edge_item = self.index_to_item_map[persistent_index]
			self.scene().removeItem(edge_item)
			del self.index_to_item_map[persistent_index]

	def handleInletsInserted(self, parent:QModelIndex, first:int, last:int):
		if parent.isValid():
			raise ValueError("inlets are flat table, not a tree model")

		for row in range(first, last+1):
			# get inlet and create the gaphics item
			graph:GraphModel = self.graph_model
			inlet = graph.inlets.index(row, 0) # get the inlet reference
			inlet_node = graph.getInlet(inlet)["node"] # get the node reference
			parent_node_item = self.index_to_item_map[QPersistentModelIndex(inlet_node)] # get the node graphics item
			inlet_item = parent_node_item.addInlet()

			# map inlet to graphics item
			persistent_index = QPersistentModelIndex(inlet)
			inlet_item.persistent_index = persistent_index
			self.index_to_item_map[persistent_index] = inlet_item

			# update graphics item and add to scene
			self.handleInletsDataChanged(inlet, inlet.siblingAtColumn(2))

	def handleOutletsInserted(self, parent:QModelIndex, first:int, last:int):
		if parent.isValid():
			raise ValueError("inlets are flat table, not a tree model")

		for row in range(first, last+1):
			# get inlet and create the gaphics item
			graph:GraphModel = self.graph_model
			outlet = graph.outlets.index(row, 0) # get the inlet reference
			outlet_node = graph.getInlet(outlet)["node"] # get the node reference
			parent_node_item = self.index_to_item_map[QPersistentModelIndex(outlet_node)] # get the node graphics item
			outlet_item = parent_node_item.addOutlet()

			# map inlet to graphics item
			persistent_index = QPersistentModelIndex(outlet)
			outlet_item.persistent_index = persistent_index
			self.index_to_item_map[persistent_index] = outlet_item

			# update graphics item and add to scene
			self.handleOutletsDataChanged(outlet, outlet.siblingAtColumn(2))

	def handleEdgesInserted(self, parent:QModelIndex, first:int, last:int):
		if parent.isValid():
			raise NotImplementedError("Subgraphs are not implemented yet!")

		for row in range(first, last+1):
			# get node and create the gaphics item
			graph:GraphModel = self.graph_model
			edge = graph.edges.index(row, 0)

			target_inlet = graph.getEdge(edge)["target"]
			target_inlet_item = self.index_to_item_map[QPersistentModelIndex(target_inlet)]
			source_outlet = graph.getEdge(edge)["source"]
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
			graph:GraphModel = self.graph_model
			node_index = graph.nodes.index(row, 0)
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

	def handleOutletsDataChanged(self, topLeft:QModelIndex, bottomRight:QModelIndex, roles=[]):
		for row in range(topLeft.row(), bottomRight.row()+1):
			graph:GraphModel = self.graph_model
			outlet = graph.outlets.index(row, 0)
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

	def handleEdgesDataChanged(self, topLeft:QModelIndex, bottomRight:QModelIndex, roles=[]):
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
						pass
					case 2:
						"""target inlet changed"""
						pass

	# def drawBackground(self, painter, rect):
	# 	# Create a QPainter to draw the background
	# 	painter.setRenderHint(QPainter.Antialiasing)

	# 	# Set the color for the polka dots
	# 	dot_color = QColor(255, 0, 0)  # Red dots

	# 	# Calculate the bounds for drawing dots
	# 	left = int(rect.left())
	# 	right = int(rect.right())
	# 	top = int(rect.top())
	# 	bottom = int(rect.bottom())

	# 	spacing = 25
	# 	radius = 1

	# 	# Draw polka dots
	# 	painter.setBrush(dot_color)
	# 	for x in range(left, right, spacing):
	# 		for y in range(top, bottom, spacing):
	# 			painter.drawEllipse(x, y, radius, radius)


from GraphTableView import GraphTableView
from GraphDetailsView import GraphDetailsView
class MainWindow(QWidget):
	def __init__(self):
		super().__init__()

		self.setWindowTitle("Graph Viewer Example")
		self.resize(700, 500)

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



if __name__ == "__main__":
	app = QApplication(sys.argv)
	window = MainWindow()
	window.show()
	sys.exit(app.exec())
