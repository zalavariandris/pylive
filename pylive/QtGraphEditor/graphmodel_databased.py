from collections import defaultdict
from enum import IntEnum, StrEnum
from pylive import unique
import sys
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from typing import *


class NodeRef():
	def __init__(self, index:str, graph:'GraphModel'):
		self._index = index
		self._graph = graph

	def graph(self):
		return self._graph

	def __eq__(self, other: object, /) -> bool:
		if isinstance(other, NodeRef):
			return self._graph == other._graph and self._index == other._index
		else:
			return False

	def __hash__(self) -> int:
		return hash((self._index))

	def isValid(self):
		return self in self._graph._nodes

	def __repr__(self) -> str:
		return f"{self.__class__.__name__}({self._index})"


class EdgeRef():
	def __init__(self, index:str, graph:'GraphModel'):
		self._index = index
		self._graph = graph

	def graph(self):
		return self._graph

	def __eq__(self, other: object, /) -> bool:
		if isinstance(other, EdgeRef):
			return self._graph == other._graph and self._index == other._index
		else:
			return False

	def __hash__(self) -> int:
		return hash((self._index))

	def isValid(self):
		return self in self._graph._edges

	def __repr__(self) -> str:
		return f"{self.__class__.__name__}({self._index})"


class InletRef():
	def __init__(self, index:str, graph:'GraphModel'):
		self._index = index
		self._graph = graph

	def graph(self):
		return self._graph

	def __eq__(self, other: object, /) -> bool:
		if isinstance(other, InletRef):
			return self._graph == other._graph and self._index == other._index
		else:
			return False

	def __hash__(self) -> int:
		return hash((self._index))

	def isValid(self):
		return self in self._graph._inlets

	def __repr__(self) -> str:
		return f"{self.__class__.__name__}({self._index})"


class OutletRef():
	def __init__(self, index:str, graph:'GraphModel'):
		self._index = index
		self._graph = graph

	def graph(self):
		return self._graph

	def __eq__(self, other: object, /) -> bool:
		if isinstance(other, OutletRef):
			return self._graph == other._graph and self._index == other._index
		else:
			return False

	def __hash__(self) -> int:
		return hash((self._index))

	def isValid(self):
		return self in self._graph._outlets

	def __repr__(self) -> str:
		return f"{self.__class__.__name__}({self._index})"


class GraphModel(QObject):
	"""
    A graph model emitting signals.

    Signals:
        nodesAdded (nodes:List[NodeRef]): Emitted when nodes are added.
        nodesAboutToBeRemoved (List[NodeRef]): Emitted before nodes are removed.
        nodesPropertyChanged (nodes:List[NodeRef], properties:List[str]): Emitted when node properties change.
        nodesRemoved (List[NodeRef]): Emitted after nodes are removed.
        
        edgesAdded (edges:List[EdgeRef]): Emitted when edges are added.
        edgesAboutToBeRemoved (edges:List[EdgeRef]): Emitted before edges are removed.
        edgesPropertyChanged (edges:List[EdgeRef], properties:List[str]): Emitted when edge properties change.
        edgesRemoved (edges:List[EdgeRef]): Emitted after edges are removed.

        inletsAdded (inlets:List[InletRef]): Emitted when inlets are added.
        inletsAboutToBeRemoved (inlets:List[InletRef]): Emitted before inlets are removed.
        inletsPropertyChanged (inlets:List[InletRef], properties:List[str]): Emitted when inlet properties change.
        inletsRemoved (inlets:List[InletRef]): Emitted after inlets are removed.
        
        outletsAdded (outlets:List[OutletRef]): Emitted when outlets are added.
        outletsAboutToBeRemoved (outlets:List[OutletRef]): Emitted before outlets are removed.
        outletsPropertyChanged (outlets:List[OutletRef], properties:List[str]): Emitted when outlet properties change.
        outletsRemoved (outlets:List[OutletRef]): Emitted after outlets are removed.
    """
	nodesAdded = Signal(list) #List[NodeRef]
	nodesAboutToBeRemoved = Signal(list) #List[NodeRef]
	nodesPropertyChanged = Signal(list, list) #List[NodeRef], List[str]
	nodesRemoved = Signal(list)

	inletsAdded = Signal(list) #List[InletRef]
	inletsAboutToBeRemoved = Signal(list) #List[InletRef]
	inletsPropertyChanged = Signal(list, list) #List[InletRef], List[str]
	inletsRemoved = Signal(list)

	outletsAdded = Signal(list) #List[OutletIndex]
	outletsAboutToBeRemoved = Signal(list) #List[OutletRef]
	outletsPropertyChanged = Signal(list, list) #List[OutletRef], List[str]
	outletsRemoved = Signal(list)

	edgesAdded = Signal(list) #List[EdgeRef]
	edgesAboutToBeRemoved = Signal(list) #List[EdgeRef]
	edgesPropertyChanged = Signal(list, list) #List[EdgeRef], List[str]
	edgesRemoved = Signal(list)

	def __init__(self, parent=None):
		super().__init__(parent)
		### CREATE QT MODELS ###

		### Nodes Model ###
		self._nodes:Dict[NodeRef, Dict] = defaultdict(dict)
		self._inlets:Dict[InletRef, Dict] = defaultdict(dict)
		self._outlets:Dict[OutletRef, Dict] = defaultdict(dict)
		self._edges:Dict[EdgeRef, Dict] = defaultdict(dict)

		# store relations
		self._inlets_owner:Dict[InletRef, NodeRef] = dict()
		self._outlets_owner:Dict[OutletRef, NodeRef] = dict()
		self._nodes_inlets:Dict[NodeRef, List[InletRef]] = defaultdict(list)
		self._nodes_outlets:Dict[NodeRef, List[OutletRef]] = defaultdict(list)
		self._edges_source:Dict[EdgeRef, OutletRef] = dict()
		self._edges_target:Dict[EdgeRef, InletRef] = dict()
		self._inlets_edges:Dict[InletRef, List[EdgeRef]] = defaultdict(list)
		self._outlets_edges:Dict[OutletRef, List[EdgeRef]] = defaultdict(list)

	def __del__(self):
		self._nodes.clear()
		self._inlets.clear()
		self._outlets.clear()
		self._edges.clear()

		# relations
		self._inlets_owner.clear()
		self._outlets_owner.clear()
		self._nodes_inlets.clear()
		self._nodes_outlets.clear()
		self._edges_source.clear()
		self._edges_target.clear()
		self._inlets_edges.clear()
		self._outlets_edges.clear()

	# Query
	def getNodes(self)->Iterable[NodeRef]:
		for node in self._nodes:
			yield node

	def getEdges(self)->Iterable[EdgeRef]:
		for edge in self._edges.keys():
			yield edge

	def nodeCount(self)->int:
		return len(self._nodes)

	def inletCount(self)->int:
		return len(self._inlets)

	def outletCount(self)->int:
		return len(self._outlets)

	def edgeCount(self)->int:
		return len(self._edges)

	# CREATE
	def addNode(self, /, **props)->NodeRef:
		unique_id = unique.make_unique_id()
		node = NodeRef(unique_id, self)
		self._nodes[node] = props
		self.nodesAdded.emit([node])
		return node

	def addInlet(self, node:NodeRef, /, **props)->InletRef:
		assert node.isValid()

		unique_id = unique.make_unique_id()
		inlet = InletRef(unique_id, self)

		if inlet in self._inlets: #change guard
			return inlet

		# setup relations
		self._inlets_owner[inlet] = node
		self._nodes_inlets[node].append(inlet)

		# setup properties
		self._inlets[inlet].update(props)

		self.inletsAdded.emit([inlet])
		return inlet

	def addOutlet(self, node:NodeRef,/, **props)->OutletRef:
		assert node.isValid()

		unique_id = unique.make_unique_id()
		outlet = OutletRef(unique_id, self)

		if outlet in self._outlets: #change guard
			return outlet

		# setup relations
		self._outlets_owner[outlet] = node
		self._nodes_outlets[node].append(outlet)

		# setup properties
		self._outlets[outlet].update(props)

		self.outletsAdded.emit([outlet])
		return outlet

	def addEdge(self, outlet:OutletRef, inlet:InletRef, /, **props)->EdgeRef:
		assert isinstance(outlet, OutletRef)
		assert isinstance(inlet, InletRef)
		assert inlet.isValid()
		assert outlet.isValid()
		assert "SOURCE_OUTLET" not in props and "TARGET_INLET" not in props

		unique_id = unique.make_unique_id()
		edge = EdgeRef(unique_id, self)

		if edge in self._edges: #change guard
			return edge

		# setup relations
		self._edges_source[edge] = outlet
		self._outlets_edges[outlet].append(edge)
		self._edges_target[edge] = inlet
		self._inlets_edges[inlet].append(edge)

		# setup properties
		self._edges[edge].update(props)

		self.edgesAdded.emit([edge])
		return edge

	# DELETE
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

		self.nodesAboutToBeRemoved.emit(nodes_to_remove)
		for node in nodes_to_remove:
			# remove properties
			del self._nodes[node]
		self.nodesRemoved.emit(nodes_to_remove)

	def removeOutlets(self, outlets_to_remove:List[OutletRef]):
		# collect edges to be removed
		assert all( isinstance(outlet, OutletRef) for outlet in outlets_to_remove )

		edges_to_remove = []
		for outlet in outlets_to_remove:
			outlet_edges = self.getOutletEdges(outlet)
			edges_to_remove+=outlet_edges
		self.removeEdges(edges_to_remove)

		self.outletsAboutToBeRemoved.emit(outlets_to_remove)
		for outlet in outlets_to_remove:
			owner = self._outlets_owner.pop(outlet)
			self._nodes_outlets[owner].remove(outlet)
			del self._outlets[outlet]
		self.outletsRemoved.emit(outlets_to_remove)

	def removeInlets(self, inlets_to_remove:List[InletRef]):
		# collect edges to be removed
		assert all( isinstance(inlet, InletRef) for inlet in inlets_to_remove ), f"got: {inlets_to_remove}"
		assert all( inlet.isValid() for inlet in inlets_to_remove)

		edges_to_remove = []
		for inlet in inlets_to_remove:
			inlet_edges = self.getInletEdges(inlet)
			edges_to_remove+=inlet_edges
		self.removeEdges(edges_to_remove)

		self.inletsAboutToBeRemoved.emit(inlets_to_remove)
		for inlet in inlets_to_remove:
			owner = self._inlets_owner.pop(inlet)
			self._nodes_inlets[owner].remove(inlet)
			del self._inlets[inlet]
		self.inletsRemoved.emit(inlets_to_remove)

	def removeEdges(self, edges_to_remove:List[EdgeRef]):
		# Remove the rows from the GraphModel (starting from the last one, to avoid shifting indices)
		assert all( isinstance(edge, EdgeRef) for edge in edges_to_remove )

		self.edgesAboutToBeRemoved.emit(edges_to_remove)
		for edge in edges_to_remove:
			source_outlet = self._edges_source.pop(edge)
			self._outlets_edges[source_outlet].remove(edge)
			target_inlet = self._edges_target.pop(edge)
			self._inlets_edges[target_inlet].remove(edge)
			del self._edges[edge]
		self.edgesRemoved.emit(edges_to_remove)

	# RELATIONS
	def getNodeInlets(self, node:NodeRef)->Iterable[InletRef]:
		assert isinstance(node, NodeRef)
		assert node.isValid()

		for inlet in self._nodes_inlets[node]:
			yield inlet

	def getNodeOutlets(self, node:NodeRef)->Iterable[OutletRef]:
		assert isinstance(node, NodeRef)
		assert node.isValid()

		for outlet in self._nodes_outlets[node]:
			yield outlet

	def getOutletEdges(self, outlet:OutletRef)->Iterable[EdgeRef]:
		assert isinstance(outlet, OutletRef)
		assert outlet.isValid()
		
		for edge in self._outlets_edges[outlet]:
			yield edge

	def getInletEdges(self, inlet:InletRef)->Iterable[EdgeRef]:
		assert isinstance(inlet, InletRef)
		assert inlet.isValid()

		for edge in self._inlets_edges[inlet]:
			yield edge

	def getOutletOwner(self, outlet: OutletRef)->NodeRef:
		assert isinstance(outlet, OutletRef)
		assert outlet.isValid()

		return self._outlets_owner[outlet]

	def getInletOwner(self, inlet:InletRef)->NodeRef:
		assert isinstance(inlet, InletRef)
		assert inlet.isValid()

		return self._inlets_owner[inlet]

	def getEdgeSource(self, edge: EdgeRef)->OutletRef:
		assert isinstance(edge, EdgeRef)
		assert edge.isValid()

		return self._edges_source[edge]

	def getEdgeTarget(self, edge:EdgeRef)->InletRef:
		assert isinstance(edge, EdgeRef)
		assert edge.isValid()

		return self._edges_target[edge]

	def getSourceNodes(self, node:NodeRef):
		assert isinstance(node, NodeRef)
		assert node.isValid()

		inlets = self.getNodeInlets(node)
		for inlet in inlets:
			for edge in self.getInletEdges(inlet):
				outlet = self.getEdgeSource(edge)
				yield self.getOutletOwner(outlet)

	def getTargetNodes(self, node:NodeRef):
		assert isinstance(node, NodeRef)
		assert node.isValid()

		outlets = self.getNodeOutlets(node)
		for outlet in outlets:
			for edge in self.getOutletEdges(outlet):
				inlet = self.getEdgeTarget(edge)
				yield self.getInletOwner(inlet)

	# ALGORHITMS
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

	# PROPERTIES
	def getNodeProperty(self, node:NodeRef, /, prop:str)->Any:
		assert isinstance(node, NodeRef)
		assert node.isValid()

		return self._nodes[node].get(prop)

	def setNodeProperty(self, node:NodeRef, /, **props)->None:
		assert isinstance(node, NodeRef)
		assert node.isValid()

		# change guard
		change = {}
		for key, val in props.items():
			if key not in self._nodes[node] or val != self._nodes[node][key]:
				change[key] = val

		self._nodes[node].update(change)
		self.nodesPropertyChanged.emit([node], list(change.keys()))

	def getInletProperty(self, inlet:InletRef, /, prop:str)->Any:
		assert isinstance(inlet, InletRef)
		assert inlet.isValid()

		return self._inlets[inlet].get(prop)

	def setInletProperty(self, inlet: InletRef, /, **props)->None:
		assert isinstance(inlet, InletRef)
		assert inlet.isValid()

		# change guard
		change = {}
		for key, val in props.items():
			if key not in self._inlets[inlet] or val != self._inlets[inlet][key]:
				change[key] = val

		self._inlets[inlet].update(change)
		self.inletsPropertyChanged.emit([inlet], list(change.keys()))

	def getOutletProperty(self, outlet:OutletRef, /, prop:str)->Any:
		assert isinstance(outlet, OutletRef)
		assert outlet.isValid()

		return self._outlets[outlet].get(prop)

	def setOutletProperty(self, outlet: OutletRef, /, **props)->None:
		assert isinstance(outlet, OutletRef)
		assert outlet.isValid()

		# change guard
		change = {}
		for key, val in props.items():
			if key not in self._outlets[outlet] or val != self._outlets[outlet][key]:
				change[key] = val

		self._outlets[outlet].update(change)
		self.outletsPropertyChanged.emit([outlet], list(change.keys()))

	def getEdgeProperty(self, edge:EdgeRef, /, prop:str)->Any:
		assert isinstance(edge, EdgeRef)
		assert edge.isValid()

		return self._edges[edge][prop]

	def setEdgeProperty(self, edge:EdgeRef, /, **props)->None:
		assert isinstance(edge, EdgeRef)
		assert edge.isValid()

		# change guard
		change = {}
		for key, val in props.items():
			if key not in self._edges[edge] or val != self._edges[edge][key]:
				change[key] = val

		self._edges[edge].update(change)
		self.edgesPropertyChanged.emit([edge], list(change.keys()))
