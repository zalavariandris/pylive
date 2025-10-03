from typing import List, Tuple
import numpy as np

Point2D = Tuple[float, float]
LineSegment = Tuple[Point2D, Point2D]
PrincipalPoint = Tuple[float, float]
VanishingPoint = np.ndarray
RotationMatrix = np.ndarray

__all__ = ["Point2D"]