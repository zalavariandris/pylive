from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from pylive.utils.geo import intersect_ray_with_polygon, intersect_ray_with_rectangle


def intersectLineWithPath(p1: QPointF, p2: QPointF, path: QPainterPath) -> QPointF|None:
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
    intersection_elements:List[QPainterPath.Element] = [intersection_path.elementAt(i) for i in range(intersection_path.elementCount())]

    # Filter intersection points in the forward direction of the ray
    for element in intersection_elements:
        intersection_point = QPointF(element.x, element.y)
        ray_to_point = QLineF(ray_start, intersection_point)

        # Ensure the point is in the forward direction of the ray
        if ray_to_point.dx() * ray_direction.x() >= 0 and ray_to_point.dy() * ray_direction.y() >= 0:
            return intersection_point

    # No valid intersection in the ray's forward direction
    return None


def getShapeCenter(shape:QPointF|QRectF|QPainterPath):
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
	center = getShapeCenter(shape)

	match shape:
		case QPointF():
			intersection = center

		case QRectF():
			rect = shape
			V = center-origin
			if xy:=intersect_ray_with_rectangle(
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
			if P:=intersectLineWithPath(origin, center, shape): #TODO: use intersect_ray_with_polygon
				intersection = P
			else:
				intersection = center

		case _:
			raise ValueError

	return QLineF(center, intersection)

def makeLineBetweenShapes(A:QPointF|QRectF|QPainterPath, B:QPointF|QRectF|QPainterPath)->QLineF:
	Ac = getShapeCenter(A)
	Bc = getShapeCenter(B)

	I2 = makeLineToShape(Ac, B).p2()
	I1 = makeLineToShape(Bc, A).p2()

	return QLineF(I1, I2)



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
	view.setRenderHints(QPainter.RenderHint.Antialiasing)
	view.setScene(scene)
	view.show()
	view.fitInView(scene.itemsBoundingRect().adjusted(-100,-100,100,100), Qt.AspectRatioMode.KeepAspectRatio)

	app.exec()