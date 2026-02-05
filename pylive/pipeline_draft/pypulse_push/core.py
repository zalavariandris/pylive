import threading
import heapq
import cv2
import numpy as np
from typing import Self, Callable, List, Optional, Dict, Any

class Graph:
    _storage = threading.local()

    def __init__(self, name="PyPulse"):
        self._nodes = set()
        self._dirty_nodes = set()
        self._batch_depth = 0
        self.name = name

    @classmethod
    def current(cls) -> Optional['Graph']:
        return getattr(cls._storage, 'active_graph', None)

    def add_node(self, node: 'Node'):
        self._nodes.add(node)
        node.subscribe(self.on_node_change)

    def __enter__(self):
        self._old_context = Graph.current()
        Graph._storage.active_graph = self
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        Graph._storage.active_graph = self._old_context
        if not exc_type:
            # First-time ignition: everything is dirty
            self._dirty_nodes.update(self._nodes)
            self._render()

    def on_node_change(self, node: 'Node', changes: dict):
        self._dirty_nodes.add(node)
        if self._batch_depth == 0:
            self._render()

    def _render(self):
        if not self._dirty_nodes:
            return

        # 1. JIT ADJACENCY BUILD
        # We build the map of who is listening to whom right now
        adj = {n: set() for n in self._nodes}
        in_degree = {n: 0 for n in self._nodes}
        
        for downstream in self._nodes:
            for val in downstream._inputs.values():
                if isinstance(val, Node):
                    adj[val].add(downstream)
                    in_degree[downstream] += 1

        # 2. TOPOLOGICAL SORT (Kahn's)
        # Determines the correct mathematical order of operations
        queue = [n for n in self._nodes if in_degree[n] == 0]
        order = []
        while queue:
            u = queue.pop(0)
            order.append(u)
            for v in adj[u]:
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    queue.append(v)

        if len(order) < len(self._nodes):
            raise RuntimeError("Cycle detected in graph logic!")

        # 3. SELECTIVE EXECUTION
        # Only process nodes that are dirty or downstream of dirty nodes
        lookup = {node: i for i, node in enumerate(order)}
        exec_queue = []
        
        for node in self._dirty_nodes:
            heapq.heappush(exec_queue, (lookup[node], id(node), node))
        
        self._dirty_nodes.clear()
        processed = set()

        while exec_queue:
            priority, _, node = heapq.heappop(exec_queue)
            if node in processed: continue
            
            # Resolve Inputs (Constants vs Nodes)
            resolved = {k: (v.value if isinstance(v, Node) else v) 
                       for k, v in node._inputs.items()}
            
            # Execute
            node.value = node.render(**resolved)
            processed.add(node)

            # Propagate to children in the JIT map
            for child in adj[node]:
                heapq.heappush(exec_queue, (lookup[child], id(child), child))

    def batch(self):
        class BatchContext:
            def __init__(self, g): self.g = g
            def __enter__(self): self.g._batch_depth += 1
            def __exit__(self, *args):
                self.g._batch_depth -= 1
                if self.g._batch_depth == 0: self.g._execute()
        return BatchContext(self)


class Node:
    def __init__(self, **inputs):
        self._inputs = inputs
        self._observers = []
        self.value = None
        if g := Graph.current(): g.add_node(self)

    def set_inputs(self, **inputs):
        self._inputs.update(inputs)
        self.notify()

    def subscribe(self, callback):
        self._observers.append(callback)

    def notify(self): 
        for cb in self._observers: cb(self, {})

    def render(self, **inputs):
        raise NotImplementedError