from typing import *

import math
def intersectRayWithRectangle(origin:Tuple[float, float], 
							  direction:Tuple[float, float],
							  top:float,
							  left:float,
							  bottom:float,
							  right:float
	)->Tuple[float, float]|None:
	rect_min, rect_max = (left, bottom), (right, top)

	t_min = float('-inf')
	t_max = float('inf')

	if direction[0]==0 or direction[1] == 0:
		return None

	# normalize direction
	length = math.sqrt(direction[0]*direction[0]+direction[1]*direction[1])
	direction = direction[0]/length, direction[1]/length

	for i in range(2):  # For x and y axis
		if direction[i] != 0:
			# Calculate the intersection for the current axis
			t1 = (rect_min[i] - origin[i]) / direction[i]
			t2 = (rect_max[i] - origin[i]) / direction[i]

			# Ensure t1 is the smaller and t2 is the larger value
			if t1 > t2:
				t1, t2 = t2, t1

			# Update the overall intersection interval
			t_min = max(t_min, t1)
			t_max = min(t_max, t2)

			# If no valid intersection range, return None
			if t_min > t_max:
				return None

		elif origin[i] < rect_min[i] or origin[i] > rect_max[i]:
			# Ray is parallel and outside the rectangle
			return None

	# Calculate the point of intersection at t_min (if valid)
	return (
		origin[0] + t_min * direction[0],
		origin[1] + t_min * direction[1]
	)

def line_intersection(p1, p2, q1, q2)->Tuple[float, float]|None:
	"""
	Helper function to compute the intersection of two line segments (p1-p2 and q1-q2).
	Returns the intersection point or None if no intersection.
	"""
	dx1, dy1 = p2.x() - p1.x(), p2.y() - p1.y()
	dx2, dy2 = q2.x() - q1.x(), q2.y() - q1.y()
	
	det = dx1 * dy2 - dy1 * dx2
	if abs(det) < 1e-10:  # Parallel lines
		return None
	
	# Parametric intersection calculation
	t = ((q1.x() - p1.x()) * dy2 - (q1.y() - p1.y()) * dx2) / det
	u = ((q1.x() - p1.x()) * dy1 - (q1.y() - p1.y()) * dx1) / det
	
	if t >= 0 and 0 <= u <= 1:  # t >= 0 ensures the intersection is along the ray
		x = p1.x() + t * dx1
		y = p1.y() + t * dy1
		return x, y

	return None

def distance(p1:Tuple[float, float], p2:Tuple[float, float])->float:
	x1, y1 = p1
	x2, y2 = p2
	dx = x2-x1
	dy = y2-y1
	return math.sqrt(dx*dx+dy*dy)

def intersectRayWithPolygon(origin:Tuple[float, float], 
							direction:Tuple[float, float],
							vertices:List[Tuple[float, float]]
	)->Tuple[float, float]|None:


	closest_point = None
	min_distance = float('inf')

	# Define the ray's endpoint far in the direction
	ray_end = (origin[0] + direction[0] * 1e6, origin[1] + direction[1] * 1e6)

	# Iterate over all edges of the polygon defined by vertices
	for i in range(len(vertices)):
		p1 = vertices[i]
		p2 = vertices[(i + 1) % len(vertices)]  # Wrap around to the first vertex
		
		intersection = line_intersection(origin, ray_end, p1, p2)
		if intersection:
			d = distance(intersection, origin)
			if d < min_distance:
				closest_point = intersection
				min_distance = d

	return closest_point