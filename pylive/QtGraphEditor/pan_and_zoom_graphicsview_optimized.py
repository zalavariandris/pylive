from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
import math

class RectItem(QGraphicsRectItem):
    def __init__(self, x, y, w, h, view):
        super().__init__(x, y, w, h)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setBrush(Qt.GlobalColor.green)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self._view = view

class PanAndZoomGraphicsView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Optimize viewport updates
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.MinimalViewportUpdate)
        self.setOptimizationFlags(
            QGraphicsView.OptimizationFlag.DontAdjustForAntialiasing
        )
        
        # Setup view properties
        self.setInteractive(True)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.NoAnchor)
        self.setCacheMode(QGraphicsView.CacheModeFlag.CacheNone)
        
        # Set scene rect
        max_size = 10000
        self.setSceneRect(-max_size, -max_size, max_size * 2, max_size * 2)
        
        self.mouseMode = "DEFAULT"
        self.mousePressPos = None
        self._zoom_with_mousewheel = True
        
        # Update timer for smooth panning
        self._update_timer = QTimer(self)
        self._update_timer.setSingleShot(True)
        self._update_timer.setInterval(16)
        self._update_timer.timeout.connect(self.viewport().update)

    def setZoomWithMouswheel(self, value):
        self._zoom_with_mousewheel = value

    def zoomWithMouswheel(self):
        return self._zoom_with_mousewheel

    def getScale(self):
        return self.transform().m11()

    def wheelEvent(self, event: QWheelEvent):
        ModifierDown = event.modifiers() in (Qt.KeyboardModifier.MetaModifier, Qt.KeyboardModifier.ControlModifier)
        if ModifierDown or self.zoomWithMouswheel():
            delta = event.angleDelta()
            if delta.y() == 0:
                event.ignore()
                return

            factor = math.pow(1.3, delta.y() / 120.0)
            if 0.3 <= self.getScale() * factor <= 10:
                pos = event.position()
                oldPos = self.mapToScene(pos.toPoint())
                self.scale(factor, factor)
                newPos = self.mapToScene(pos.toPoint())
                delta = newPos - oldPos
                self.translate(delta.x(), delta.y())
        else:
            super().wheelEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        IsMiddleButton = event.buttons() == Qt.MouseButton.MiddleButton
        IsLeftButtonWithAlt = (event.modifiers() == Qt.KeyboardModifier.AltModifier and 
                             event.buttons() == Qt.MouseButton.LeftButton)
        
        if IsMiddleButton or IsLeftButtonWithAlt:
            self.mouseMode = "PAN"
            self.mousePressTransform = self.transform()
            self.mousePressPos = event.position()
            self.viewport().setMouseTracking(True)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.mouseMode == "PAN" and self.mousePressPos is not None:
            delta = (self.mapToScene(event.position().toPoint()) - 
                    self.mapToScene(self.mousePressPos.toPoint()))
            
            transform = QTransform(self.mousePressTransform).translate(delta.x(), delta.y())
            self.setTransform(transform)
            self._update_timer.start()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if self.mouseMode == "PAN":
            self.mouseMode = None
            self.viewport().setMouseTracking(False)
        else:
            super().mouseReleaseEvent(event)

    def drawBackground(self, painter: QPainter, rect: QRectF):
        """Draw background grid directly without caching."""
        super().drawBackground(painter, rect)
        
        # Save painter state
        painter.save()
        
        # Get visible scene rect in scene coordinates
        visible_rect = self.mapToScene(self.viewport().rect()).boundingRect()
        
        # Calculate grid size based on scale
        scale = self.getScale()
        if scale > 2:
            grid_size = 20
            dot_radius = 1
            alpha = 15
        elif scale > 0.5:
            grid_size = 40
            dot_radius = 2
            alpha = 12
        else:
            grid_size = 80
            dot_radius = 2
            alpha = 10
            
        # Set up painter
        color = self.palette().text().color()
        color.setAlpha(alpha)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        
        # Calculate grid bounds
        left = math.floor(visible_rect.left() / grid_size)
        right = math.ceil(visible_rect.right() / grid_size)
        top = math.floor(visible_rect.top() / grid_size)
        bottom = math.ceil(visible_rect.bottom() / grid_size)
        
        # Draw dots
        for x in range(left, right + 1):
            for y in range(top, bottom + 1):
                point = QPointF(x * grid_size, y * grid_size)
                # Only draw if point is in visible rect (optimization)
                if visible_rect.contains(point):
                    painter.drawEllipse(point, dot_radius, dot_radius)
        
        # Restore painter state
        painter.restore()

    def fitItems(self):
        if not self.scene() or not self.scene().items():
            self.centerOn(0, 0)
            return
            
        brect = self.scene().itemsBoundingRect()
        self.centerOn(brect.center())
        
        viewport_rect = self.viewport().rect()
        scene_rect = self.mapToScene(viewport_rect).boundingRect()
        zoom = min(scene_rect.width() / brect.width(),
                  scene_rect.height() / brect.height())
        
        if 0.3 <= zoom <= 10:
            self.scale(zoom, zoom)

    def centerItems(self):
        if self.scene():
            self.centerOn(self.scene().itemsBoundingRect().center())

    def showEvent(self, event: QShowEvent) -> None:
        self.fitItems()
        super().showEvent(event)

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = PanAndZoomGraphicsView()
    scene = QGraphicsScene()
    window.setScene(scene)
    
    # Add test items
    for x, y in [(0, 0), (100, 0), (0, 100)]:
        rect = RectItem(x, y, 50, 50, window)
        scene.addItem(rect)
    
    window.show()
    sys.exit(app.exec())