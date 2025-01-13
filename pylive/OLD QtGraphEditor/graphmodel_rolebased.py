
"""
TODO
12. Potential Mislabeling in Signals
    The signals nodesDataChanged, inletsDataChanged, and others
    take a roles parameter but do not use it consistently.
    Ensure roles is propagated and processed as needed for
    clarity and debugging.


"""
from typing_extensions import NoDefault
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

from enum import IntEnum


class NodeDataRole(IntEnum):
	IdRole =       Qt.ItemDataRole.UserRole+1
	NameRole =     Qt.ItemDataRole.DisplayRole
	LocationRole = Qt.ItemDataRole.UserRole+2
	UserRole =     Qt.ItemDataRole.UserRole+3

class InletDataRole(IntEnum):
	IdRole =    Qt.ItemDataRole.UserRole+1
	OwnerRole = Qt.ItemDataRole.UserRole+2
	NameRole =  Qt.ItemDataRole.DisplayRole
	UserRole =  Qt.ItemDataRole.UserRole+3


class OutletDataRole(IntEnum):
	IdRole =    Qt.ItemDataRole.UserRole+1
	OwnerRole = Qt.ItemDataRole.UserRole+2
	NameRole =  Qt.ItemDataRole.DisplayRole

class EdgeDataRole(IntEnum):
	IdRole =    Qt.ItemDataRole.DisplayRole
	TargetInletIdRole = Qt.ItemDataRole.UserRole+2
	SourceOutletIdRole =  Qt.ItemDataRole.UserRole+3

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


class GraphModel(QObject):
	nodesAdded = Signal(list)
	nodesAboutToBeRemoved = Signal(list)
	nodesDataChanged = Signal(list, list)

	inletsAdded = Signal(list)
	inletsAboutToBeRemoved = Signal(list)
	inletsDataChanged = Signal(list, list)

	outletsAdded = Signal(list)
	outletsAboutToBeRemoved = Signal(list)
	outletsDataChanged = Signal(list, list)

	edgesAdded = Signal(list)
	edgesAboutToBeRemoved = Signal(list)
	edgesDataChanged = Signal(list, list)


	def __init__(self, parent=None):
		super().__init__(parent)
		### CREATE QT MODELS ###

		### Nodes Model ###
		self.nodeList = QStandardItemModel()
		self.nodeList.setHorizontalHeaderLabels(['name'])
		self.nodeList.rowsInserted.connect(lambda parent, first, last:
			self.nodesAdded.emit([NodeIndex(self.nodeList.index(row, 0)) for row in range(first, last+1)])
		)

		self.nodeList.rowsAboutToBeRemoved.connect(lambda parent, first, last:
			self.nodesAboutToBeRemoved.emit([NodeIndex(self.nodeList.index(row, 0)) for row in range(first, last+1)])
		)

		self.nodeList.dataChanged.connect(lambda topLeft, bottomRight, roles:
			self.nodesDataChanged.emit(
				[NodeIndex(self.nodeList.index(row, 0)) for row in range(topLeft.row(), bottomRight.row()+1)],
				roles
			)
		)

		### Inlets Model ###
		self.inletList = QStandardItemModel()
		self.inletList.setHorizontalHeaderLabels(["name"])
		self.inletList.rowsInserted.connect(lambda parent, first, last:
			self.inletsAdded.emit([InletIndex(self.inletList.index(row, 0)) for row in range(first, last+1)])
		)

		self.inletList.rowsAboutToBeRemoved.connect(lambda parent, first, last:
			self.inletsAboutToBeRemoved.emit([InletIndex(self.inletList.index(row, 0)) for row in range(first, last+1)])
		)

		self.inletList.dataChanged.connect(lambda topLeft, bottomRight, roles:
			self.inletsDataChanged.emit(
				[InletIndex(self.inletList.index(row, 0)) for row in range(topLeft.row(), bottomRight.row()+1)],
				roles
			)
		)

		### Outlets Model ###
		self.outletList = QStandardItemModel()
		self.outletList.setHorizontalHeaderLabels(["name"])
		self.outletList.rowsInserted.connect(lambda parent, first, last:
			self.outletsAdded.emit([OutletIndex(self.outletList.index(row, 0)) for row in range(first, last+1)])
		)

		self.outletList.rowsAboutToBeRemoved.connect(lambda parent, first, last:
			self.outletsAboutToBeRemoved.emit([OutletIndex(self.outletList.index(row, 0)) for row in range(first, last+1)])
		)

		self.outletList.dataChanged.connect(lambda topLeft, bottomRight, roles:
			self.outletsDataChanged.emit(
				[OutletIndex(self.outletList.index(row, 0)) for row in range(topLeft.row(), bottomRight.row()+1)],
				roles
			)
		)

		### Edges Model ###
		self.edgeList = QStandardItemModel()
		self.edgeList.setHorizontalHeaderLabels(["edge"])
		self.edgeList.rowsInserted.connect(lambda parent, first, last:
			self.edgesAdded.emit([EdgeIndex(self.edgeList.index(row, 0)) for row in range(first, last+1)])
		)

		self.edgeList.rowsAboutToBeRemoved.connect(lambda parent, first, last:
			self.edgesAboutToBeRemoved.emit([EdgeIndex(self.edgeList.index(row, 0)) for row in range(first, last+1)])
		)

		self.edgeList.dataChanged.connect(lambda topLeft, bottomRight, roles:
			self.edgesDataChanged.emit(
				[EdgeIndex(self.edgeList.index(row, 0)) for row in range(topLeft.row(), bottomRight.row()+1)],
				roles
			)
		)

	def getNodes(self)->Iterable[NodeIndex]:
		for row in range(self.nodeList.rowCount()):
			yield NodeIndex(self.nodeList.index(row, 0))

	def getInlets(self)->Iterable[InletIndex]:
		for row in range(self.inletList.rowCount()):
			yield InletIndex(self.inletList.index(row, 0))

	def getOutlets(self)->Iterable[OutletIndex]:
		for row in range(self.outletList.rowCount()):
			yield OutletIndex(self.outletList.index(row, 0))

	def getEdges(self)->Iterable[EdgeIndex]:
		for row in range(self.edgeList.rowCount()):
			yield EdgeIndex(self.edgeList.index(row, 0))

	def addNode(self, name:str, posx:int, posy:int)->NodeIndex:
		if not isinstance(name, str):
			raise TypeError(f"'name' must be s tring, got: '{name}'")
		if not isinstance(posx, int) or not isinstance(posy, int):
			raise TypeError(f"'posx and posy' must be s tring, got: '{posx}', '{posy}")

		node_item = QStandardItem()
		node_item.setData( unique.make_unique_id(), NodeDataRole.IdRole)
		node_item.setData( name, NodeDataRole.NameRole)
		node_item.setData( (posx, posy), NodeDataRole.LocationRole)

		self.nodeList.appendRow(node_item)

		return NodeIndex(self.nodeList.indexFromItem(node_item))

	def addInlet(self, node:NodeIndex, name:str)->InletIndex:
		if not node.isValid():
			raise ValueError(f"Node {node.data()}, does not exist!")

		inlet_item = QStandardItem()
		inlet_item.setData(unique.make_unique_id(), InletDataRole.IdRole)
		inlet_item.setData(node.data(NodeDataRole.IdRole), InletDataRole.OwnerRole)
		inlet_item.setData(name, InletDataRole.NameRole)
		
		self.inletList.appendRow(inlet_item)
		return InletIndex(self.inletList.indexFromItem(inlet_item))


	def addOutlet(self, node:NodeIndex, name:str)->OutletIndex:
		if not node.isValid():
			raise ValueError(f"Node {node.data()}, does not exist!")

		outlet_item = QStandardItem()
		outlet_item.setData(unique.make_unique_id(), OutletDataRole.IdRole)
		outlet_item.setData(node.data(NodeDataRole.IdRole), OutletDataRole.OwnerRole)
		outlet_item.setData(name, OutletDataRole.NameRole)
		
		self.outletList.appendRow(outlet_item)
		return OutletIndex(self.outletList.indexFromItem(outlet_item))

	def addEdge(self, outlet:OutletIndex, inlet:InletIndex)->EdgeIndex:
		if not outlet.isValid():
			raise ValueError(f"outlet '{outlet}'' does not exist")
		if not inlet.isValid():
			raise ValueError(f"inlet {inlet} does not exist")

		edge_item = QStandardItem()
		edge_item.setData(unique.make_unique_id(), EdgeDataRole.IdRole)
		inlet_id = self.inletList.data(inlet, InletDataRole.IdRole)
		edge_item.setData(inlet_id, EdgeDataRole.TargetInletIdRole)
		outlet_id = self.outletList.data(outlet, OutletDataRole.IdRole)
		edge_item.setData(outlet_id, EdgeDataRole.SourceOutletIdRole)

		self.edgeList.appendRow(edge_item)
		return EdgeIndex(self.edgeList.indexFromItem(edge_item))

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
			self.nodeList.removeRow(node.row())

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
			self.outletList.removeRow(outlet.row())

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
			self.inletList.removeRow(inlet.row())

	def removeEdges(self, edges_to_remove:List[EdgeIndex]):
		# Remove the rows from the GraphModel (starting from the last one, to avoid shifting indices)
		assert all( isinstance(edge, EdgeIndex) for edge in edges_to_remove )
		assert all( edge.column()==0 for edge in edges_to_remove )

		for edge in sorted(edges_to_remove, key=lambda edge: edge.row(), reverse=True):
			self.edgeList.removeRow(edge.row())

	def getNodeData(self, node:NodeIndex, role:NodeDataRole):
		assert isinstance(node, NodeIndex) and node.isValid(), f"got: {node}"
		assert node.column() == 0

		match role:
			case NodeDataRole.IdRole:
				return self.nodeList.data(node, NodeDataRole.IdRole)
			case NodeDataRole.NameRole:
				return self.nodeList.data(node, NodeDataRole.NameRole)
			case NodeDataRole.LocationRole:
				return self.nodeList.data(node, NodeDataRole.LocationRole)
			case _:
				return self.nodeList.data(node, role)

	def setNodeData(self, node:NodeIndex, value, role:NodeDataRole):
		assert isinstance(node, NodeIndex) and node.isValid(), f"got: {node}"
		assert node.column() == 0

		match role:
			case NodeDataRole.IdRole:
				assert isinstance(value, str)
				self.nodeList.setData(node, value, NodeDataRole.IdRole)
			case NodeDataRole.NameRole:
				assert isinstance(value, str)
				self.nodeList.setData(node, value, NodeDataRole.NameRole)
			case NodeDataRole.LocationRole:
				assert isinstance(value, tuple)
				self.nodeList.setData(node, value, NodeDataRole.LocationRole)
			case _:
				return self.nodeList.setData(node, role)

	def getInletData(self, inlet:InletIndex, role:InletDataRole):
		assert isinstance(inlet, InletIndex) and inlet.isValid()
		assert inlet.model() == self.inletList
		assert inlet.column() == 0

		match role:
			case InletDataRole.IdRole:
				return self.inletList.data(inlet, InletDataRole.IdRole)
			case InletDataRole.NameRole:
				return self.inletList.data(inlet, InletDataRole.NameRole)
			case _:
				return self.inletList.data(inlet, role)

	def setInletData(self, inlet: InletIndex, value, role:InletDataRole):
		assert isinstance(inlet, InletIndex) and inlet.isValid()
		assert inlet.model() == self.inletList
		assert inlet.column() == 0

		match role:
			case InletDataRole.IdRole:
				self.inletList.setData(inlet, value, role)
			case InletDataRole.NameRole:
				self.inletList.setData(inlet, value, role)
			case _:
				self.inletList.setData(inlet, value, role)

	def getOutletData(self, outlet:OutletIndex, role:OutletDataRole):
		assert isinstance(outlet, OutletIndex) and outlet.isValid()
		assert outlet.model() == self.outletList
		assert outlet.column() == 0

		match role:
			case OutletDataRole.IdRole:
				return self.outletList.data(outlet, OutletDataRole.IdRole)
			case OutletDataRole.NameRole:
				return self.outletList.data(outlet, OutletDataRole.NameRole)
			case _:
				return self.outletList.data(outlet, role)

	def setOutletData(self, outlet: OutletIndex, value, role:OutletDataRole):
		assert isinstance(outlet, OutletIndex) and outlet.isValid()
		assert outlet.model() == self.outletList
		assert outlet.column() == 0

		match role:
			case OutletDataRole.IdRole:
				self.outletList.setData(outlet, value, role)
			case OutletDataRole.NameRole:
				self.outletList.setData(outlet, value, role)
			case _:
				self.outletList.setData(outlet, value, role)

	def getEdgeData(self, edge:EdgeIndex, role:EdgeDataRole):
		assert isinstance(edge, EdgeIndex)
		assert edge.model() == self.edgeList
		assert edge.column() == 0

		match role:
			case EdgeDataRole.IdRole:
				return self.edgeList.data(edge, EdgeDataRole.IdRole)
			case _:
				return self.edgeList.data(edge, role)

	def setEdgeData(self, edge:EdgeIndex, value, role:EdgeDataRole):
		assert isinstance(edge, EdgeIndex)
		assert edge.model() == self.edgeList
		assert edge.column() == 0

		match role:
			case EdgeDataRole.IdRole:
				if not isinstance(value, str):
					raise ValueError(f"id must be a string, got: {value}")
				return self.edgeList.setData(edge, value, EdgeDataRole.IdRole)
			case _:
				return self.edgeList.setData(edge, value, role)

	def getNodeInlets(self, node:NodeIndex)->List[InletIndex]:
		assert isinstance(node, NodeIndex)
		assert node.model() == self.nodeList
		assert node.column() == 0

		node_id = self.nodeList.data(node, NodeDataRole.IdRole)
		inlets = [InletIndex(idx) for idx in self.inletList.match(
			self.inletList.index(0,0), InletDataRole.OwnerRole, node_id, 1, Qt.MatchFlag.MatchExactly
		)]
		return inlets

	def getNodeOutlets(self, node:NodeIndex)->List[OutletIndex]:
		assert isinstance(node, NodeIndex)
		assert node.model() == self.nodeList
		assert node.column() == 0

		node_id = self.nodeList.data(node, NodeDataRole.IdRole)
		outlets = [OutletIndex(idx) for idx in self.outletList.match(
			self.outletList.index(0,0), OutletDataRole.OwnerRole, node_id, 1, Qt.MatchFlag.MatchExactly
		)]
		return outlets

	def getInletOwner(self, inlet:InletIndex)->NodeIndex:
		assert isinstance(inlet, InletIndex) and inlet.isValid()
		assert inlet.model() == self.inletList
		assert inlet.column() == 0

		node_id:str = self.inletList.data(inlet, InletDataRole.OwnerRole)
		owner_nodes = [NodeIndex(index) for index in self.nodeList.match(
			self.nodeList.index(0,0), NodeDataRole.IdRole, node_id, 1, Qt.MatchFlag.MatchExactly
		)]
		assert len(owner_nodes)==1
		return owner_nodes[0]

	def setInletOwner(self, inlet:InletIndex, node:NodeIndex):
		assert isinstance(inlet, InletIndex) and inlet.isValid()
		assert inlet.model() == self.inletList
		assert inlet.column() == 0

		if not isinstance(node, NodeIndex):
			raise ValueError(f"Value must be a node, got: {node}")

		node_id:str = self.nodeList.data(node, NodeDataRole.IdRole)
		self.inletList.setData(inlet, node_id, InletDataRole.OwnerRole)

	def getInletEdges(self, inlet:InletIndex)->List[EdgeIndex]:
		assert isinstance(inlet, InletIndex) and inlet.isValid()
		assert inlet.model() == self.inletList
		assert inlet.column() == 0

		inlet_id = inlet.data(InletDataRole.IdRole)
		connected_edges = [EdgeIndex(idx) for idx in self.edgeList.match(
			self.edgeList.index(0,0), EdgeDataRole.TargetInletIdRole, inlet_id, 1, Qt.MatchFlag.MatchExactly
		)]
		return connected_edges

	def getOutletOwner(self, outlet: OutletIndex)->NodeIndex:
		assert isinstance(outlet, OutletIndex) and outlet.isValid()
		assert outlet.model() == self.outletList
		assert outlet.column() == 0

		node_id:str = outlet.data(OutletDataRole.OwnerRole)
		owner_nodes = [NodeIndex(index) for index in self.nodeList.match(
			self.nodeList.index(0,0), NodeDataRole.IdRole, node_id, 1, Qt.MatchFlag.MatchExactly
		)]
		assert len(owner_nodes)==1
		return owner_nodes[0]

	def setOutletOwner(self, outlet:OutletIndex, node:NodeIndex):
		assert isinstance(outlet, OutletIndex) and outlet.isValid()
		assert outlet.model() == self.outletList
		assert outlet.column() == 0

		if not isinstance(node, NodeIndex):
			raise ValueError(f"Value must be a node, got: {node}")

		node_id:str = self.nodeList.data(node, NodeDataRole.IdRole)
		self.outletList.setData(outlet, node_id, InletDataRole.OwnerRole)

	def getOutletEdges(self, outlet:OutletIndex)->List[EdgeIndex]:
		assert isinstance(outlet, OutletIndex) and outlet.isValid()
		assert outlet.model() == self.outletList
		assert outlet.column() == 0
		
		outlet_id = outlet.data(OutletDataRole.IdRole)
		connected_edges = [EdgeIndex(idx) for idx in self.edgeList.match(
			self.edgeList.index(0,0), EdgeDataRole.SourceOutletIdRole, outlet_id, 1, Qt.MatchFlag.MatchExactly
		)]
		return connected_edges

	def getEdgeSource(self, edge: EdgeIndex)->OutletIndex:
		assert isinstance(edge, EdgeIndex)
		assert edge.model() == self.edgeList
		assert edge.column() == 0

		outlet_id:str = edge.data(EdgeDataRole.SourceOutletIdRole)
		source_outlets = [OutletIndex(idx) for idx in self.outletList.match(
			self.outletList.index(0,0), OutletDataRole.IdRole, outlet_id, 1, Qt.MatchFlag.MatchExactly
		)]
		assert len(source_outlets) == 1
		return source_outlets[0]

	def setEdgeSource(self, edge:EdgeIndex, outlet:OutletIndex):
		assert isinstance(edge, EdgeIndex) and edge.isValid()
		assert edge.model() == self.edgeList
		assert edge.column() == 0

		if not isinstance(outlet, OutletIndex):
			raise ValueError(f"Value must be an outlet, got: {value}")

		outlet_id:str = self.outletList.data(outlet, OutletDataRole.IdRole)
		self.edgeList.setData(edge, outlet_id, EdgeDataRole.SourceOutletIdRole)

	def getEdgeTarget(self, edge:EdgeIndex)->InletIndex:
		assert isinstance(edge, EdgeIndex)
		assert edge.model() == self.edgeList
		assert edge.column() == 0

		inlet_id:str = self.edgeList.data(edge, EdgeDataRole.TargetInletIdRole)
		assert isinstance(inlet_id, str)
		target_inlets = [InletIndex(idx) for idx in self.inletList.match(
			self.inletList.index(0,0), InletDataRole.IdRole, inlet_id, 1, Qt.MatchFlag.MatchExactly
		)]
		assert len(target_inlets) == 1
		return target_inlets[0]

	def setEdgeTarget(self, edge:EdgeIndex, inlet:InletIndex):
		assert isinstance(edge, EdgeIndex) and edge.isValid()
		assert edge.model() == self.edgeList
		assert edge.column() == 0

		if not isinstance(inlet, InletIndex):
			raise ValueError(f"Value must be an inlet, got: {value}")

		inlet_id:str = self.inletList.data(inlet, InletDataRole.IdRole)
		assert isinstance(inlet_id, str)
		self.edgeList.setData(edge, inlet_id, EdgeDataRole.TargetInletIdRole)

	def getSourceNodes(self, node:NodeIndex):
		assert isinstance(node, NodeIndex)
		assert node.model() == self.nodeList
		assert node.column() == 0

		inlets = self.getNodeInlets(node)
		for inlet in inlets:
			for edge in self.getInletEdges(inlet):
				outlet = self.getEdgeSource(edge)
				yield self.getOutletOwner(outlet)

	def getTargetNodes(self, node:NodeIndex):
		assert isinstance(node, NodeIndex)
		assert node.model() == self.nodeList
		assert node.column() == 0

		outlets = self.getNodeOutlets(node)
		for outlet in outlets:
			for edge in self.getOutletEdges(outlet):
				inlet = self.getEdgeTarget(edge)
				yield self.getInletOwner(inlet)

	def rootRodes(self)->Iterable[NodeIndex]:
		"""Yield all root nodes (nodes without outlets) in the graph."""
		def hasTargets(node:NodeIndex):
			assert isinstance(node, NodeIndex)
			assert node.model() == self.nodeList
			assert node.column() == 0
			return len(list(self.getTargetNodes(node)))>0
		
		for row in range(self.nodeList.rowCount()):
			node = NodeIndex(self.nodeList.index(row, 0))
			if not hasTargets(node):
				yield node

	def dfs(self)->Iterable[NodeIndex]:
		"""Perform DFS starting from the root nodes and yield each node."""
		visited = set()  # Set to track visited nodes
		def dfs_visit(node:NodeIndex):
			"""Recursive helper function to perform DFS."""
			assert isinstance(node, NodeIndex)
			assert node.model() == self.nodeList
			assert node.column() == 0

			visited.add(node)
			yield node  # Yield the current node

			# Iterate through all adjacent edges from the current node
			for target_node in self.getSourceNodes(node):
				if target_node not in visited:  # Check if the target node has been visited
					yield from dfs_visit(target_node)  # Recursive call

		for start_node in self.rootRodes():
			if start_node not in visited:  # Check if the start node has been visited
				yield from dfs_visit(start_node)  # Start DFS from the start node