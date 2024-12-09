from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

class ArrowItem(QGraphicsItem):
	def __init__(self, parent=None):
		super().__init__(parent=parent)
		self.source:Optional[ConnectableShape] = None
		self.source_offset = QPointF(0,0)
		self.target:Optional[ConnectableShape] = None
		self.target_offset = QPointF(0,0)

		# components

	def setSource(self, source:ConnectableShape|QPointF|None, offset:QPointF=QPointF(0,0)):
		print("setSource")
		# disconnect signals from current source
		try:
			self.source.scenePositionChanged.disconnect(self.update) #type: ignore
		except AttributeError:
			pass
		try:
			self.source.shapeChanged.disconnect(self.update)  #type: ignore
		except AttributeError:
			pass

		match source:
			case QGraphicsItem():
				self.source = source
				self.source_offset = offset
			case QPointF():
				self.source = None
				self.source_offset = source+offset
			case None:
				self.source = None
				self.source_offset = offset
			case _:
				raise ValueError()

		# connect signals from new source
		try:
			source.scenePositionChanged.connect(self.update) #type: ignore
		except AttributeError:
			pass
		try:
			source.shapeChanged.connect(self.update)  #type: ignore
		except AttributeError:
			pass

		self.update()

	def setTarget(self, target:ConnectableShape|QPointF|None, offset:QPointF=QPointF(0,0)):
		# disconnect signals from current source
		try:
			self.target.scenePositionChanged.disconnect(self.update) #type: ignore
		except AttributeError:
			pass
		try:
			self.target.shapeChanged.disconnect(self.update)  #type: ignore
		except AttributeError:
			pass

		match target:
			case QGraphicsItem():
				self.target = target
				self.target_offset = offset
			case QPointF():
				self.target = None
				self.target_offset = target+offset
			case None:
				self.target = None
				self.target_offset = offset
			case _:
				raise ValueError()

		# connect signals from new source
		try:
			target.scenePositionChanged.connect(self.update) #type: ignore
		except AttributeError:
			pass
		try:
			target.shapeChanged.connect(self.update)  #type: ignore
		except AttributeError:
			pass

		self.update()

	def setSource(self, source:ConnectableShape|QPointF|None, offset:QPointF=QPointF(0,0)):
		print("setSource")
		# disconnect signals from current source
		try:
			self.source.scenePositionChanged.disconnect(self.update) #type: ignore
		except AttributeError:
			pass
		try:
			self.source.shapeChanged.disconnect(self.update)  #type: ignore
		except AttributeError:
			pass

		match source:
			case QGraphicsItem():
				self.source = source
				self.source_offset = offset
			case QPointF():
				self.source = None
				self.source_offset = source+offset
			case None:
				self.source = None
				self.source_offset = offset
			case _:
				raise ValueError()

		# connect signals from new source
		try:
			source.scenePositionChanged.connect(self.update) #type: ignore
		except AttributeError:
			pass
		try:
			source.shapeChanged.connect(self.update)  #type: ignore
		except AttributeError:
			pass

		self.update()

	def setTarget(self, target:ConnectableShape|QPointF|None, offset:QPointF=QPointF(0,0)):
		# disconnect signals from current source
		try:
			self.target.scenePositionChanged.disconnect(self.update) #type: ignore
		except AttributeError:
			pass
		try:
			self.target.shapeChanged.disconnect(self.update)  #type: ignore
		except AttributeError:
			pass

		match target:
			case QGraphicsItem():
				self.target = target
				self.target_offset = offset
			case QPointF():
				self.target = None
				self.target_offset = target+offset
			case None:
				self.target = None
				self.target_offset = offset
			case _:
				raise ValueError()

		# connect signals from new source
		try:
			target.scenePositionChanged.connect(self.update) #type: ignore
		except AttributeError:
			pass
		try:
			target.shapeChanged.connect(self.update)  #type: ignore
		except AttributeError:
			pass

		self.update()

	def shape(self)->QPainterPath:
		p1 = QPointF(self.source_offset)
		if self.source:
			shape_pos = self.source.scenePos()
			shape_center = self.source.boundingRect().center()
			p1+=shape_pos+shape_center

		p2 = QPointF(self.target_offset)
		if self.target:
			shape_pos = self.target.scenePos()
			shape_center = self.target.boundingRect().center()
			p2+=shape_pos+shape_center

		line = QLineF(p1, p2)

		# arrow shape
		width = 2
		head_width = 6
		head_length = 6
		# create an arrow on X+ axis with line length

		vertices = [
			(0, -width/2),
			(line.length()-head_length, -width/2),
			(line.length()-head_length, -head_width),
			(line.length(), 0),
			(line.length()-head_length, +head_width),
			(line.length()-head_length, +width/2),
			(0, +width/2)
		]

		arrow_polygon = QPolygonF([QPointF(x, y) for x, y in vertices])
		transform = QTransform()
		transform.translate(p1.x(), p1.y())
		transform.rotate(-line.angle())

		path = QPainterPath()
		path.addPolygon(transform.map(arrow_polygon))

		return path

	def paint(self, painter, option, widget=None):
		# draw arrow body
		painter.setPen(Qt.NoPen)
		color = QPalette().color(QPalette.ColorRole.Text)
		painter.setBrush(color)
		path = self.shape()
		painter.drawPath(path)

	def boundingRect(self):
		margin = 25/2
		return self.shape().boundingRect().adjusted(-margin, -margin, margin, margin)