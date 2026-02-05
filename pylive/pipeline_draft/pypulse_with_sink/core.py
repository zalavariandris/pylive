import cv2
import numpy as np
from functools import wraps
from typing import Callable, Any, Optional
import hashlib


class Node:
    def __init__(self, **inputs):
        self._inputs = inputs
        self._observers = []
        self.value = None
        self._hash_cache = None  # Cache for the last computed hash

    def get_hash(self) -> str:
        # If we already calculated the hash for this specific render, reuse it
        if self._hash_cache:
            return self._hash_cache

        hasher = hashlib.md5()
        # 1. Identity of the logic (Class name)
        hasher.update(self.__class__.__name__.encode())
        
        # 2. State of the logic (Function name if it's a FunctionNode)
        if hasattr(self, 'func'):
            hasher.update(self.func.__name__.encode())

        # 3. Inputs (The "DNA" of this specific instance)
        for key in sorted(self._inputs.keys()):
            val = self._inputs[key]
            if isinstance(val, Node):
                # Recursive call: The hash of this node depends on the hash of parents
                hasher.update(val.get_hash().encode())
            else:
                # Literal values (strings, numbers)
                hasher.update(f"{key}:{val}".encode())
        
        self._hash_cache = hasher.hexdigest()
        return self._hash_cache

    def set_inputs(self, **inputs):
        structure_changed = False
        for k, v in inputs.items():
            if isinstance(v, Node) or isinstance(self._inputs.get(k), Node):
                if self._inputs.get(k) is not v:
                    structure_changed = True
            self._inputs[k] = v
        
        self._hash_cache = None # Invalidate hash cache on input change
        self.notify({"structure_changed": structure_changed})

    def subscribe(self, callback):
        if callback not in self._observers:
            self._observers.append(callback)

    def unsubscribe(self, callback):
        if callback in self._observers:
            self._observers.remove(callback)

    def notify(self, changes=None): 
        for cb in self._observers: 
            cb(self, changes or {})

    def execute(self, **inputs):
        raise NotImplementedError


class FunctionNode(Node):
    def __init__(self, func, *args, **kwargs):
        self.func = func
        inputs = {f"_arg{i}": v for i, v in enumerate(args)}
        inputs.update(kwargs)
        super().__init__(**inputs)

    def execute(self, **resolved):
        args = [v for k, v in resolved.items() if k.startswith("_arg")]
        kwargs = {k: v for k, v in resolved.items() if not k.startswith("_arg")}
        return self.func(*args, **kwargs)
    

def op(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return FunctionNode(func, *args, **kwargs)
    return wrapper


class CacheNode(Node):
    def __init__(self, target: Node):
        super().__init__(**target._inputs)
        self.target = target
        self._last_executed_hash = None

    def execute(self, **resolved):
        # Ask the target for its current fingerprint
        current_hash = self.target.get_hash()

        # If the fingerprints match, return the stored value
        if current_hash == self._last_executed_hash and self.value is not None:
            return self.value

        # Miss: Compute and store
        self.value = self.target.execute(**resolved)
        self._last_executed_hash = current_hash
        return self.value

    def set_inputs(self, **inputs):
        # Sync inputs to target and invalidate target's hash
        self.target.set_inputs(**inputs)
        super().set_inputs(**inputs)


class Sink:
    def __init__(self, target: Node, side_effect: Callable):
        self.target = target
        self.side_effect = side_effect
        self._batch_depth = 0
        self._nodes_in_branch = set()
        
        self._rebuild_and_subscribe()
        self.render()

    def batch(self):
        """Context manager to group multiple updates into one render."""
        class BatchContext:
            def __init__(self, g): self.g = g
            def __enter__(self): 
                self.g._batch_depth += 1
                return self.g
            def __exit__(self, *args):
                self.g._batch_depth -= 1
                # Trigger execution only when the outermost batch closes
                if self.g._batch_depth == 0: 
                    self.g.render()
        return BatchContext(self)

    def _rebuild_and_subscribe(self):
        for node in self._nodes_in_branch:
            node.unsubscribe(self._on_bump)
        self._nodes_in_branch = self._discover(self.target)
        for node in self._nodes_in_branch:
            node.subscribe(self._on_bump)

    def _discover(self, node: Node, visited=None) -> set:
        if visited is None: visited = set()
        if node in visited: return visited
        visited.add(node)
        for val in node._inputs.values():
            if isinstance(val, Node):
                self._discover(val, visited)
        return visited

    def _on_bump(self, node, changes):
        if changes.get("structure_changed"):
            self._rebuild_and_subscribe()
            
        # Only render immediately if we aren't currently in a batch block
        if self._batch_depth == 0:
            self.render()

    def render(self):
        # 1. Build Adjacency
        adj = {n: set() for n in self._nodes_in_branch}
        in_degree = {n: 0 for n in self._nodes_in_branch}
        for u in self._nodes_in_branch:
            for val in u._inputs.values():
                if isinstance(val, Node):
                    adj[val].add(u)
                    in_degree[u] += 1

        # 2. Topological Sort
        queue = [n for n in self._nodes_in_branch if in_degree[n] == 0]
        order = []
        while queue:
            u = queue.pop(0)
            order.append(u)
            for v in adj[u]:
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    queue.append(v)

        # 3. Execution
        for node in order:
            resolved = {k: (v.value if isinstance(v, Node) else v) 
                        for k, v in node._inputs.items()}
            node.value = node.execute(**resolved)

        # 4. Final Pulse
        self.side_effect(self.target.value)

