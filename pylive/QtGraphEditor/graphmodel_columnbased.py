from enum import IntEnum, StrEnum
from os import set_inheritable
from pylive import unique
import sys
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from typing import *

def group_consecutive_numbers(data):
	from itertools import groupby
	from operator import itemgetter

	ranges =[]

	for k,g in groupby(enumerate(data),lambda x:x[0]-x[1]):
		group = (map(itemgetter(1),g))
		group = list(map(int,group))
		ranges.append((group[0],group[-1]))
	return ranges

class NodeProperty(IntEnum):
	Id = 0
	Name = 1
	LocationX = 2
	LocationY = 3
	User = 4

class InletProperty(IntEnum):
	Id = 0
	Owner = 1
	Name = 2
	User = 3

class OutletProperty(IntEnum):
	Id = 0
	Owner = 1
	Name = 2
	User = 3

class EdgeProperty(IntEnum):
	Id = 0
	SourceOutlet =  1
	TargetInlet = 2


class NodeIndex(QPersistentModelIndex):
	def __repr__(self) -> str:
		return f"{self.__class__.__name__}({self.row()},{self.column()})"

class EdgeIndex(QPersistentModelIndex):
	def __repr__(self) -> str:
		return f"{self.__class__.__name__}({self.row()},{self.column()})"

class InletIndex(QPersistentModelIndex):
	def __repr__(self) -> str:
		return f"{self.__class__.__name__}({self.row()},{self.column()})"

class OutletIndex(QPersistentModelIndex):
	def __repr__(self) -> str:
		return f"{self.__class__.__name__}({self.row()},{self.column()})"


class NodeTableView(QAbstractItemModel):
	def __init__(self, parent: Optional[QObject] = None) -> None:
		super().__init__(parent)
		self._sourceModel = GraphModel()

	def sourceModel(self):
		return self._sourceModel

	def index(self, row:int, column:int, parent:QModelIndex|QPersistentModelIndex = QModelIndex())->QModelIndex:
		node = NodeIndex(self._sourceModel._nodeTable.index(row, 0))
		identification = (node, column)
		return self.createIndex(row, column, identification)	

	def parent(self, child:QModelIndex=QModelIndex())->QModelIndex|QObject: #type:ignore
		if child.isValid():
			return QModelIndex()
		else:
			return QObject.parent(self)

	def rowCount(self, parent:QModelIndex|QPersistentModelIndex=QModelIndex())->int:
		return self.sourceModel().nodeCount()

	def columnCount(self, parent:QModelIndex|QPersistentModelIndex=QModelIndex())->int:
		return 1

	def data(self, index:QModelIndex|QPersistentModelIndex, role=Qt.ItemDataRole.DisplayRole)->Any:
		match role:
			case Qt.ItemDataRole.DisplayRole:
				return "value"
			case Qt.ItemDataRole.ToolTipRole:
				pass
			case Qt.ItemDataRole.WhatsThisRole:
				pass

	# def setData(self, index, value, role=Qt.ItemDataRole.DisplayRole)->bool:
	# 	match role:
	# 		case Qt.ItemDataRole.DisplayRole:
	# 			return True
	# 		case Qt.ItemDataRole.ToolTipRole:
	# 			return True
	# 		case Qt.ItemDataRole.WhatsThisRole:
	# 			return True
	# 	return False

	# def flags(self, index:QModelIndex|QPersistentModelIndex=QModelIndex())->Qt.ItemFlag:
	# 	return Qt.ItemFlag.ItemIsEditable

	# def hasChildren(self, parent: Union[QModelIndex, QPersistentModelIndex]=QModelIndex()) -> bool:
	# 	return False

	# def insertRows(self, row:int, count:int, parent:QModelIndex|QPersistentModelIndex=QModelIndex())->bool:
	# 	self.beginInsertRows(parent, row, row+count)
	# 	self.endInsertRows()
	# 	return True



class GraphModel(QObject):
	nodesAdded = Signal(list) #List[NodeIndex]
	nodesAboutToBeRemoved = Signal(list) #List[NodeIndex]
	nodesDataChanged = Signal(list, list) #List[NodeIndex], List[NodeProperty]

	inletsAdded = Signal(list) #List[InletIndex]
	inletsAboutToBeRemoved = Signal(list) #List[InletIndex]
	inletsDataChanged = Signal(list, list) #List[InletIndex], List[InletProperty]

	outletsAdded = Signal(list) #List[OutletIndex]
	outletsAboutToBeRemoved = Signal(list) #List[OutletIndex]
	outletsDataChanged = Signal(list, list) #List[OutletIndex], List[OutletProperty]

	edgesAdded = Signal(list) #List[EdgeIndex]
	edgesAboutToBeRemoved = Signal(list) #List[EdgeIndex]
	edgesDataChanged = Signal(list, list) #List[EdgeIndex], List[EdgeProperty]

	def __init__(self, parent=None):
		super().__init__(parent)
		### CREATE QT MODELS ###

		m = QStandardItemModel()
		m.parent()
		m.setData()

		### Nodes Model ###
		self._nodeTable = QStandardItemModel()

		self._nodeTable.setHorizontalHeaderLabels(NodeProperty._member_names_)
		self._nodeTable.rowsInserted.connect(lambda parent, first, last:
			self.nodesAdded.emit([NodeIndex(self._nodeTable.index(row, 0)) for row in range(first, last+1)])
		)

		self._nodeTable.rowsAboutToBeRemoved.connect(lambda parent, first, last:
			self.nodesAboutToBeRemoved.emit([NodeIndex(self._nodeTable.index(row, 0)) for row in range(first, last+1)])
		)

		self._nodeTable.dataChanged.connect(lambda topLeft, bottomRight, roles:
			self.nodesDataChanged.emit(
				[NodeIndex(self._nodeTable.index(row, 0)) for row in range(topLeft.row(), bottomRight.row()+1)],
				roles
			)
		)

		### Inlets Model ###
		self._inletTable = QStandardItemModel()
		self._inletTable.setHorizontalHeaderLabels(InletProperty._member_names_)
		self._inletTable.rowsInserted.connect(lambda parent, first, last:
			self.inletsAdded.emit([InletIndex(self._inletTable.index(row, 0)) for row in range(first, last+1)])
		)

		self._inletTable.rowsAboutToBeRemoved.connect(lambda parent, first, last:
			self.inletsAboutToBeRemoved.emit([InletIndex(self._inletTable.index(row, 0)) for row in range(first, last+1)])
		)

		self._inletTable.dataChanged.connect(lambda topLeft, bottomRight, roles:
			self.inletsDataChanged.emit(
				[InletIndex(self._inletTable.index(row, 0)) for row in range(topLeft.row(), bottomRight.row()+1)],
				roles
			)
		)

		### Outlets Model ###
		self._outletTable = QStandardItemModel()
		self._outletTable.setHorizontalHeaderLabels(OutletProperty._member_names_)
		self._outletTable.rowsInserted.connect(lambda parent, first, last:
			self.outletsAdded.emit([OutletIndex(self._outletTable.index(row, 0)) for row in range(first, last+1)])
		)

		self._outletTable.rowsAboutToBeRemoved.connect(lambda parent, first, last:
			self.outletsAboutToBeRemoved.emit([OutletIndex(self._outletTable.index(row, 0)) for row in range(first, last+1)])
		)

		self._outletTable.dataChanged.connect(lambda topLeft, bottomRight, roles:
			self.outletsDataChanged.emit(
				[OutletIndex(self._outletTable.index(row, 0)) for row in range(topLeft.row(), bottomRight.row()+1)],
				roles
			)
		)

		### Edges Model ###
		self._edgeTable = QStandardItemModel()
		self._edgeTable.setHorizontalHeaderLabels(EdgeProperty._member_names_)
		self._edgeTable.rowsInserted.connect(lambda parent, first, last:
			self.edgesAdded.emit([EdgeIndex(self._edgeTable.index(row, 0)) for row in range(first, last+1)])
		)

		self._edgeTable.rowsAboutToBeRemoved.connect(lambda parent, first, last:
			self.edgesAboutToBeRemoved.emit([EdgeIndex(self._edgeTable.index(row, 0)) for row in range(first, last+1)])
		)

		self._edgeTable.dataChanged.connect(lambda topLeft, bottomRight, roles:
			self.edgesDataChanged.emit(
				[EdgeIndex(self._edgeTable.index(row, 0)) for row in range(topLeft.row(), bottomRight.row()+1)],
				roles
			)
		)

	def getNodes(self)->Iterable[NodeIndex]:
		for row in range(self._nodeTable.rowCount()):
			yield NodeIndex(self._nodeTable.index(row, 0))

	def getInlets(self)->Iterable[InletIndex]:
		for row in range(self._inletTable.rowCount()):
			yield InletIndex(self._inletTable.index(row, 0))

	def getOutlets(self)->Iterable[OutletIndex]:
		for row in range(self._outletTable.rowCount()):
			yield OutletIndex(self._outletTable.index(row, 0))

	def getEdges(self)->Iterable[EdgeIndex]:
		for row in range(self._edgeTable.rowCount()):
			yield EdgeIndex(self._edgeTable.index(row, 0))

	def nodeCount(self)->int:
		return self._nodeTable.rowCount()

	def inletCount(self)->int:
		return self._inletTable.rowCount()

	def outletCount(self)->int:
		return self._outletTable.rowCount()

	def edgeCount(self)->int:
		return self._edgeTable.rowCount()

	def addNode(self, name:str, posx:int, posy:int)->NodeIndex:
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

		return NodeIndex(self._nodeTable.indexFromItem(id_item))

	def addInlet(self, node:NodeIndex, name:str)->InletIndex:
		if not node.isValid():
			raise ValueError(f"Node {node.data()}, does not exist!")
		if not node.column() == 0:
			raise ValueError("Node column must be 0")

		id_item    = QStandardItem()
		id_item.setData(unique.make_unique_id(), Qt.ItemDataRole.DisplayRole)
		owner_item = QStandardItem()
		owner_item.setData(node.data(), Qt.ItemDataRole.DisplayRole)
		name_item  = QStandardItem()
		name_item.setData(name, Qt.ItemDataRole.DisplayRole)
		
		self._inletTable.appendRow([id_item, owner_item, name_item])
		return InletIndex(self._inletTable.indexFromItem(id_item))

	def addOutlet(self, node:NodeIndex, name:str)->OutletIndex:
		if not node.isValid():
			raise ValueError(f"Node {node.data()}, does not exist!")
		if not node.column() == 0:
			raise ValueError("Node column must be 0")

		id_item    = QStandardItem()
		id_item.setData(unique.make_unique_id(), Qt.ItemDataRole.DisplayRole)
		owner_item = QStandardItem()
		owner_item.setData(node.data(), Qt.ItemDataRole.DisplayRole)
		name_item  = QStandardItem()
		name_item.setData(name, Qt.ItemDataRole.DisplayRole)
		
		self._outletTable.appendRow([id_item, owner_item, name_item])
		return OutletIndex(self._outletTable.indexFromItem(id_item))

	def addEdge(self, outlet:OutletIndex, inlet:InletIndex)->EdgeIndex:
		if not outlet.isValid():
			raise ValueError(f"outlet '{outlet}'' does not exist")
		if not inlet.isValid():
			raise ValueError(f"inlet {inlet} does not exist")
		if outlet.column() != 0:
			raise ValueError(f"outlet column must be 0")
		if inlet.column() !=0:
			raise ValueError(f"inlet column must be 0")

		id_item =        QStandardItem(unique.make_unique_id())
		outlet_id_item = QStandardItem(outlet.data())
		inlet_id_item =  QStandardItem(inlet.data())

		self._edgeTable.appendRow([id_item, outlet_id_item, inlet_id_item])
		return EdgeIndex(self._edgeTable.indexFromItem(id_item))

	def removeNodes(self, nodes_to_remove:List[NodeIndex]):
		assert all( isinstance(node, NodeIndex) for node in nodes_to_remove )
		assert all( node.column() == 0 for node in nodes_to_remove)

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

		for node in sorted(nodes_to_remove, key=lambda node:node.row(), reverse=True):
			self._nodeTable.removeRow(node.row())

	def removeOutlets(self, outlets_to_remove:List[OutletIndex]):
		# collect edges to be removed
		assert all( isinstance(outlet, OutletIndex) for outlet in outlets_to_remove )
		assert all( outlet.column()==0 for outlet in outlets_to_remove )

		edges_to_remove = []
		for outlet in outlets_to_remove:
			outlet_edges = self.getOutletEdges(outlet)
			edges_to_remove+=outlet_edges
		self.removeEdges(edges_to_remove)

		for outlet in sorted(outlets_to_remove, key=lambda outlet: outlet.row(), reverse=True):
			self._outletTable.removeRow(outlet.row())

	def getOutletEdges(self, outlet:OutletIndex)->List[EdgeIndex]:
		assert isinstance(outlet, OutletIndex) and outlet.isValid()
		assert outlet.model() == self._outletTable
		assert outlet.column() == 0
		
		outlet_id = outlet.data()
		connected_edges = [EdgeIndex(idx.siblingAtColumn(0)) for idx in self._edgeTable.match(
			self._edgeTable.index(0,EdgeProperty.SourceOutlet), Qt.ItemDataRole.DisplayRole, outlet_id, 1, Qt.MatchFlag.MatchExactly
		)]
		return connected_edges

	def getInletEdges(self, inlet:InletIndex)->List[EdgeIndex]:
		assert isinstance(inlet, InletIndex) and inlet.isValid()
		assert inlet.model() == self._inletTable
		assert inlet.column() == 0

		inlet_id = inlet.data()
		connected_edges = [EdgeIndex(idx.siblingAtColumn(0)) for idx in self._edgeTable.match(
			self._edgeTable.index(0,EdgeProperty.TargetInlet), Qt.ItemDataRole.DisplayRole, inlet_id, 1, Qt.MatchFlag.MatchExactly
		)]
		return connected_edges

	def getOutletOwner(self, outlet: OutletIndex)->NodeIndex:
		assert isinstance(outlet, OutletIndex) and outlet.isValid()
		assert outlet.model() == self._outletTable
		assert outlet.column() == 0

		node_id:str = self._outletTable.data(outlet.sibling(outlet.row(), OutletProperty.Owner), Qt.ItemDataRole.DisplayRole)
		owner_nodes = [NodeIndex(index) for index in self._nodeTable.match(
			self._nodeTable.index(0, NodeProperty.Id), Qt.ItemDataRole.DisplayRole, node_id, 1, Qt.MatchFlag.MatchExactly
		)]
		assert len(owner_nodes)==1
		return owner_nodes[0]

	def setOutletOwner(self, outlet:OutletIndex, node:NodeIndex):
		assert isinstance(outlet, OutletIndex) and outlet.isValid()
		assert outlet.model() == self._outletTable
		assert outlet.column() == 0

		if not isinstance(node, NodeIndex):
			raise ValueError(f"Value must be a node, got: {node}")

		node_id:str = self._nodeTable.data(node.sibling(node.row(), NodeProperty.Id), Qt.ItemDataRole.DisplayRole)
		self._outletTable.setData(outlet.sibling(outlet.row(), OutletProperty.Owner), node_id, Qt.ItemDataRole.DisplayRole)


	def removeInlets(self, inlets_to_remove:List[InletIndex]):
		# collect edges to be removed
		assert all( isinstance(inlet, InletIndex) for inlet in inlets_to_remove ), f"got: {inlets_to_remove}"
		assert all( inlet.column()==0 for inlet in inlets_to_remove)

		edges_to_remove = []
		for inlet in inlets_to_remove:
			inlet_edges = self.getInletEdges(inlet)
			edges_to_remove+=inlet_edges
		self.removeEdges(edges_to_remove)

		for inlet in sorted(inlets_to_remove, key=lambda inlet: inlet.row(), reverse=True):
			self._inletTable.removeRow(inlet.row())

	def removeEdges(self, edges_to_remove:List[EdgeIndex]):
		# Remove the rows from the GraphModel (starting from the last one, to avoid shifting indices)
		assert all( isinstance(edge, EdgeIndex) for edge in edges_to_remove )
		rows_to_remove = set([edge.row() for edge in edges_to_remove]) # keep unique rows
		for row in sorted(rows_to_remove, reverse=True):
			self._edgeTable.removeRow(row)

	def getNodeData(self, node:NodeIndex, propertyId:NodeProperty):
		assert isinstance(node, NodeIndex) and node.isValid(), f"got: {node}"
		assert node.column() == 0

		match propertyId:
			case NodeProperty.Id:
				return self._nodeTable.data(node.sibling(node.row(), propertyId), Qt.ItemDataRole.DisplayRole)
			case NodeProperty.Name:
				return self._nodeTable.data(node.sibling(node.row(), propertyId), Qt.ItemDataRole.DisplayRole)
			case NodeProperty.LocationX:
				return self._nodeTable.data(node.sibling(node.row(), propertyId), Qt.ItemDataRole.DisplayRole)
			case NodeProperty.LocationY:
				return self._nodeTable.data(node.sibling(node.row(), propertyId), Qt.ItemDataRole.DisplayRole)
			case _:
				return self._nodeTable.data(node.sibling(node.row(), propertyId), Qt.ItemDataRole.DisplayRole)

	def setNodeData(self, node:NodeIndex, value, propertyId:NodeProperty):
		assert isinstance(node, NodeIndex) and node.isValid(), f"got: {node}"
		assert node.column() == 0
		# self._nodeTable.blockSignals(True)
		columnsChanged = []
		match propertyId:
			case NodeProperty.Id: #id
				assert isinstance(value, str)
				self._nodeTable.setData(node.sibling(node.row(), propertyId), value, Qt.ItemDataRole.DisplayRole)
			case NodeProperty.Name: #name
				assert isinstance(value, str)
				self._nodeTable.setData(node.sibling(node.row(), propertyId), value, Qt.ItemDataRole.DisplayRole)
			case NodeProperty.LocationX: #"posx":
				assert isinstance(value, int)
				self._nodeTable.setData(node.sibling(node.row(), propertyId), value, Qt.ItemDataRole.DisplayRole)
			case NodeProperty.LocationY: #"posy":
				assert isinstance(value, int)
				self._nodeTable.setData(node.sibling(node.row(), propertyId), value, Qt.ItemDataRole.DisplayRole)
			case _:
				self._nodeTable.setData(node.sibling(node.row(), propertyId), value, Qt.ItemDataRole.DisplayRole)
			
		# self._nodeTable.blockSignals(False)
		# for start, end in group_consecutive_numbers(columnsChanged):
		# 	self._nodeTable.dataChanged.emit(node.siblingAtColumn(start), node.siblingAtColumn(end))

	def getInletData(self, inlet:InletIndex, propertyId:InletProperty):
		assert isinstance(inlet, InletIndex) and inlet.isValid()
		assert inlet.model() == self._inletTable
		assert inlet.column() == 0

		match propertyId:
			case InletProperty.Id: #Id:
				return self._inletTable.data(inlet.sibling(inlet.row(), propertyId))
			case InletProperty.Name: #Name
				return self._inletTable.data(inlet.sibling(inlet.row(), propertyId))
			case _:
				return self._inletTable.data(inlet.sibling(inlet.row(), propertyId))

	def setInletData(self, inlet: InletIndex, value, propertyId:InletProperty):
		assert isinstance(inlet, InletIndex) and inlet.isValid()
		assert inlet.model() == self._outletTable
		assert inlet.column() == 0

		match propertyId:
			case InletProperty.Id: #Id:
				self._outletTable.setData(inlet.sibling(inlet.row(), propertyId), value, Qt.ItemDataRole.DisplayRole)
			case InletProperty.Name: #Name
				self._outletTable.setData(inlet.sibling(inlet.row(), propertyId), value, Qt.ItemDataRole.DisplayRole)
			case _:
				self._outletTable.setData(inlet.sibling(inlet.row(), propertyId), value, Qt.ItemDataRole.DisplayRole)

	def getOutletData(self, outlet:OutletIndex, propertyId:OutletProperty):
		assert isinstance(outlet, OutletIndex) and outlet.isValid()
		assert outlet.model() == self._outletTable
		assert outlet.column() == 0

		match propertyId:
			case OutletProperty.Id: #Id
				return self._outletTable.data(outlet.sibling(outlet.row(), propertyId), Qt.ItemDataRole.DisplayRole)
			case OutletProperty.Name: #Name:
				return self._outletTable.data(outlet.sibling(outlet.row(), propertyId), Qt.ItemDataRole.DisplayRole)
			case _:
				return self._outletTable.data(outlet.sibling(outlet.row(), propertyId), Qt.ItemDataRole.DisplayRole)

	def setOutletData(self, outlet: OutletIndex, value, propertyId:OutletProperty):
		assert isinstance(outlet, OutletIndex) and outlet.isValid()
		assert outlet.model() == self._outletTable
		assert outlet.column() == 0

		match propertyId:
			case OutletProperty.Id: #Id
				self._outletTable.setData(outlet.sibling(outlet.row(), propertyId), value, Qt.ItemDataRole.DisplayRole)
			case OutletProperty.Name: #Name
				self._outletTable.setData(outlet.sibling(outlet.row(), propertyId), value, Qt.ItemDataRole.DisplayRole)
			case _:
				self._outletTable.setData(outlet.sibling(outlet.row(), propertyId), value, Qt.ItemDataRole.DisplayRole)

	def getEdgeData(self, edge:EdgeIndex, propertyId:EdgeProperty):
		assert isinstance(edge, EdgeIndex)
		assert edge.model() == self._edgeTable
		assert edge.column() == 0

		match propertyId:
			case EdgeProperty.Id: #Id
				return self._edgeTable.data(edge.sibling(edge.row(), propertyId), Qt.ItemDataRole.DisplayRole)
			case _:
				return self._edgeTable.data(edge.sibling(edge.row(), propertyId), Qt.ItemDataRole.DisplayRole)

	def setEdgeData(self, edge:EdgeIndex, value, propertyId:EdgeProperty):
		assert isinstance(edge, EdgeIndex)
		assert edge.model() == self._edgeTable
		assert edge.column() == 0

		match propertyId:
			case EdgeProperty.Id: #Id
				if not isinstance(value, str):
					raise ValueError(f"id must be a string, got: {value}")
				return self._edgeTable.setData(edge.sibling(edge.row(), propertyId), value, Qt.ItemDataRole.DisplayRole)
			case _:
				return self._edgeTable.setData(edge.sibling(edge.row(), propertyId), value, Qt.ItemDataRole.DisplayRole)

	def getNodeInlets(self, node:NodeIndex)->List[InletIndex]:
		assert isinstance(node, NodeIndex)
		assert node.model() == self._nodeTable
		assert node.column() == 0

		node_id = self._nodeTable.data(node.sibling(node.row(), NodeProperty.Id))
		inlets = [InletIndex(idx.siblingAtColumn(0)) for idx in self._inletTable.match(
			self._inletTable.index(0,InletProperty.Owner), Qt.ItemDataRole.DisplayRole, node_id, 1, Qt.MatchFlag.MatchExactly
		)]
		return inlets

	def getNodeOutlets(self, node:NodeIndex)->List[OutletIndex]:
		assert isinstance(node, NodeIndex)
		assert node.model() == self._nodeTable
		assert node.column() == 0

		node_id = self._nodeTable.data(node.sibling(node.row(), NodeProperty.Id))
		outlets = [OutletIndex(idx.siblingAtColumn(OutletProperty.Id)) for idx in self._outletTable.match(
			self._outletTable.index(0, OutletProperty.Owner), Qt.ItemDataRole.DisplayRole, node_id, 1, Qt.MatchFlag.MatchExactly
		)]
		return outlets

	def getInletOwner(self, inlet:InletIndex)->NodeIndex:
		assert isinstance(inlet, InletIndex) and inlet.isValid()
		assert inlet.model() == self._inletTable
		assert inlet.column() == InletProperty.Id

		node_id:str = self._inletTable.data(inlet.sibling(inlet.row(), InletProperty.Owner), Qt.ItemDataRole.DisplayRole)
		owner_nodes = [NodeIndex(idx.siblingAtColumn(NodeProperty.Id)) for idx in self._nodeTable.match(
			self._nodeTable.index(0,NodeProperty.Id), Qt.ItemDataRole.DisplayRole, node_id, 1, Qt.MatchFlag.MatchExactly
		)]
		assert len(owner_nodes)==1
		return owner_nodes[0]

	def getEdgeSource(self, edge: EdgeIndex)->OutletIndex:
		assert isinstance(edge, EdgeIndex)
		assert edge.model() == self._edgeTable
		assert edge.column() == 0

		outlet_id:str = self._edgeTable.data(edge.sibling(edge.row(), EdgeProperty.SourceOutlet))
		source_outlets = [OutletIndex(idx.siblingAtColumn(OutletProperty.Id)) for idx in self._outletTable.match(
			self._outletTable.index(0, OutletProperty.Id), Qt.ItemDataRole.DisplayRole, outlet_id, 1, Qt.MatchFlag.MatchExactly
		)]
		assert len(source_outlets) == 1
		return source_outlets[0]

	def setEdgeSource(self, edge:EdgeIndex, outlet:OutletIndex):
		assert isinstance(edge, EdgeIndex) and edge.isValid()
		assert edge.model() == self._edgeTable
		assert edge.column() == 0

		if not isinstance(outlet, OutletIndex):
			raise ValueError(f"Value must be an outlet, got: {value}")

		outlet_id:str = self._outletTable.data(outlet.sibling(outlet.row(), OutletProperty.Id), Qt.ItemDataRole.DisplayRole)
		self._edgeTable.setData(edge.sibling(edge.row(), EdgeProperty.SourceOutlet), outlet_id,  Qt.ItemDataRole.DisplayRole)

	def getEdgeTarget(self, edge:EdgeIndex)->InletIndex:
		assert isinstance(edge, EdgeIndex)
		assert edge.model() == self._edgeTable
		assert edge.column() == EdgeProperty.Id

		inlet_id:str = self._edgeTable.data(edge.sibling(edge.row(), EdgeProperty.TargetInlet), Qt.ItemDataRole.DisplayRole)
		assert isinstance(inlet_id, str)
		target_inlets = [InletIndex(idx.siblingAtColumn(InletProperty.Id)) for idx in self._inletTable.match(
			self._inletTable.index(0,InletProperty.Id), Qt.ItemDataRole.DisplayRole, inlet_id, 1, Qt.MatchFlag.MatchExactly
		)]
		assert len(target_inlets) == 1
		return target_inlets[0]

	def setEdgeTarget(self, edge:EdgeIndex, inlet:InletIndex):
		assert isinstance(edge, EdgeIndex) and edge.isValid()
		assert edge.model() == self._edgeTable
		assert edge.column() == 0

		if not isinstance(inlet, InletIndex):
			raise ValueError(f"Value must be an inlet, got: {value}")

		inlet_id:str = self._inletTable.data(inlet.sibling(inlet.row(), InletProperty.Id), Qt.ItemDataRole.DisplayRole)
		assert isinstance(inlet_id, str)
		self._edgeTable.setData(edge.sibling(edge.row(), EdgeProperty.TargetInlet), inlet_id, Qt.ItemDataRole.DisplayRole)

	def getSourceNodes(self, node:NodeIndex):
		assert isinstance(node, NodeIndex)
		assert node.model() == self._nodeTable
		assert node.column() == 0

		inlets = self.getNodeInlets(node)
		for inlet in inlets:
			for edge in self.getInletEdges(inlet):
				outlet = self.getEdgeSource(edge)
				yield self.getOutletOwner(outlet)

	def getTargetNodes(self, node:NodeIndex):
		assert isinstance(node, NodeIndex)
		assert node.model() == self._nodeTable
		assert node.column() == NodeProperty.Id

		outlets = self.getNodeOutlets(node)
		for outlet in outlets:
			for edge in self.getOutletEdges(outlet):
				inlet = self.getEdgeTarget(edge)
				yield self.getInletOwner(inlet)

	def rootRodes(self)->Iterable[NodeIndex]:
		"""Yield all root nodes (nodes without outlets) in the graph."""
		def hasTargets(node:NodeIndex):
			assert isinstance(node, NodeIndex)
			assert node.model() == self._nodeTable
			assert node.column() == 0
			return len(list(self.getTargetNodes(node)))>0
		
		for row in range(self._nodeTable.rowCount()):
			node = NodeIndex(self._nodeTable.index(row, NodeProperty.Id))
			if not hasTargets(node):
				yield node

	def dfs(self)->Iterable[NodeIndex]:
		"""Perform DFS starting from the root nodes and yield each node."""
		visited = set()  # Set to track visited nodes
		def dfs_visit(node:NodeIndex):
			"""Recursive helper function to perform DFS."""
			assert isinstance(node, NodeIndex)
			assert node.model() == self._nodeTable
			assert node.column() == NodeProperty.Id

			visited.add(node)
			yield node  # Yield the current node

			# Iterate through all adjacent edges from the current node
			for target_node in self.getSourceNodes(node):
				if target_node not in visited:  # Check if the target node has been visited
					yield from dfs_visit(target_node)  # Recursive call

		for start_node in self.rootRodes():
			if start_node not in visited:  # Check if the start node has been visited
				yield from dfs_visit(start_node)  # Start DFS from the start node