import cv2
import numpy as np
import heapq
from typing import List, Callable, Any

# --- PyPulse Engine ---

class PulseNode:
    def __init__(self, inputs: List['PulseNode'] = None):
        self.inputs = inputs or []
        self.outputs = []
        self.level = max([i.level for i in self.inputs], default=-1) + 1
        self._dirty = True
        self._cache = None
        for i in self.inputs:
            i.outputs.append(self)

    def invalidate(self):
        self._dirty = True

    def pull(self) -> Any:
        if self._dirty:
            input_data = [i.pull() for i in self.inputs]
            self._cache = self.execute(input_data)
            self._dirty = False
        return self._cache

    def execute(self, inputs: List[Any]) -> Any:
        raise NotImplementedError

class PulseGraph:
    def __init__(self):
        self._queue = []

    def trigger(self, origin_node: PulseNode):
        processed = set()
        heapq.heappush(self._queue, (origin_node.level, id(origin_node), origin_node))
        while self._queue:
            _, _, node = heapq.heappop(self._queue)
            if node in processed:
                continue
            
            node.invalidate()
            processed.add(node)

            if isinstance(node, PulseSink) and not self._queue:
                node.on_pulse_complete()

            for out in node.outputs:
                heapq.heappush(self._queue, (out.level, id(out), out))

class PulseSink(PulseNode):
    def __init__(self, source: PulseNode, callback: Callable):
        super().__init__([source])
        self.callback = callback

    def on_pulse_complete(self):
        self.callback()

    def execute(self, inputs):
        return inputs[0]

# --- Custom Nodes ---

class ReadNode(PulseNode):
    def __init__(self, path):
        super().__init__([])
        self.img = cv2.imread(path)
        if self.img is None: # Fallback if image not found
            self.img = np.zeros((512, 512, 3), dtype=np.uint8)
            cv2.putText(self.img, "Image Not Found", (50, 250), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
    def execute(self, _):
        return self.img.astype(np.float32) / 255.0

class BrightenNode(PulseNode):
    def __init__(self, source: PulseNode, factor: float, graph: PulseGraph):
        super().__init__([source])
        self._factor = factor
        self.graph = graph

    @property
    def factor(self): return self._factor

    @factor.setter
    def factor(self, val):
        if self._factor != val:
            self._factor = val
            self.graph.trigger(self)

    def execute(self, inputs):
        # inputs[0] is our normalized float image
        return np.clip(inputs[0] * self._factor, 0, 1)