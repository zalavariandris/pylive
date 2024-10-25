from typing import Optional
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
class InfiniteGraphicsView(QGraphicsView):
	def __init__(self, parent=None):
		super().__init__(parent=parent)

		self._scene = QGraphicsScene()
		self._click_pos = None

		self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
		self.setRenderHint(QPainter.RenderHint.Antialiasing)

		# setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
		# setViewportUpdateMode(QGraphicsView.MinimalViewportUpdate)
		self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

		self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

		self.setCacheMode(QGraphicsView.CacheModeFlag.CacheBackground)

		self.setScene(self._scene)

	def scale_up(self):
		step = 1.2
		factor = step ** 1.0
		t = self.transform()
		if t.m11() <= 2.0:
			self.scale(factor, factor)

	def scale_down(self):
		step = 1.2
		factor = step ** -1.0
		self.scale(factor, factor)

	def mousePressEvent(self, event: QMouseEvent):
		super().mousePressEvent(event)
		if event.button() == Qt.MouseButton.LeftButton:
			self._click_pos = self.mapToScene(event.pos())

	def mouseMoveEvent(self, event: QMouseEvent):
		super().mouseMoveEvent(event)
		if self._scene.mouseGrabberItem() is None and event.buttons() == Qt.MouseButton.LeftButton:
			# Make sure shift is not being pressed
			if not (event.modifiers() & Qt.ShiftModifier):
				difference = self._click_pos - self.mapToScene(event.position().toPoint())
				self.setSceneRect(self.sceneRect().translated(difference.x(), difference.y()))

	def wheelEvent(self, event: QWheelEvent):
		delta = event.angleDelta()
		if delta.y() == 0:
			event.ignore()
			return

		d = delta.y() / abs(delta.y())
		if d > 0.0:
			self.scale_up()
		else:
			self.scale_down()


if __name__ == "__main__":
	import sys
	app = QApplication(sys.argv)
	window = InfiniteGraphicsView()
	rect = QGraphicsRectItem(0,0,100,100)
	window.scene().addItem(rect)
	window.show()
	sys.exit(app.exec())
