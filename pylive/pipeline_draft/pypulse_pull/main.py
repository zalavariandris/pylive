# Initialize PyPulse
from core import *
import cv2


graph = PulseGraph()
win_name = "PyPulse Interactive"

# 1. Build the Graph
# Note: Provide a valid image path or use a placeholder
source = ReadNode("assets\\colorchecker-classic_01.png") 
brighten = BrightenNode(source, factor=1.0, graph=graph)

def on_dirty():
    """This is called by PulseSink when the graph is ready to redraw."""
    # Pull the processed data
    result = viewer.pull()
    # Convert back to 8-bit for OpenCV display
    display_img = (result * 255).astype(np.uint8)
    cv2.imshow(win_name, display_img)

viewer = PulseSink(brighten, callback=on_dirty)

# 2. Mouse Callback
def mouse_callback(event, x, y, flags, param):
    if event == cv2.EVENT_MOUSEMOVE:
        # Get window width to normalize X
        rect = cv2.getWindowImageRect(win_name)
        width = max(rect[2], 1)
        # Map 0 -> width to 0.0 -> 3.0 factor
        new_factor = (x / width) * 3.0
        brighten.factor = new_factor

# 3. OpenCV Setup
cv2.namedWindow(win_name)
cv2.setMouseCallback(win_name, mouse_callback)

# Initial render
on_dirty()

print("Move mouse horizontally to adjust brightness. Press 'q' to quit.")
while True:
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()