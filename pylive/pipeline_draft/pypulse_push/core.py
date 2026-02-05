from typing import Self, Callable, List, Optional
import cv2
import numpy as np
import threading
import heapq

class Graph:
    _storage = threading.local()

    def __init__(self, name="PyPulse"):
        self._nodes = set()
        self.name = name
        self._batch_depth = 0
        self._dirty_nodes = set()

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
            # Ignition: Mark roots as dirty to start the first flow
            for node in self._nodes:
                if not node.inputs:
                    self._dirty_nodes.add(node)
            self._execute_()

    def batch(self):
        class BatchContext:
            def __init__(self, g):
                self.g = g
                
            def __enter__(self):
                self.g._batch_depth += 1

            def __exit__(self, *args):
                self.g._batch_depth -= 1
                if self.g._batch_depth == 0: self.g._execute_()

        return BatchContext(self)

    def on_node_change(self, node: 'Node', changes: dict):
        self._dirty_nodes.add(node)
        if self._batch_depth == 0:
            self._execute_()

    def _execute_(self):
        if not self._dirty_nodes:
            return

        queue = []
        seen = set()

        def add_to_queue(n):
            if n not in seen:
                # level ensures topological order, id(n) breaks ties
                heapq.heappush(queue, (n.level, id(n), n))
                seen.add(n)

        for node in self._dirty_nodes:
            add_to_queue(node)
        
        self._dirty_nodes.clear()

        while queue:
            _, _, node = heapq.heappop(queue)
            
            input_vals = [i.value for i in node.inputs]
            
            # Guard against cold starts/empty inputs
            if any(v is None for v in input_vals) and node.inputs:
                continue

            node.value = node.execute(input_vals)
            
            # Propagate to children
            if node.value is not None:
                for out in node.outputs:
                    add_to_queue(out)

class Node:
    def __init__(self, inputs: Optional[List['Node']] = None):
        current = Graph.current()
        if not current:
            raise RuntimeError("Nodes must be created inside a 'with Graph():' block.")
        
        self.graph = current
        # Fix: Standardize inputs as a list
        self.inputs = inputs if isinstance(inputs, list) else ([inputs] if inputs else [])
        self.outputs = []
        self.value = None
        self._observers: List[Callable] = []

        # Fix: Level calculation
        self.level = max([i.level for i in self.inputs], default=-1) + 1

        for i in self.inputs:
            i.outputs.append(self)

        self.graph.add_node(self)

    def subscribe(self, callback: Callable[[Self, dict], None]):
        self._observers.append(callback)

    def notify(self, changes: Optional[dict] = None):
        """Triggers the graph update via the subscription."""
        changes = changes or {}
        for callback in self._observers:
            callback(self, changes)

    def execute(self, inputs: list):
        raise NotImplementedError