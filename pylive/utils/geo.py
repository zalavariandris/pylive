from typing import *

def intersectRayWithRectangle(origin:Tuple[float, float], 
							 direction:Tuple[float, float],
							 top:float,
							 left:float,
							 bottom:float,
							 right:float
							 )->Tuple[float, float]:
	rect_min, rect_max = (left, bottom), (right, top)

	t_min = float('-inf')
	t_max = float('inf')

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
