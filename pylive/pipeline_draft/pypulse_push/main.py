from core import Graph, Node
import cv2
import numpy as np
import warnings

class ReadNode(Node):
    def __init__(self, path):
        self.path = path
        super().__init__([])

    def execute(self, inputs):
        img = cv2.imread(self.path)
        if img is None:
            pink_placeholder = np.zeros((512, 512, 3), np.float32)
            pink_placeholder[:] = (1.0, 0.0, 1.0) 
            
            warnings.warn(f"Warning: Could not read {self.path}. Using pink fallback.")
            return pink_placeholder
        
        return img.astype(np.float32) / 255.0

class EdgeNode(Node):
    def execute(self, inputs):
        gray = cv2.cvtColor(inputs[0], cv2.COLOR_BGR2GRAY)
        laplacian = cv2.Laplacian(gray, cv2.CV_32F)
        # Return as 3-channel for blending
        edges = cv2.cvtColor(np.abs(laplacian), cv2.COLOR_GRAY2BGR)
        return np.clip(edges, 0, 1)

class GlowNode(Node):
    def __init__(self, source, intensity=1.0):
        self._intensity = intensity
        super().__init__([source])

    @property
    def intensity(self): return self._intensity

    @intensity.setter
    def intensity(self, val):
        self._intensity = val
        self.notify({"param": "intensity"}) # The observer pattern in action

    def execute(self, inputs):
        k = 21 # Large blur for glow
        glow = cv2.GaussianBlur(inputs[0], (k, k), 0)
        return glow * self._intensity

class BlendNode(Node):
    def execute(self, inputs):
        # A + B = Glowy Edges
        return np.clip(inputs[0] + inputs[1], 0, 1)

class ViewerNode(Node):
    def __init__(self, source, name="Output"):
        self.name = name
        super().__init__([source])

    def execute(self, inputs):
        if inputs[0] is not None:
            cv2.imshow(self.name, (inputs[0] * 255).astype(np.uint8))
        return inputs[0]

# --- MAIN ---

with Graph("EdgeGlow") as g:
    src   = ReadNode("assets\\colorchecker-classic_01.png") # Ensure test.jpg is in your folder
    edges = EdgeNode([src])
    glow  = GlowNode(edges)
    final = BlendNode([src, glow])
    view  = ViewerNode(final)

def on_mouse(event, x, y, flags, param):
    if event == cv2.EVENT_MOUSEMOVE:
        rect = cv2.getWindowImageRect("Output")
        h = max(rect[3], 1)
        # Update intensity based on mouse Y
        glow.intensity = (y / h) * 5.0

cv2.setMouseCallback("Output", on_mouse)
print("Move mouse Y to change Edge Glow intensity. Press 'q' to quit.")

while True:
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
cv2.destroyAllWindows()