from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
import math


class InfiniteGraphicsView(QGraphicsView):
	def __init__(self, parent=None):
		super().__init__(parent=parent)

		self._scene = QGraphicsScene()
		self._click_pos = None

		# self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
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

	# def mousePressEvent(self, event: QMouseEvent):
	# 	super().mousePressEvent(event)
	# 	if event.button() == Qt.MouseButton.LeftButton:
	# 		self._click_pos = self.mapToScene(event.pos())

	# def mouseMoveEvent(self, event: QMouseEvent):
	# 	super().mouseMoveEvent(event)
	# 	if self._scene.mouseGrabberItem() is None and event.buttons() == Qt.MouseButton.LeftButton:
	# 		# Make sure shift is not being pressed
	# 		if not (event.modifiers() & Qt.ShiftModifier):
	# 			difference = self._click_pos - self.mapToScene(event.position().toPoint())
	# 			self.setSceneRect(self.sceneRect().translated(difference.x(), difference.y()))

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


if __name__ == "__main__":
	import sys
	app = QApplication(sys.argv)
	window = InfiniteGraphicsView()
	rect = QGraphicsRectItem(0,0,100,100)
	window.scene().addItem(rect)
	window.show()
	sys.exit(app.exec())
