from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

class QGraphicsArrowItem(QGraphicsLineItem):

	def _arrow_shape(self)->QPainterPath:
		line = self.line()

		# arrow shape
		width = self.pen().width()
		head_width, head_length = width*2, width*4
		# create an arrow on X+ axis with line length

		vertices = [
			(0, -width/2),
			(line.length()-head_length, -width/2),
			(line.length()-head_length, -head_width),
			(line.length(), 0),
			(line.length()-head_length, +head_width),
			(line.length()-head_length, +width/2),
			(0, +width/2),
			(0, -width/2)
		]

		arrow_polygon = QPolygonF([QPointF(x, y) for x, y in vertices])
		transform = QTransform()
		transform.translate(self.line().p1().x(), self.line().p1().y())
		transform.rotate(-line.angle())

		path = QPainterPath()
		path.addPolygon(transform.map(arrow_polygon))


		return path

	def shape(self)->QPainterPath:
		return self._arrow_shape()

	def paint(self, painter, option, widget=None):
		# draw arrow body
		painter.setPen(Qt.PenStyle.NoPen)
		painter.setBrush(self.pen().color())
		path = self._arrow_shape()
		painter.drawPath(path)

	def boundingRect(self):
		margin = self.pen().widthF()/2.0
		return self.shape().boundingRect().adjusted(-margin, -margin, margin, margin)

if __name__ == "__main__":
	app = QApplication()
	

	# create and configure arrow
	arrow = QGraphicsArrowItem(0,0,200,200)
	arrow.setPen(QPen(QPalette().color(QPalette.ColorRole.Text), 4))

	# show arrow
	scene = QGraphicsScene()
	scene.addItem(arrow)
	view = QGraphicsView()
	view.setRenderHints(QPainter.RenderHint.Antialiasing)
	view.setScene(scene)
	view.show()
	view.fitInView(scene.itemsBoundingRect().adjusted(-100,-100,100,100), Qt.AspectRatioMode.KeepAspectRatio)

	app.exec()