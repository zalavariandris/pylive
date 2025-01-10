from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from pylive.utils.geo import makeArrowShape

class QGraphicsArrowItem(QGraphicsLineItem):
	def shape(self)->QPainterPath:
		return makeArrowShape(self.line(), self.pen().width())

	def paint(self, painter, option, widget=None):
		# draw arrow body
		painter.setPen(Qt.PenStyle.NoPen)
		painter.setBrush(self.pen().color())
		path = makeArrowShape(self.line(), self.pen().width())
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