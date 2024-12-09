from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from pylive.utils.geo import intersectRayWithPolygon, intersectRayWithRectangle

# class ConnectableProtocol:
# 	sceneGeometryChanged = Signal()


# class Connectable(QGraphicsWidget):
# 	sceneGeometryChange = Signal()
# 	def __init__(self, parent:QGraphicsItem):
# 		super().__init__(parent=parent)

# 	def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
# 		match change:
# 			case QGraphicsItem.GraphicsItemChange.ItemScenePositionHasChanged:
# 				self.sceneGeometryChange.emit()

# 		return super().itemChange(change, value)

def intersectLineWithRectangle(line:QLineF, rect:QRectF, direction:Literal['forward','backward']='forward'):
	assert direction in {'forward','backward'}
	if direction == "backward":
		line = QLineF(line.p2(), line.p1())

	I=intersectRayWithRectangle(
		origin=(line.x2(), line.y2()),
		direction = (line.dx(), line.dy()),
		top = rect.top(),
		left = rect.left(),
		bottom = rect.bottom(),
		right = rect.right())

	line = QLineF(line)
	if I:
		line.setP2(QPointF(I[0], I[1]))

	if direction == "backward":
		line = QLineF(line.p2(), line.p1())
	return line



def intersectLineWithPath(p1: QPointF, p2: QPointF, path: QPainterPath) -> QPointF:
    """
    Finds the intersection point of a line segment (ray) defined by p1 and p2 with a given QPainterPath.
    
    :param p1: Start point of the ray
    :param p2: End point of the ray
    :param path: QPainterPath to intersect with
    :return: The intersection point as QPointF or None if no intersection is found
    """
    ray_start = p1
    ray_end = p2
    ray_direction = ray_end - ray_start

    # Create a path for the ray
    ray_path = QPainterPath()
    ray_path.moveTo(ray_start)
    ray_path.lineTo(ray_end)
    # Add thickness to the paths
    stroker = QPainterPathStroker()
    stroker.setWidth(1)
    stroked_ray_path = stroker.createStroke(ray_path)

    # Check for intersections
    intersection_path = stroked_ray_path.intersected(path)
    if intersection_path.isEmpty():
        # No intersection found
        return None

    # Retrieve the intersection points
    intersection_points = [intersection_path.elementAt(i) for i in range(intersection_path.elementCount())]

    # Filter intersection points in the forward direction of the ray
    for point in intersection_points:
        intersection_point = QPointF(point.x, point.y)
        ray_to_point = QLineF(ray_start, intersection_point)

        # Ensure the point is in the forward direction of the ray
        if ray_to_point.dx() * ray_direction.x() >= 0 and ray_to_point.dy() * ray_direction.y() >= 0:
            return intersection_point

    # No valid intersection in the ray's forward direction
    return None


def getCenter(shape:QPointF|QRectF|QPainterPath):
	match shape:
		case QPointF():
			return shape
		case QRectF():
			return shape.center()
		case QPainterPath():
			return shape.boundingRect().center()
		case _:
			raise ValueError


def makeLineToShape(origin:QPointF, shape:QPointF|QRectF|QPainterPath):
	center = getCenter(shape)

	match shape:
		case QPointF():
			intersection = center

		case QRectF():
			rect = shape
			V = center-origin
			if xy:=intersectRayWithRectangle(
				origin=(origin.x(), origin.y()),
				direction = (V.x(), V.y()),
				top = rect.top(),
				left = rect.left(),
				bottom = rect.bottom(),
				right = rect.right()
				):
				intersection = QPointF(*xy)
			else:
				intersection = center


		case QPainterPath():
			if P:=intersectLineWithPath(origin, center, shape):
				intersection = P
			else:
				intersection = center

		case _:
			raise ValueError

	return QLineF(center, intersection)

def makeLineBetweenShapes(A:QPointF|QRectF|QPainterPath, B:QPointF|QRectF|QPainterPath)->QLineF:
	Ac = getCenter(A)
	Bc = getCenter(B)

	I2 = makeLineToShape(Ac, B).p2()
	I1 = makeLineToShape(Bc, A).p2()

	return QLineF(I1, I2)



# class ConnectableShape(QGraphicsWidget, QAbstractGraphicsShapeItem):
# 	shapeChanged = Signal()
# 	scenePositionChanged = Signal()

# 	def __init__(self, shape:Optional[QPainterPath]=None, parent:Optional[QGraphicsItem]=None):
# 		QGraphicsWidget.__init__(self, parent=parent)
# 		QAbstractGraphicsShapeItem.__init__(self, parent=parent)
# 		self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges)


# 		# cache geometry
# 		self._shape = QPainterPath()
# 		self._boundingrect = QRectF()

# 		# create default shape
# 		if not shape:
# 			# create default shape
# 			shape = QPainterPath()
# 			shape.addEllipse(-50,-50,100,100)
# 		self.setShape(shape)
# 		self.setBrush(self.palette().color(QPalette.ColorRole.Base))
# 		self.setPen(QPen(self.palette().color(QPalette.ColorRole.Text), 2))

# 	def setShape(self, shape:QPainterPath):
# 		margin = self.pen().widthF()/2
# 		boundingrect = shape.boundingRect().adjusted(-margin,-margin,margin,margin)

# 		self._shape = shape
# 		self._boundingrect = boundingrect
# 		self.setGeometry(
# 			boundingrect.x()+self.x(), 
# 			boundingrect.y()+self.y(),
# 			boundingrect.width(),
# 			boundingrect.height()
# 		)
# 		self.shapeChanged.emit()
# 		self.update()

# 	def shape(self)->QPainterPath:
# 		return self._shape

# 	def boundingRect(self) -> QRectF:
# 		return self._boundingrect

# 	def paint(self, painter, option, widget=None):
# 		painter.setPen(self.pen())
# 		painter.setBrush(self.brush())
# 		path = self.shape()
# 		painter.drawPath(path)

# 	def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
# 		match change:
# 			case QGraphicsItem.GraphicsItemChange.ItemScenePositionHasChanged:
# 				self.scenePositionChanged.emit()

# 		return super().itemChange(change, value)



# class ConnectableLink(QGraphicsWidget):
# 	def __init__(self, parent: Optional[QGraphicsItem]=None) -> None:
# 		super().__init__(parent)
# 		self._source:Optional[ConnectableShape] = None
# 		self._source_offset = QPointF(0,0)
# 		self._target:Optional[ConnectableShape] = None
# 		self._target_offset = QPointF(0,0)

# 		# components
# 		palette = self.palette()
# 		textColor = palette.color(QPalette.ColorGroup.All, QPalette.ColorRole.Text)
		
# 		# arrow shaft
# 		self.shaft = QGraphicsLineItem(self)
# 		pen = QPen( QPen(textColor, 1.5) )
# 		pen.setCapStyle(Qt.FlatCap)
# 		self.shaft.setPen(pen)

# 		# arrow head
# 		self.headsize=8
# 		triangle = QPolygonF([
# 			QPointF(0, 0),
# 			QPointF(-self.headsize, self.headsize / 2),
# 			QPointF(-self.headsize, -self.headsize / 2)
# 		])
# 		self.arrowhead = QGraphicsPolygonItem(self)  # Add arrowhead as a child
# 		self.arrowhead.setPolygon(triangle)
# 		self.arrowhead.setPen(Qt.NoPen)
# 		self.arrowhead.setBrush(textColor)

# 		# arrow tail
# 		self.tailsize=8
# 		self.arrowtail = QGraphicsEllipseItem(-self.tailsize/2, -self.tailsize/2, self.tailsize, self.tailsize, parent=self)
# 		self.arrowtail.setPen(Qt.NoPen)
# 		self.arrowtail.setBrush(textColor)

# 		# #
# 		# self.updatePosition()

# 	def link(self, source, target):
# 		self._setSource(source)
# 		self._setTarget(target)
# 		self.update()

# 	def _setSource(self, source:ConnectableShape|QPointF|None, offset:QPointF=QPointF(0,0)):
# 		# disconnect signals from current source
# 		try:
# 			self._source.scenePositionChanged.disconnect(self.update) #type: ignore
# 		except AttributeError:
# 			pass
# 		try:
# 			self._source.shapeChanged.disconnect(self.update)  #type: ignore
# 		except AttributeError:
# 			pass

# 		match source:
# 			case QGraphicsItem():
# 				self._source = source
# 				self._source_offset = offset
# 			case QPointF():
# 				self._source = None
# 				self._source_offset = source+offset
# 			case None:
# 				self._source = None
# 				self._source_offset = offset
# 			case _:
# 				raise ValueError()

# 		# connect signals from new source
# 		try:
# 			source.scenePositionChanged.connect(self.update) #type: ignore
# 		except AttributeError:
# 			pass
# 		try:
# 			source.shapeChanged.connect(self.update)  #type: ignore
# 		except AttributeError:
# 			pass

# 		# self.update()

# 	def _setTarget(self, target:ConnectableShape|QPointF|None, offset:QPointF=QPointF(0,0)):
# 		# disconnect signals from current source
# 		try:
# 			self._target.scenePositionChanged.disconnect(self.update) #type: ignore
# 		except AttributeError:
# 			pass
# 		try:
# 			self._target.shapeChanged.disconnect(self.update)  #type: ignore
# 		except AttributeError:
# 			pass

# 		match target:
# 			case QGraphicsItem():
# 				self._target = target
# 				self._target_offset = offset
# 			case QPointF():
# 				self._target = None
# 				self._target_offset = target+offset
# 			case None:
# 				self._target = None
# 				self._target_offset = offset
# 			case _:
# 				raise ValueError()

# 		# connect signals from new source
# 		try:
# 			target.scenePositionChanged.connect(self.update) #type: ignore
# 		except AttributeError:
# 			pass
# 		try:
# 			target.shapeChanged.connect(self.update)  #type: ignore
# 		except AttributeError:
# 			pass

# 		# self.update()

# 	@overload
# 	def update(self, rect:QRectF|QRect=QRectF()):...

# 	@overload
# 	def update(self, x:float, y:float,w:float, h:float)->None:...

# 	@override
# 	def update(self, *args): #type: ignore
# 		match len(args):
# 			case 0:
# 				rect  = QRectF()
# 			case 1:
# 				rect = QRectF(args[0])
# 			case 4:
# 				x,y,w,h = args
# 				rect = QRectF(x,y,w,h)
# 			case _:
# 				raise ValueError(f"{args}")

# 		self.updatePosition()

# 		super().update(rect)

# 	def updatePosition(self):
# 		assert self._source
# 		assert self._target

# 		margin = 0
# 		source_rect = self._source.mapToScene(
# 			self._source.boundingRect().adjusted(-margin,-margin,margin,margin)
# 		).boundingRect()

# 		target_rect = self._target.mapToScene(
# 			self._target.boundingRect().adjusted(-margin,-margin,margin,margin)
# 		).boundingRect()

# 		# source_center = source_rect.center()
# 		# target_center = target_rect.center()
# 		# direction = target_center-source_center

# 		### line between center points ###
# 		line = QLineF(
# 			self.shaft.mapFromScene(source_rect.center()), 
# 			self.shaft.mapFromScene(target_rect.center())
# 		)

# 		### intersect line with rectangle ###
# 		# line = intersectLineWithRectangle(line, target_rect)
# 		# line = intersectLineWithRectangle(line, source_rect, direction='backward')

# 		### intersect line with shapes ###
# 		target_shape = self._target.sceneTransform().map(self._target.shape())
# 		source_shape = self._source.sceneTransform().map(self._source.shape())

# 		I2 = intersectLineWithPath(line.p1(), line.p2(), target_shape)
# 		I1 = intersectLineWithPath(line.p2(), line.p1(), source_shape)
# 		if I2:
# 			line.setP2(I2)
# 		if I1:
# 			line.setP1(I1)

# 		self.setVisible(True if I1 and I2 else False)

# 		# adjust shaft length, with head size
# 		line = QLineF(
# 			self.shaft.mapFromScene(line.p1()), 
# 			self.shaft.mapFromScene(line.p2())
# 		)
# 		shaft_line = QLineF(line)
# 		shaft_line.setLength(shaft_line.length()-self.headsize)
# 		self.shaft.setLine(shaft_line)

# 		# transform head
# 		transform = QTransform()
# 		transform.translate(line.p2().x(), line.p2().y())
# 		transform.rotate(-line.angle())
# 		self.arrowhead.setTransform(transform)

# 		# transform the tail
# 		transform = QTransform()
# 		transform.translate(line.p1().x(), line.p1().y())
# 		transform.rotate(-line.angle())
# 		self.arrowtail.setTransform(transform)


if __name__ == "__main__":
	app = QApplication()


	scene = QGraphicsScene()

	def link_two_circles(scene):
		circle1 = QGraphicsEllipseItem(0,0,100,100)
		circle1.moveBy(-100, -10)
		scene.addItem(circle1)

		circle2 = QGraphicsEllipseItem(0,0,100,100)
		circle2.moveBy(100, 10)
		scene.addItem(circle2)

		link = QGraphicsLineItem()
		link.setLine( makeLineBetweenShapes(
			circle1.sceneTransform().map(circle1.shape()),
			circle2.sceneTransform().map(circle2.shape())
		) )
		scene.addItem(link)

		pen = QPen(app.palette().color(QPalette.ColorRole.Text), 2)
		for item in circle1, circle2, link:
			item.setPen(pen)

	link_two_circles(scene)

	def link_two_draggable_widgets(scene):
		def create_widget(geometry=QRectF(0,0,100, 100), color=QColor("purple")):
			widget = QGraphicsWidget()
			widget.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
			widget.setGeometry(geometry)
			widget.setAutoFillBackground(True)
			palette1 = widget.palette()
			palette1.setColor(QPalette.ColorRole.Window, color)
			widget.setPalette(palette1)
			return widget
		
		widget1 = create_widget(QRectF(-100,100,100,100), QColor("orange"))
		scene.addItem(widget1)
		widget2 = create_widget(QRectF(100,100,100,100), QColor("purple"))
		scene.addItem(widget2)

		link = QGraphicsLineItem()
		def update_link():
			link.setLine( makeLineBetweenShapes(
				widget1.sceneTransform().map(widget1.shape()),
				widget2.sceneTransform().map(widget2.shape())
			) )

		widget1.geometryChanged.connect(update_link)
		widget2.geometryChanged.connect(update_link)
		scene.addItem(link)

		pen = QPen(app.palette().color(QPalette.ColorRole.Text), 2)
		link.setPen(pen)
		update_link()
		

	link_two_draggable_widgets(scene)

	view = QGraphicsView()
	view.setRenderHints(QPainter.Antialiasing)
	view.setScene(scene)
	view.show()
	view.fitInView(scene.itemsBoundingRect().adjusted(-100,-100,100,100), Qt.AspectRatioMode.KeepAspectRatio)

	app.exec()