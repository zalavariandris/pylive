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
