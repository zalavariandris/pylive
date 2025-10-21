from typing import List, Tuple, NewType
from enum import IntEnum
import math

from . import glmx

class Axis(IntEnum):
    PositiveX = 0
    NegativeX = 1
    PositiveY = 2
    NegativeY = 3
    PositiveZ = 4
    NegativeZ = 5

LineSegmentType = Tuple[glmx.vec2, glmx.vec2]

###
def focal_length_from_fov(fovy, image_height):
    return (image_height / 2) / math.tan(fovy / 2)

def fov_from_focal_length(focal_length_pixel, image_height):
    return math.atan(image_height / 2 / focal_length_pixel) * 2

def _axisVector(axis: Axis)->glmx.vec3:
    match axis:
      case Axis.NegativeX:
        return glmx.vec3(-1, 0, 0)
      case Axis.PositiveX:
        return glmx.vec3(1, 0, 0)
      case Axis.NegativeY:
        return glmx.vec3(0, -1, 0)
      case Axis.PositiveY:
        return glmx.vec3(0, 1, 0)
      case Axis.NegativeZ:
        return glmx.vec3(0, 0, -1)
      case Axis.PositiveZ:
        return glmx.vec3(0, 0, 1)

def _vectorAxis(vector: glmx.vec3)->Axis:
    if vector.x == 0 and vector.y == 0:
      return Axis.PositiveZ if vector.z > 0 else Axis.NegativeZ
    elif vector.x == 0 and vector.z == 0:
      return Axis.PositiveY if vector.y > 0 else Axis.NegativeY
    elif vector.y == 0 and vector.z == 0:
      return Axis.PositiveX if vector.x > 0 else Axis.NegativeX
    
    raise Exception('Invalid axis vector')

###
# MAIN SOLVER FUNCTIONS
###
def solve1vp(
        width:int,
        height:int,
        Fu: glmx.vec2,
        f:float,
        P: glmx.vec2=None,
        O: glmx.vec2=None,
        first_axis = Axis.PositiveZ,
        second_axis = Axis.PositiveX,
        scale:float=1.0
    )->Tuple[glmx.mat3, glmx.vec3]:
        if P is None:
            P = glmx.vec2(width/2, height/2)
        if O is None:
            O = glmx.vec2(width/2, height/2)
        #################################
        # 3. COMPUTE Camera Orientation #
        #################################
        view_orientation_matrix = compute_orientation_from_single_vanishing_point(
            Fu,
            P,
            f
        )

        # apply axis assignment
        axis_assignment_matrix:glmx.mat3 = create_axis_assignment_matrix(first_axis, second_axis)            
        view_orientation_matrix:glmx.mat3 = view_orientation_matrix * glmx.inverse(axis_assignment_matrix)

        # convert to 4x4 matrix for transformations
        view_rotation_transform:glmx.mat4 = glmx.mat4(view_orientation_matrix)
        view_rotation_transform[3][3] = 1.0

        ##############################
        # 4. COMPUTE Camera Position #
        ##############################
        camera_position = compute_camera_position(
            width, 
            height, 
            f, 
            view_orientation_matrix, 
            O, 
            scale
        )

        return view_orientation_matrix, camera_position

def solve2vp(
        width:int,
        height:int,
        Fu: glmx.vec2,
        Fv: glmx.vec2,
        P: glmx.vec2,
        O: glmx.vec2,
        first_axis = Axis.PositiveZ,
        second_axis = Axis.PositiveX,
        scale:float=1.0
    )->Tuple[float, glmx.mat3, glmx.vec3]:
    """ Solve camera intrinsics and orientation from 3 orthogonal vanishing points.
    returns (fovy in radians, camera_orientation_matrix, camera_position)
    """

    ###########################
    # 2. COMPUTE Focal Length #
    ###########################
    f = compute_focal_length_from_vanishing_points(
        Fu = Fu, 
        Fv = Fv, 
        P =  P
    )
    fovy = fov_from_focal_length(f, height)

    #################################
    # 3. COMPUTE Camera Orientation #
    #################################
    view_orientation_matrix = compute_orientation_from_two_vanishing_points(
        Fu,
        Fv,
        P,
        f
    )

    # apply axis assignment
    axis_assignment_matrix:glmx.mat3 = create_axis_assignment_matrix(first_axis, second_axis)            
    view_orientation_matrix:glmx.mat3 = view_orientation_matrix * glmx.inverse(axis_assignment_matrix)

    ##############################
    # 4. COMPUTE Camera Position #
    ##############################
    camera_position = compute_camera_position(
        width, 
        height, 
        f, 
        view_orientation_matrix, 
        O, 
        scale
    )
    
    return fovy, view_orientation_matrix, camera_position

###
# CORE SOLVER FUNCTIOS
###
def second_vanishing_point_from_focal_length(
        Fu: glmx.vec2, 
        f: float, 
        P: glmx.vec2, 
        horizonDir: glmx.vec2
    )->glmx.vec2|None:
    """
    Computes the coordinates of the second vanishing point
    based on the first, a focal length, the center of projection and
    the desired horizon tilt angle. The equations here are derived from
    section 3.2 "Determining the focal length from a single image".

    @param Fu the first vanishing point in _image plane_ coordinates.
    @param f the relative focal length
    @param P the center of projection in _normalized image_ coordinates
    @param horizonDir The desired horizon direction
    """
    
    # find the second vanishing point
    # // TODO_ take principal point into account here
    if glmx.distance(Fu, P) < 1e-7:
        return None

    if glmx.distance(Fu, P) < 1e-7:
        return None

    Fu_P = Fu - P

    k = -(glmx.dot(Fu_P, Fu_P) + f * f) / glmx.dot(Fu_P, horizonDir)
    Fv = Fu_P + k * horizonDir + P

    return Fv

def compute_orientation_from_two_vanishing_points_manual(
        Fu:glmx.vec2, # first vanishing point
        Fv:glmx.vec2, # second vanishing point
        P:glmx.vec2,
        f:float
    )->glmx.mat3:
    """
    Computes the camera orientation matrix from two vanishing points and the principal point.

    Note: we actually using the method with the orientartion function. But i keep this one around, 
    cause i like the low level matrix constructtion from directional vectors"""
    forward = glmx.normalize(glmx.vec3(Fu-P,  -f))
    right =   glmx.normalize(glmx.vec3(Fv-P, -f))
    up = glmx.cross(forward, right)
    view_orientation_matrix = glmx.mat3(forward, right, up)

    # validate if matrix is a purely rotational matrix
    determinant = glmx.determinant(view_orientation_matrix)
    if math.fabs(determinant - 1) > 1e-6:
        view_orientation_matrix = _gram_schmidt_orthogonalization(view_orientation_matrix)
        print("Warning: View orientation matrix was not orthogonal, applied Gram-Schmidt orthogonalization")
        # raise Exception(f'Invalid vanishing point configuration. Rotation determinant {determinant}')

    return view_orientation_matrix

def compute_orientation_from_two_vanishing_points(
        Fu:glmx.vec2, # first vanishing point
        Fv:glmx.vec2, # second vanishing point
        P:glmx.vec2,
        f:float
    )->glmx.mat3:
        ...

def compute_orientation_from_single_vanishing_point(
        Fu:glmx.vec2,
        Fv:glmx.vec2,
        f:float
    ):
    forward = glmx.normalize(glmx.vec3(Fu-Fv,  -f))
    up_world = glmx.vec3(0, 1, 0)
    right = glmx.normalize(glmx.cross(up_world, forward))
    up = glmx.cross(forward, right)
    view_orientation_matrix = glmx.mat3_from_directions(forward, right, up)

    # validate if matrix is a purely rotational matrix
    determinant = glmx.determinant(view_orientation_matrix)
    if math.fabs(determinant - 1) > 1e-6:
        view_orientation_matrix = _gram_schmidt_orthogonalization(view_orientation_matrix)
        print("Warning: View orientation matrix was not orthogonal, applied Gram-Schmidt orthogonalization")
        # raise Exception(f'Invalid vanishing point configuration. Rotation determinant {determinant}')
    return view_orientation_matrix

def compute_camera_position(
        width:int,
        height:int,
        f:float,
        view_orientation_matrix:glmx.mat3,
        O:glmx.vec2,
        scale:float=1.0,
    )-> glmx.vec3:
    """
    Computes the camera position in 3D space from 2D image coordinates and camera parameters.
    """
    fovy = fov_from_focal_length(f, height)
    near = 0.1
    far = 100
    projection_matrix = glmx.perspective(
        fovy, # fovy in radians
        width/height, # aspect 
        near,
        far
    )

    # convert to 4x4 matrix for transformations
    view_rotation_transform:glmx.mat4 = glmx.mat4(view_orientation_matrix)
    view_rotation_transform[3][3] = 1.0

    origin_3D = glmx.unProject(
        glmx.vec3(
            O.x, 
            O.y, 
            _world_depth_to_ndc_z(scale, near, far)
        ),
        view_rotation_transform, 
        projection_matrix, 
        glmx.vec4(0,0,width,height)
    )

    return -origin_3D

def compute_roll_matrix(
        width:int,
        height:int,
        second_vanishing_line:Tuple[glmx.vec2, glmx.vec2],
        projection_matrix:glmx.mat4,
        view_matrix:glmx.mat4
):
    """
    Compute a roll correction matrix to align the horizon based on the second vanishing lines.
    """

    # Project the horizon line to the XY plane in 3D world space
    viewport = glmx.vec4(0, 0, width, height)
    projected_horizontal_line = project_line_to_xy_plane(
        second_vanishing_line[0], second_vanishing_line[1],
        view_matrix, projection_matrix,
        viewport
    )

    A, B = projected_horizontal_line

    # Calculate how much this line deviates from horizontal (y = constant)
    delta = B.xy - A.xy
    roll = math.atan2(delta.y, delta.x)

    # Apply negative roll to correct the deviation (counter-rotate)
    return glmx.rotate(glmx.mat4(1.0), roll, glmx.vec3(0, 0, 1))

def compute_focal_length_from_vanishing_points(
        Fu: glmx.vec2, # first vanishing point
        Fv: glmx.vec2, # second vanishing point
        P: glmx.vec2   # principal point
    )-> float:
    """
    Computes the focal length from two orthogonal vanishing points using the cross-ratio formula.
    Enhanced with numerical stability improvements for distant vanishing points.
    """
    # Check for degenerate cases
    Fu_Fv_distance = glmx.distance(Fu, Fv)
    if Fu_Fv_distance < 1e-6:
        raise ValueError(f"Vanishing points are too close together: distance = {Fu_Fv_distance:.2e}")
    
    # Detect if vanishing points are very far away and need special handling
    max_reasonable_distance = 1e4  # Configurable threshold
    Fu_distance = glmx.distance(Fu, P)
    Fv_distance = glmx.distance(Fv, P)
    
    # For very distant VPs, clamp them to reasonable bounds to prevent numerical issues
    if Fu_distance > max_reasonable_distance or Fv_distance > max_reasonable_distance:
        print(f"Warning: Very distant vanishing points detected (Fu: {Fu_distance:.1f}, Fv: {Fv_distance:.1f})")
        
        # Clamp to reasonable distance while preserving direction
        if Fu_distance > max_reasonable_distance:
            direction = glmx.normalize(Fu - P)
            Fu = P + direction * max_reasonable_distance
            
        if Fv_distance > max_reasonable_distance:
            direction = glmx.normalize(Fv - P)
            Fv = P + direction * max_reasonable_distance
    
    # Use the standard cross-ratio formula with improved numerical precision
    horizon_vector = Fu - Fv
    horizon_direction = glmx.normalize(horizon_vector)
    
    principal_to_fv = P - Fv
    projection_length = glmx.dot(horizon_direction, principal_to_fv)
    projection_point = Fv + projection_length * horizon_direction
    
    # Use double precision for critical calculations
    distance_fv_to_proj = float(glmx.distance(Fv, projection_point))
    distance_fu_to_proj = float(glmx.distance(Fu, projection_point))
    distance_p_to_proj =  float(glmx.distance(P, projection_point))
    
    focal_length_squared = distance_fv_to_proj * distance_fu_to_proj - distance_p_to_proj * distance_p_to_proj
    
    if focal_length_squared <= 0:
        vanishing_point_distance = glmx.distance(Fu, Fv)
        angle_deg = math.degrees(math.acos(glmx.clamp(
            glmx.dot(glmx.normalize(Fu - P), glmx.normalize(Fv - P)), -1.0, 1.0
        )))
        
        raise ValueError(
            f"Invalid vanishing point configuration: cannot compute focal length.\n"
            f"  f² = {focal_length_squared:.6f} (must be > 0)\n"
            f"  Vanishing point separation: {vanishing_point_distance:.2f} pixels\n"
            f"  Angle between VP directions: {angle_deg:.1f}° (should be close to 90°)\n"
            f"  Distance Fu->projection: {distance_fu_to_proj:.2f}\n"
            f"  Distance Fv->projection: {distance_fv_to_proj:.2f}\n"
            f"  Distance P->projection: {distance_p_to_proj:.2f}\n"
            f"  Possible causes: VPs too close to principal point, VPs not orthogonal, or VPs collinear with principal point"
        )
    
    focal_length = math.sqrt(focal_length_squared)
    
    # Sanity check the result
    min_focal = 10.0   # Minimum reasonable focal length
    max_focal = 10000.0 # Maximum reasonable focal length
    
    if focal_length < min_focal or focal_length > max_focal:
        print(f"Warning: Computed focal length {focal_length:.1f} is outside reasonable range [{min_focal}, {max_focal}]")
    
    return focal_length

def _compute_focal_length_from_vanishing_points_simple(
        Fu: glmx.vec2, # first vanishing point
        Fv: glmx.vec2, # second vanishing point
        P: glmx.vec2   # principal point
    )-> float:
    """
    Computes the focal length from two orthogonal vanishing points using the cross-ratio formula.
    
    The formula is derived from the constraint that orthogonal directions in 3D space
    project to vanishing points that satisfy: f² = |Fv_Puv| * |Fu_Puv| - |P_Puv|²
    where Puv is the orthogonal projection of P onto the line FuFv.
    
    Args:
        Fu: First vanishing point in pixel coordinates
        Fv: Second vanishing point in pixel coordinates  
        P: Principal point in pixel coordinates
        
    Returns:
        Focal length in pixels
        
    Raises:
        ValueError: If vanishing points are too close, collinear with principal point,
                   or configuration is otherwise invalid
    """
    # Check for degenerate cases
    Fu_Fv_distance = glmx.distance(Fu, Fv)
    if Fu_Fv_distance < 1e-6:
        raise ValueError(f"Vanishing points are too close together: distance = {Fu_Fv_distance:.2e}")
    
    # Compute Puv: orthogonal projection of principal point P onto line segment Fu-Fv
    horizon_vector = Fu - Fv
    horizon_direction = glmx.normalize(horizon_vector)
    
    # Vector from Fv to principal point
    principal_to_fv = P - Fv
    
    # Project onto horizon line
    projection_length = glmx.dot(horizon_direction, principal_to_fv)
    projection_point = Fv + projection_length * horizon_direction
    
    # Compute distances for focal length formula
    # f² = |Fv_Puv| * |Fu_Puv| - |P_Puv|²
    distance_fv_to_proj = glmx.distance(Fv, projection_point)
    distance_fu_to_proj = glmx.distance(Fu, projection_point)
    distance_p_to_proj = glmx.distance(P, projection_point)
    
    # Apply focal length formula
    focal_length_squared = distance_fv_to_proj * distance_fu_to_proj - distance_p_to_proj * distance_p_to_proj
    
    # Validate result
    if focal_length_squared <= 0:
        # Provide detailed diagnostic information
        vanishing_point_distance = glmx.distance(Fu, Fv)
        angle_deg = math.degrees(math.acos(glmx.clamp(
            glmx.dot(glmx.normalize(Fu - P), glmx.normalize(Fv - P)), -1.0, 1.0
        )))
        
        raise ValueError(
            f"Invalid vanishing point configuration: cannot compute focal length.\n"
            f"  f² = {focal_length_squared:.6f} (must be > 0)\n"
            f"  Vanishing point separation: {vanishing_point_distance:.2f} pixels\n"
            f"  Angle between VP directions: {angle_deg:.1f}° (should be close to 90°)\n"
            f"  Distance Fu->projection: {distance_fu_to_proj:.2f}\n"
            f"  Distance Fv->projection: {distance_fv_to_proj:.2f}\n"
            f"  Distance P->projection: {distance_p_to_proj:.2f}\n"
            f"  Possible causes: VPs too close to principal point, VPs not orthogonal, or VPs collinear with principal point"
        )
    
    return math.sqrt(focal_length_squared)

def _compute_focal_length_from_vanishing_points_OLD(
        Fu: glmx.vec2, # first vanishing point
        Fv: glmx.vec2, # second vanishing point
        P: glmx.vec2   # principal point
    )-> float:
    """Computes the relative focal length from two vanishing points and the principal point."""
    # compute Puv, the orthogonal projection of P onto FuFv
    Fu_Fv = glmx.vec3(Fu-Fv, 0.0)
    dirFu_Fv = glmx.normalize(Fu_Fv)

    P_Fv = glmx.vec3(P - Fv, 0.0)
    proj = glmx.dot(dirFu_Fv, P_Fv)
    Puv = glmx.vec2(
      proj * dirFu_Fv.x + Fv.x,
      proj * dirFu_Fv.y + Fv.y
    )

    # compute focal length using the _focal length formula_: f² = |Fv_Puv| * |Fu_Puv| - |P_Puv|²
    P_Puv  = glmx.vec3(P  - Puv, 0.0) #TODO: check if z=0 is necessary
    Fv_Puv = glmx.vec3(Fv - Puv, 0.0)
    Fu_Puv = glmx.vec3(Fu - Puv, 0.0)

    fSq = glmx.length(Fv_Puv) * glmx.length(Fu_Puv) - glmx.length2(P_Puv)

    if fSq <= 0:
        raise ValueError(f"Invalid vanishing point configuration: cannot compute focal length. "
                        f"Vanishing points may be too close together or collinear with principal point. "
                        f"fSq = {fSq}, distances: FvPuv={glmx.length(Fv_Puv):.6f}, FuPuv={glmx.length(Fu_Puv):.6f}, PPuv={glmx.length(P_Puv):.6f}")

    return math.sqrt(fSq)

def create_axis_assignment_matrix(first_axis: Axis, second_axis: Axis) -> glmx.mat3:
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
    axis_aqssignment_matrix = glmx.identity(glmx.mat3)
    
    # Get the unit vectors for the specified axes
    row1 = _axisVector(first_axis)
    row2 = _axisVector(second_axis)
    row3 = glmx.cross(row1, row2)
    
    # Build the matrix with each row representing the target world axis
    axis_aqssignment_matrix[0][0] = row1.x
    axis_aqssignment_matrix[0][1] = row1.y
    axis_aqssignment_matrix[0][2] = row1.z
    axis_aqssignment_matrix[1][0] = row2.x
    axis_aqssignment_matrix[1][1] = row2.y
    axis_aqssignment_matrix[1][2] = row2.z
    axis_aqssignment_matrix[2][0] = row3.x
    axis_aqssignment_matrix[2][1] = row3.y
    axis_aqssignment_matrix[2][2] = row3.z
    
    # Validate that we have a proper orthogonal matrix
    assert math.fabs(1 - glmx.determinant(axis_aqssignment_matrix)) < 1e-7, "Invalid axis assignment: axes must be orthogonal"
    return axis_aqssignment_matrix


###
# 2D-3D GOMETRY FUNCTIONS
###
def cast_ray(
    pos: glmx.vec2, 
    view_matrix: glmx.mat4, 
    projection_matrix: glmx.mat4, 
    viewport: glmx.vec4
) -> Tuple[glmx.vec3, glmx.vec3]:
    """
    Cast a ray from the camera through a pixel in screen space.
    
    Args:
        screen_x: X coordinate in pixel space
        screen_y: Y coordinate in pixel space
        view_matrix: Camera view matrix
        projection_matrix: Camera projection matrix
        viewport: Viewport (x, y, width, height)
    """

    world_near = glmx.unProject(
        glmx.vec3(pos.x, pos.y, 0.0),
        view_matrix, projection_matrix, viewport
    )

    world_far = glmx.unProject(
        glmx.vec3(pos.x, pos.y, 1.0),
        view_matrix, projection_matrix, viewport
    )

    return world_near, world_far

def least_squares_intersection_of_lines(line_segments: List[Tuple[glmx.vec2, glmx.vec2]]) -> glmx.vec2:
    """
    Compute the least-squares intersection (vanishing point) of a set of 2D lines
    defined by their endpoints. Uses pure PyGLM math, no numpy.

    Args:
        line_segments: list of ((x1, y1), (x2, y2)) as glm.vec2 pairs.

    Returns:
        glm.vec2: the least-squares intersection point.
    """
    if len(line_segments) < 2:
        raise ValueError("At least two lines are required to compute a vanishing point")

    # Accumulate normal equation components
    S_aa = S_ab = S_bb = S_ac = S_bc = 0.0

    for P, Q in line_segments:
        # Line equation coefficients: a*x + b*y + c = 0
        a = P.y - Q.y
        b = Q.x - P.x
        c = P.x * Q.y - Q.x * P.y

        S_aa += a * a
        S_ab += a * b
        S_bb += b * b
        S_ac += a * c
        S_bc += b * c

    # Solve normal equations:
    # [S_aa S_ab][x] = -[S_ac]
    # [S_ab S_bb][y]   -[S_bc]
    det = S_aa * S_bb - S_ab * S_ab
    if abs(det) < 1e-12:
        raise ValueError("Lines are nearly parallel or determinant is zero")

    x = (-S_bb * S_ac + S_ab * S_bc) / det
    y = (-S_aa * S_bc + S_ab * S_ac) / det

    return glmx.vec2(x, y)

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

def intersect_ray_with_plane(ray_origin: glmx.vec3, ray_direction: glmx.vec3, plane_point: glmx.vec3, plane_normal: glmx.vec3) -> glmx.vec3:
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
    denom = glmx.dot(plane_normal, ray_direction)
    
    if abs(denom) < 1e-6:
        raise ValueError("Ray is parallel to the plane")
    
    t = glmx.dot(plane_normal, plane_point - ray_origin) / denom
    
    # if t < 0:
    #     raise ValueError("Intersection is behind the ray origin")
    
    return ray_origin + t * ray_direction

def project_line_to_xy_plane(line_start_pixel: glmx.vec2, line_end_pixel: glmx.vec2, 
                           view_matrix: glmx.mat4, projection_matrix: glmx.mat4, 
                           viewport: glmx.vec4) -> Tuple[glmx.vec3, glmx.vec3]:
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
    start_ray_dir = glmx.normalize(start_world_far - start_world_near)
    end_ray_dir = glmx.normalize(end_world_far - end_world_near)
    
    # XY plane definition (z = 0)
    plane_point = glmx.vec3(0, 0, 0)
    plane_normal = glmx.vec3(0, 0, 1)
    
    # Intersect rays with XY plane
    start_3d = intersect_ray_with_plane(start_world_near, start_ray_dir, plane_point, plane_normal)
    end_3d =   intersect_ray_with_plane(end_world_near,   end_ray_dir,   plane_point, plane_normal)
    
    return start_3d, end_3d

def _gram_schmidt_orthogonalization(matrix: glmx.mat3) -> glmx.mat3:
    """
    Apply Gram-Schmidt orthogonalization to a 3x3 matrix to make it orthogonal.
    This ensures the matrix represents a valid rotation matrix.
    """
    # Extract the three column vectors
    v1 = glmx.vec3(matrix[0])  # First column
    v2 = glmx.vec3(matrix[1])  # Second column
    v3 = glmx.vec3(matrix[2])  # Third column
    
    # Step 1: Normalize the first vector
    u1 = glmx.normalize(v1)
    
    # Step 2: Make v2 orthogonal to u1
    u2 = v2 - glmx.dot(v2, u1) * u1
    u2 = glmx.normalize(u2)
    
    # Step 3: Make v3 orthogonal to both u1 and u2
    u3 = v3 - glmx.dot(v3, u1) * u1 - glmx.dot(v3, u2) * u2
    u3 = glmx.normalize(u3)
    
    # Construct the orthogonal matrix
    result = glmx.mat3()
    result[0] = u1  # First column
    result[1] = u2  # Second column
    result[2] = u3  # Third column
    
    return result



###
# Post-processing functions
###
def adjust_vanishing_lines(
        old_vp:glmx.vec2, 
        new_vp:glmx.vec2, 
        vanishing_lines:List[Tuple[glmx.vec2, glmx.vec2]]
    ) -> List[Tuple[glmx.vec2, glmx.vec2]]:
    # When vanishing point moves, adjust only the closest endpoint of each vanishing line
    new_vanishing_lines = vanishing_lines.copy()
    for i, (P, Q) in enumerate(vanishing_lines):
        # Find which endpoint is closer to the old vanishing point
        dist_P = glmx.length(P - old_vp)
        dist_Q = glmx.length(Q - old_vp)
        
        # Choose the closer endpoint and the fixed endpoint
        if dist_P < dist_Q:
            moving_point, fixed_point = P, Q
        else:
            moving_point, fixed_point = Q, P
        
        # Calculate relative position and apply to new vanishing point
        line_to_old_vp = old_vp - fixed_point
        line_to_moving = moving_point - fixed_point
        
        if glmx.length(line_to_old_vp) > 1e-6:
            ratio = glmx.length(line_to_moving) / glmx.length(line_to_old_vp)
            new_line_to_vp = new_vp - fixed_point
            new_moving_point = fixed_point + glmx.normalize(new_line_to_vp) * glmx.length(new_line_to_vp) * ratio
            
            # Update the correct endpoint
            if dist_P < dist_Q:
                new_vanishing_lines[i] = (new_moving_point, Q)
            else:
                new_vanishing_lines[i] = (P, new_moving_point)
    return new_vanishing_lines

def adjust_vanishing_lines_by_rotation(
        old_vp: glmx.vec2, 
        new_vp: glmx.vec2, 
        vanishing_lines: List[Tuple[glmx.vec2, glmx.vec2]],
        principal_point: glmx.vec2
    ) -> List[Tuple[glmx.vec2, glmx.vec2]]:
    """
    Adjust vanishing lines by rotating them around the principal point so they point to the new vanishing point.
    """
    
    # Create rotation matrix
    def rotate_point_around_center(point: glmx.vec2, center: glmx.vec2, rotation_angle:float) -> glmx.vec2:
        # Rotation matrix components
        cos_angle = math.cos(rotation_angle)
        sin_angle = math.sin(rotation_angle)

        # Translate to origin
        translated = point - center
        # Apply rotation
        rotated_x = translated.x * cos_angle - translated.y * sin_angle
        rotated_y = translated.x * sin_angle + translated.y * cos_angle
        # Translate back
        return glmx.vec2(rotated_x, rotated_y) + center
    
    # Apply the same rotation to all line endpoints
    new_vanishing_lines = []
    for P, Q in vanishing_lines:
        # Calculate the global rotation from old VP to new VP (relative to principal point)
        old_dir = glmx.normalize(old_vp - P)
        new_dir = glmx.normalize(new_vp - P)
        
        # Calculate rotation angle
        dot_product = glmx.dot(old_dir, new_dir)
        dot_product = max(-1.0, min(1.0, dot_product))  # Clamp to avoid numerical errors
        rotation_angle = math.acos(dot_product)
        
        # Determine rotation direction using cross product (in 2D, this gives the z-component)
        cross_z = old_dir.x * new_dir.y - old_dir.y * new_dir.x
        if cross_z < 0:
            rotation_angle = -rotation_angle
        new_P = rotate_point_around_center(P, principal_point, rotation_angle)
        new_Q = rotate_point_around_center(Q, principal_point, rotation_angle)
        new_vanishing_lines.append((new_P, new_Q))
    
    return new_vanishing_lines

def vanishing_points_from_camera(
        view_matrix: glmx.mat3, 
        projection_matrix: glmx.mat4, 
        viewport: glmx.vec4
    ) -> Tuple[glmx.vec2, glmx.vec2, glmx.vec2]:
    # Project vanishing Points
    MAX_FLOAT32 = (2 - 2**-23) * 2**127
    VPX = glmx.project(glmx.vec3(MAX_FLOAT32,0,0), view_matrix, projection_matrix, viewport)
    VPY = glmx.project(glmx.vec3(0,MAX_FLOAT32,0), view_matrix, projection_matrix, viewport)
    VPZ = glmx.project(glmx.vec3(0,0,MAX_FLOAT32), view_matrix, projection_matrix, viewport)
    return glmx.vec2(VPX), glmx.vec2( VPY), glmx.vec2(VPZ)


