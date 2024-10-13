import unique

import sys
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from typing import List, Tuple, Iterable

class NodeFilterProxyModel(QSortFilterProxyModel):
	def __init__(self, node_column, parent=None):
		super().__init__(parent)
		self.node_column = node_column
		self.node_name = ""

	def setNodeName(self, node_name):
		self.node_name = node_name
		self.invalidateFilter()

	def filterAcceptsRow(self, source_row, source_parent):
		index = self.sourceModel().index(source_row, self.node_column, source_parent)
		return self.sourceModel().data(index) == self.node_name

class GraphModel(QObject):
	nodesInserted = Signal(QModelIndex, int, int)
	nodesRemoved = Signal(QModelIndex, int, int)
	nodesAboutToBeRemoved = Signal(QModelIndex, int, int)
	nodeChanged = Signal(QModelIndex)

	outletsInserted = Signal(QModelIndex, int, int)
	outletsRemoved = Signal(QModelIndex, int, int)
	outletsAboutToBeRemoved = Signal(QModelIndex, int, int)
	outletChanged = Signal(QModelIndex)

	inletsInserted = Signal(QModelIndex, int, int)
	inletsRemoved = Signal(QModelIndex, int, int)
	inletsAboutToBeRemoved = Signal(QModelIndex, int, int)
	inletChanged = Signal(QModelIndex)

	edgesInserted = Signal(QModelIndex, int, int)
	edgesRemoved = Signal(QModelIndex, int, int)
	edgesAboutToBeRemoved = Signal(QModelIndex, int, int)
	edgeChanged = Signal(QModelIndex)

	def __init__(self, parent=None):
		super().__init__(parent)
		### CREATE QT MODELS ###

		### Nodes Model ###
		self.nodes = QStandardItemModel()
		self.nodes.setHorizontalHeaderLabels(['id', 'name', 'posx', 'posy'])
		self.nodes.rowsInserted.connect(self.nodesInserted.emit)
		self.nodes.rowsRemoved.connect(self.nodesRemoved.emit)
		self.nodes.rowsAboutToBeRemoved.connect(self.nodesAboutToBeRemoved.emit)
		self.nodes.itemChanged.connect(self.nodeChanged.emit)

		### Inlets Model ###
		self.inlets = QStandardItemModel()
		self.inlets.setHorizontalHeaderLabels(['id', 'owner', "name"])
		self.inlets.rowsInserted.connect(self.inletsInserted.emit)
		self.inlets.rowsRemoved.connect(self.inletsRemoved.emit)
		self.inlets.rowsAboutToBeRemoved.connect(self.inletsAboutToBeRemoved.emit)
		self.inlets.itemChanged.connect(self.inletChanged.emit)

		### Outlets Model ###
		self.outlets = QStandardItemModel()
		self.outlets.setHorizontalHeaderLabels(['id', 'owner', "name"])
		self.outlets.rowsInserted.connect(self.outletsInserted.emit)
		self.outlets.rowsRemoved.connect(self.outletsRemoved.emit)
		self.outlets.rowsAboutToBeRemoved.connect(self.outletsAboutToBeRemoved.emit)
		self.outlets.itemChanged.connect(self.outletChanged.emit)

		### Edges Model ###
		self.edges = QStandardItemModel()
		self.edges.setHorizontalHeaderLabels(["id", "outlet_id", "inlet_id"])
		self.edges.rowsInserted.connect(self.edgesInserted.emit)
		self.edges.rowsRemoved.connect(self.edgesRemoved.emit)
		self.edges.rowsAboutToBeRemoved.connect(self.edgesAboutToBeRemoved.emit)
		self.edges.itemChanged.connect(self.edgeChanged.emit)

	def readNodeData(self, row:int):
		return [self.nodes.indexFromItem(self.nodes.item(row, i)).data() for i in range(self.nodes.columnCount())]

	def readInletData(self, row:int):
		return [self.inlets.indexFromItem(self.inlets.item(row, i)).data() for i in range(self.inlets.columnCount())]

	def readOutletData(self, row:int):
		return [self.outlets.indexFromItem(self.outlets.item(row, i)).data() for i in range(self.outlets.columnCount())]

	def readEdgeData(self, row:int):
		return [self.edges.indexFromItem(self.edges.item(row, i)).data() for i in range(self.edges.columnCount())]

	def addNode(self, name:str, posx:int, posy:int)->str:
		unique_id = unique.make_unique_id()
		id_item =   QStandardItem(unique_id)
		name_item = QStandardItem(name)
		posx_item = QStandardItem(str(posx))
		posy_item = QStandardItem(str(posy))
		self.nodes.appendRow([id_item, name_item, posx_item, posy_item])

		return unique_id

	def addInlet(self, owner_id:str, name:str)->str:
		if not self.nodes.findItems(owner_id):
			raise KeyError(f"node `{owner_id}` does not exist")

		unique_id = unique.make_unique_id()
		id_item =    QStandardItem(unique_id)
		owner_item = QStandardItem(owner_id)
		name_item =  QStandardItem(name)
		
		self.inlets.appendRow([id_item, owner_item, name_item])
		return unique_id

	def readNodeData(self, row:int):
		return [self.nodes.indexFromItem(self.nodes.item(row, i)).data() for i in range(self.nodes.columnCount())]

	def addOutlet(self, owner_id:str, name:str)->str:
		if not self.nodes.findItems(owner_id):
			raise KeyError(f"node `{owner_id}` does not exist")
		unique_id = unique.make_unique_id()
		id_item = QStandardItem(unique_id)
		owner_item =   QStandardItem(owner_id)
		name_item =   QStandardItem(name)
		
		self.outlets.appendRow([id_item, owner_item, name_item])
		return unique_id

	def addEdge(self, outlet_id, inlet_id)->str:
		if not self.outlets.findItems(outlet_id):
			raise KeyError(f"outlet '{outlet_id}'' does not exist")
		if not self.inlets.findItems(inlet_id):
			raise KeyError(f"inlet {inlet_id} does not exist")

		unique_id = unique.make_unique_id()
		id_item =        QStandardItem(unique_id)
		outlet_id_item = QStandardItem(outlet_id)
		inlet_id_item =  QStandardItem(inlet_id)
		self.edges.appendRow([id_item, outlet_id_item, inlet_id_item])
		return unique_id

	def findNodeRowById(self, node_id)->int:
		foundItems = self.nodes.findItems(node_id)
		assert(len(foundItems)==1)
		index = found_items[0].index()
		return index.row()

	def findOutletRowById(self, outlet_id)->int:
		foundItems = self.outlets.findItems(outlet_id)
		assert(len(foundItems)==1)
		index = found_items[0].index()
		return index.row()

	def findOutletRowById(self, outlet_id)->int:
		foundItems = self.nodes.findItems(outlet_id)
		assert(len(foundItems)==1)
		index = found_items[0].index()
		return index.row()

	def findEdgeRowById(self, edge_id)->int:
		foundItems = self.edges.findItems(node_id)
		assert(len(foundItems)==1)
		index = found_items[0].index()
		return index.row()

	def removeNodes(self, indexes):
		# Collect the rows to be removed
		rows_to_remove = sorted(set(index.row() for index in indexes), reverse=True)

		# collect inlets to be removed
		inlet_rows_to_remove = []
		for row in rows_to_remove:
			owner_id = self.nodes.item(row, 0).text()
			inlet_items = self.inlets.findItems(owner_id, Qt.MatchExactly, 1)
			for inlet_item in inlet_items:
				inlet_rows_to_remove.append( inlet_item.index().row() )
		self.removeInlets(inlet_rows_to_remove)

		# collect outlets to be removed
		outlet_rows_to_remove = []
		for row in rows_to_remove:
			owner_id = self.nodes.item(row, 0).text()
			outlet_items = self.outlets.findItems(owner_id, Qt.MatchExactly, 1)
			for outlet_item in outlet_items:
				outlet_rows_to_remove.append( outlet_item.index().row() )
		self.removeOutlets(outlet_rows_to_remove)

		# Remove the node rows from the GraphModel (starting from the last one, to avoid shifting indices)
		for row in reversed(rows_to_remove):
			self.nodes.removeRow(row)

	def removeNodeById(self, node_id:str):
		# Collect the rows to be removed
		row = []
		found_items = self.nodes.findItems(node_id)
		if not len(found_items)==1:
			raise KeyError("Node {node_id} does not exist!")

		self.removeNodes([item.index() for item in found_items])

	def removeEdges(self, rows_to_remove:List[int]):
		# Remove the rows from the GraphModel (starting from the last one, to avoid shifting indices)
		for row in sorted(set(rows_to_remove), reverse=True):
			self.edges.removeRow(row)

	def removeOutlets(self, rows_to_remove:List[int]):
		# Collect the rows to be removed

		# collect edges to be removed
		edge_rows_to_remove = []
		for row in sorted(set(rows_to_remove), reverse=True):
			outlet_id = self.outlets.item(row, 0).text()
			edge_items = self.edges.findItems(outlet_id, Qt.MatchExactly, 1)
			for edge_item in edge_items:
				edge_rows_to_remove.append( edge_item.index().row() )

		self.removeEdges(edge_rows_to_remove)


		# Remove the rows from the GraphModel (starting from the last one, to avoid shifting indices)
		for row in rows_to_remove:
			self.outlets.removeRow(row)

	def removeInlets(self, rows_to_remove:List[int]):

		# collect edges to be removed
		edge_rows_to_remove = []
		for row in rows_to_remove:
			inlet_id = self.inlets.item(row, 0).text()
			edge_items = self.edges.findItems(inlet_id, Qt.MatchExactly, 2)
			for edge_item in edge_items:
				edge_rows_to_remove.append( edge_item.index().row() )
		self.removeEdges(edge_rows_to_remove)

		# Remove the rows from the GraphModel (starting from the last one, to avoid shifting indices)
		for row in sorted(set(rows_to_remove), reverse=True):
			self.inlets.removeRow(row)

	def findInlets(self, node:QModelIndex)->QModelIndex:
		items = self.inlets.findItems(node.data(), Qt.MatchExactly, 1)
		for item in items:
			yield item.index().siblingAtColumn(0) # return the ndex at the id column

	def findOutlets(self, node)->QModelIndex:
		items = self.outlets.findItems(node.data(), Qt.MatchExactly, 1)
		for item in items:
			yield item.index().siblingAtColumn(0) # return the ndex at the id column

	def findEdges(self, source:QModelIndex=None, target:QModelIndex=None):
		# find edges from source outlet
		edges_from_source = self.edges.findItems(source.data(), Qt.MatchExactly, 1)

		# find edges to target inlet
		edges_to_target = self.edges.findItems(target.data(), Qt.MatchExactly, 2)

		# return edges matching source and target:
		for edge in edges_from_source:
			if edge in edges_to_target:
				yield edge.index().siblingAtColumn(0) # return the ndex at the id column


	def findEdgesToInlet(self, inlet:QModelIndex):
		edges_to_target = self.edges.findItems(target.data(), Qt.MatchExactly, 2)
		for edge in edges_to_target:
			yield edge.index().siblingAtColumn(0)

	def findSources(self, node:QModelIndex())->Iterable[QModelIndex]:
		print("nodeid:", node.siblingAtColumn(0).data())
		inlets = self.findInlets(node.siblingAtColumn(0))
		for inlet in inlets:
			# find edges to inlet
			edges_to_target = self.edges.findItems(inlet.data(), Qt.MatchExactly, 2)
			for edge in edges_to_target:
				source_outlet_id = edge.index().siblingAtColumn(1).data() # get the index of the source outlet
				outlet_items = self.outlets.findItems(source_outlet_id)
				for outlet_item in outlet_items:
					owner_node_id = outlet_item.index().siblingAtColumn(1).data()
					for source_node_item in self.nodes.findItems(owner_node_id):
						yield source_node_item.index()

	def findConnectedNodes(self, node:QModelIndex(), direction:str)->Iterable[QModelIndex]:
		print("nodeid:", node.siblingAtColumn(0).data())
		if direction == "SOURCE":
			findPorts = self.findInlets
			column = 2
		elif direction == "TARGET":
			findPorts = self.findOutlets
			column = 1
		
		ports = findPorts(node.siblingAtColumn(0))
		for port in ports:
			# find edges to inlet
			edges_to_target = self.edges.findItems(port.data(), Qt.MatchExactly, column)
			for edge in edges_to_target:
				connected_id = edge.index().siblingAtColumn(1).data() # get the index of the source outlet
				connected_items = self.outlets.findItems(connected_id)
				for connected_item in connected_items:
					owner_node_id = connected_item.index().siblingAtColumn(1).data()
					for connected_node_item in self.nodes.findItems(owner_node_id):
						yield connected_node_item.index()



		# for index in indexes:
		# 	edges = [item.index().siblingAtColumn(0) for item in self.edges.findItems(index.data(), Qt.MatchExactly, 2)]

		# 	for edges in edges:
		# 		yield from [item.index() for item in self.edges.findItems(edge_id.data())]


	def rootRodes(self)->Iterable[QModelIndex]:
		"""Yield all root nodes (nodes without outlets) in the graph."""
		for i in range(self.nodes.rowCount()):
			node = self.nodes.item(i, 0).index()
			target_nodes = list(self.findConnectedNodes(node, direction="TARGET"))
			if not target_nodes:
				yield node
			# print(list(sources))
			# if not sources:  # Check if the node has no outlets
			# 	yield node  # Yield the root node

	def dfs(self)->Iterable[QModelIndex]:
		"""Perform DFS starting from the root notes and yield each node."""

		start_nodes = self.rootRodes()
		visited = set()  # Set to track visited nodes

		def dfs_visit(node:QModelIndex):
			"""Recursive helper function to perform DFS."""
			visited.add(node)
			yield node  # Yield the current node

			# Iterate through all adjacent edges from the current node
			for target_node in self.findSources(node):
				if target_node not in visited:  # Check if the target node has been visited
					yield from dfs_visit(target_node)  # Recursive call

		for start_node in start_nodes:
			if start_node not in visited:  # Check if the start node has been visited
				yield from dfs_visit(start_node)  # Start DFS from the start node
