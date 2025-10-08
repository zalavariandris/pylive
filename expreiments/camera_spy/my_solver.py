import numpy as np
from typing import List, Tuple, Dict, Any
from imgui_bundle import imgui
import math
import glm
from core import LineSegment, Point2D, VanishingPoint, PrincipalPoint, RotationMatrix
from typing import NewType
Degrees = NewType("Degrees", float)
Radians = NewType("Radians", float)

def compute_vanishing_point(vanishing_lines: List[LineSegment]) -> glm.vec2:
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
    return glm.vec2(result[0], result[1])


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


def _compute_camera_position(*,viewport_size:imgui.ImVec2, fov:float, screen_origin:imgui.ImVec2, principal_point:imgui.ImVec2, camera_pitch:float, distance:float):
    ## 2. Compute camera POSITION from origin marker
    # Origin marker tells us where the world origin (0,0,0) appears on screen
    # We need to position the camera so that (0,0,0) projects to the origin marker
    
    # Convert origin to NDC space
    origin_ndc_x = (screen_origin.x - principal_point.x) / (viewport_size.x / 2.0)
    origin_ndc_y = (principal_point.y - screen_origin.y) / (viewport_size.y / 2.0)  # Flip Y
    
    # Calculate the ray direction from camera through the origin point in screen space
    # In camera space (before rotation):
    # - Camera looks down -Z axis
    # - X is right, Y is up
    aspect = viewport_size.x / viewport_size.y
    tan_half_fov = math.tan(math.radians(fov) / 2.0)
    
    # Ray direction in camera space (normalized device coordinates)
    ray_x = origin_ndc_x * tan_half_fov * aspect
    ray_y = origin_ndc_y * tan_half_fov
    ray_z = -1.0  # Looking down -Z
    
    # Normalize the ray
    ray_length = math.sqrt(ray_x**2 + ray_y**2 + ray_z**2)
    ray_x /= ray_length
    ray_y /= ray_length
    ray_z /= ray_length
    
    # Apply camera pitch rotation to ray (rotate around X axis)
    # After rotation, the ray is in world space
    cos_pitch = math.cos(camera_pitch)
    sin_pitch = math.sin(camera_pitch)
    
    ray_world_x = ray_x
    ray_world_y = ray_y * cos_pitch - ray_z * sin_pitch
    ray_world_z = ray_y * sin_pitch + ray_z * cos_pitch
    
    # Now solve: camera_pos + t * ray_world = (0, 0, 0)
    # We want the ray to hit the world origin at the given distance
    # Assuming world origin is on the ground plane (y=0):
    # camera_y + t * ray_world_y = 0
    # t = -camera_y / ray_world_y
    
    # But we also want: distance = ||camera_pos||
    # So we need to solve for camera position where:
    # 1. Ray passes through world origin (0,0,0)
    # 2. Camera is at distance 'distance' from world origin
    
    # Simplification: camera_pos = -t * ray_world, and ||camera_pos|| = distance
    # Therefore: t = distance
    
    camera_pos_x = -distance * ray_world_x
    camera_pos_y = -distance * ray_world_y
    camera_pos_z = -distance * ray_world_z

    return camera_pos_x, camera_pos_y, camera_pos_z

def _estimate_pitch_from_horizon(horizon:float, principal_point:imgui.ImVec2, size:imgui.ImVec2, fov:float)->float:
    # Convert horizon to NDC space
    horizon_ndc_y = (principal_point.y - horizon) / (size.y / 2.0)  # Flip Y
    
    # Calculate pitch angle from horizon NDC position
    pitch = math.atan2(-horizon_ndc_y * math.tan(math.radians(fov) / 2), 1.0)
    return pitch

def _build_camera_transform(camera_pitch, camera_pos_x, camera_pos_y, camera_pos_z):
    ## Build camera transform
    # The camera should be oriented based on pitch (from horizon) and positioned
    # so that the world origin (0,0,0) appears at the origin marker's screen position
    
    # Build the camera's local coordinate system
    # Start with camera looking down -Z with up being +Y
    camera_forward = glm.vec3(0, 0, -1)
    camera_up = glm.vec3(0, 1, 0)
    camera_right = glm.vec3(1, 0, 0)
    
    # Apply pitch rotation to the camera axes
    cos_pitch = math.cos(camera_pitch)
    sin_pitch = math.sin(camera_pitch)
    
    # Rotate forward and up vectors around X-axis (right vector stays the same)
    camera_forward = glm.vec3(0, sin_pitch, -cos_pitch)
    camera_up = glm.vec3(0, cos_pitch, sin_pitch)
    
    # Build rotation matrix from camera axes
    # OpenGL camera: right = +X, up = +Y, forward = -Z (view direction)
    rotation_matrix = glm.mat4(
        glm.vec4(camera_right, 0),
        glm.vec4(camera_up, 0),
        glm.vec4(-camera_forward, 0),  # Negative because camera looks down -Z
        glm.vec4(0, 0, 0, 1)
    )
    
    # Create translation matrix
    translation = glm.translate(glm.mat4(1.0), glm.vec3(camera_pos_x, camera_pos_y, camera_pos_z))
    
    # Combine: first rotate, then translate
    return translation * rotation_matrix

def solve_no_axis(*, 
        viewport_size:imgui.ImVec2, 
        screen_origin:imgui.ImVec2, 
        principal_point:imgui.ImVec2, 
        fov:Degrees, 
        distance:float, 
        horizon:float
    ) -> Tuple[float, float, float, float]:
    """Estimate camera pitch and position given no axis lines, just horizon and origin.
    
    return (camera_pitch, camera_pos_x, camera_pos_y, camera_pos_z)
    """
    ## 1. Compute camera PITCH from horizon line (camera orientation)
    # Horizon tells us where the camera is looking vertically

    # horizon_ndc_dy = (principal_point.y - horizon) / (size.y / 2.0)
    # camera_pitch = math.atan2(-horizon_ndc_dy * math.tan(math.radians(fov) / 2), 1.0)

    camera_pitch = _estimate_pitch_from_horizon(
        horizon, 
        principal_point, 
        viewport_size, 
        fov
    )

    camera_pos_x, camera_pos_y, camera_pos_z = _compute_camera_position(
        viewport_size=viewport_size,
        fov=fov,
        screen_origin=screen_origin,
        principal_point=principal_point,
        camera_pitch=camera_pitch,
        distance=distance
    )

    return camera_pitch, camera_pos_x, camera_pos_y, camera_pos_z
