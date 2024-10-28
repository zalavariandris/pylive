from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
import math

class InfiniteGraphicsView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setRenderHint(QPainter.Antialiasing)

        # Background brush color (set your preferred color)
        self.setBackgroundBrush(Qt.white)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

        self.setCacheMode(QGraphicsView.CacheBackground)
        self.setViewportUpdateMode(QGraphicsView.BoundingRectViewportUpdate)

        self.set_scale_range(0.3, 2)

        max_size = 32767
        self.setSceneRect(-max_size, -max_size, max_size * 2, max_size * 2)
        self.scale_step = 1.2

    def center_scene(self):
        if self.scene():
            self.scene().setSceneRect(QRectF())
            scene_rect = self.scene().sceneRect()

            if scene_rect.width() > self.rect().width() or scene_rect.height() > self.rect().height():
                self.fitInView(scene_rect, Qt.KeepAspectRatio)

            self.centerOn(scene_rect.center())

    def wheelEvent(self, event):
        delta = event.angleDelta()

        if delta.y() == 0:
            event.ignore()
            return

        d = delta.y() / abs(delta.y())

        if d > 0.0:
            self.scale_up()
        else:
            self.scale_down()

    def get_scale(self):
        return self.transform().m11()

    def set_scale_range(self, minimum, maximum):
        if maximum < minimum:
            minimum, maximum = maximum, minimum
        minimum = max(0.0, minimum)
        maximum = max(0.0, maximum)

        self._scale_range = (minimum, maximum)
        self.setup_scale(self.transform().m11())

    def scale_up(self):
        factor = math.pow(self.scale_step, 1.0)

        if self._scale_range[1] > 0:
            t = self.transform()
            t.scale(factor, factor)
            if t.m11() >= self._scale_range[1]:
                self.setup_scale(t.m11())
                return

        self.scale(factor, factor)

    def scale_down(self):

        factor = math.pow(self.scale_step, -1.0)

        if self._scale_range[0] > 0:
            t = self.transform()
            t.scale(factor, factor)
            if t.m11() <= self._scale_range[0]:
                self.setup_scale(t.m11())
                return

        self.scale(factor, factor)

    def setup_scale(self, scale):
        scale = max(self._scale_range[0], min(self._scale_range[1], scale))

        if scale <= 0:
            return

        if scale == self.transform().m11():
            return

        matrix = self.transform()
        matrix.scale(scale, scale)
        self.setTransform(matrix, False)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Alt:
            self.setDragMode(QGraphicsView.ScrollHandDrag)
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Alt:
            self.setDragMode(QGraphicsView.RubberBandDrag)
        return super().keyReleaseEvent(event)

    def mousePressEvent(self, event):
        # super().mousePressEvent(event)
        # if event.button() == Qt.LeftButton:
        self.mousePressPos = event.scenePosition()
        if event.buttons() == Qt.MiddleButton:
            print("set drag mode to ScrollHandDrag")
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            self._last_mouse_pos = event.position()
        return super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.dragMode() == QGraphicsView.ScrollHandDrag and event.buttons() == Qt.MiddleButton:
            if self._last_mouse_pos is not None:
                # Calculate the difference and move the view accordingly
                diff = event.position() - self._last_mouse_pos
                self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - diff.x())
                self.verticalScrollBar().setValue(self.verticalScrollBar().value() - diff.y())

            self._last_mouse_pos = event.position()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if self.dragMode() == QGraphicsView.ScrollHandDrag and  not (event.modifiers() & Qt.AltModifier):
            self.setDragMode(QGraphicsView.RubberBandDrag)
        return super().mouseReleaseEvent(event)

    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)

        def draw_grid(grid_step):
            window_rect = self.rect()
            tl = self.mapToScene(window_rect.topLeft())
            br = self.mapToScene(window_rect.bottomRight())

            left = math.floor(tl.x() / grid_step - 0.5)
            right = math.floor(br.x() / grid_step + 1.0)
            bottom = math.floor(tl.y() / grid_step - 0.5)
            top = math.floor(br.y() / grid_step + 1.0)

            # Draw vertical lines
            for xi in range(int(left), int(right) + 1):
                line = QLineF(xi * grid_step, bottom * grid_step, xi * grid_step, top * grid_step)
                painter.drawLine(line)

            # Draw horizontal lines
            for yi in range(int(bottom), int(top) + 1):
                line = QLineF(left * grid_step, yi * grid_step, right * grid_step, yi * grid_step)
                painter.drawLine(line)

        # Set your preferred colors for the grid lines
        fine_grid_color = Qt.lightGray  # Replace with desired color
        coarse_grid_color = Qt.gray  # Replace with desired color

        pen_fine = QPen(fine_grid_color, 1.0)
        painter.setPen(pen_fine)
        draw_grid(15)

        pen_coarse = QPen(coarse_grid_color, 1.0)
        painter.setPen(pen_coarse)
        draw_grid(150)

    def showEvent(self, event):
        super().showEvent(event)
        self.center_scene()

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = InfiniteGraphicsView()
    scene = QGraphicsScene()
    scene.setSceneRect(QRect(-9999//2,-9999//2, 9999, 9999))
    window.setScene(scene)
    
    rect = QGraphicsRectItem(0,0,100,100)
    window.scene().addItem(rect)
    window.show()
    sys.exit(app.exec())