import numpy as np
import streamlit as st
import plotly.graph_objects as go
from typing import List, Tuple, Dict, Any

# --- Calibration functions ---

from core import LineSegment, VanishingPoint, PrincipalPoint, RotationMatrix


def compute_vanishing_point(lines: List[LineSegment]) -> VanishingPoint:
    """
    Compute the vanishing point from a set of 2D lines assumed to be parallel in 3D.

    Args:
        lines (List[LineSegment]): List of line segments ((x1,y1),(x2,y2)).

    Returns:
        VanishingPoint: Homogeneous coordinates of the vanishing point [x, y, 1].
    """
    if len(lines) < 2:
        raise ValueError("At least two lines are required to compute a vanishing point")
    A = []
    for (x1, y1), (x2, y2) in lines:
        a = y1 - y2
        b = x2 - x1
        c = x1*y2 - x2*y1
        A.append([a, b, c])
    A = np.array(A)
    _, _, Vt = np.linalg.svd(A)
    vp = Vt[-1]
    result = vp / vp[2]
    return result[0], result[1]


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


def compute_camera_orientation(vps: List[VanishingPoint], f: float, principal_point: PrincipalPoint) -> RotationMatrix:
    """
    Compute the camera rotation matrix from vanishing points and focal length.

    Args:
        vps (List[VanishingPoint]): List of vanishing points for each axis.
        f (float): Focal length.
        principal_point (PrincipalPoint): Image principal point (u0, v0).

    Returns:
        RotationMatrix: 3x3 rotation matrix representing camera orientation.
    """
    u0, v0 = principal_point
    K = np.array([[f, 0, u0],
                  [0, f, v0],
                  [0, 0, 1]])
    Kinv = np.linalg.inv(K)

    dirs = []
    for vp in vps:
        d = Kinv @ np.array([vp[0], vp[1], 1.0])
        d /= np.linalg.norm(d)
        dirs.append(d)

    x_axis = dirs[0]
    y_axis = dirs[1] - np.dot(dirs[1], x_axis) * x_axis
    y_axis /= np.linalg.norm(y_axis)
    z_axis = np.cross(x_axis, y_axis)
    z_axis /= np.linalg.norm(z_axis)

    R = np.column_stack((x_axis, y_axis, z_axis))
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
