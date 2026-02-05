# --- Concrete Example ---
from pylive.pipeline_draft.pypulse_push.core_classbased import Graph, Node
import cv2
import numpy as np
import warnings


class ReadNode(Node):
    def render(self, path=""):
        print(f"Reading image from {path}")
        img = cv2.imread(path)
        if img is None: 
            pink = np.zeros((512, 512, 3), np.float32)
            pink[:] = (1.0, 0.0, 1.0) # Pink of Death
            warnings.warn(f"Warning: Could not read {self.path}. Using pink fallback.")
            return pink

        return img.astype(np.float32) / 255.0


class BlurNode(Node):
    def render(self, image=None, sigma=1.0):
        k = int(sigma * 3) | 1
        return cv2.GaussianBlur(image, (k, k), sigma)


class ViewerNode(Node):
    def render(self, image=None, title="Render"):
        if image is not None:
            cv2.imshow(title, (image * 255).astype(np.uint8))
        return image

# Usage
with Graph() as g:
    # Notice: we can define sigma as a constant here
    src = ReadNode(path="assets\\colorchecker-classic_01.png")
    blur = BlurNode(image=src, sigma=5.0) 
    view = ViewerNode(image=blur, title="JIT Pipeline")


def on_mouse(event, x, y, flags, param):
    if event == cv2.EVENT_MOUSEMOVE:
        rect = cv2.getWindowImageRect("JIT Pipeline")
        h = max(rect[3], 1)
        # Update intensity based on mouse Y
        blur.set_inputs(sigma=(y / h) * 10)  # Scale to [0, 10]

cv2.setMouseCallback("JIT Pipeline", on_mouse)
print("Move mouse Y to change Edge Glow intensity. Press 'q' to quit.")

while True:
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()

