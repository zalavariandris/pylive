from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

import networkx as nx

from pylive.utils.geo import intersect_ray_with_rectangle

class GraphModel(QObject):
	nodesAdded = Signal(list) #List[Tuple[Hashable, Hashable]]
	nodesAboutToBeRemoved = Signal(list) #List[Tuple[Hashable, Hashable]]
	nodesChanged = Signal(dict) # Dict[Hashable, Dict[str, Any]]
	nodesRemoved = Signal(list)

	edgesAdded = Signal(list) #List[Tuple[Hashable, Hashable]]
	edgesAboutToBeRemoved = Signal(list) #List[Tuple[Hashable, Hashable]]
	edgesPropertiesChanged = Signal(dict) # Dict[Hashable, Dict[str, Any]]
	edgesRemoved = Signal(list)

	def __init__(self, G:nx.DiGraph=nx.DiGraph(), parent=None):
		super().__init__(parent=parent)
		self.G:nx.DiGraph = G

		for n in self.G.nodes:
			node = self.addNode(n)

		for e in self.G.edges:
			u, v = e
			
			self.addEdge(u, v)

	def patch(self, G:nx.DiGraph):
		...
		raise NotImplementedError("Not yet implemented")

	def nodes(self)->list[Hashable]:
		return [n for n in self.G.nodes]

	def __del__(self):
		del self.G
		# self.nodesAdded.disconnect()
		# self.nodesAboutToBeRemoved.disconnect()
		# self.nodesPropertyChanged.disconnect()
		# self.nodesRemoved.disconnect()
		# self.edgesAdded.disconnect()
		# self.edgesAboutToBeRemoved.disconnect()
		# self.edgesPropertyChanged.disconnect()
		# self.edgesRemoved.disconnect()

	def addNode(self, n:Hashable, / , **props):
		print("add node", n)
		self.G.add_node(n, **props)
		self.nodesAdded.emit([n])
		self.nodesChanged.emit({n:props})

	def addEdge(self, u:Hashable, v:Hashable, / , **props):
		if u not in self.G.nodes:
			self.addNode(u)
		if v not in self.G.nodes:
			self.addNode(v)

		self.G.add_edge(u, v, **props)
		self.edgesAdded.emit([(u, v)])

	def removeNode(self, n:Hashable):
		self.nodesAboutToBeRemoved.emit([n])
		self.G.remove_node(n)

	def removeEdge(self, u:Hashable, v:Hashable):
		self.edgesAboutToBeRemoved.emit([(u,v)])
		self.G.remove_edge( u,v )

	def setNodeProperties(self, n:Hashable, /, **props):
		# change guard TODO: find removed props
		change = {}
		for key, val in props.items():
			if key not in self.G.nodes[n] or val != self.G.nodes[n][key]:
				change[key] = val
		nx.set_node_attributes(self.G, {n: change})
		self.nodesChanged.emit({n: change})

	def getNodeProperty(self, n:Hashable, name, /):
		return self.G.nodes[n][name]

	def setEdgeProperties(self, u:Hashable, v:Hashable, /, **props):
		nx.set_edge_attributes(self.G, {(u,v): props})
		self.nodesChanged.emit([n], list(props.keys()) )

	def getEdgeProperty(self, u:Hashable, v:Hashable, prop, /):
		return self.G.edges[u, v][prop]

