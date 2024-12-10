from typing import List, Tuple, Optional
import math


def intersect_ray_with_rectangle(
	origin: Tuple[float, float],
	direction: Tuple[float, float],
	top: float,
	left: float,
	bottom: float,
	right: float
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
    if left-EPSILON <= intersection_point[0] <= right and top-EPSILON <= intersection_point[1] <= bottom:
        return intersection_point
    return None

def line_intersection(p1:Tuple[float, float], p2:Tuple[float, float], q1:Tuple[float, float], q2:Tuple[float, float])->Tuple[float, float]|None:
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
	
	if t >= 0 and 0 <= u <= 1:  # t >= 0 ensures the intersection is along the ray
		x = p1[0] + t * dx1
		y = p1[1] + t * dy1
		return x, y

	return None

def distance(p1:Tuple[float, float], p2:Tuple[float, float])->float:
	x1, y1 = p1
	x2, y2 = p2
	dx = x2-x1
	dy = y2-y1
	return math.sqrt(dx*dx+dy*dy)

def intersect_ray_with_polygon(origin:Tuple[float, float], 
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