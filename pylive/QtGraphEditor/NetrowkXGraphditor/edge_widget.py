
class EdgeWidget(QGraphicsWidget):
	def __init__(self, source_node:QGraphicsWidget, target_node:QGraphicsWidget, parent=None):
		super().__init__(parent=parent)
		self._source_node = source_node
		source_node.geometryChanged.connect(self.updatePosition)
		self._target_node = target_node
		target_node.geometryChanged.connect(self.updatePosition)

		# components
		palette = self.palette()
		textColor = palette.color(QPalette.ColorGroup.All, QPalette.ColorRole.Text)
		
		# arrow shaft
		self.body = QGraphicsLineItem(self)
		pen = QPen( QPen(textColor, 1.5) )
		pen.setCapStyle(Qt.FlatCap)
		self.body.setPen(pen)

		# arrow head
		self.headsize=8
		triangle = QPolygonF([
			QPointF(0, 0),
			QPointF(-self.headsize, self.headsize / 2),
			QPointF(-self.headsize, -self.headsize / 2)
		])
		self.arrowhead = QGraphicsPolygonItem(self)  # Add arrowhead as a child
		self.arrowhead.setPolygon(triangle)
		self.arrowhead.setPen(Qt.NoPen)
		self.arrowhead.setBrush(textColor)

		# arrow tail
		self.tailsize=8
		self.arrowtail = QGraphicsEllipseItem(-self.tailsize/2, -self.tailsize/2, self.tailsize, self.tailsize, parent=self)
		self.arrowtail.setPen(Qt.NoPen)
		self.arrowtail.setBrush(textColor)

		#
		self.updatePosition()

	def setSource(self, source_node:QGraphicsWidget):
		if self._source_node:
			self._source_node.geometryChanged.disconnect(self.updatePosition)
		if source_node:
			self._source_node = source_node
			source_node.geometryChanged.connect(self.updatePosition)
		else:
			self._source_node = None
		self.updatePosition()

	def setTarget(self, target_node:QGraphicsWidget):
		if self._target_node:
			self._target_node.geometryChanged.disconnect(self.updatePosition)
		
		if target_node:
			self._target_node = target_node
			target_node.geometryChanged.connect(self.updatePosition)
		else:
			self._target_node = None
		
		self.updatePosition()

	def updatePosition(self):
		if not self._source_node or not self._target_node:
			print("warning: unconnected edges are not yet implemented")

		line = QLineF()
		
		if self._source_node and self._target_node:
			margin = 0
			source_rect = self._source_node.geometry()\
			.adjusted(-margin,-margin,margin,margin)
			target_rect = self._target_node.geometry()\
			.adjusted(-margin,-margin,margin,margin)
			source_center = source_rect.center()
			target_center = target_rect.center()
			direction = target_center-source_center

			if I:=intersectRayWithRectangle(
				origin=(source_center.x(), source_center.y()),
				direction = (direction.x(), direction.y()),
				top = target_rect.top(),
				left = target_rect.left(),
				bottom = target_rect.bottom(),
				right = target_rect.right()):

				line.setP2(QPointF(I[0], I[1]))

			direction = source_center - target_center
			if I:=intersectRayWithRectangle(
				origin=(target_center.x(), target_center.y()),
				direction = (direction.x(), direction.y()),
				top = source_rect.top(),
				left = source_rect.left(),
				bottom = source_rect.bottom(),
				right = source_rect.right()
			):
				line.setP1(QPointF(I[0], I[1]))
		else:

			if self._source_node:
				line.setP1(self._source_node.geometry().center().toPoint())
			if self._target_node:
				line.setP2(self._target_node.geometry().center().toPoint())

		body_line = QLineF(line)
		body_line.setLength(body_line.length()-self.headsize)
		self.body.setLine(body_line)

		
		# # P = QPointF(QPointF(I[0]-normal.x(), I[1]-normal.y()))
		# # body_line.setP2(P)
		# self.body.line().setP2(QPointF())

		# update head and tails
		transform = QTransform()
		transform.translate(line.p2().x(), line.p2().y())
		transform.rotate(-line.angle())
		self.arrowhead.setTransform(transform)

		transform = QTransform()
		transform.translate(line.p1().x(), line.p1().y())
		transform.rotate(-line.angle())
		self.arrowtail.setTransform(transform)

