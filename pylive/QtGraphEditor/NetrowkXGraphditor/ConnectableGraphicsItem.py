from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from pylive.utils.geo import intersectRayWithRectangle

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


class ConnectableShape(QGraphicsWidget, QAbstractGraphicsShapeItem):
	shapeChanged = Signal()
	scenePositionChanged = Signal()

	def __init__(self, shape:Optional[QPainterPath]=None, parent:Optional[QGraphicsItem]=None):
		QGraphicsWidget.__init__(self, parent=parent)
		QAbstractGraphicsShapeItem.__init__(self, parent=parent)
		self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges)



		# cache geometry
		self._shape = QPainterPath()
		self._boundingrect = QRectF()

		# create default shape
		if not shape:
			# create default shape
			shape = QPainterPath()
			shape.addEllipse(-50,-50,100,100)
		self.setShape(shape)
		self.setBrush(self.palette().color(QPalette.ColorRole.Base))
		self.setPen(QPen(self.palette().color(QPalette.ColorRole.Text), 2))

	# @overload
	# def resize(self, w:float, h:float):...

	# @overload
	# def resize(self, size:QSizeF):...

	# def resize(self, *args): #type:ignore
	# 	match len(args):
	# 		case 1:
	# 			size = QRectF( args[0] )
	# 		case 2:
	# 			size = QRectF( args[0], args[1])

	# 	super().resize(size)

	def setShape(self, shape:QPainterPath):
		margin = self.pen().widthF()/2
		boundingrect = shape.boundingRect().adjusted(-margin,-margin,margin,margin)

		self._shape = shape
		self._boundingrect = boundingrect
		self.setGeometry(
			boundingrect.x()+self.x(), 
			boundingrect.y()+self.y(),
			boundingrect.width(),
			boundingrect.height()
		)
		self.shapeChanged.emit()
		self.update()

	def shape(self)->QPainterPath:
		return self._shape

	def boundingRect(self) -> QRectF:
		return self._boundingrect

	def paint(self, painter, option, widget=None):
		painter.setPen(self.pen())
		painter.setBrush(self.brush())
		path = self.shape()
		painter.drawPath(path)

	def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
		match change:
			case QGraphicsItem.GraphicsItemChange.ItemScenePositionHasChanged:
				self.scenePositionChanged.emit()

		return super().itemChange(change, value)



class ConnectableLink(QGraphicsWidget):
	def __init__(self, parent: Optional[QGraphicsItem]=None) -> None:
		super().__init__(parent)
		self._source:Optional[ConnectableShape] = None
		self._source_offset = QPointF(0,0)
		self._target:Optional[ConnectableShape] = None
		self._target_offset = QPointF(0,0)

		# components
		palette = self.palette()
		textColor = palette.color(QPalette.ColorGroup.All, QPalette.ColorRole.Text)
		
		# arrow shaft
		self.shaft = QGraphicsLineItem(self)
		pen = QPen( QPen(textColor, 1.5) )
		pen.setCapStyle(Qt.FlatCap)
		self.shaft.setPen(pen)

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

		# #
		# self.updatePosition()

	def link(self, source, target):
		self._setSource(source)
		self._setTarget(target)
		self.update()

	def _setSource(self, source:ConnectableShape|QPointF|None, offset:QPointF=QPointF(0,0)):
		# disconnect signals from current source
		try:
			self._source.scenePositionChanged.disconnect(self.update) #type: ignore
		except AttributeError:
			pass
		try:
			self._source.shapeChanged.disconnect(self.update)  #type: ignore
		except AttributeError:
			pass

		match source:
			case QGraphicsItem():
				self._source = source
				self._source_offset = offset
			case QPointF():
				self._source = None
				self._source_offset = source+offset
			case None:
				self._source = None
				self._source_offset = offset
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

		# self.update()

	def _setTarget(self, target:ConnectableShape|QPointF|None, offset:QPointF=QPointF(0,0)):
		# disconnect signals from current source
		try:
			self._target.scenePositionChanged.disconnect(self.update) #type: ignore
		except AttributeError:
			pass
		try:
			self._target.shapeChanged.disconnect(self.update)  #type: ignore
		except AttributeError:
			pass

		match target:
			case QGraphicsItem():
				self._target = target
				self._target_offset = offset
			case QPointF():
				self._target = None
				self._target_offset = target+offset
			case None:
				self._target = None
				self._target_offset = offset
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

		# self.update()

	@overload
	def update(self, rect:QRectF|QRect=QRectF()):...

	@overload
	def update(self, x:float, y:float,w:float, h:float)->None:...

	@override
	def update(self, *args): #type: ignore
		match len(args):
			case 0:
				rect  = QRectF()
			case 1:
				rect = QRectF(args[0])
			case 4:
				x,y,w,h = args
				rect = QRectF(x,y,w,h)
			case _:
				raise ValueError(f"{args}")

		self.updatePosition()

		super().update(rect)

	def updatePosition(self):
		assert self._source
		assert self._target

		margin = 0
		source_rect = self._source.mapToScene(
			self._source.boundingRect().adjusted(-margin,-margin,margin,margin)
		).boundingRect()

		target_rect = self._target.mapToScene(
			self._target.boundingRect().adjusted(-margin,-margin,margin,margin)
		).boundingRect()

		# source_center = source_rect.center()
		# target_center = target_rect.center()
		# direction = target_center-source_center

		### line between center points ###
		line = QLineF(
			self.shaft.mapFromScene(source_rect.center()), 
			self.shaft.mapFromScene(target_rect.center())
		)

		### intersect line with rectangle ###
		# line = intersectLineWithRectangle(line, target_rect)
		# line = intersectLineWithRectangle(line, source_rect, direction='backward')

		### intersect line with shapes ###
		target_shape = self._target.sceneTransform().map(self._target.shape())
		source_shape = self._source.sceneTransform().map(self._source.shape())

		I2 = intersectLineWithPath(line.p1(), line.p2(), target_shape)
		I1 = intersectLineWithPath(line.p2(), line.p1(), source_shape)
		if I2:
			line.setP2(I2)
		if I1:
			line.setP1(I1)

		self.setVisible(True if I1 and I2 else False)

		# adjust shaft length, with head size
		line = QLineF(
			self.shaft.mapFromScene(line.p1()), 
			self.shaft.mapFromScene(line.p2())
		)
		shaft_line = QLineF(line)
		shaft_line.setLength(shaft_line.length()-self.headsize)
		self.shaft.setLine(shaft_line)

		# transform head
		transform = QTransform()
		transform.translate(line.p2().x(), line.p2().y())
		transform.rotate(-line.angle())
		self.arrowhead.setTransform(transform)

		# transform the tail
		transform = QTransform()
		transform.translate(line.p1().x(), line.p1().y())
		transform.rotate(-line.angle())
		self.arrowtail.setTransform(transform)


if __name__ == "__main__":
	app = QApplication()
	view = QGraphicsView()
	view.setRenderHints(QPainter.Antialiasing)
	scene = QGraphicsScene()
	view.setSceneRect(-1000,-1000,2000,2000)
	view.setScene(scene)
	view.show()

	class GroupWidget(QGraphicsWidget):
		def __init__(self, parent=None):
			super().__init__(parent=parent)

			self.frame = QGraphicsRectItem(0,0,300,300, parent=self)
			self.setGeometry(0,0,300,300)
			self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)

		# def paint(self, painter, option, widget=None):
		# 	painter.drawRoundedRect(QRectF(0,0,self.geometry().width(), self.geometry().height()), 5, 5)

	circle = QPainterPath()
	circle.addEllipse(-50,-50,100,100)
	circle_shape = ConnectableShape(circle)
	circle_shape.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
	scene.addItem(circle_shape)

	rect = QPainterPath()
	rect.addRoundedRect(-50,-50,100,100, 10, 10)
	rect_shape = ConnectableShape(rect)
	rect_shape.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
	scene.addItem(rect_shape)

	link = ConnectableLink()
	link.link(circle_shape, rect_shape)
	scene.addItem(link)

	def test_path_intersection():
		ray_path = QPainterPath()
		ray_path.moveTo(-100,0,)
		ray_path.lineTo(100,0)
		stroker = QPainterPathStroker(QPen(QColor("red"), 5))
		ray_stroke = stroker.createStroke(ray_path)

		rect_path = QPainterPath()
		rect_path.addRect(0,-10,20,20)

		intersection = ray_stroke.intersected(rect_path)
		print(intersection)
	test_path_intersection()


	app.exec()