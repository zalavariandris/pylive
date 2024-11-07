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

class NodeIndex(QModelIndex):
	pass

class EdgeIndex(QModelIndex):
	pass

class InletIndex(QModelIndex):
	pass

class OutletIndex(QModelIndex):
	pass


class GraphModel(QObject):
	# nodesInserted = Signal(QModelIndex, int, int)
	# nodesRemoved = Signal(QModelIndex, int, int)
	# nodesAboutToBeRemoved = Signal(QModelIndex, int, int)
	# nodesChanged = Signal(QModelIndex, QModelIndex, List[int])

	# outletsInserted = Signal(QModelIndex, int, int)
	# outletsRemoved = Signal(QModelIndex, int, int)
	# outletsAboutToBeRemoved = Signal(QModelIndex, int, int)
	# outletsChanged = Signal(QModelIndex, QModelIndex, List[int])

	# inletsInserted = Signal(QModelIndex, int, int)
	# inletsRemoved = Signal(QModelIndex, int, int)
	# inletsAboutToBeRemoved = Signal(QModelIndex, int, int)
	# inletsChanged = Signal(QModelIndex, QModelIndex, List[int])

	# edgesInserted = Signal(QModelIndex, int, int)
	# edgesRemoved = Signal(QModelIndex, int, int)
	# edgesAboutToBeRemoved = Signal(QModelIndex, int, int)
	# edgesChanged = Signal(QModelIndex, QModelIndex, List[int])

	def __init__(self, parent=None):
		super().__init__(parent)
		### CREATE QT MODELS ###

		### Nodes Model ###
		self.nodes = QStandardItemModel()
		self.nodes.setHorizontalHeaderLabels(['id', 'name', 'posx', 'posy', 'script'])
		# self.nodes.rowsInserted.connect(self.nodesInserted.emit)
		# self.nodes.rowsRemoved.connect(self.nodesRemoved.emit)
		# self.nodes.rowsAboutToBeRemoved.connect(self.nodesAboutToBeRemoved.emit)
		# self.nodes.dataChanged.connect(self.nodesChanged.emit)

		### Inlets Model ###
		self.inlets = QStandardItemModel()
		self.inlets.setHorizontalHeaderLabels(['id', 'owner', "name"])
		# self.inlets.rowsInserted.connect(self.inletsInserted.emit)
		# self.inlets.rowsRemoved.connect(self.inletsRemoved.emit)
		# self.inlets.rowsAboutToBeRemoved.connect(self.inletsAboutToBeRemoved.emit)
		# self.inlets.dataChanged.connect(self.inletsChanged.emit)

		### Outlets Model ###
		self.outlets = QStandardItemModel()
		self.outlets.setHorizontalHeaderLabels(['id', 'owner', "name"])
		# self.outlets.rowsInserted.connect(self.outletsInserted.emit)
		# self.outlets.rowsRemoved.connect(self.outletsRemoved.emit)
		# self.outlets.rowsAboutToBeRemoved.connect(self.outletsAboutToBeRemoved.emit)
		# self.outlets.dataChanged.connect(self.outletsChanged.emit)

		### Edges Model ###
		self.edges = QStandardItemModel()
		self.edges.setHorizontalHeaderLabels(["id", "outlet_id", "inlet_id"])
		# self.edges.rowsInserted.connect(self.edgesInserted.emit)
		# self.edges.rowsRemoved.connect(self.edgesRemoved.emit)
		# self.edges.rowsAboutToBeRemoved.connect(self.edgesAboutToBeRemoved.emit)
		# self.edges.dataChanged.connect(self.edgesChanged.emit)

	def addNode(self, name:str, posx:int, posy:int, script:str)->NodeIndex:
		assert isinstance(name, str)
		assert isinstance(posx, int)
		assert isinstance(posy, int)
		id_item =   QStandardItem(unique.make_unique_id())
		name_item = QStandardItem()
		name_item.setData(name, Qt.ItemDataRole.DisplayRole)
		posx_item = QStandardItem()
		posx_item.setData(int(posx), Qt.ItemDataRole.DisplayRole)
		posy_item = QStandardItem()
		posy_item.setData(int(posy), Qt.ItemDataRole.DisplayRole)
		script_item = QStandardItem(script)
		script_item.setData(script, Qt.ItemDataRole.DisplayRole)
		self.nodes.appendRow([id_item, name_item, posx_item, posy_item, script_item])

		return NodeIndex(self.nodes.indexFromItem(id_item))

	def addInlet(self, node:NodeIndex, name:str)->InletIndex:
		if not node.isValid():
			raise KeyError(f"Node {node.data()}, does not exist!")

		id_item =    QStandardItem(unique.make_unique_id())
		owner_item = QStandardItem(node.data())
		name_item =  QStandardItem(name)
		
		self.inlets.appendRow([id_item, owner_item, name_item])
		return InletIndex(self.inlets.indexFromItem(id_item))

	def addOutlet(self, node:NodeIndex, name:str)->OutletIndex:
		if not node.isValid():
			raise KeyError(f"Node {node.data()}, does not exist!")
		id_item =    QStandardItem(unique.make_unique_id())
		owner_item = QStandardItem(node.data())
		name_item =  QStandardItem(name)
		
		self.outlets.appendRow([id_item, owner_item, name_item])
		return OutletIndex(self.outlets.indexFromItem(id_item))

	def addEdge(self, outlet:QModelIndex, inlet:QModelIndex)->EdgeIndex:
		if not outlet.isValid():
			raise KeyError(f"outlet '{outlet}'' does not exist")
		if not inlet.isValid():
			raise KeyError(f"inlet {inlet} does not exist")

		id_item =        QStandardItem(unique.make_unique_id())
		outlet_id_item = QStandardItem(outlet.data())
		inlet_id_item =  QStandardItem(inlet.data())
		self.edges.appendRow([id_item, outlet_id_item, inlet_id_item])
		return EdgeIndex(self.edges.indexFromItem(id_item))

	def removeNodes(self, nodes:List[NodeIndex]):
		# Collect the rows to be removed
		rows_to_remove = sorted(set(index.row() for index in nodes), reverse=True)

		# collect inlets to be removed
		inlets_to_remove = []
		for row in rows_to_remove:
			owner_id = self.nodes.item(row, 0).text()
			inlet_items = self.inlets.findItems(owner_id, Qt.MatchFlag.MatchExactly, 1)
			for inlet_item in inlet_items:
				inlets_to_remove.append( inlet_item.index().siblingAtColumn(0) )
		self.removeInlets(inlets_to_remove)

		# collect outlets to be removed
		outlets_to_remove = []
		for row in rows_to_remove:
			owner_id = self.nodes.item(row, 0).text()
			outlet_items = self.outlets.findItems(owner_id, Qt.MatchFlag.MatchExactly, 1)
			for outlet_item in outlet_items:
				outlets_to_remove.append( outlet_item.index().siblingAtColumn(0) )
		self.removeOutlets(outlets_to_remove)

		# Remove the node rows from the GraphModel (starting from the last one, to avoid shifting indices)
		for row in reversed(rows_to_remove):
			self.nodes.removeRow(row)

	def removeOutlets(self, outlets_to_remove:List[OutletIndex]):
		# collect edges to be removed
		assert all( isinstance(outlet, OutletIndex) for outlet in outlets_to_remove )
		edges_to_remove = []
		for outlet in outlets_to_remove:
			edge_items = self.edges.findItems(outlet.data(), Qt.MatchFlag.MatchExactly, 1)
			for edge_item in edge_items:
				edges_to_remove.append( edge_item.index() )
		self.removeEdges(edges_to_remove)

		# Remove the rows from the GraphModel (starting from the last one, to avoid shifting indices)
		rows_to_remove = set([outlet.row() for outlet in outlets_to_remove]) # keep unique rows
		for row in sorted(rows_to_remove, reverse=True):
			self.outlets.removeRow(row)

	def removeInlets(self, inlets_to_remove:List[InletIndex]):
		# collect edges to be removed
		assert all( isinstance(inlet, InletIndex) for inlet in inlets_to_remove )
		edges_to_remove = []
		for inlet in inlets_to_remove:
			edge_items = self.edges.findItems(inlet.data(), Qt.MatchFlag.MatchExactly, 2)
			for edge_item in edge_items:
				edges_to_remove.append( edge_item.index() )
		self.removeEdges(edges_to_remove)

		# Remove the rows from the GraphModel (starting from the last one, to avoid shifting indices)
		rows_to_remove = set([inlet.row() for inlet in inlets_to_remove]) # keep unique rows
		for row in sorted(rows_to_remove, reverse=True):
			self.inlets.removeRow(row)

	def removeEdges(self, edges_to_remove:List[EdgeIndex]):
		# Remove the rows from the GraphModel (starting from the last one, to avoid shifting indices)
		assert all( isinstance(edge, EdgeIndex) for edge in edges_to_remove )
		rows_to_remove = set([edge.row() for edge in edges_to_remove]) # keep unique rows
		for row in sorted(rows_to_remove, reverse=True):
			self.edges.removeRow(row)

	def getNode(self, node:NodeIndex, relations=True):
		assert isinstance(node, NodeIndex) and node.isValid(), f"got: {node}"
		assert node.column() == 0
		properties = {
			'id': node.data(),
			'name': node.siblingAtColumn(1).data(),
			'posx': int(node.siblingAtColumn(2).data()),
			'posy': int(node.siblingAtColumn(3).data()),
		}
		if relations:
			inlets = [InletIndex(item.index().siblingAtColumn(0)) for item in self.inlets.findItems(node.data(), Qt.MatchFlag.MatchExactly, 1)]
			outlets = [OutletIndex(item.index().siblingAtColumn(0)) for item in self.outlets.findItems(node.data(), Qt.MatchFlag.MatchExactly, 1)]
			properties.update({
				'outlets': outlets,
				'inlets': inlets
			})
		return properties

	def setNode(self, node:NodeIndex, properties:dict):
		assert isinstance(node, NodeIndex) and node.isValid(), f"got: {node}"
		assert node.column() == 0
		# self.nodes.blockSignals(True)
		columnsChanged = []
		for key, value in properties.items():
			match key:
				case "id":
					assert isinstance(value, str)
					columnsChanged.append(0)
					self.nodes.setData(node.siblingAtColumn(0), value)
				case "name":
					assert isinstance(value, str)
					columnsChanged.append(1)
					prevValue = self.nodes.data(node.siblingAtColumn(1))
					res = self.nodes.setData(node.siblingAtColumn(1), value)
					print(res, value, prevValue)
				case "posx":
					assert isinstance(value, int)
					columnsChanged.append(2)
					self.nodes.setData(node.siblingAtColumn(2), value)
				case "posy":
					assert isinstance(value, int)
					columnsChanged.append(3)
					self.nodes.setData(node.siblingAtColumn(3), value)
			
		# self.nodes.blockSignals(False)
		# for start, end in group_consecutive_numbers(columnsChanged):
		# 	self.nodes.dataChanged.emit(node.siblingAtColumn(start), node.siblingAtColumn(end))

	def setNodeData(self, node:NodeIndex, role):
		raise NotImplementedError

	def getInlet(self, inlet:InletIndex, relations=True):
		assert isinstance(inlet, InletIndex) and inlet.isValid()
		assert inlet.model() == self.inlets
		assert inlet.column() == 0

		properties = {
			'id': inlet.data(),
			"name": inlet.siblingAtColumn(2).data(),
		}
		if relations:
			node_id = inlet.siblingAtColumn(1).data()
			owner_nodes = [NodeIndex(item.index()) for item in self.nodes.findItems(node_id, Qt.MatchFlag.MatchExactly, 0)]
			assert len(owner_nodes)==1, f"Outlet {inlet} supposed to have exacly one owner node!"
			edges = [EdgeIndex(item.index().siblingAtColumn(0)) for item in self.edges.findItems(inlet.data(), Qt.MatchFlag.MatchExactly, 2)]
			properties.update({
				'node': owner_nodes[0],
				"edges": edges
			})
		return properties

	def getOutlet(self, outlet:OutletIndex, relations=True):
		assert isinstance(outlet, OutletIndex)
		assert outlet.model() == self.outlets
		assert outlet.column() == 0

		properties = {
			'id': outlet.data(),
			'name': outlet.siblingAtColumn(2).data(),
		}
		if relations:
			node_id = outlet.siblingAtColumn(1).data()
			owner_nodes = [NodeIndex(item.index()) for item in self.nodes.findItems(node_id, Qt.MatchFlag.MatchExactly, 0)]
			assert len(owner_nodes)==1, f"Outlet {outlet} supposed to have exacly one owner node!"
			edges = [EdgeIndex(item.index().siblingAtColumn(0)) for item in self.edges.findItems(outlet.data(), Qt.MatchFlag.MatchExactly, 1)]
			properties.update({
				'node': owner_nodes[0],
				"edges": edges
			})
		return properties

	def getEdge(self, edge:EdgeIndex, relations=True):
		assert isinstance(edge, EdgeIndex)
		assert edge.model() == self.edges
		assert edge.column() == 0

		properties = {
			'id': edge.data(),
		}
		if relations:
			outlet_id:str = edge.siblingAtColumn(1).data()
			inlet_id:str = edge.siblingAtColumn(2).data()
			source_outlets = [OutletIndex(item.index()) for item in self.outlets.findItems(outlet_id, Qt.MatchFlag.MatchExactly, 0)]
			target_inlets =  [InletIndex(item.index()) for item in self.inlets.findItems(inlet_id, Qt.MatchFlag.MatchExactly, 0)]
			assert len(source_outlets)==1, f"Edges {edge} supposed to have exacly one source, got {len(source_outlets)}!"
			assert len(target_inlets)==1, f"Edges {edge} supposed to have exacly one target, got {len(source_outlets)}!"
			properties.update({
				'source': source_outlets[0],
				"target": target_inlets[0]
			})
		return properties

	def setEdge(self, edge:EdgeIndex, properties:dict):
		assert isinstance(edge, EdgeIndex)
		assert edge.model() == self.edges
		assert edge.column() == 0

		for key, value in properties.items():
			match key:
				case "source":
					IsValidSource = (isinstance(value, QModelIndex)
									and value.model() == self.outlets
									and value.isValid())
					if not IsValidSource:
						raise ValueError(f"source is not an outlet, got: {value}")

					source_id:str = value.data()
					self.edges.setData(edge.siblingAtColumn(1), source_id)
				case "target":
					IsValidTarget = (isinstance(value, QModelIndex)
									and value.model() == self.inlets
									and value.isValid())
					if not IsValidTarget:
						raise ValueError(f"source is not an inlet, got: {value}")
					target_id:str = value.data()
					self.edges.setData(edge.siblingAtColumn(2), target_id)

	def getSourceNodes(self, node:NodeIndex):
		assert isinstance(node, QModelIndex)
		assert node.model() == self.nodes
		assert node.column() == 0

		inlets = self.getNode(node)["inlets"]
		for inlet in inlets:
			for edge in self.getInlet(inlet)["edges"]:
				outlet = self.getEdge(edge)["source"]
				yield self.getOutlet(outlet)["node"]

	def getTargetNodes(self, node:NodeIndex):
		assert isinstance(node, NodeIndex)
		assert node.model() == self.nodes
		assert node.column() == 0

		outlets = self.getNode(node)["outlets"]
		for outlet in outlets:
			for edge in self.getOutlet(outlet)["edges"]:
				inlet = self.getEdge(edge)["target"]
				yield self.getInlet(inlet)["node"]

	def rootRodes(self)->Iterable[NodeIndex]:
		"""Yield all root nodes (nodes without outlets) in the graph."""
		def hasTargets(node:NodeIndex):
			assert isinstance(node, QModelIndex)
			assert node.model() == self.nodes
			assert node.column() == 0
			return len(list(self.getTargetNodes(node)))>0
		
		for row in range(self.nodes.rowCount()):
			node = NodeIndex(self.nodes.index(row, 0))
			if not hasTargets(node):
				yield node

	def dfs(self)->Iterable[NodeIndex]:
		"""Perform DFS starting from the root nodes and yield each node."""
		visited = set()  # Set to track visited nodes
		def dfs_visit(node:NodeIndex):
			"""Recursive helper function to perform DFS."""
			assert isinstance(node, QModelIndex)
			assert node.model() == self.nodes
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