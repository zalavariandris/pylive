from typing import List, Tuple, Optional
import math


def intersect_ray_with_rectangle(
    origin: Tuple[float, float],
    direction: Tuple[float, float],
    top: float,
    left: float,
    bottom: float,
    right: float,
) -> Optional[Tuple[float, float]]:
    """
    Intersects a ray with an axis-aligned rectangle.
    """
    EPSILON = 0.00001
    # Parametrize the ray: Ray = ray_origin + t * ray_direction
    t_min = -math.inf
    t_max = math.inf

    # Check intersection with the x boundaries of the rectangle
    if direction[0] != 0:
        t_x_min = (left - origin[0]) / direction[0]
        t_x_max = (right - origin[0]) / direction[0]

        if t_x_min > t_x_max:
            t_x_min, t_x_max = t_x_max, t_x_min

        t_min = max(t_min, t_x_min)
        t_max = min(t_max, t_x_max)
    elif not (left <= origin[0] <= right):
        # If the ray is parallel to the x-axis but not within the rectangle's x bounds
        return None

    # Check intersection with the y boundaries of the rectangle
    if direction[1] != 0:
        t_y_min = (top - origin[1]) / direction[1]
        t_y_max = (bottom - origin[1]) / direction[1]

        if t_y_min > t_y_max:
            t_y_min, t_y_max = t_y_max, t_y_min

        t_min = max(t_min, t_y_min)
        t_max = min(t_max, t_y_max)
    elif not (top <= origin[1] <= bottom):
        # If the ray is parallel to the y-axis but not within the rectangle's y bounds
        return None

    # Check if the ray actually intersects the rectangle
    if t_min > t_max or t_max < 0:
        return None

    # Calculate the intersection point using the valid t_min
    intersection_point = (
        origin[0] + t_min * direction[0],
        origin[1] + t_min * direction[1],
    )

    # Check if the intersection point is within the rectangle's boundaries
    if (
        left - EPSILON <= intersection_point[0] <= right
        and top - EPSILON <= intersection_point[1] <= bottom
    ):
        return intersection_point
    return None


def line_intersection(
    p1: Tuple[float, float],
    p2: Tuple[float, float],
    q1: Tuple[float, float],
    q2: Tuple[float, float],
) -> Tuple[float, float] | None:
    """
    Helper function to compute the intersection of two line segments (p1-p2 and q1-q2).
    Returns the intersection point or None if no intersection.
    """
    dx1, dy1 = p2[0] - p1[0], p2[1] - p1[1]
    dx2, dy2 = q2[0] - q1[0], q2[1] - q1[1]

    det = dx1 * dy2 - dy1 * dx2
    if abs(det) < 1e-10:  # Parallel lines
        return None

    # Parametric intersection calculation
    t = ((q1[0] - p1[0]) * dy2 - (q1[1] - p1[1]) * dx2) / det
    u = ((q1[0] - p1[0]) * dy1 - (q1[1] - p1[1]) * dx1) / det

    if (
        t >= 0 and 0 <= u <= 1
    ):  # t >= 0 ensures the intersection is along the ray
        x = p1[0] + t * dx1
        y = p1[1] + t * dy1
        return x, y

    return None


def distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    x1, y1 = p1
    x2, y2 = p2
    dx = x2 - x1
    dy = y2 - y1
    return math.sqrt(dx * dx + dy * dy)


def intersect_ray_with_polygon(
    origin: Tuple[float, float],
    direction: Tuple[float, float],
    vertices: List[Tuple[float, float]],
) -> Tuple[float, float] | None:
    closest_point = None
    min_distance = float("inf")

    # Define the ray's endpoint far in the direction
    ray_end = (origin[0] + direction[0] * 1e6, origin[1] + direction[1] * 1e6)

    # Iterate over all edges of the polygon defined by vertices
    for i in range(len(vertices)):
        p1 = vertices[i]
        p2 = vertices[
            (i + 1) % len(vertices)
        ]  # Wrap around to the first vertex

        intersection = line_intersection(origin, ray_end, p1, p2)
        if intersection:
            d = distance(intersection, origin)
            if d < min_distance:
                closest_point = intersection
                min_distance = d

    return closest_point


from pylive.utils.geo import (
    intersect_ray_with_polygon,
    intersect_ray_with_rectangle,
)

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *


def intersectLineWithPath(
    p1: QPointF, p2: QPointF, path: QPainterPath
) -> QPointF | None:
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
    intersection_elements: List[QPainterPath.Element] = [
        intersection_path.elementAt(i)
        for i in range(intersection_path.elementCount())
    ]

    # Filter intersection points in the forward direction of the ray
    for element in intersection_elements:
        intersection_point = QPointF(element.x, element.y)
        ray_to_point = QLineF(ray_start, intersection_point)

        # Ensure the point is in the forward direction of the ray
        if (
            ray_to_point.dx() * ray_direction.x() >= 0
            and ray_to_point.dy() * ray_direction.y() >= 0
        ):
            return intersection_point

    # No valid intersection in the ray's forward direction
    return None


def getShapeRight(shape:QGraphicsItem | QPainterPath | QRectF | QPointF)->QPointF:
    """return scene position"""
    match shape:
        case QGraphicsItem():
            return shape.mapToScene(QPointF(shape.boundingRect().right(), shape.boundingRect().center().y()))
        case QPainterPath():
            rect = shape.boundingRect()
            return QPointF(rect.right(), rect.center().y())
        case QRectF():
            return QPointF(shape.right(), shape.center().y())
        case QPointF():
            return shape
        case _:
            raise ValueError()


def getShapeLeft(shape:QGraphicsItem | QPainterPath | QRectF | QPointF)->QPointF:
    match shape:
        case QGraphicsItem():
            return shape.mapToScene(QPointF(shape.boundingRect().left(), shape.boundingRect().center().y()))#+QPointF(shape.boundingRect().right(), 0)
        case QPainterPath():
            rect = shape.boundingRect()
            return QPointF(rect.left(), rect.center().y())
        case QRectF():
            return QPointF(shape.left(), shape.center().y())
        case QPointF():
            return shape
        case _:
            raise ValueError()


def getShapeCenter(shape: QPointF | QRectF | QPainterPath | QGraphicsItem):
    match shape:
        case QPointF():
            return shape
        case QRectF():
            return shape.center()
        case QPainterPath():
            return shape.boundingRect().center()
        case QGraphicsItem():
            sceneShape = shape.sceneTransform().map(shape.shape())
            return sceneShape.boundingRect().center()
        case _:
            raise ValueError


def makeLineToShape(
    origin: QPointF, shape: QPointF | QRectF | QPainterPath | QGraphicsItem
):
    center = getShapeCenter(shape)

    match shape:
        case QPointF():
            intersection = center

        case QRectF():
            rect = shape
            V = center - origin
            if xy := intersect_ray_with_rectangle(
                origin=(origin.x(), origin.y()),
                direction=(V.x(), V.y()),
                top=rect.top(),
                left=rect.left(),
                bottom=rect.bottom(),
                right=rect.right(),
            ):
                intersection = QPointF(*xy)
            else:
                intersection = center

        case QPainterPath():
            if P := intersectLineWithPath(
                origin, center, shape
            ):  # TODO: use intersect_ray_with_polygon
                intersection = P
            else:
                intersection = center
        case QGraphicsItem():
            sceneShape = shape.sceneTransform().map(shape.shape())
            if P := intersectLineWithPath(
                origin, center, sceneShape
            ):  # TODO: use intersect_ray_with_polygon
                intersection = P
            else:
                intersection = center
        case _:
            raise ValueError

    return QLineF(origin, intersection)


def makeLineBetweenShapes(
    A: QPointF | QRectF | QPainterPath | QGraphicsItem,
    B: QPointF | QRectF | QPainterPath | QGraphicsItem,
) -> QLineF:
    Ac = getShapeCenter(A)
    Bc = getShapeCenter(B)

    I2 = makeLineToShape(Ac, B).p2()
    I1 = makeLineToShape(Bc, A).p2()

    return QLineF(I1, I2)


def makeRoundedPath(line:QLineF):
    A = line.p1()
    B = line.p2()
    Ax, Ay = A.x(), A.y()
    Bx, By = B.x(), B.y()
    dx = Bx - Ax
    dy = By - Ay

    path = QPainterPath()
    path.moveTo(A)
    r = 27
    if dx < 0:
        r1 = min(r, min(abs(dx/4), abs(dy/4)))
        r2 = min(abs(dx), abs(dy)-r1*3)
        # angle = abs(angle)
        if dy > 0:
            # pen.setColor("cyan") # upper left DONE
            angle = math.degrees(math.atan2(dy-(r1+r2)*2, dx-(r1+r2)))
            path.arcTo(
                Ax-r1, Ay, r1*2,r1*2, 90, -180
            )
            path.arcTo(
                Bx-r1, 
                Ay+r2*2+r1*2, 
                r2*2,
                -r2*2, 
                -90, -90
            )
            path.arcTo(
                Bx+r1,
                By-r1*2,
                -r1*2,
                r1*2,
                0,-90
            )
        else:
            # pen.setColor("yellow") # upper left DONE
            angle = math.degrees(math.atan2(dy-(r1+r2)*2, dx-(r1+r2)))
            path.arcTo(
                Ax-r1, Ay, r1*2,-r1*2, 90, -180
            )
            path.arcTo(
                Bx-r1, 
                Ay-r2*2-r1*2, 
                r2*2,
                r2*2, 
                -90, -90
            )
            path.arcTo(
                Bx+r1,
                By+r1*2,
                -r1*2,
                -r1*2,
                0,-90
            )
    else:
        r1 = min(r, min(abs(dx/2), abs(dy/2)))
        r2 = min(abs(dx), abs(dy))-r1
        # angle = abs(angle)
        if dy > 0:
            # pen.setColor("red") # lower right DONE
            path.arcTo(
                Ax-r1, Ay, r1*2,r1*2, 90, -90
            )
            path.arcTo(
                Ax+r1,
                By-r2*2,
                r2*2,
                r2*2,
                180,
                90
            )
        else:
            # pen.setColor("green") #upper right DONE
            r1 = min(r, min(abs(dx/2), abs(dy/2)))
            r2 = min(abs(dx), abs(dy))-r1
            path.arcTo(
                Ax-r1, Ay, r1*2,-r1*2, 90, -90
            )
            path.arcTo(
                Ax+r1,
                By+r2*2,
                r2*2,
                -r2*2,
                180,
                90
            )
    path.lineTo(B)
    return path

def makeArrowShape(line:QLineF, width=1.0):
    # arrow shape
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
    transform.translate(line.p1().x(), line.p1().y())
    transform.rotate(-line.angle())

    path = QPainterPath()
    path.addPolygon(transform.map(arrow_polygon))


    return path



# import math
# def fillet(A: QPointF, B: QPointF, C: QPointF, r: float) -> tuple[QPointF, QPointF, QPointF, float, float]:
#     """
#     NOT WOKRING
#     Calculate fillet between two lines defined by points A-B and B-C, including arc angles.
    
#     Args:
#         A: First point of first line
#         B: Corner point (intersection of lines)
#         C: Second point of second line
#         r: Radius of the fillet
        
#     Returns:
#         Tuple of (tangent_point1, tangent_point2, center_point, start_angle, sweep_angle)
#         Angles are in radians. Sweep angle is positive for counterclockwise direction.
#     """
#     def unit_vector(v: QPointF) -> QPointF:
#         length = math.sqrt(v.x()**2 + v.y()**2)
#         if abs(length) < 1e-10:
#             raise ValueError("Zero length vector")
#         return QPointF(v.x() / length, v.y() / length)
    
#     def dot_product(v1: QPointF, v2: QPointF) -> float:
#         return v1.x() * v2.x() + v1.y() * v2.y()
    
#     def vector_angle(v: QPointF) -> float:
#         """Calculate angle of vector from positive x-axis in radians."""
#         angle = math.atan2(v.y(), v.x())
#         return angle if angle >= 0 else angle + 2 * math.pi

#     # Input validation
#     if r <= 0:
#         raise ValueError("Radius must be positive")
    
#     # Get direction vectors for both lines
#     dir1 = unit_vector(QPointF(A.x() - B.x(), A.y() - B.y()))
#     dir2 = unit_vector(QPointF(C.x() - B.x(), C.y() - B.y()))
    
#     # Calculate angle between lines
#     cos_theta = dot_product(dir1, dir2)
#     if abs(cos_theta - 1) < 1e-10:
#         raise ValueError("Lines are parallel or nearly parallel")
    
#     # Calculate tangent distance from corner
#     angle = math.acos(cos_theta)
#     tan_distance = r / math.tan(angle / 2)
    
#     # Calculate tangent points
#     tangent1 = QVector2D(
#         B.x() + dir1.x() * tan_distance,
#         B.y() + dir1.y() * tan_distance
#     )
    
#     tangent2 = QVector2D(
#         B.x() + dir2.x() * tan_distance,
#         B.y() + dir2.y() * tan_distance
#     )
    
#     # Calculate center point
#     center_dir = unit_vector(QVector2D(
#         dir1.x() + dir2.x(),
#         dir1.y() + dir2.y()
#     ))
    
#     center_distance = r / math.sin(angle / 2)
    
#     center = QPointF(
#         B.x() + center_dir.x() * center_distance,
#         B.y() + center_dir.y() * center_distance
#     )
    
#     # Calculate arc angles
#     # Vector from center to first tangent point
#     radius_vector1 = QPointF(
#         tangent1.x() - center.x(),
#         tangent1.y() - center.y()
#     )
    
#     # Calculate start angle (from positive x-axis to first radius vector)
#     start_angle = vector_angle(radius_vector1)
    
#     # Calculate sweep angle
#     sweep_angle = angle
    
#     # Determine if we need to sweep clockwise or counterclockwise
#     # Cross product of radius vectors to determine orientation
#     cross_product = (radius_vector1.x() * (tangent2.y() - center.y()) - 
#                     radius_vector1.y() * (tangent2.x() - center.x()))
#     if cross_product < 0:
#         sweep_angle = -sweep_angle
    
#     return tangent1, tangent2, center, start_angle, sweep_angle