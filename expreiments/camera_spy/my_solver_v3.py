import numpy as np
import glm
from typing import List, Tuple
import math

from enum import IntEnum
class Axis(IntEnum):
    PositiveX = 0
    NegativeX = 1
    PositiveY = 2
    NegativeY = 3
    PositiveZ = 4
    NegativeZ = 5

from gizmos import draw

def solve1vp(
    image_width:int,
    image_height:int,
    principal_point_pixel: glm.vec2,
    origin_pixel: glm.vec2,
    first_vanishing_lines_pixel: List[Tuple[glm.vec2, glm.vec2]],
    second_vanishing_line_pixel: Tuple[glm.vec2, glm.vec2], # determines the horizon roll
    focal_length_pixel: float,
    first_axis = Axis.PositiveZ,
    second_axis = Axis.PositiveX,
    scene_scale:float=1.0
):
    # Compute Camera
    ###############################
    # 1. COMPUTE vanishing points #
    ###############################
    first_vanishing_point_pixel =  least_squares_intersection_of_lines(first_vanishing_lines_pixel)
    draw.points([first_vanishing_point_pixel], ["1st VP"])

    #################################
    # 2. COMPUTE Camera Orientation #
    #################################
    import fspy_solver_functional as fspy
    forward = glm.normalize(glm.vec3(first_vanishing_point_pixel-principal_point_pixel, -focal_length_pixel))
    up = glm.normalize(glm.cross(forward, glm.vec3(1,0,0)))
    right = glm.cross(forward, up)
    view_orientation_matrix = glm.mat3(forward, right, up)

    glm.determinant(view_orientation_matrix)
    if 1-math.fabs(glm.determinant(view_orientation_matrix)) > 1e-5:
        raise Exception(f'Invalid vanishing point configuration. Rotation determinant {glm.determinant(view_orientation_matrix)}')

    # apply axis assignment
    axis_assignment_matrix:glm.mat3 = create_axis_assignment_matrix(first_axis, second_axis)            
    view_orientation_matrix:glm.mat3 = view_orientation_matrix * glm.inverse(axis_assignment_matrix)

    # convert to 4x4 matrix for transformations
    view_rotation_transform:glm.mat4 = glm.mat4(view_orientation_matrix)
    view_rotation_transform[3][3] = 1.0

    ##############################
    # 3. COMPUTE Camera Position #
    ##############################
    fovy = math.atan(image_height / 2 / focal_length_pixel) * 2
    near = 0.1
    far = 100
    projection_matrix = glm.perspective(
        fovy, # fovy in radians
        image_width/image_height, # aspect 
        near,
        far
    )

    origin_3D = glm.unProject(
        glm.vec3(
            origin_pixel.x, 
            origin_pixel.y, 
            _world_depth_to_ndc_z(scene_scale, near, far)
        ),
        view_rotation_transform, 
        projection_matrix, 
        glm.vec4(0,0,image_width,image_height)
    )


    # create transformation
    view_translate_transform = glm.translate(glm.mat4(1.0), -origin_3D)
    view_rotation_transform = glm.mat4(view_orientation_matrix)
    view_transform = view_rotation_transform * view_translate_transform
    return view_orientation_matrix, -origin_3D

def solve2vp(
        image_width:int,
        image_height:int,
        principal_point_pixel: glm.vec2,
        origin_pixel: glm.vec2,
        first_vanishing_lines_pixel: List[Tuple[glm.vec2, glm.vec2]],
        second_vanishing_lines_pixel: List[Tuple[glm.vec2, glm.vec2]],
        first_axis = Axis.PositiveZ,
        second_axis = Axis.PositiveX,
        scene_scale:float=1.0
    )->Tuple[float, glm.mat3, glm.vec3]:
    """
    Solve camera intrinsics and orientation from 3 orthogonal vanishing points.
    returns (fovy in radians, camera_orientation_matrix, camera_position)
    """
    ###############################
    # 1. COMPUTE vanishing points #
    ###############################
    first_vanishing_point_pixel =  least_squares_intersection_of_lines(first_vanishing_lines_pixel)
    second_vanishing_point_pixel = least_squares_intersection_of_lines(second_vanishing_lines_pixel)

    ###########################
    # 2. COMPUTE Focal Length #
    ###########################
    focal_length_pixel = compute_focal_length_from_vanishing_points(
        Fu = first_vanishing_point_pixel, 
        Fv = second_vanishing_point_pixel, 
        P =  principal_point_pixel
    )

    #################################
    # 3. COMPUTE Camera Orientation #
    #################################
    forward = glm.normalize(glm.vec3(first_vanishing_point_pixel-principal_point_pixel,  -focal_length_pixel))
    right =   glm.normalize(glm.vec3(second_vanishing_point_pixel-principal_point_pixel, -focal_length_pixel))
    up = glm.cross(forward, right)
    view_orientation_matrix = glm.mat3(forward, right, up)

    # validate if matrix is a purely rotational matrix
    determinant = glm.determinant(view_orientation_matrix)
    if math.fabs(determinant - 1) > 1e-6:
        raise Exception(f'Invalid vanishing point configuration. Rotation determinant {determinant}')

    # apply axis assignment
    axis_assignment_matrix:glm.mat3 = create_axis_assignment_matrix(first_axis, second_axis)            
    view_orientation_matrix:glm.mat3 = view_orientation_matrix * glm.inverse(axis_assignment_matrix)

    # convert to 4x4 matrix for transformations
    view_rotation_transform:glm.mat4 = glm.mat4(view_orientation_matrix)
    view_rotation_transform[3][3] = 1.0

    ##############################
    # 4. COMPUTE Camera Position #
    ##############################
    fovy = math.atan(image_height / 2 / focal_length_pixel) * 2
    near = 0.1
    far = 100
    projection_matrix = glm.perspective(
        fovy, # fovy in radians
        image_width/image_height, # aspect 
        near,
        far
    )

    origin_3D = glm.unProject(
        glm.vec3(
            origin_pixel.x, 
            origin_pixel.y, 
            _world_depth_to_ndc_z(scene_scale, near, far)
        ),
        view_rotation_transform, 
        projection_matrix, 
        glm.vec4(0,0,image_width,image_height)
    )
    view_translate_matrix = glm.translate(glm.mat4(1.0), -origin_3D)

    return fovy, view_orientation_matrix, -origin_3D


def least_squares_intersection_of_lines(line_segments: List[Tuple[glm.vec2, glm.vec2]]) -> glm.vec2:
    """
    Compute the intersection point from a set of 2D lines assumed to be parallel in 3D.
    This gives the best-fit intersection point in a least-squares sense when the lines don’t intersect exactly

    Args:
        lines (List[LineSegment]): List of line segments ((x1,y1),(x2,y2)).

    Returns:
        IntersectionPoint: [x, y].ishingPoint: Homogeneous coordinates of the vanishing point [x, y, 1].
    """
    if len(line_segments) < 2:
        raise ValueError("At least two lines are required to compute a vanishing point")
    
    # Build the constraint matrix
    constraint_matrix = [] # Each row is [a, b, c] for the line equation ax + by + c = 0
    for line_segment in line_segments:
        P, Q = line_segment
        a = P.y - Q.y
        b = Q.x - P.x
        c = P.x * Q.y - Q.x * P.y
        constraint_matrix .append([a, b, c])
    constraint_matrix  = np.array(constraint_matrix )

    # Solve for the vanishing point using SVD
    _, _, Vt = np.linalg.svd(constraint_matrix ) # Singular Value Decomposition
    vp = Vt[-1]
    result = vp / vp[2]
    return glm.vec2(result[0], result[1])

def compute_focal_length_from_vanishing_points(
        Fu: glm.vec2, # first vanishing point
        Fv: glm.vec2, # second vanishing point
        P: glm.vec2   # principal point
    )-> float:
    """Computes the relative focal length from two vanishing points and the principal point."""
    # compute Puv, the orthogonal projection of P onto FuFv
    Fu_Fv = glm.vec3(Fu-Fv, 0.0)
    dirFu_Fv = glm.normalize(Fu_Fv)

    P_Fv = glm.vec3(P - Fv, 0.0)
    proj = glm.dot(dirFu_Fv, P_Fv)
    Puv = glm.vec2(
      proj * dirFu_Fv.x + Fv.x,
      proj * dirFu_Fv.y + Fv.y
    )

    # compute focal length using the _focal length formula_: f² = |Fv_Puv| * |Fu_Puv| - |P_Puv|²
    P_Puv  = glm.vec3(P  - Puv, 0.0) #TODO: check if z=0 is necessary
    Fv_Puv = glm.vec3(Fv - Puv, 0.0)
    Fu_Puv = glm.vec3(Fu - Puv, 0.0)

    fSq = glm.length(Fv_Puv) * glm.length(Fu_Puv) - glm.length2(P_Puv)

    if fSq <= 0:
        raise ValueError(f"Invalid vanishing point configuration: cannot compute focal length. "
                        f"Vanishing points may be too close together or collinear with principal point. "
                        f"fSq = {fSq}, distances: FvPuv={glm.length(Fv_Puv):.6f}, FuPuv={glm.length(Fu_Puv):.6f}, PPuv={glm.length(P_Puv):.6f}")

    return math.sqrt(fSq)

def create_axis_assignment_matrix(firstVanishingPointAxis: Axis, secondVanishingPointAxis: Axis) -> glm.mat3:
    """
    Creates an axis assignment matrix that maps vanishing point directions to user-specified world axes.
    
    Args:
        firstVanishingPointAxis: The world axis that the first vanishing point should represent
        secondVanishingPointAxis: The world axis that the second vanishing point should represent
    
    Returns:
        A 3x3 rotation matrix that transforms from vanishing point space to world space
    
    Raises:
        Exception: If the axis assignment creates an invalid (non-orthogonal) matrix

    Note:
        Identity if:
        - if First vanishing point naturally points along the world's +X direction
        - Second vanishing point naturally points along the world's +Y direction
        - Third direction (computed via cross product) naturally points along the world's +Z direction
    """
    axisAssignmentMatrix = glm.identity(glm.mat3)
    
    # Get the unit vectors for the specified axes
    row1 = _axisVector(firstVanishingPointAxis)
    row2 = _axisVector(secondVanishingPointAxis)
    row3 = glm.cross(row1, row2)
    
    # Build the matrix with each row representing the target world axis
    axisAssignmentMatrix[0][0] = row1.x
    axisAssignmentMatrix[0][1] = row1.y
    axisAssignmentMatrix[0][2] = row1.z
    axisAssignmentMatrix[1][0] = row2.x
    axisAssignmentMatrix[1][1] = row2.y
    axisAssignmentMatrix[1][2] = row2.z
    axisAssignmentMatrix[2][0] = row3.x
    axisAssignmentMatrix[2][1] = row3.y
    axisAssignmentMatrix[2][2] = row3.z
    
    # Validate that we have a proper orthogonal matrix
    assert math.fabs(1 - glm.determinant(axisAssignmentMatrix)) < 1e-7, "Invalid axis assignment: axes must be orthogonal"

    
    return axisAssignmentMatrix

def _axisVector(axis: Axis)->glm.vec3:
    match axis:
      case Axis.NegativeX:
        return glm.vec3(-1, 0, 0)
      case Axis.PositiveX:
        return glm.vec3(1, 0, 0)
      case Axis.NegativeY:
        return glm.vec3(0, -1, 0)
      case Axis.PositiveY:
        return glm.vec3(0, 1, 0)
      case Axis.NegativeZ:
        return glm.vec3(0, 0, -1)
      case Axis.PositiveZ:
        return glm.vec3(0, 0, 1)

def _vectorAxis(vector: glm.vec3)->Axis:
    if vector.x == 0 and vector.y == 0:
      return Axis.PositiveZ if vector.z > 0 else Axis.NegativeZ
    elif vector.x == 0 and vector.z == 0:
      return Axis.PositiveY if vector.y > 0 else Axis.NegativeY
    elif vector.y == 0 and vector.z == 0:
      return Axis.PositiveX if vector.x > 0 else Axis.NegativeX
    
    raise Exception('Invalid axis vector')

def _world_depth_to_ndc_z(distance:float, near:float, far:float, clamp=False) -> float:
    """Convert world depth to NDC z-coordinate using perspective-correct mapping
    world_distance: The distance from the camera in world units
    near: The near clipping plane distance
    far: The far clipping plane distance
    returns: NDC z-coordinate in [0, 1], where 0 is near and 1 is far
    """
    # Clamp the distance between near and far
    if clamp:
        distance = max(near, min(far, distance))

    # Perspective-correct depth calculation
    # This matches how the depth buffer actually works
    ndc_z = (far + near) / (far - near) + (2 * far * near) / ((far - near) * distance)
    ndc_z = (ndc_z + 1) / 2  # Convert from [-1, 1] to [0, 1]
    return ndc_z

def intersect_ray_with_plane(ray_origin: glm.vec3, ray_direction: glm.vec3, plane_point: glm.vec3, plane_normal: glm.vec3) -> glm.vec3:
    """
    Intersect a ray with a plane.
    
    Args:
        ray_origin: Point where the ray starts
        ray_direction: Direction vector of the ray (should be normalized)
        plane_point: Any point on the plane
        plane_normal: Normal vector of the plane (should be normalized)
    
    Returns:
        The intersection point, or raises exception if no intersection
    """
    denom = glm.dot(plane_normal, ray_direction)
    
    if abs(denom) < 1e-6:
        raise ValueError("Ray is parallel to the plane")
    
    t = glm.dot(plane_normal, plane_point - ray_origin) / denom
    
    if t < 0:
        raise ValueError("Intersection is behind the ray origin")
    
    return ray_origin + t * ray_direction

def cast_ray(
    pos_pixel: glm.vec2, 
    view_matrix: glm.mat4, 
    projection_matrix: glm.mat4, 
    viewport: glm.vec4
) -> Tuple[glm.vec3, glm.vec3]:
    """
    Cast a ray from the camera through a pixel in screen space.
    
    Args:
        screen_x: X coordinate in pixel space
        screen_y: Y coordinate in pixel space
        view_matrix: Camera view matrix
        projection_matrix: Camera projection matrix
        viewport: Viewport (x, y, width, height)
    """

    world_near = glm.unProject(
        glm.vec3(pos_pixel.x, pos_pixel.y, 0.0),
        view_matrix, projection_matrix, viewport
    )

    world_far = glm.unProject(
        glm.vec3(pos_pixel.x, pos_pixel.y, 1.0),
        view_matrix, projection_matrix, viewport
    )

    return world_near, world_far

def project_line_to_xy_plane(line_start_pixel: glm.vec2, line_end_pixel: glm.vec2, 
                           view_matrix: glm.mat4, projection_matrix: glm.mat4, 
                           viewport: glm.vec4) -> Tuple[glm.vec3, glm.vec3]:
    """
    Project a 2D line from screen space to the XY plane (z=0) in world space.
    
    Args:
        line_start_pixel: Start point of line in pixel coordinates
        line_end_pixel: End point of line in pixel coordinates
        view_matrix: Camera view matrix
        projection_matrix: Camera projection matrix
        viewport: Viewport (x, y, width, height)
    
    Returns:
        Tuple of (start_3d, end_3d) points on the XY plane
    """    
    # Unproject pixel coordinates to world space rays
    start_world_near, start_world_far = cast_ray(line_start_pixel, view_matrix, projection_matrix, viewport)
    end_world_near, end_world_far = cast_ray(line_end_pixel, view_matrix, projection_matrix, viewport)

    # Create ray directions
    start_ray_dir = glm.normalize(start_world_far - start_world_near)
    end_ray_dir = glm.normalize(end_world_far - end_world_near)
    
    # XY plane definition (z = 0)
    plane_point = glm.vec3(0, 0, 0)
    plane_normal = glm.vec3(0, 0, 1)
    
    # Intersect rays with XY plane
    start_3d = intersect_ray_with_plane(start_world_near, start_ray_dir, plane_point, plane_normal)
    end_3d =   intersect_ray_with_plane(end_world_near,   end_ray_dir,   plane_point, plane_normal)
    
    return start_3d, end_3d

def compute_roll_matrix(
        image_width:int,
        image_height:int,
        second_vanishing_line:Tuple[glm.vec2, glm.vec2],
        projection_matrix:glm.mat4,
        view_matrix:glm.mat4
):
    horizon_line = second_vanishing_line
    horizon_start_pixel = horizon_line[0]
    horizon_end_pixel = horizon_line[1]
    
    # Project the horizon line to the XY plane in 3D world space
    from my_solver_v3 import project_line_to_xy_plane
    
    viewport = glm.vec4(0, 0, image_width, image_height)
    start_3d, end_3d = project_line_to_xy_plane(
        horizon_start_pixel, horizon_end_pixel,
        view_matrix, projection_matrix,
        viewport
    )
    
    # Calculate roll angle from 3D line in XY plane
    dx_3d = end_3d.x - start_3d.x
    dy_3d = end_3d.y - start_3d.y
    roll_angle = math.atan2(dy_3d, dx_3d)
    
    # Apply roll to the camera transform
    return glm.rotate(glm.mat4(1.0), roll_angle, glm.vec3(0, 0, 1))