import sys
import numpy as np
from PySide6.QtWidgets import QApplication, QGraphicsScene, QGraphicsView, QGraphicsPixmapItem
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import QTimer, Qt

def numpy_to_qimage(image: np.ndarray) -> QImage:
    if image.ndim == 2:
        height, width = image.shape
        return QImage(image.data, width, height, width, QImage.Format_Grayscale8)
    elif image.ndim == 3:
        height, width, channels = image.shape
        if channels == 3:
            return QImage(image.data, width, height, width * 3, QImage.Format_RGB888)
        elif channels == 4:
            return QImage(image.data, width, height, width * 4, QImage.Format_RGBA8888)
    raise ValueError("Unsupported image shape")

import qimage2ndarray
class LiveImageViewer(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        # Placeholder image
        dummy_image = np.zeros((200, 300, 3), dtype=np.uint8)
        qimage = numpy_to_qimage(dummy_image)
        pixmap = QPixmap.fromImage(qimage)

        self.pixmap_item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(self.pixmap_item)

        self.setRenderHint(QPainter.Antialiasing)

    def update_image(self, image: np.ndarray):
        image = np.ascontiguousarray(image)
        qimage = numpy_to_qimage(image)
        pixmap = QPixmap.fromImage(qimage)
        self.pixmap_item.setPixmap(pixmap)

if __name__ == "__main__":
    from PySide6.QtGui import QPainter

    app = QApplication(sys.argv)
    viewer = LiveImageViewer()
    viewer.setWindowTitle("Live Updating NumPy Image")
    viewer.resize(400, 300)
    viewer.show()

    def generate_image_frame(tick):
        """Simulate an image that changes over time."""
        h, w = 2000, 3000
        frame = np.zeros((h, w, 3), dtype=np.uint8)
        frame[:, :w//2] = [tick % 255, 0, 0]  # Red intensity cycles
        frame[:, w//2:] = [0, tick % 255, 0]  # Green intensity cycles
        return frame

    counter = 0
    def update_frame():
        global counter
        image = generate_image_frame(counter)
        viewer.update_image(image)
        counter += 5

    # Update image every 100 ms
    timer = QTimer()
    timer.timeout.connect(update_frame)
    timer.start(1000/60)

    sys.exit(app.exec_())
