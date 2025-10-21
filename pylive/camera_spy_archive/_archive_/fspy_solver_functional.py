import glm
from typing import *
from enum import StrEnum, IntEnum
from dataclasses import dataclass, field
import math
from imgui_bundle import imgui
import itertools


############################# 
# Geometry helper functions #
#############################
def _gram_schmidt_orthogonalization(matrix: glm.mat3) -> glm.mat3:
    """
    Apply Gram-Schmidt orthogonalization to a 3x3 matrix to make it orthogonal.
    This ensures the matrix represents a valid rotation matrix.
    """
    # Extract the three column vectors
    v1 = glm.vec3(matrix[0])  # First column
    v2 = glm.vec3(matrix[1])  # Second column
    v3 = glm.vec3(matrix[2])  # Third column
    
    # Step 1: Normalize the first vector
    u1 = glm.normalize(v1)
    
    # Step 2: Make v2 orthogonal to u1
    u2 = v2 - glm.dot(v2, u1) * u1
    u2 = glm.normalize(u2)
    
    # Step 3: Make v3 orthogonal to both u1 and u2
    u3 = v3 - glm.dot(v3, u1) * u1 - glm.dot(v3, u2) * u2
    u3 = glm.normalize(u3)
    
    # Construct the orthogonal matrix
    result = glm.mat3()
    result[0] = u1  # First column
    result[1] = u2  # Second column
    result[2] = u3  # Third column
    
    return result

def _thirdTriangleVertex(firstVertex: glm.vec2, secondVertex: glm.vec2, orthocenter: glm.vec2)->glm.vec2:
    a = firstVertex
    b = secondVertex
    o = orthocenter

    # compute p, the orthogonal projection of the orthocenter onto the line through a and b
    a_to_b = glm.normalize(b - a)
    proj = glm.dot(a_to_b, o - a)
    p = a + proj * a_to_b
    
    # // the vertex c can be expressed as p + hn, where n is orthogonal to ab.
    n = glm.vec2(a_to_b.y, -a_to_b.x)

    # Compute scalar h
    numerator = glm.dot(a - p, o - b)
    denominator = glm.dot(n, o - b)
    if math.fabs(denominator) < 1e-9:
        raise ValueError("Degenerate geometry: line AB perpendicular to (OH) direction.")
    
    h = numerator / denominator
    c = p + h * n
    return c

def _triangleOrthoCenter(k: glm.vec2, l: glm.vec2, m: glm.vec2)->glm.vec2:
    a = k.x
    b = k.y
    c = l.x
    d = l.y
    e = m.x
    f = m.y

    N = b * c + d * e + f * a - c * f - b * e - a * d
    x = ((d - f) * b * b + (f - b) * d * d + (b - d) * f * f + a * b * (c - e) + c * d * (e - a) + e * f * (a - c)) / N
    y = ((e - c) * a * a + (a - e) * c * c + (c - a) * e * e + a * b * (f - d) + c * d * (b - f) + e * f * (d - b)) / N

    return glm.vec2(x, y)

################
# Solver Enums #
################
class Unit(StrEnum):
    NoUnit = 'No unit',
    Millimeters = 'Millimeters',
    Centimeters = 'Centimeters',
    Meters = 'Meters',
    Kilometers = 'Kilometers',
    Inches = 'Inches',
    Feet = 'Feet',
    Miles = 'Miles'

class Axis(IntEnum):
    PositiveX = 0
    NegativeX = 1
    PositiveY = 2
    NegativeY = 3
    PositiveZ = 4
    NegativeZ = 5

################
# Solver Types #
################
LineSegmentType = Tuple[glm.vec2, glm.vec2]



################
# Solver UTILS #
################
from typing import TypeVar, Generic
T = TypeVar('T', int, float, glm.vec2)
def remap(value:T|List[T]|Tuple[T], from_min:T, from_max:T, to_min:T, to_max:T) -> T:
    match value:
        # value
        case float() | int():
            return (value - from_min) * (to_max - to_min) / (from_max - from_min) + to_min
        
        # Point2D
        case glm.vec2():
            return glm.vec2(
                remap(value.x, from_min.x, from_max.x, to_min.x, to_max.x),
                remap(value.y, from_min.y, from_max.y, to_min.y, to_max.y)
            )
        
        # LineSegment
        case tuple() if len(value) == 2 and all(isinstance(_, (glm.vec2)) for _ in value):
            # linesegment
            return (
                remap(value[0], from_min, from_max, to_min, to_max),
                remap(value[1], from_min, from_max, to_min, to_max)
            )

        # list or tuple of the above
        case tuple() | list() if all(isinstance(v, (int, float, glm.vec2)) for v in value):
            result = []
            for v in zip(value, from_min, from_max, to_min, to_max):
                result.append(remap(v, from_min, from_max, to_min, to_max))

            return tuple(result) if isinstance(value, tuple) else result 
            
        case _:
            raise ValueError(f"Unsupported type for remap: {type(value)}")
    

def _relative_to_image_plane_coords(
        P: glm.vec2, 
        image_width: int, 
        image_height: int
    ) -> glm.vec2:
    aspect_ratio = image_width / image_height
    
    if aspect_ratio <= 1:
        # tall image
        return remap(P, 
                     glm.vec2(0,0),                         glm.vec2(1,1), 
                     glm.vec2(-aspect_ratio, aspect_ratio), glm.vec2(1,-1)
        )
        
    else:
        # wide image
        return remap(P, 
                     glm.vec2(0,0),                         glm.vec2(1,1), 
                     glm.vec2(-aspect_ratio, aspect_ratio), glm.vec2(1,-1)
        )
    
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

import numpy as np
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

######################
# Validation Helpers #
######################

def are_lines_near_parallel(line1: LineSegmentType, line2: LineSegmentType, threshold: float = 0.99995) -> bool:
    """Check if two lines are nearly parallel based on their direction vectors.
    threshold: Cosine of the angle between the lines. Closer to 1 means more parallel."""
    line1_dir = glm.normalize(glm.vec2(line1[1]) - glm.vec2(line1[0]))
    line2_dir = glm.normalize(glm.vec2(line2[1]) - glm.vec2(line2[0]))
    dot = glm.dot(line1_dir, line2_dir)
    return abs(dot) > threshold


###########################
# Solver Helper Functions #
###########################

def _compute_field_of_view(
    image_width: float,
    image_height: float,
    fRelative: float,
    vertical: bool
  )->float:
    """Computes the field of view (horizontal or vertical) in radians."""
    aspect_ratio = image_width / image_height
    d = 1 / aspect_ratio if vertical else 1
    return 2 * math.atan(d / fRelative)

def _createAxisAssignmentMatrix(firstVanishingPointAxis: Axis, secondVanishingPointAxis: Axis) -> glm.mat3:
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
    imgui.text(f"Axis assignment: {firstVanishingPointAxis}, {secondVanishingPointAxis}")
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

def _create_orientation_matrix_from_vanishing_points(
        Fu: glm.vec2, # first vanishing point
        Fv: glm.vec2, # second vanishing point
        f: float,     # relative vertical focal length
        P: glm.vec2   # principal point
    )->glm.mat3:
    """Computes the camera rotation matrix from two vanishing points, the focal length and the principal point.
    param Fu the first vanishing point in _image plane_ coordinates.
    param Fv the second vanishing point in _image plane_ coordinates.
    param f the focal length. relative to the image height. TODO: what is relatve focal length?
    param P the principal point in _image plane_ coordinates TODO: what is image plane coordinates.
    """
    
    OFu = glm.vec3(Fu.x - P.x, Fu.y - P.y, -f)
    OFv = glm.vec3(Fv.x - P.x, Fv.y - P.y, -f)

    s1 = glm.length(OFu)
    upRc = glm.normalize(OFu)

    s2 = glm.length(OFv)
    vpRc = glm.normalize(OFv)

    wpRc = glm.cross(upRc, vpRc)

    M = glm.identity(glm.mat3)
    M[0][0] = OFu.x / s1
    M[0][1] = OFv.x / s2
    M[0][2] = wpRc.x

    M[1][0] = OFu.y / s1
    M[1][1] = OFv.y / s2
    M[1][2] = wpRc.y

    M[2][0] = -f / s1
    M[2][1] = -f / s2
    M[2][2] = wpRc.z

    return M

def _world_depth_to_ndc_z(world_distance:float, near:float, far:float) -> float:
    """Convert world depth to NDC z-coordinate using perspective-correct mapping
    world_distance: The distance from the camera in world units
    near: The near clipping plane distance
    far: The far clipping plane distance
    returns: NDC z-coordinate in [0, 1], where 0 is near and 1 is far
    """
    # Clamp the distance between near and far
    clamped_distance = max(near, min(far, world_distance))
    
    # Perspective-correct depth calculation
    # This matches how the depth buffer actually works
    ndc_z = (far + near) / (far - near) + (2 * far * near) / ((far - near) * clamped_distance)
    ndc_z = (ndc_z + 1) / 2  # Convert from [-1, 1] to [0, 1]
    return ndc_z

def _compute_camera_position_from_origin(
            view_rotation_transform:glm.mat4, 
            projection_matrix:glm.mat4, 
            origin_pixel:glm.vec2, 
            image_width:int,
            image_height:int, 
            scale: float
        )->glm.vec3:
        
        # Convert world distance to NDC z-coordinate
        origin_3D = glm.unProject(
            glm.vec3(
                origin_pixel.x, 
                origin_pixel.y, 
                _world_depth_to_ndc_z(world_distance=scale, near=0.1, far=100)
            ),
            view_rotation_transform, 
            projection_matrix, 
            glm.vec4(0,0,image_width,image_height)
        )
        return origin_3D

#######################
# Solver Computations #
#######################
def _compute_all_vanishing_points_from_control_points(
    vanishing_lines_for_multiple_axes: List[Tuple[LineSegmentType, ...]]
)->List[glm.vec2] | None:
    results: List[glm.vec2] = []
    for vanishing_lines_for_a_single_axis in vanishing_lines_for_multiple_axes:
        vanishing_point = least_squares_intersection_of_lines(vanishing_lines_for_a_single_axis)
        results.append(vanishing_point)

    return results

def _compute_focal_length_from_vanishing_points(
        Fu: glm.vec2, # first vanishing point
        Fv: glm.vec2, # second vanishing point
        P: glm.vec2   # principal point
    )-> float:
    """Computes the relative focal length from two vanishing points and the principal point.
    TODO: what is relative focal length?"""
    # compute Puv, the orthogonal projection of P onto FuFv
    dirFuFv = glm.normalize(glm.vec3(Fu.x - Fv.x, Fu.y - Fv.y, 0.0))
    FvP = glm.vec3(P.x - Fv.x, P.y - Fv.y, 0.0)
    proj = glm.dot(dirFuFv, FvP)
    Puv = glm.vec2(
      proj * dirFuFv.x + Fv.x,
      proj * dirFuFv.y + Fv.y
    )

    PPuv  = glm.length(glm.vec3(P.x - Puv.x, P.y - Puv.y, 0.0)) #TODO: check if z=0 is necessary
    FvPuv = glm.length(glm.vec3(Fv.x - Puv.x, Fv.y - Puv.y, 0.0))
    FuPuv = glm.length(glm.vec3(Fu.x - Puv.x, Fu.y - Puv.y, 0.0))

    fSq = FvPuv * FuPuv - PPuv * PPuv

    if fSq <= 0:
        raise ValueError(f"Invalid vanishing point configuration: cannot compute focal length. "
                        f"Vanishing points may be too close together or collinear with principal point. "
                        f"fSq = {fSq}, distances: FvPuv={FvPuv:.6f}, FuPuv={FuPuv:.6f}, PPuv={PPuv:.6f}")

    return math.sqrt(fSq)

def _compute_second_vanishing_point(
        Fu: glm.vec2,        # first vanishing point
        f: float,            # relative vertical focal length
        P: glm.vec2,         # principal point
        dir: glm.vec2 # horizon direction
    )->glm.vec2|None:
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
    if glm.distance(Fu, P) < 1e-7:
        return None

    Fu_P =Fu-P

    k = -(Fu_P.x * Fu_P.x + Fu_P.y * Fu_P.y + f * f) / (Fu_P.x * dir.x + Fu_P.y * dir.y)
    Fv = glm.vec2(
        x=Fu_P.x + k * dir.x + P.x,
        y=Fu_P.y + k * dir.y + P.y
    )
    return Fv

def _compute_camera_parameters(
    # control points
    origin_relative: glm.vec2, # relative coords [0,1]

    # settings
    first_axis: Axis,
    second_axis: Axis,

    # parameters
    principal_point_image_plane: glm.vec2, # relative coords [0,1]
    first_vanishing_point_relative: glm.vec2,
    second_vanishing_point_relative: glm.vec2,
    fovy: float,
    image_width: float,
    image_height: float,
    scale: float
  )->Dict | None:

    camera_orientation_matrix:glm.mat3 = _create_orientation_matrix_from_vanishing_points(
        Fu = first_vanishing_point_relative, 
        Fv = second_vanishing_point_relative, 
        f =  1 / math.tan(fovy / 2), # fovy is vertical fov in radians, 
        P =  principal_point_image_plane
    )

    # validate if matrix is a purely rotational matrix
    determinant = glm.determinant(camera_orientation_matrix)
    if math.fabs(determinant - 1) > 1e-6:
        raise Exception(f'Invalid vanishing point configuration. Rotation determinant {determinant}')

    # apply axis assignment
    axis_assignment_matrix:glm.mat3 = _createAxisAssignmentMatrix(first_axis, second_axis)
    camera_orientation_matrix:glm.mat3 = axis_assignment_matrix * camera_orientation_matrix
    view_orientation_matrix:glm.mat3 = glm.inverse(camera_orientation_matrix)
    if math.fabs(1 - glm.determinant(axis_assignment_matrix) ) > 1e-7:
        raise Exception("Invalid axis assignment")
    
    # convert to 4x4 matrix for transformations
    view_rotation_transform:glm.mat4 = glm.mat4(view_orientation_matrix)
    view_rotation_transform[3][3] = 1.0

    # 2. compute camera FOV
    # horizontal field of view
    imgui.text(f"fovy: {fovy}")

    projection_matrix = glm.perspective(
        fovy, # fovy in radians
        image_width/image_height, # aspect 
        0.1, # near
        100 # far
    )

    # 3. compute camera translation
    origin_3D = _compute_camera_position_from_origin(
        view_rotation_transform = view_rotation_transform, 
        projection_matrix =       projection_matrix, 
        origin_pixel =                  origin_relative, 
        image_width =             image_width,
        image_height =            image_height, 
        scale =                   scale
    )

    view_translate_transform = glm.translate(glm.mat4(1.0), -origin_3D)
    
    return {
        'view_transform': view_rotation_transform * view_translate_transform,
        'fovy': fovy
    }

###########
# Solvers #
###########
def solve1VP(
        # control points
        first_vanishing_lines: Tuple[LineSegmentType, ...],
        originPoint: glm.vec2,
        horizon_line_ctrl: LineSegmentType,
        principal_point_ctrl: glm.vec2,
        #parameters
        image_width, 
        image_height,
        fovy: float, # vertical field of view in radians
        scale: float = 1.0,
        # settings
        sensor_size=(36, 24),
        first_vanishing_lines_axis=Axis.PositiveX,
        second_vanishing_lines_axis=Axis.PositiveY,
        principal_point_mode: Literal['Default', 'Manual']='Default'
    ) -> Dict:

    # TODO: validate sensor match image dimensions?
    imgui.text(f"Image size: {image_width}x{image_height}, sensor size: {sensor_size[0]}x{sensor_size[1]} mm")

    # Check vanishing line sets for near-parallel lines
    for line1, line2 in itertools.combinations(first_vanishing_lines, 2):
        if are_lines_near_parallel(line1, line2):
            raise Exception("Near parallel lines detected between vanishing line sets")

    # Compute the input vanishing point in image plane coordinates
    for i, line in enumerate(first_vanishing_lines):
        P = _relative_to_image_plane_coords(
            P =            line[0],
            image_width =  image_width,
            image_height = image_height
        )
        Q = _relative_to_image_plane_coords(
            P =            line[1],
            image_width =  image_width,
            image_height = image_height
        )
        first_vanishing_lines[i] = P, Q

    all_vanishing_points = _compute_all_vanishing_points_from_control_points(
        vanishing_lines_for_multiple_axes=[first_vanishing_lines]
    )
    # TODO: THESE COORDINATE CONVERSION ARE SUSPICOUS. CHECK THEM!
    # for i, vp in enumerate(all_vanishing_points):
    #     all_vanishing_points[i] = _relative_to_image_plane_coords(
    #         P=            vp, 
    #         image_width=  image_width, 
    #         image_height= image_height
    #     )

    # Get the principal point in ImagePlane coordinates
    match principal_point_mode:
        case 'Default':
            principal_point = _relative_to_image_plane_coords(
                P =            glm.vec2(0.5, 0.5), 
                image_width =  image_width, 
                image_height = image_height
            )
        case 'Manual':
            principal_point = _relative_to_image_plane_coords(
                vp =           principal_point_ctrl, 
                image_width =  image_width, 
                image_height = image_height
            )
        case _:
            raise Exception(f"Unsupported principal point mode: {principal_point_mode}")
    
    # Compute the horizon direction
    horizonDirection = glm.vec2(1, 0) # flat by default
    # Convert horizon points from relative coordinates to ImagePlane coordinates
    horizonStart = _relative_to_image_plane_coords(
        P =            horizon_line_ctrl[0], 
        image_width =  image_width, 
        image_height = image_height
    )
    horizonEnd = _relative_to_image_plane_coords(
        P =            horizon_line_ctrl[1], 
        image_width =  image_width, 
        image_height = image_height
    )

    horizonDirection = glm.normalize(horizonEnd - horizonStart)

    # Compute relative focal length (normalized by larger sensor dimension)
    second_vanishing_point = _compute_second_vanishing_point(
        Fu =         all_vanishing_points[0],
        f =          1 / math.tan(fovy / 2),
        P =          principal_point,
        dir = horizonDirection
    )

    return _compute_camera_parameters(
        origin_relative =                      originPoint,
        first_axis =  first_vanishing_lines_axis,
        second_axis = second_vanishing_lines_axis,
        principal_point_image_plane =             principal_point,
        first_vanishing_point_relative =       all_vanishing_points[0],
        second_vanishing_point_relative =      second_vanishing_point,
        fovy =                        fovy,
        image_width =                 image_width,
        image_height =                image_height,
        scale =                       scale
    )

def solve2VP(
    # control points
    principal_point_relative: glm.vec2,
    origin_relative: glm.vec2,
    first_vanishing_lines_relative:  Tuple[LineSegmentType, ...],
    second_vanishing_lines_relative: Tuple[LineSegmentType, ...],
    third_vanishing_lines_relative:  Tuple[LineSegmentType, ...]|None,
    # parameters
    image_width, 
    image_height,
    scale: float = 1.0,
    # settings
    sensor_size=(36, 24),
    first_vanishing_lines_axis=Axis.PositiveX,
    second_vanishing_lines_axis=Axis.PositiveY,
    principal_point_mode: Literal['Default', 'Manual', 'FromThirdVanishingPoint']='Default',
    quad_mode_enabled: bool=False

)->Dict:

    # Map input coord to image plane coordinates
    for i, line in enumerate(first_vanishing_lines_relative):
        P = _relative_to_image_plane_coords(
            P =            line[0],
            image_width =  image_width,
            image_height = image_height
        )
        Q = _relative_to_image_plane_coords(
            P =            line[1],
            image_width =  image_width,
            image_height = image_height
        )
        first_vanishing_lines_relative[i] = P, Q
    
    for i, line in enumerate(second_vanishing_lines_relative):
        P = _relative_to_image_plane_coords(
            P =            line[0],
            image_width =  image_width,
            image_height = image_height
        )
        Q = _relative_to_image_plane_coords(
            P =            line[1],
            image_width =  image_width,
            image_height = image_height
        )
        second_vanishing_lines_relative[i] = P, Q

    # Compute the two input vanishing points from the provided control points
    all_vanishing_points = _compute_all_vanishing_points_from_control_points(
      vanishing_lines_for_multiple_axes = [first_vanishing_lines_relative, second_vanishing_lines_relative],
    )

    if not all_vanishing_points or len(all_vanishing_points) < 2:
        raise Exception("Failed to compute vanishing points")
    
    match principal_point_mode:
        case 'Default':
            principal_point = _relative_to_image_plane_coords(
                P =           glm.vec2(0.5, 0.5), 
                image_width =  image_width, 
                image_height = image_height
            )

        case 'Manual':
            principal_point = _relative_to_image_plane_coords(
                P =            principal_point_relative, 
                image_width =  image_width, 
                image_height = image_height
            )

        case 'FromThirdVanishingPoint':
            thirdVanishingPointArray = _compute_all_vanishing_points_from_control_points(
               vanishing_lines_for_multiple_axes = [third_vanishing_lines_relative],
            )
            for i, vp in enumerate(thirdVanishingPointArray):
                thirdVanishingPointArray[i] = _relative_to_image_plane_coords(
                    P=            vp, 
                    image_width=  image_width, 
                    image_height= image_height
                )

            if thirdVanishingPointArray:
                thirdVanishingPoint = thirdVanishingPointArray[0]
                principal_point = _triangleOrthoCenter(
                    all_vanishing_points[0], 
                    all_vanishing_points[1], 
                    thirdVanishingPoint
                )
            else:
                raise Exception("Failed to compute third vanishing point for principal point calculation")
        case _:
            raise Exception(f"Unsupported principal point mode: {principal_point_mode}")
        
    # Check vanishing line sets for near-parallel lines
    for vanishing_lines in filter(lambda _:bool(_), [first_vanishing_lines_relative, second_vanishing_lines_relative, third_vanishing_lines_relative]):
        for line1, line2 in itertools.combinations(vanishing_lines, 2):
            if are_lines_near_parallel(line1, line2):
                raise Exception("Near parallel lines detected between vanishing line sets")

    relative_focal_length = _compute_focal_length_from_vanishing_points(
        Fu = all_vanishing_points[0], 
        Fv = all_vanishing_points[1], 
        P =  principal_point
    )

    fovy = math.atan(1 / relative_focal_length) * 2
    
    return _compute_camera_parameters(
        # control points
        origin_relative =                      origin_relative,
        first_axis =  first_vanishing_lines_axis,
        second_axis = second_vanishing_lines_axis,
        principal_point_image_plane =             principal_point,
        first_vanishing_point_relative =       all_vanishing_points[0],
        second_vanishing_point_relative =      all_vanishing_points[1],
        # parameters
        fovy =                        fovy,
        image_width =                 image_width,
        image_height =                image_height,
        scale =                       scale
    )
