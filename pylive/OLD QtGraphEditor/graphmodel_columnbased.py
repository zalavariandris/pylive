from enum import IntEnum, StrEnum
from pylive import unique
import sys
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from typing import *


class NodeAttribute(StrEnum):
	Id = "ID"
	Name = "NAME"
	LocationX = "LOCATION_X"
	LocationY = "LOCATION_Y"

class InletAttribute(StrEnum):
	Id = "ID"
	Owner = "OWNER"
	Name = "NAME"

class OutletAttribute(StrEnum):
	Id = "ID"
	Owner = "OWNER"
	Name = "NAME"

class EdgeAttribute(StrEnum):
	Id = "ID"
	SourceOutlet = "SOURCE_OUTLET"
	TargetInlet = "TARGET_INLET"


class NodeRef():
	def __init__(self, index:QModelIndex, graph:'GraphModel'):
		if not index.isValid():
			raise ValueError(f"Node {index.data()}, does not exist!")
		if not index.column() == 0:
			raise ValueError("Node column must be 0")

		self._index = QPersistentModelIndex(index)
		self._graph = graph

	def graph(self):
		return self._graph

	def __eq__(self, value: object, /) -> bool:
		if isinstance(value, NodeRef):
			return self._index == value._index
		else:
			return False

	def __hash__(self) -> int:
		return hash((self._index, self._index.row(), self._index.column()))

	def isValid(self):
		return self._index.isValid() and self._index.column() == 0 and self._index.model() == self._graph._nodeTable

	def __repr__(self) -> str:
		return f"{self.__class__.__name__}({self._index.row()},{self._index.column()})"


class EdgeRef():
	def __init__(self, index:QModelIndex, graph:'GraphModel'):
		if not index.isValid():
			raise ValueError(f"Node {index.data()}, does not exist!")
		if not index.column() == 0:
			raise ValueError("Node column must be 0")

		self._index = QPersistentModelIndex(index)
		self._graph = graph

	def __eq__(self, value: object, /) -> bool:
		if isinstance(value, EdgeRef):
			return self._index == value._index
		else:
			return False

	def __hash__(self) -> int:
		return hash(self._index)

	def isValid(self):
		return self._index.isValid() and self._index.column() == 0 and self._index.model() == self._graph._edgeTable

	def __repr__(self) -> str:
		return f"{self.__class__.__name__}({self._index.row()},{self._index.column()})"


class InletRef():
	def __init__(self, index:QModelIndex, graph:'GraphModel'):
		if not index.isValid():
			raise ValueError(f"Node {index.data()}, does not exist!")
		if not index.column() == 0:
			raise ValueError("Node column must be 0")

		self._index = QPersistentModelIndex(index)
		self._graph = graph

	# def __hash__(self) -> int:
	# 	return hash(self._index)

	def __eq__(self, value: object, /) -> bool:
		if isinstance(value, InletRef):
			return (
				self._index.row() == value._index.row()
				and self._index.column() == value._index.column()
				and self._index.model() == value._index.model()
			)
		else:
			return False

	def __hash__(self) -> int:
		return hash(self._index)

	def isValid(self):
		return self._index.isValid() and self._index.column() == 0 and self._index.model() == self._graph._inletTable

	def __repr__(self) -> str:
		return f"{self.__class__.__name__}({self._index.row()},{self._index.column()})"


class OutletRef():
	def __init__(self, index:QModelIndex, graph:'GraphModel'):
		if not index.isValid():
			raise ValueError(f"Node {index.data()}, does not exist!")
		if not index.column() == 0:
			raise ValueError("Node column must be 0")

		self._index = QPersistentModelIndex(index)
		self._graph = graph

	def __eq__(self, value: object, /) -> bool:
		if isinstance(value, OutletRef):
			return self._index == value._index
		else:
			return False

	def __hash__(self) -> int:
		return hash(self._index)

	def isValid(self):
		return self._index.isValid() and self._index.column() == 0 and self._index.model() == self._graph._outletTable

	def __repr__(self) -> str:
		return f"{self.__class__.__name__}({self._index.row()},{self._index.column()})"


class GraphModel(QObject):
	nodesAdded = Signal(list) #List[NodeRef]
	nodesAboutToBeRemoved = Signal(list) #List[NodeRef]
	nodesDataChanged = Signal(list, list) #List[NodeRef], List[NodeDataColumn]

	inletsAdded = Signal(list) #List[InletRef]
	inletsAboutToBeRemoved = Signal(list) #List[InletRef]
	inletsDataChanged = Signal(list, list) #List[InletRef], List[InletDataColumn]

	outletsAdded = Signal(list) #List[OutletIndex]
	outletsAboutToBeRemoved = Signal(list) #List[OutletRef]
	outletsDataChanged = Signal(list, list) #List[OutletRef], List[OutletDataColumn]

	edgesAdded = Signal(list) #List[EdgeRef]
	edgesAboutToBeRemoved = Signal(list) #List[EdgeRef]
	edgesDataChanged = Signal(list, list) #List[EdgeRef], List[EdgeDataColumn]

	# class NodeDataColumn(IntEnum):
	# 	Id = 0
	# 	Name = 1
	# 	LocationX = 2
	# 	LocationY = 3
	# 	User = 4

	# class InletDataColumn(IntEnum):
	# 	Id = 0
	# 	Owner = 1
	# 	Name = 2
	# 	User = 3

	# class OutletDataColumn(IntEnum):
	# 	Id = 0
	# 	Owner = 1
	# 	Name = 2
	# 	User = 3

	# class EdgeDataColumn(IntEnum):
	# 	Id = 0
	# 	SourceOutlet =  1
	# 	TargetInlet = 2

	def __init__(self, parent=None):
		super().__init__(parent)
		### CREATE QT MODELS ###

		### Nodes Model ###
		self._nodeTable = QStandardItemModel()

		self._nodeTable.setHorizontalHeaderLabels([member.name for member in NodeAttribute])
		self._nodeTable.rowsInserted.connect(lambda parent, first, last:
			self.nodesAdded.emit([NodeRef(self._nodeTable.index(row, 0), self) for row in range(first, last+1)])
		)

		self._nodeTable.rowsAboutToBeRemoved.connect(lambda parent, first, last:
			self.nodesAboutToBeRemoved.emit([NodeRef(self._nodeTable.index(row, 0), self) for row in range(first, last+1)])
		)

		self._nodeTable.dataChanged.connect(lambda topLeft, bottomRight, roles:
			self.nodesDataChanged.emit(
				[NodeRef(self._nodeTable.index(row, 0), self) for row in range(topLeft.row(), bottomRight.row()+1)],
				None
			)
		)

		### Inlets Model ###
		self._inletTable = QStandardItemModel()
		self._inletTable.setHorizontalHeaderLabels([member.name for member in InletAttribute])
		self._inletTable.rowsInserted.connect(lambda parent, first, last:
			self.inletsAdded.emit([InletRef(self._inletTable.index(row, 0), self) for row in range(first, last+1)])
		)

		self._inletTable.rowsAboutToBeRemoved.connect(lambda parent, first, last:
			self.inletsAboutToBeRemoved.emit([InletRef(self._inletTable.index(row, 0), self) for row in range(first, last+1)])
		)

		self._inletTable.dataChanged.connect(lambda topLeft, bottomRight, roles:
			self.inletsDataChanged.emit(
				[InletRef(self._inletTable.index(row, 0), self) for row in range(topLeft.row(), bottomRight.row()+1)],
				roles
			)
		)

		### Outlets Model ###
		self._outletTable = QStandardItemModel()
		self._outletTable.setHorizontalHeaderLabels([member.name for member in OutletAttribute])
		self._outletTable.rowsInserted.connect(lambda parent, first, last:
			self.outletsAdded.emit([OutletRef(self._outletTable.index(row, 0), self) for row in range(first, last+1)])
		)

		self._outletTable.rowsAboutToBeRemoved.connect(lambda parent, first, last:
			self.outletsAboutToBeRemoved.emit([OutletRef(self._outletTable.index(row, 0), self) for row in range(first, last+1)])
		)

		self._outletTable.dataChanged.connect(lambda topLeft, bottomRight, roles:
			self.outletsDataChanged.emit(
				[OutletRef(self._outletTable.index(row, 0), self) for row in range(topLeft.row(), bottomRight.row()+1)],
				roles
			)
		)

		### Edges Model ###
		self._edgeTable = QStandardItemModel()
		self._edgeTable.setHorizontalHeaderLabels([member.name for member in EdgeAttribute])
		self._edgeTable.rowsInserted.connect(lambda parent, first, last:
			self.edgesAdded.emit([EdgeRef(self._edgeTable.index(row, 0), self) for row in range(first, last+1)])
		)

		self._edgeTable.rowsAboutToBeRemoved.connect(lambda parent, first, last:
			self.edgesAboutToBeRemoved.emit([EdgeRef(self._edgeTable.index(row, 0), self) for row in range(first, last+1)])
		)

		self._edgeTable.dataChanged.connect(lambda topLeft, bottomRight, roles:
			self.edgesDataChanged.emit(
				[EdgeRef(self._edgeTable.index(row, 0), self) for row in range(topLeft.row(), bottomRight.row()+1)],
				roles
			)
		)
		
	def getNodes(self)->Iterable[NodeRef]:
		for row in range(self._nodeTable.rowCount()):
			yield NodeRef(self._nodeTable.index(row, 0), self)

	def getEdges(self)->Iterable[EdgeRef]:
		for row in range(self._edgeTable.rowCount()):
			yield EdgeRef(self._edgeTable.index(row, 0), self)

	def nodeCount(self)->int:
		return self._nodeTable.rowCount()

	def inletCount(self)->int:
		return self._inletTable.rowCount()

	def outletCount(self)->int:
		return self._outletTable.rowCount()

	def edgeCount(self)->int:
		return self._edgeTable.rowCount()

	def addNode(self, name:str, posx:int, posy:int)->NodeRef:
		if not isinstance(name, str):
			raise TypeError(f"'name' must be s tring, got: '{name}'")
		if not isinstance(posx, int) or not isinstance(posy, int):
			raise TypeError(f"'posx and posy' must be s tring, got: '{posx}', '{posy}")

		id_item   = QStandardItem()
		id_item.setData(unique.make_unique_id(), Qt.ItemDataRole.DisplayRole)
		name_item = QStandardItem()
		name_item.setData(name, Qt.ItemDataRole.DisplayRole)
		posx_item = QStandardItem()
		posx_item.setData(int(posx), Qt.ItemDataRole.DisplayRole)
		posy_item = QStandardItem()
		posy_item.setData(int(posy), Qt.ItemDataRole.DisplayRole)

		self._nodeTable.appendRow([id_item, name_item, posx_item, posy_item])

		return NodeRef(self._nodeTable.indexFromItem(id_item), self)

	def addInlet(self, node:NodeRef, name:str)->InletRef:
		if not node.isValid():
			raise ValueError(f"Node {node._index.data()}, does not exist!")

		id_item    = QStandardItem()
		id_item.setData(unique.make_unique_id(), Qt.ItemDataRole.DisplayRole)
		owner_item = QStandardItem()
		owner_item.setData(self._nodeTable.data(node._index, Qt.ItemDataRole.DisplayRole), Qt.ItemDataRole.DisplayRole)
		name_item  = QStandardItem()
		name_item.setData(name, Qt.ItemDataRole.DisplayRole)
		
		self._inletTable.appendRow([id_item, owner_item, name_item])
		return InletRef(self._inletTable.indexFromItem(id_item), self)

	def addOutlet(self, node:NodeRef, name:str)->OutletRef:
		id_item    = QStandardItem()
		id_item.setData(unique.make_unique_id(), Qt.ItemDataRole.DisplayRole)
		owner_item = QStandardItem()
		owner_item.setData(self._nodeTable.data(node._index, Qt.ItemDataRole.DisplayRole), Qt.ItemDataRole.DisplayRole)
		name_item = QStandardItem()
		name_item.setData(name, Qt.ItemDataRole.DisplayRole)
		
		self._outletTable.appendRow([id_item, owner_item, name_item])
		return OutletRef(self._outletTable.indexFromItem(id_item), self)

	def addEdge(self, outlet:OutletRef, inlet:InletRef)->EdgeRef:
		if not outlet.isValid():
			raise ValueError(f"outlet '{outlet}'' does not exist")
		if not inlet.isValid():
			raise ValueError(f"inlet {inlet} does not exist")

		unique_id = unique.make_unique_id()
		outlet_id = self._outletTable.data(outlet._index, Qt.ItemDataRole.DisplayRole)
		inlet_id = self._inletTable.data(inlet._index, Qt.ItemDataRole.DisplayRole)
		assert isinstance(outlet_id, str)
		assert isinstance(inlet_id, str)
		assert isinstance(unique_id, str)

		id_item =        QStandardItem()
		id_item.setData(unique_id, Qt.ItemDataRole.DisplayRole)
		outlet_id_item = QStandardItem()
		outlet_id_item.setData(outlet_id, Qt.ItemDataRole.DisplayRole)
		inlet_id_item =  QStandardItem()

		inlet_id_item.setData(inlet_id, Qt.ItemDataRole.DisplayRole)

		self._edgeTable.appendRow([id_item, outlet_id_item, inlet_id_item])
		return EdgeRef(self._edgeTable.indexFromItem(id_item), self)

	def removeNodes(self, nodes_to_remove:List[NodeRef]):
		assert all( isinstance(node, NodeRef) for node in nodes_to_remove )
		assert all( node.isValid() for node in nodes_to_remove )

		# collect inlets to be removed
		inlets_to_remove = []
		for node in nodes_to_remove:
			node_inlets = self.getNodeInlets(node)
			inlets_to_remove+=node_inlets
		self.removeInlets(inlets_to_remove)

		outlets_to_remove = []
		for node in nodes_to_remove:
			node_outlets = self.getNodeOutlets(node)
			outlets_to_remove+=node_outlets
		self.removeOutlets(outlets_to_remove)


		for node in sorted(nodes_to_remove, key=lambda node:node._index.row(), reverse=True):
			self._nodeTable.removeRow(node._index.row())

	def removeOutlets(self, outlets_to_remove:List[OutletRef]):
		# collect edges to be removed
		assert all( isinstance(outlet, OutletRef) for outlet in outlets_to_remove )

		edges_to_remove = []
		for outlet in outlets_to_remove:
			outlet_edges = self.getOutletEdges(outlet)
			edges_to_remove+=outlet_edges
		self.removeEdges(edges_to_remove)

		for outlet in sorted(outlets_to_remove, key=lambda outlet: outlet._index.row(), reverse=True):
			self._outletTable.removeRow(outlet._index.row())

	def getOutletEdges(self, outlet:OutletRef)->List[EdgeRef]:
		assert isinstance(outlet, OutletRef) and outlet.isValid()
		
		outlet_id = self._outletTable.data(outlet._index)
		connected_edges = [EdgeRef(idx.siblingAtColumn(0), self) for idx in self._edgeTable.match(
			self._edgeTable.index(0, GraphModel.EdgeDataColumn.SourceOutlet), Qt.ItemDataRole.DisplayRole, outlet_id, 1, Qt.MatchFlag.MatchExactly
		)]
		return connected_edges

	def getInletEdges(self, inlet:InletRef)->List[EdgeRef]:
		assert isinstance(inlet, InletRef) and inlet.isValid()

		inlet_id = self._inletTable.data(inlet._index)
		connected_edges = [EdgeRef(idx.siblingAtColumn(0), self) for idx in self._edgeTable.match(
			self._edgeTable.index(0, GraphModel.EdgeDataColumn.TargetInlet), Qt.ItemDataRole.DisplayRole, inlet_id, 1, Qt.MatchFlag.MatchExactly
		)]
		return connected_edges

	def getOutletOwner(self, outlet: OutletRef)->NodeRef:
		assert isinstance(outlet, OutletRef) and outlet.isValid()

		node_id:str = self._outletTable.data(outlet._index.sibling(outlet._index.row(), GraphModel.OutletDataColumn.Owner), Qt.ItemDataRole.DisplayRole)
		owner_nodes = [NodeRef(index, self) for index in self._nodeTable.match(
			self._nodeTable.index(0, GraphModel.NodeDataColumn.Id), Qt.ItemDataRole.DisplayRole, node_id, 1, Qt.MatchFlag.MatchExactly
		)]
		assert len(owner_nodes)==1
		return owner_nodes[0]

	def removeInlets(self, inlets_to_remove:List[InletRef]):
		# collect edges to be removed
		assert all( isinstance(inlet, InletRef) for inlet in inlets_to_remove ), f"got: {inlets_to_remove}"
		assert all( inlet.isValid() for inlet in inlets_to_remove)

		edges_to_remove = []
		for inlet in inlets_to_remove:
			inlet_edges = self.getInletEdges(inlet)
			edges_to_remove+=inlet_edges
		self.removeEdges(edges_to_remove)

		for inlet in sorted(inlets_to_remove, key=lambda inlet: inlet._index.row(), reverse=True):
			self._inletTable.removeRow(inlet._index.row())

	def removeEdges(self, edges_to_remove:List[EdgeRef]):
		# Remove the rows from the GraphModel (starting from the last one, to avoid shifting indices)
		assert all( isinstance(edge, EdgeRef) for edge in edges_to_remove )

		for edge in sorted(edges_to_remove, key=lambda edge: edge._index.row(), reverse=True):
			self._edgeTable.removeRow(edge._index.row())

	def getNodeData(self, node:NodeRef, attr:NodeAttribute|str):
		assert isinstance(node, NodeRef) and node.isValid(), f"got: {node}"

		def findColumn(label)->int:
			for column in range(self._nodeTable.columnCount()):
				if self._nodeTable.horizontalHeaderItem(column).text() == label:
					return column
			raise KeyError(f"No '{label}' in node table")
		
		match attr:
			case NodeAttribute.Id:
				column = [self._nodeTable.horizontalHeaderItem(col).text() for col in range(self._nodeTable.columnCount())]
				return self._nodeTable.data(node._index.sibling(node._index.row(), findColumn(NodeAttribute.Id)), Qt.ItemDataRole.DisplayRole)
			case NodeAttribute.Name:
				return self._nodeTable.data(node._index.sibling(node._index.row(), findColumn(NodeAttribute.Name)), Qt.ItemDataRole.DisplayRole)
			case NodeAttribute.LocationX:
				return self._nodeTable.data(node._index.sibling(node._index.row(), findColumn(NodeAttribute.LocationX)), Qt.ItemDataRole.DisplayRole)
			case NodeAttribute.LocationY:
				return self._nodeTable.data(node._index.sibling(node._index.row(), findColumn(NodeAttribute.LocationY)), Qt.ItemDataRole.DisplayRole)
			case _:
				column = findColumn(attr)
				return self._nodeTable.data(node._index.sibling(node._index.row(), column), Qt.ItemDataRole.DisplayRole)


	def setNodeData(self, node:NodeRef, value, attr:NodeAttribute|str):
		assert isinstance(node, NodeRef) and node.isValid(), f"got: {node}"

		def findColumn(label)->int:
			for column in range(self._nodeTable.columnCount()):
				if self._nodeTable.horizontalHeaderItem(column).text() == label:
					return column
			raise KeyError(f"No '{label}' in node table")

		# self._nodeTable.blockSignals(True)
		columnsChanged = []
		match attr:
			case NodeAttribute.Id: #id
				assert isinstance(value, str)
				self._nodeTable.setData(node._index.sibling(node._index.row(), findColumn(NodeAttribute.Id)), value, Qt.ItemDataRole.DisplayRole)
			case NodeAttribute.Name: #name
				assert isinstance(value, str)
				self._nodeTable.setData(node._index.sibling(node._index.row(), findColumn(NodeAttribute.Name)), value, Qt.ItemDataRole.DisplayRole)
			case NodeAttribute.LocationX: #"posx":
				assert isinstance(value, int)
				self._nodeTable.setData(node._index.sibling(node._index.row(), findColumn(NodeAttribute.LocationX)), value, Qt.ItemDataRole.DisplayRole)
			case NodeAttribute.LocationY: #"posy":
				assert isinstance(value, int)
				self._nodeTable.setData(node._index.sibling(node._index.row(), findColumn(NodeAttribute.LocationY)), value, Qt.ItemDataRole.DisplayRole)
			case _:
				column = findColumn(attr)
				self._nodeTable.setData(node._index.sibling(node._index.row(), column), value, Qt.ItemDataRole.DisplayRole)


		# self._nodeTable.blockSignals(False)
		# for start, end in group_consecutive_numbers(columnsChanged):
		# 	self._nodeTable.dataChanged.emit(node.siblingAtColumn(start), node.siblingAtColumn(end))

	def getInletData(self, inlet:InletRef, attr:InletAttribute):
		assert isinstance(inlet, InletRef) and inlet.isValid()

		match attr:
			case InletAttribute.Id: #Id:
				return self._inletTable.data(inlet._index.sibling(inlet._index.row(), GraphModel.InletDataColumn.Id))
			case InletAttribute.Name: #Name
				return self._inletTable.data(inlet._index.sibling(inlet._index.row(), GraphModel.InletDataColumn.Name))
			case _:
				raise ValueError(f"cant get attribute for inlet: attribute column {attr} does not exist")

	def setInletData(self, inlet: InletRef, value, attr:InletAttribute):
		assert isinstance(inlet, InletRef) and inlet.isValid()

		match attr:
			case InletAttribute.Id: #Id:
				self._inletTable.setData(inlet._index.sibling(inlet._index.row(), GraphModel.InletDataColumn.Id), value, Qt.ItemDataRole.DisplayRole)
			case InletAttribute.Name: #Name
				self._inletTable.setData(inlet._index.sibling(inlet._index.row(), GraphModel.InletDataColumn.Name), value, Qt.ItemDataRole.DisplayRole)
			case _:
				raise ValueError(f"cant set attribute for inlet: attribute column {attr} does not exist")

	def getOutletData(self, outlet:OutletRef, attr:OutletAttribute):
		assert isinstance(outlet, OutletRef) and outlet.isValid()

		match attr:
			case OutletAttribute.Id: #Id
				return self._outletTable.data(outlet._index.sibling(outlet._index.row(), GraphModel.OutletDataColumn.Id), Qt.ItemDataRole.DisplayRole)
			case OutletAttribute.Name: #Name:
				return self._outletTable.data(outlet._index.sibling(outlet._index.row(), GraphModel.OutletDataColumn.Name), Qt.ItemDataRole.DisplayRole)
			case _:
				raise ValueError(f"cant get attribute for outlet: attribute column {attr} does not exist")

	def setOutletData(self, outlet: OutletRef, value, attr:OutletAttribute):
		assert isinstance(outlet, OutletRef) and outlet.isValid()

		match attr:
			case OutletAttribute.Id: #Id
				self._outletTable.setData(outlet._index.sibling(outlet._index.row(), GraphModel.OutletDataColumn.Id), value, Qt.ItemDataRole.DisplayRole)
			case OutletAttribute.Name: #Name
				self._outletTable.setData(outlet._index.sibling(outlet._index.row(), GraphModel.OutletDataColumn.Name), value, Qt.ItemDataRole.DisplayRole)
			case _:
				raise ValueError(f"cant get attribute for outlet: attribute column {attr} does not exist")

	def getEdgeData(self, edge:EdgeRef, attr:EdgeAttribute):
		assert isinstance(edge, EdgeRef)

		match attr:
			case GraphModel.EdgeDataColumn.Id: #Id
				return self._edgeTable.data(edge._index.sibling(edge._index.row(), GraphModel.EdgeDataColumn.Id), Qt.ItemDataRole.DisplayRole)
			case _:
				raise ValueError(f"cant get attribute for edge: attribute column {attr} does not exist")

	def setEdgeData(self, edge:EdgeRef, value, attr:EdgeAttribute):
		assert isinstance(edge, EdgeRef)

		match attr:
			case EdgeAttribute.Id: #Id
				if not isinstance(value, str):
					raise ValueError(f"id must be a string, got: {value}")
				return self._edgeTable.setData(edge._index.sibling(edge._index.row(), GraphModel.EdgeDataColumn.Id), value, Qt.ItemDataRole.DisplayRole)
			case _:
				raise ValueError(f"cant set attribute for edge: attribute column {attr} does not exist")

	def getNodeInlets(self, node:NodeRef)->List[InletRef]:
		assert isinstance(node, NodeRef)

		node_id = self._nodeTable.data(node._index.sibling(node._index.row(), GraphModel.NodeDataColumn.Id))
		inlets = [InletRef(idx.siblingAtColumn(0), self) for idx in self._inletTable.match(
			self._inletTable.index(0, GraphModel.InletDataColumn.Owner), Qt.ItemDataRole.DisplayRole, node_id, 1, Qt.MatchFlag.MatchExactly
		)]
		return inlets

	def getNodeOutlets(self, node:NodeRef)->List[OutletRef]:
		assert isinstance(node, NodeRef)

		node_id = self._nodeTable.data(node._index.sibling(node._index.row(), GraphModel.NodeDataColumn.Id))
		outlets = [OutletRef(idx.siblingAtColumn(GraphModel.OutletDataColumn.Id), self) for idx in self._outletTable.match(
			self._outletTable.index(0, GraphModel.OutletDataColumn.Owner), Qt.ItemDataRole.DisplayRole, node_id, 1, Qt.MatchFlag.MatchExactly
		)]
		return outlets

	def getInletOwner(self, inlet:InletRef)->NodeRef:
		assert isinstance(inlet, InletRef) and inlet.isValid()

		node_id:str = self._inletTable.data(inlet._index.sibling(inlet._index.row(), GraphModel.InletDataColumn.Owner), Qt.ItemDataRole.DisplayRole)
		owner_nodes = [NodeRef(idx.siblingAtColumn(GraphModel.NodeDataColumn.Id), self) for idx in self._nodeTable.match(
			self._nodeTable.index(0, GraphModel.NodeDataColumn.Id), Qt.ItemDataRole.DisplayRole, node_id, 1, Qt.MatchFlag.MatchExactly
		)]
		assert len(owner_nodes)==1
		return owner_nodes[0]

	def getEdgeSource(self, edge: EdgeRef)->OutletRef:
		assert isinstance(edge, EdgeRef)

		outlet_id:str = self._edgeTable.data(edge._index.sibling(edge._index.row(), GraphModel.EdgeDataColumn.SourceOutlet))
		source_outlets = [OutletRef(idx.siblingAtColumn(GraphModel.OutletDataColumn.Id), self) for idx in self._outletTable.match(
			self._outletTable.index(0, GraphModel.OutletDataColumn.Id), Qt.ItemDataRole.DisplayRole, outlet_id, 1, Qt.MatchFlag.MatchExactly
		)]
		assert len(source_outlets) == 1
		return source_outlets[0]

	def getEdgeTarget(self, edge:EdgeRef)->InletRef:
		assert isinstance(edge, EdgeRef)

		inlet_id:str = self._edgeTable.data(edge._index.sibling(edge._index.row(), GraphModel.EdgeDataColumn.TargetInlet), Qt.ItemDataRole.DisplayRole)
		assert isinstance(inlet_id, str), f"got: {inlet_id}"
		target_inlets = [InletRef(idx.siblingAtColumn(GraphModel.InletDataColumn.Id), self) for idx in self._inletTable.match(
			self._inletTable.index(0, GraphModel.InletDataColumn.Id), Qt.ItemDataRole.DisplayRole, inlet_id, 1, Qt.MatchFlag.MatchExactly
		)]
		assert len(target_inlets) == 1
		return target_inlets[0]

	def getSourceNodes(self, node:NodeRef):
		assert isinstance(node, NodeRef)
		assert node._index.model() == self._nodeTable
		assert node._index.column() == 0

		inlets = self.getNodeInlets(node)
		for inlet in inlets:
			for edge in self.getInletEdges(inlet):
				outlet = self.getEdgeSource(edge)
				yield self.getOutletOwner(outlet)

	def getTargetNodes(self, node:NodeRef):
		assert isinstance(node, NodeRef)
		assert node._index.model() == self._nodeTable
		assert node._index.column() == GraphModel.NodeDataColumn.Id

		outlets = self.getNodeOutlets(node)
		for outlet in outlets:
			for edge in self.getOutletEdges(outlet):
				inlet = self.getEdgeTarget(edge)
				yield self.getInletOwner(inlet)

	def rootRodes(self)->Iterable[NodeRef]:
		"""Yield all root nodes (nodes without outlets) in the graph."""
		def hasTargets(node:NodeRef):
			assert isinstance(node, NodeRef)
			assert node.isValid()
			return len(list(self.getTargetNodes(node))) > 0
		
		for node in self.getNodes():
			if not hasTargets(node):
				yield node

	def dfs(self)->Iterable[NodeRef]:
		"""Perform DFS starting from the root nodes and yield each node."""
		visited = set()  # Set to track visited nodes
		def dfs_visit(node:NodeRef):
			"""Recursive helper function to perform DFS."""
			assert isinstance(node, NodeRef)
			assert node.isValid()

			visited.add(node)
			yield node  # Yield the current node

			# Iterate through all adjacent edges from the current node
			for target_node in self.getSourceNodes(node):
				if target_node not in visited:  # Check if the target node has been visited
					yield from dfs_visit(target_node)  # Recursive call

		for start_node in self.rootRodes():
			if start_node not in visited:  # Check if the start node has been visited
				yield from dfs_visit(start_node)  # Start DFS from the start node
