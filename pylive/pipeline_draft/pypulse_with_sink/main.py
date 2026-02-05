
import cv2
import numpy as np
from core import Node, Sink, op, CacheNode

if __name__ == "__main__":
    # ... (rest of your original setup code) ...
    def read_image(path):
        print("Reading image from:", path)
        img = cv2.imread(path)
        return img.astype(np.float32) / 255.0 if img is not None else None

    def blur_image(image, sigma):
        if image is None: return None
        k = int(sigma * 3) | 1
        return cv2.GaussianBlur(image, (k, k), sigma)
    
    def edge_detect(image, low_threshold, high_threshold):
        if image is None: return None
        gray = cv2.cvtColor((image * 255).astype(np.uint8), cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, low_threshold, high_threshold)
        return cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR).astype(np.float32) / 255.0
    
    def blend_images(foreground, background, mix):
        if foreground is None:
            return background
        
        if background is None:
            return foreground
        
        return cv2.addWeighted(foreground, mix, background, 1 - mix, 0)

    img_node =   op(read_image)(path="assets\\colorchecker-classic_01.png")
    img_cached = CacheNode(img_node)  # Wrap the read image node in a cache
    blur_node =  op(blur_image)(image=img_cached, sigma=5.0)
    edge_node =  op(edge_detect)(image=img_cached, low_threshold=50, high_threshold=150)
    blend_node = op(blend_images)(foreground=blur_node, background=edge_node, mix=0.5)

    def update_viewer(data):
        if data is not None:
            display = (data * 255).astype(np.uint8)
            cv2.imshow("Effect", display)

    app = Sink(blend_node, update_viewer)

    # Example of batch usage in a callback
    def on_mouse(event, x, y, flags, param):
        if event == cv2.EVENT_MOUSEMOVE:
            rect = cv2.getWindowImageRect("Effect")
            if rect:
                h = max(rect[3], 1)
                # Using the batch functionality
                print(f"Mouse at ({x}, {y}), updating parameters...")
                with app.batch():
                    # Even if we changed 10 nodes here, render() only runs once at the end
                    blur_node.set_inputs(sigma=(y / h) * 20.0)
                    edge_node.set_inputs(low_threshold=(x / rect[2]) * 100, high_threshold=((rect[2] - x) / rect[2]) * 200)

    cv2.setMouseCallback("Effect", on_mouse)
    
    while True:
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cv2.destroyAllWindows()