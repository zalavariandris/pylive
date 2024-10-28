from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
import math


class RectItem(QGraphicsRectItem):
    def __init__(self, x, y, w, h):
        super().__init__(x, y, w, h)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)

        self.setBrush(Qt.green)

        # self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        # self._view = view

class InfiniteGraphicsView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        

        self._defaultDragMode = QGraphicsView.RubberBandDrag
        self.setDragMode(self._defaultDragMode)
        self.setRenderHint(QPainter.Antialiasing)

        # Background brush color (set your preferred color)
        self.setBackgroundBrush(Qt.white)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.setTransformationAnchor(QGraphicsView.NoAnchor)

        self.setCacheMode(QGraphicsView.CacheBackground)
        self.setViewportUpdateMode(QGraphicsView.BoundingRectViewportUpdate)

        # self.set_scale_range(0.3, 2)

        max_size = 32767
        self.setSceneRect(-max_size, -max_size, max_size * 2, max_size * 2)
        self.scale_step = 1.2

        self.centerOn(0,0)

    def showEvent(self, event):
        if self.scene():
            self.centerScene()
            self.fitScene()
        else:
            self.centerOn(0,0)

    def centerScene(self):
        if self.scene():
            boundingRect = self.scene().itemsBoundingRect()
            self.centerOn(boundingRect.center())

    def fitScene(self, margin=5):
        if self.scene():
            boundingRect = self.scene().itemsBoundingRect()
            boundingRect.adjust(-margin, -margin, margin, margin)
            # print()
            self.fitInView(QRectF(-300,-300, 600, 600))

    def getScale(self):
        return self.transform().m11()

    def wheelEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifiers.MetaModifier:
            delta = event.angleDelta()

            if delta.y() == 0:
                event.ignore()
                return

            d = delta.y() / abs(delta.y())
            factor = math.pow(1.003, delta.y())
            if self.getScale() * factor < 10 and self.getScale() * factor > 0.3:
                oldPos = self.mapToScene(event.position().toPoint())
                
                self.scale(factor, factor)
                newPos = self.mapToScene(event.position().toPoint())
                delta = newPos-oldPos
                self.translate(delta.x(), delta.y())

        else:
            return super().wheelEvent(event)

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        if event.key() == Qt.Key_Alt:
            self.setDragMode(QGraphicsView.ScrollHandDrag)
        return super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        super().keyReleaseEvent(event)
        if event.key() == Qt.Key_Alt:
            self.setDragMode(QGraphicsView.RubberBandDrag)
        return super().keyReleaseEvent(event)
        


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = InfiniteGraphicsView()
    scene = QGraphicsScene()
    # scene.setSceneRect(QRect(-9999//2,-9999//2, 9999, 9999))

    window.setScene(scene)
    max_size = 32767
    window.setSceneRect(-max_size, -max_size, max_size * 2, max_size * 2)
    
    rect = RectItem(0,0,50,50)
    window.scene().addItem(rect)
    rect = RectItem(100,0,50,50)
    window.scene().addItem(rect)
    rect = RectItem(0,100,50,50)
    window.scene().addItem(rect)
    window.show()
    # window.fitInView(scene.sceneRect())
    sys.exit(app.exec())