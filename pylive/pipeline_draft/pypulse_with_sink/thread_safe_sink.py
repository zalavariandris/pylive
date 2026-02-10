import queue

class ThreadSafeSink(Sink):
    def __init__(self, target, side_effect):
        self.render_queue = queue.Queue()
        super().__init__(target, side_effect)

    def _on_bump(self, node, changes):
        # Instead of rendering immediately, we push a "request" to a queue
        self.render_queue.put(True)

    def tick(self):
        """Call this in your main loop."""
        # Check if any node pushed a change
        needs_render = False
        while not self.render_queue.empty():
            self.render_queue.get()
            needs_render = True
        
        if needs_render and self._batch_depth == 0:
            self.render()