from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
import math


class RectItem(QGraphicsRectItem):
    def __init__(self, x, y, w, h, view):
        super().__init__(x, y, w, h)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)

        self.setBrush(Qt.green)

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self._view = view


    # def itemChange(self, change, value):
    #     if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
    #         print("pos changed", self._view.fitItems())
    #     else:
    #         print("item change")
    #         return super().itemChange(change, value)

class PanAndZoomGraphicsView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setDragMode(QGraphicsView.RubberBandDrag) # optional, default mouse behaviour
        self.setRenderHint(QPainter.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.NoAnchor) # important for panning and zooming
        # self.setCacheMode(QGraphicsView.CacheBackground)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)

        max_size = 32767
        self.setSceneRect(-max_size, -max_size, max_size * 2, max_size * 2) # important for infinite canvas

        self.mouseMode = "DEFAULT"
        self.mousePressPos = None
        self._zoom_with_mousewheel = True

    def setZoomWithMouswheel(self, value):
        self._zoom_with_mousewheel = value

    def zoomWithMouswheel(self):
        return self._zoom_with_mousewheel

    def getScale(self):
        return self.transform().m11()

    def wheelEvent(self, event:QWheelEvent):
        ModifierDown = event.modifiers() == Qt.KeyboardModifier.MetaModifier or event.modifiers() == Qt.KeyboardModifier.ControlModifier
        if ModifierDown or self.zoomWithMouswheel()==True:
            delta = event.angleDelta()
            if delta.y() == 0:
                event.ignore()
                return

            d = delta.y() / abs(delta.y())
            factor = math.pow(1.3, delta.y()/100)
            if self.getScale() * factor < 10 and self.getScale() * factor > 0.3:
                oldPos = self.mapToScene(event.position().toPoint())
                self.scale(factor, factor)
                newPos = self.mapToScene(event.position().toPoint())
                delta = newPos-oldPos
                self.translate(delta.x(), delta.y())
        else:
            return super().wheelEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        IsMiddleButton =      event.buttons() == Qt.MouseButton.MiddleButton
        IsLeftButtonWithAlt = event.modifiers() == Qt.KeyboardModifier.AltModifier and event.buttons() == Qt.MouseButton.LeftButton
        if IsMiddleButton or IsLeftButtonWithAlt:
            self.mouseMode = "PAN"
            self.mousePressTransform = self.transform()
            self.mousePressPos = event.position()
        else:
            return super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.mouseMode == "PAN" and self.mousePressPos is not None:
            delta = self.mapToScene(event.position().toPoint()) - self.mapToScene(self.mousePressPos.toPoint())

            transform = QTransform(self.mousePressTransform).translate(delta.x(), delta.y())
            self.setTransform(transform)
        else:
            return super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if self.mouseMode == "PAN":
            self.mouseMode = None
        else:
            return super().mouseReleaseEvent(event)

    def drawBackground(self, painter: QPainter, rect:QRectF | QRect):
        super().drawBackground(painter, rect);

        def drawGrid(gridStep:int):
            windowRect:QRect = self.rect()
            tl:QPointF = self.mapToScene(windowRect.topLeft())
            br:QPointF = self.mapToScene(windowRect.bottomRight())

            left = math.floor(tl.x() / gridStep - 0.5)
            right = math.floor(br.x() / gridStep + 1.0)
            bottom = math.floor(tl.y() / gridStep - 0.5)
            top = math.floor(br.y() / gridStep + 1.0)

            # vertical lines
            for xi in range(left, right):
                line = QLineF(xi * gridStep, bottom * gridStep, xi * gridStep, top * gridStep);
                painter.drawLine(line)

            # horizontal lines
            for yi in range(bottom, top):
                line = QLineF(left * gridStep, yi * gridStep, right * gridStep, yi * gridStep);
                painter.drawLine(line)

        def drawDots(gridStep:int, radius=2):
            windowRect:QRect = self.rect()
            tl:QPointF = self.mapToScene(windowRect.topLeft())
            br:QPointF = self.mapToScene(windowRect.bottomRight())

            left = math.floor(tl.x() / gridStep - 0.5)
            right = math.floor(br.x() / gridStep + 1.0)
            bottom = math.floor(tl.y() / gridStep - 0.5)
            top = math.floor(br.y() / gridStep + 1.0)

            for xi in range(left, right):
                for yi in range(bottom, top):
                    painter.drawEllipse(QPoint(xi*gridStep, yi*gridStep), radius,radius)

        fineGridColor = self.palette().text().color()
        fineGridColor.setAlpha(5)
        pFine = QPen(fineGridColor, 1.0)

        coarseGridColor = self.palette().text().color()
        coarseGridColor.setAlpha(10)
        pCoarse = QPen(coarseGridColor, 1.0)

        # painter.setPen(pFine)
        # drawGrid(10)
        # painter.setPen(pCoarse)
        # drawGrid(100)
        painter.setPen(Qt.NoPen)
        painter.setBrush(coarseGridColor)
        drawDots(20, radius=1)

    def fitItems(self):
        if self.scene():
            self.blockSignals(True)
            brect = QRectF(0,0,1,1)
            for item in self.scene().items():
                bbox = item.boundingRect()
                brect = brect.united(bbox)
            boundingRect = self.scene().itemsBoundingRect()
            self.centerOn(boundingRect.center())
            rect_in_viewport_coords = self.viewport().rect()   # This gets the rectangle in viewport coordinates.
            rect_in_scene_coords = self.mapToScene(rect_in_viewport_coords).boundingRect()
            zoom = rect_in_scene_coords.width() / boundingRect.width()
            # self.scale(zoom, zoom)
            # print(zoom)
            # print(boundingRect)
            # self.view
            # print("brect:", brect)
            # print("fit items")
            # self.fitInView(brect, Qt.AspectRatioMode.KeepAspectRatio)
            # self.blockSignals(False)

            # 

    def centerItems(self):
        if self.scene():
            boundingRect = self.scene().itemsBoundingRect()
            self.centerOn(boundingRect.center())

    def showEvent(self, event: QShowEvent) -> None:
        self.fitItems()
        return super().showEvent(event)

        


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = PanAndZoomGraphicsView()
    scene = QGraphicsScene()
    # scene.setSceneRect(QRect(-9999//2,-9999//2, 9999, 9999))

    window.setScene(scene)
    # max_size = 32767
    # window.setSceneRect(-max_size, -max_size, max_size * 2, max_size * 2)
    
    rect = RectItem(0,0,50,50, window)
    window.scene().addItem(rect)
    rect = RectItem(100,0,50,50, window)
    window.scene().addItem(rect)
    rect = RectItem(0,100,50,50, window)
    window.scene().addItem(rect)
    window.show()
    # window.fitInView(scene.sceneRect())
    sys.exit(app.exec())