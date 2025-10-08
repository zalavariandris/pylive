import numpy as np
from typing import List, Tuple, Dict, Any

# --- Calibration functions ---

from core import LineSegment, Point2D, VanishingPoint, PrincipalPoint, RotationMatrix


def compute_vanishing_point(vanishing_lines: List[LineSegment]) -> Tuple[float, float]:
    """
    Compute the vanishing point from a set of 2D lines assumed to be parallel in 3D.

    Args:
        lines (List[LineSegment]): List of line segments ((x1,y1),(x2,y2)).

    Returns:
        VanishingPoint: Homogeneous coordinates of the vanishing point [x, y, 1].
    """
    if len(vanishing_lines) < 2:
        raise ValueError("At least two lines are required to compute a vanishing point")
    A = []
    for (x1, y1), (x2, y2) in vanishing_lines:
        a = y1 - y2
        b = x2 - x1
        c = x1*y2 - x2*y1
        A.append([a, b, c])
    A = np.array(A)
    _, _, Vt = np.linalg.svd(A)
    vp = Vt[-1]
    result = vp / vp[2]
    return tuple(result[0], result[1])


def estimate_focal_length(v1: VanishingPoint, v2: VanishingPoint, principal_point: PrincipalPoint) -> float:
    """
    Estimate the camera focal length from two orthogonal vanishing points.

    Args:
        v1 (VanishingPoint): First vanishing point.
        v2 (VanishingPoint): Second vanishing point.
        principal_point (PrincipalPoint): Image principal point (u0, v0).

    Returns:
        float: Estimated focal length.

    Raises:
        ValueError: If configuration is invalid and focal length cannot be solved.
    """
    u0, v0 = principal_point
    x1, y1 = v1[0] - u0, v1[1] - v0
    x2, y2 = v2[0] - u0, v2[1] - v0
    f2 = -(x1*x2 + y1*y2)
    if f2 <= 0:
        raise ValueError("Invalid configuration, cannot solve focal length")
    return float(np.sqrt(f2))


def compute_camera_orientation(vanishing_points: List[Point2D], focal_length: float, principal_point: Point2D) -> np.ndarray:
    """
    Compute camera rotation matrix from vanishing points using fSpy's method.
    
    Args:
        vanishing_points: List of 2 or 3 vanishing points corresponding to world axes (X, Y, Z order)
        focal_length: Camera focal length in pixels
        principal_point: Principal point (u0, v0) in pixels
    
    Returns:
        3x3 rotation matrix representing the VIEW TRANSFORM (world-to-camera).
        This is the matrix that transforms world coordinates to camera coordinates.
        For the camera's transform matrix, take the transpose (inverse for rotation).
    
    Reference: fSpy solver.ts - computeCameraRotationMatrix()
    """
    if len(vanishing_points) < 2:
        raise ValueError("Need at least 2 vanishing points to compute camera orientation")
    
    u0, v0 = principal_point
    vp1, vp2 = vanishing_points[0], vanishing_points[1]
    
    # Vectors from principal point to vanishing points in image plane coordinates
    # Note: Z = -f because camera looks down -Z axis (OpenGL convention)
    OFu = np.array([vp1[0] - u0, vp1[1] - v0, -focal_length])
    OFv = np.array([vp2[0] - u0, vp2[1] - v0, -focal_length])
    
    # Normalize to get direction vectors (first two rows of rotation matrix)
    s1 = np.linalg.norm(OFu)
    s2 = np.linalg.norm(OFv)
    upRc = OFu / s1  # First world axis direction in camera space
    vpRc = OFv / s2  # Second world axis direction in camera space
    
    # Third axis via cross product
    wpRc = np.cross(upRc, vpRc)
    
    # Build rotation matrix as rows (world axes in camera space)
    # This is the world-to-camera transform
    R = np.array([
        [upRc[0], vpRc[0], wpRc[0]],  # Row 0: how world X, Y, Z map to camera X
        [upRc[1], vpRc[1], wpRc[1]],  # Row 1: how world X, Y, Z map to camera Y
        [upRc[2], vpRc[2], wpRc[2]]   # Row 2: how world X, Y, Z map to camera Z
    ])
    
    return R


def calibrate_camera(lines_by_axis: List[List[LineSegment]], principal_point: PrincipalPoint) -> Dict[str, Any]:
    """
    Perform full camera calibration given axis-aligned lines.

    Args:
        lines_by_axis (List[List[LineSegment]]): List of three lists of line segments for X, Y, Z axes.
        principal_point (PrincipalPoint): Image principal point (u0, v0).

    Returns:
        Dict[str, Any]: Dictionary containing:
            - 'focal_length': estimated focal length
            - 'rotation': camera rotation matrix
            - 'vanishing_points': list of vanishing points for each axis
    """
    vps = [compute_vanishing_point(lines) for lines in lines_by_axis]
    f = estimate_focal_length(vps[0], vps[1], principal_point)
    R = compute_camera_orientation(vps, f, principal_point)
    return {"focal_length": f, "rotation": R, "vanishing_points": vps}
