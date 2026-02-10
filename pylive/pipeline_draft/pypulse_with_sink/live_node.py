
import threading
import time
from pylive.pipeline_draft.pypulse_with_sink.core import Node
import cv2

class LiveNode(Node):
    def __init__(self, **inputs):
        super().__init__(**inputs)
        self.is_pure = False

    def get_hash(self) -> str:
        # If we are impure, we generate a fresh hash every time we are ASKED,
        # OR we generate one only when 'refresh' is called.
        # Let's use a versioning approach:
        if not self.is_pure:
            # If we don't have a hash yet (invalidated), create a unique one
            if self._hash_cache is None:
                self._hash_cache = f"{self.__class__.__name__}-{time.time_ns()}"
            return self._hash_cache
        
        return super().get_hash()

    def refresh(self):
        """The 'heartbeat' of the impure node."""
        # 1. Invalidate our own hash so get_hash() produces a new fingerprint
        self._hash_cache = None
        
        # 2. Tell the Sink to start a render pass
        self.notify({"reason": "live_update"})

class ThreadedWebcamNode(LiveNode):
    def __init__(self, device_id=0):
        super().__init__(device_id=device_id)
        self._lock = threading.Lock()
        self._latest_frame = None
        self._version = 0
        
        self.cap = cv2.VideoCapture(device_id)
        self.running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()

    def _capture_loop(self):
        while self.running:
            ret, frame = self.cap.read()
            if ret:
                with self._lock:
                    self._latest_frame = frame
                    self._version += 1
                    # Invalidate hash inside the lock so it stays 
                    # perfectly in sync with the version increment
                    self._hash_cache = None 
                
                # Notify is safe to call outside the lock
                self.notify({"reason": "new_frame"})
            else:
                time.sleep(0.01)

    def get_hash(self) -> str:
        with self._lock:
            if self._hash_cache is None:
                self._hash_cache = f"webcam-{self._version}"
            return self._hash_cache

    def execute(self, **kwargs):
        with self._lock:
            # We return a shallow copy (reference) of the current frame.
            # In Python, this is safe because the underlying memory 
            # won't be freed as long as this reference exists.
            return self._latest_frame

    def stop(self):
        self.running = False
        self.thread.join()
        self.cap.release()