from typing import Iterable

def unique_name(name, names):
	# Extract all existing names
	
	digit = 1

	# Regex to extract the name part (without trailing digits)
	match = re.search(r'(.*?)(\d*)$', name)
	if match:
		# Name part without digits
		name_part = match.group(1)
	
	# Loop to find a unique name
	while name in names:
		# Append the current digit to the name part
		name = f"{name_part}{digit}"
		digit += 1
	
	return name

import weakref
class TriggerInPort:
	def __init__(self, name, node):
		self._name = name
		self._node = node
		self._events = {
			'on_trigger': set(),
			'on_destroy': set()
		}

	@property
	def name(self):
		return self._name

	@property
	def node(self):
		return self._node

	def event(self, fn):
		self._events[fn.__name__].add(fn)

	def destroy(self):
		# Clear the listeners list when destroying
		for cb in self._events['on_destroy']:
			cb()
		self._events = dict()

	# def __del__(self):
	# 	self.destroy()

	def trigger(self, props=None):
		for cb in self._events['on_trigger']:
			cb(props)

	def __repr__(self):
		return f"Inlet({self.name})"

	def __hash__(self):
		return hash( (self.__class__, self._name) )


class TriggerOutPort:
	def __init__(self, name, node):
		self._name = name
		self._node = node
		self._events = {
			'on_destroy': set(),
			'on_connect': set(),
			'on_disconnect': set()
		}
		self._targets:Set[TriggerInPort] = set()

	def __repr__(self):
		return f"Outlet({self.name})"

	@property
	def node(self):
		return self._node

	@property
	def name(self):
		return self._name

	@property
	def targets(self):
		for target in self._targets:
			yield target

	def event(self, fn):
		self._events[fn.__name__].add(fn)

	def connect(self, target:TriggerInPort):
		for cb in self._events["on_connect"]:
			cb(self, target)
		self._targets.add(target)

	def disconnect(self, target:TriggerInPort):
		for cb in self._events["on_disconnect"]:
			cb(self, target)
		self._targets.remove(target)

	def destroy(self):
		# Clear the listeners list when destroying
		for cb in self._events['on_destroy']:
			cb(self)
		self._events = dict()

	# def __del__(self):
	# 	self.destroy()

	def trigger(self, props=None):
		for target in self._targets:
			target.trigger(props)

	def __hash__(self):
		return hash( (self.__class__, self._name) )


class Node:
	def __init__(self, name, graph):
		self._name = name
		self._graph = graph
		self._events = dict({
			"on_destroy": []
		})
		self._in_ports = dict()
		self._out_ports = dict()

	def __repr__(self):
		return f"Node({self.name})"

	@property
	def name(self):
		return self._name

	@property
	def graph(self):
		return self._graph

	@property
	def inlets(self):
		for name, port in self._in_ports.items():
			yield port

	@property
	def outlets(self):
		for name, port in self._out_ports.items():
			yield port

	def event(self, fn):
		self._events[fn.__name__].append(fn)

	def destroy(self):
		for callback in self._events["on_destroy"]:
			callback()

		for name, in_port in self._in_ports.items():
			in_port.destroy()

		for name, out_port in self._out_ports.items():
			out_port.destroy()

	def __del__(self):
		self.destroy()

	def inlet(self, name):
		assert( name not in [n.name for n in self._in_ports])
		# create an inlet
		port = TriggerInPort(name, self)
		self._in_ports[name] = port
		return port

	def outlet(self, name):
		assert( name not in [n.name for n in self._out_ports])
		# create an outlet
		port = TriggerOutPort(name, self)
		self._out_ports[name] = port
		return port

	def __hash__(self):
		return hash( (self.__class__, self._name) )


import re
class Graph:
	def __init__(self, name):
		self._name = name
		self._nodes = set()
		self._events = dict({
			"on_destroy": [],
			"on_node": [],
			"on_connect": [],
			"on_disconnect": []
		})

	def __repr__(self):
		return f"Graph({self.name})"

	@property
	def name(self):
		return self._name

	@property
	def nodes(self):
		for n in self._nodes:
			yield n

	@property
	def edges(self):
		for n in self._nodes:
			for outlet in n.outlets:
				for inlet in outlet.targets:
					yield (outlet, inlet)

	def event(self, fn):
		self._events[fn.__name__].append(fn)

	def node(self, name:str):
		#create a node
		name = self.unique_name(name)
		assert( name not in [n.name for n in self._nodes])
		node = Node(name, self)
		for cb in self._events['on_node']:
			cb(node)
		self._nodes.add(node)
		return node

	def unique_name(self, name):
		names = [n.name for n in self.nodes]
		return unique_name(name, names)

	def __hash__(self):
		return hash( (self.__class__, self._name) )

def root_nodes(G:Graph)->Iterable[Node]:
	"""Yield all root nodes (nodes without outlets) in the graph."""
	for node in G._nodes:
		if not list(node.inlets):  # Check if the node has no outlets
			yield node  # Yield the root node

def dfs(G:Graph)->Iterable[Node]:
	"""Perform DFS starting from the root notes and yield each node."""

	start_nodes = root_nodes(G)
	visited = set()  # Set to track visited nodes

	def dfs_visit(node):
		"""Recursive helper function to perform DFS."""
		visited.add(node)
		yield node  # Yield the current node

		# Iterate through all adjacent edges from the current node
		for outlet in node.outlets:
			for target in outlet.targets:
				if target.node not in visited:  # Check if the target node has been visited
					yield from dfs_visit(target.node)  # Recursive call

	for start_node in start_nodes:
		if start_node not in visited:  # Check if the start node has been visited
			yield from dfs_visit(start_node)  # Start DFS from the start node


if __name__ == "__main__":
	g = Graph("main")

	@g.event
	def on_node(node):
		print(f"node added: {node}")

	ticknode = g.node("ticknode")
	outlet = ticknode.outlet("out")
	@outlet.event
	def on_connect(outlet, inlet):
		print(f"connected: {outlet} to {inlet}")
	@outlet.event
	def on_disconnect(outlet, inlet):
		print(f"disconnected: {outlet} from {inlet}")
	prevnode = g.node("prevnode")
	inlet = prevnode.inlet("in")

	outlet.connect(inlet)

	@inlet.event
	def on_trigger(props=None):
		print(f"inlet received: '{props}'")

	outlet.trigger("hello worlds")
	print(list(g.edges))

	print("edges:", list(g.edges))


	print("# DFS #")
	for n in reversed(list(dfs(g))):
		print("-", n)

	outlet.disconnect(inlet)
	outlet.trigger("this msg is not received")

