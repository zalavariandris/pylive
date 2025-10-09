import glm
from typing import *
from enum import StrEnum, IntEnum
from dataclasses import dataclass, field
import math
from imgui_bundle import imgui
import itertools

DEFAULT_CAMERA_DISTANCE_SCALE = 5.0

############################# 
# Geometry helper functions #
#############################
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

class Axis(StrEnum):
    PositiveX = 'xPositive'
    NegativeX = 'xNegative'
    PositiveY = 'yPositive'
    NegativeY = 'yNegative'
    PositiveZ = 'zPositive'
    NegativeZ = 'zNegative'

################
# Solver Types #
################
LineSegmentType = Tuple[glm.vec2, glm.vec2]

################
# Solver UTILS #
################

def remap(value, from_min, from_max, to_min, to_max):
    return (value - from_min) * (to_max - to_min) / (from_max - from_min) + to_min

def _relative_to_image_plane_coords(vp: glm.vec2, imageWidth: int, imageHeight: int) -> glm.vec2:
    aspect_ratio = imageWidth / imageHeight
    
    if aspect_ratio <= 1:
        # tall image
        x = remap(vp.x, 0, 1, -aspect_ratio, aspect_ratio)
        y = remap(vp.y, 0, 1, 1, -1)  # Y-flipped
    else:
        # wide image  
        x = remap(vp.x, 0, 1, -1, 1)
        y = remap(vp.y, 0, 1, 1/aspect_ratio, -1/aspect_ratio)  # Y-flipped
    
    return glm.vec2(x, y)
    
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
def my_compute_vanishing_point(vanishing_lines: List[Tuple[glm.vec2, glm.vec2]]) -> glm.vec2:
    """
    Compute the vanishing point from a set of 2D lines assumed to be parallel in 3D.

    Args:
        lines (List[LineSegment]): List of line segments ((x1,y1),(x2,y2)).

    Returns:
        VanishingPoint: Homogeneous coordinates of the vanishing point [x, y, 1].
    """
    if len(vanishing_lines) < 2:
        raise ValueError("At least two lines are required to compute a vanishing point")
    
    # Build the constraint matrix
    constraint_matrix = [] # Each row is [a, b, c] for the line equation ax + by + c = 0
    for line_segment in vanishing_lines:
        P, Q = line_segment
        # a = y1 - y2
        # b = x2 - x1
        # c = x1*y2 - x2*y1
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

#####################
# Solver Parameters #
#####################

@dataclass
class CameraParameters:
  principalPoint: glm.vec2
  viewTransform: glm.mat4
  cameraTransform: glm.mat4 # the inverse of the view transform
  horizontalFieldOfView: float
  verticalFieldOfView: float
  vanishingPoints: Tuple[glm.vec2, glm.vec2, glm.vec2]
  vanishingPointAxes: Tuple[Axis, Axis, Axis]
  relativeFocalLength: float
  imageWidth: int
  imageHeight: int

@dataclass
class SolverResult:
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    cameraParameters: CameraParameters | None = None


class CalibrationSettingsBase(NamedTuple):
    sensor_size: Tuple[int, int] = (36, 24) # (width, height) in mm
    first_vanishing_lines_axis: Axis = Axis.PositiveX
    second_vanishing_lines_axis: Axis = Axis.PositiveY

###########################
# Solver Helper Functions #
###########################

def _compute_field_of_view(
    imageWidth: float,
    imageHeight: float,
    fRelative: float,
    vertical: bool
  )->float:
    """Computes the field of view (horizontal or vertical) in radians."""
    aspectRatio = imageWidth / imageHeight
    d = 1 / aspectRatio if vertical else 1
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
    if math.fabs(1 - glm.determinant(axisAssignmentMatrix)) > 1e-7:
        raise Exception("Invalid axis assignment: axes must be orthogonal")
    
    return axisAssignmentMatrix

def _compute_camera_rotation_matrix(
        Fu: glm.vec2, # first vanishing point
        Fv: glm.vec2, # second vanishing point
        f: float,     # relative focal length
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

def _compute_camera_position_from_origin(
            viewRotationTransform:glm.mat4, 
            projectionMatrix:glm.mat4, 
            origin:glm.vec2, 
            image_height:int, 
            image_width:int,
            scale: float
        )->glm.vec3:

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
        
        # Convert world distance to NDC z-coordinate
        ndc_z = _world_depth_to_ndc_z(world_distance=scale, near=0.1, far=100)
        origin_window_coords = glm.vec3(origin.x * image_width, (1-origin.y) * image_height, ndc_z)
        origin_3D = glm.unProject(origin_window_coords, viewRotationTransform, projectionMatrix, glm.vec4(0,0,image_width,image_height))
        return origin_3D

#######################
# Solver Computations #
#######################
def _compute_vanishing_points_from_control_points(
    image_width:int,
    image_height:int, 
    vanishing_lines_for_multiple_axes: List[Tuple[LineSegmentType, ...]]
)->List[glm.vec2] | None:
    results: List[glm.vec2] = []
    for vanishing_lines_for_a_single_axis in vanishing_lines_for_multiple_axes:
        # Convert ControlPointPairState to the format expected by compute_vanishing_point
        line_segments = []
        for line_segment in vanishing_lines_for_a_single_axis:
            if isinstance(line_segment[0], glm.vec2):
                # Handle glm.vec2 pairs (from your current usage)
                line_segments.append(line_segment)
            else:
                # Handle ControlPointState pairs (proper fSpy format)
                line_segments.append([
                    (line_segment[0].x, line_segment[0].y),
                    (line_segment[1].x, line_segment[1].y)
                ])
        
        vanishingPoint = my_compute_vanishing_point(line_segments)
        image_plane_vanishing_point = _relative_to_image_plane_coords(vanishingPoint, image_width, image_height)
        results.append(image_plane_vanishing_point)

    return results

def _compute_focal_length_from_vanishing_points(Fu: glm.vec2, Fv: glm.vec2, P: glm.vec2)-> float:
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
        f: float,            # relative focal length
        P: glm.vec2,         # principal point
        horizonDir: glm.vec2 # horizon direction
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
    # // TODO_ take principal point into account here
    if glm.distance(Fu, P) < 1e-7:
        return None

    Fup =Fu-P

    k = -(Fup.x * Fup.x + Fup.y * Fup.y + f * f) / (Fup.x * horizonDir.x + Fup.y * horizonDir.y)
    Fv = glm.vec2(
        x=Fup.x + k * horizonDir.x + P.x,
        y=Fup.y + k * horizonDir.y + P.y
    )
    return Fv

def _computeCameraParameters(
    # control points
    origin: glm.vec2, # relative coords [0,1]
    # settings
    firstVanishingPointAxis: Axis,
    secondVanishingPointAxis: Axis,
    # parameters
    principalPoint: glm.vec2, # relative coords [0,1]
    vp1: glm.vec2,
    vp2: glm.vec2,
    relativeFocalLength: float,
    imageWidth: float,
    imageHeight: float
  )->CameraParameters | None:

    cameraParameters = CameraParameters(
      principalPoint=glm.vec2(0,0), 
      viewTransform= glm.identity(glm.mat4),
      cameraTransform = glm.identity(glm.mat4),
      horizontalFieldOfView= 0.0,
      verticalFieldOfView= 0.0,
      vanishingPoints= [glm.vec2(0,0), glm.vec2(0,0), glm.vec2(0,0)],
      vanishingPointAxes= [Axis.NegativeX, Axis.NegativeX, Axis.NegativeX],
      relativeFocalLength= 0.0,
      imageWidth=imageWidth,
      imageHeight=imageHeight
    )

    # 1. compute camera rotation matrix
    cameraOrientationMatrix = _compute_camera_rotation_matrix(
      vp1, vp2, relativeFocalLength, principalPoint
    )

    # Check determinant with very forgiving tolerance for floating-point precision
    determinant = glm.determinant(cameraOrientationMatrix)
    if math.fabs(determinant - 1) > 1e-5:  # Much more relaxed: 1e-5 (100x more forgiving than original) TODO: why so much error?
        raise Exception(f'Invalid vanishing point configuration. Rotation determinant {determinant}')

    axisAssignmentMatrix = _createAxisAssignmentMatrix(firstVanishingPointAxis, secondVanishingPointAxis)
    cameraOrientationMatrix = axisAssignmentMatrix * cameraOrientationMatrix
    viewOrientationMatrix = glm.inverse(cameraOrientationMatrix)
    if math.fabs(1 - glm.determinant(axisAssignmentMatrix) ) > 1e-7:
      raise Exception("Invalid axis assignment")
    

    viewRotationTransform = glm.mat4(viewOrientationMatrix)
    viewRotationTransform[3][3] = 1.0

    # 2. compute camera FOV
    # horizontal field of view
    fovx = _compute_field_of_view(
      imageWidth,
      imageHeight,
      relativeFocalLength,
      False
    )

    # vertical field of view
    fovy = _compute_field_of_view(
      imageWidth,
      imageHeight,
      relativeFocalLength,
      True
    )

    projectionMatrix = glm.perspective(
        fovy, # fovy in radians
        imageWidth/imageHeight, # aspect 
        0.1, # near
        100 # far
    )

    # 3. compute camera translation
    global DEFAULT_CAMERA_DISTANCE_SCALE
    _, DEFAULT_CAMERA_DISTANCE_SCALE = imgui.slider_float("World Distance", DEFAULT_CAMERA_DISTANCE_SCALE, 0.1, 100.0)
    origin_3D = _compute_camera_position_from_origin(
        viewRotationTransform, 
        projectionMatrix, 
        origin, 
        imageHeight, 
        imageWidth,
        scale=DEFAULT_CAMERA_DISTANCE_SCALE
    )

    viewTranslateMatrix = glm.translate(glm.mat4(1.0), -origin_3D)
    
    cameraParameters.horizontalFieldOfView = fovx
    cameraParameters.verticalFieldOfView = fovy
    cameraParameters.viewTransform = viewRotationTransform * viewTranslateMatrix
    return cameraParameters

###########
# Solvers #
###########


def solve1VP(
        image_width, 
        image_height,
        # control points
        first_vanishing_lines: Tuple[LineSegmentType, ...],
        originPoint: glm.vec2,
        horizon_line_ctrl: LineSegmentType,
        principalPointCtrl: glm.vec2,
        # settings
        sensor_size=(36, 24),
        first_vanishing_lines_axis=Axis.PositiveX,
        second_vanishing_lines_axis=Axis.PositiveY,
        principalPointMode: Literal['Default', 'Manual']='Default',
        absoluteFocalLength: float =50.0
    ) -> SolverResult:

    result = SolverResult() # blank result to fill

    # TODO: validate sensor match image dimensions?
    ...

    # Check vanishing line sets for near-parallel lines
    for line1, line2 in itertools.combinations(first_vanishing_lines, 2):
        if are_lines_near_parallel(line1, line2):
            raise Exception("Near parallel lines detected between vanishing line sets")

    # Compute relative focal length (normalized by larger sensor dimension)
    relativeFocalLength = 2 * absoluteFocalLength / max(*sensor_size)

    # Compute the input vanishing point in image plane coordinates
    input_vanishing_points = _compute_vanishing_points_from_control_points(
        image_width=image_width,
        image_height=image_height,
        vanishing_lines_for_multiple_axes=[first_vanishing_lines]
    )

    # Get the principal point in ImagePlane coordinates
    match principalPointMode:
        case 'Default':
            principal_point = _relative_to_image_plane_coords(glm.vec2(0.5, 0.5), image_width, image_height)
        case 'Manual':
            principal_point = _relative_to_image_plane_coords(principalPointCtrl, image_width, image_height)
        case _:
            raise Exception(f"Unsupported principal point mode: {principalPointMode}")
    
    #/Compute the horizon direction
    horizonDirection = glm.vec2(1, 0) # flat by default
    # Convert horizon points from relative coordinates to ImagePlane coordinates
    if isinstance(horizon_line_ctrl[0], glm.vec2):
        # Handle glm.vec2 format (current usage)
        horizonStart = _relative_to_image_plane_coords(horizon_line_ctrl[0], image_width, image_height)
        horizonEnd = _relative_to_image_plane_coords(horizon_line_ctrl[1], image_width, image_height)
    else:
        # Handle ControlPointState format (proper fSpy)
        horizonStart = _relative_to_image_plane_coords(
            glm.vec2(horizon_line_ctrl[0].x, horizon_line_ctrl[0].y), 
            image_width, image_height
        )
        horizonEnd = _relative_to_image_plane_coords(
            glm.vec2(horizon_line_ctrl[1].x, horizon_line_ctrl[1].y), 
            image_width, image_height
        )
    horizonDirection = glm.normalize(horizonEnd - horizonStart)

    second_vanishing_point = _compute_second_vanishing_point(
        input_vanishing_points[0],
        relativeFocalLength,
        principal_point,
        horizonDirection
    )

    camera_parameters = _computeCameraParameters(
        origin=originPoint,
        firstVanishingPointAxis=first_vanishing_lines_axis,
        secondVanishingPointAxis=second_vanishing_lines_axis,
        principalPoint=principal_point,
        vp1=input_vanishing_points[0],
        vp2=second_vanishing_point,
        relativeFocalLength=relativeFocalLength,
        imageWidth=image_width,
        imageHeight=image_height
    )

    result.cameraParameters = camera_parameters
    return result

# @dataclass
# class CalibrationSettings2VP:
#     principalPointMode: Literal['Default', 'Manual', 'FromThirdVanishingPoint']
#     quadModeEnabled: bool

def solve2VP(
    image_width, 
    image_height,
    # control points
    principalPointCtrl: glm.vec2,
    originPoint: glm.vec2,
    first_vanishing_lines:  Tuple[LineSegmentType, ...],
    second_vanishing_lines: Tuple[LineSegmentType, ...],
    third_vanishing_lines:  Tuple[LineSegmentType, ...]|None,
    # settings
    sensor_size=(36, 24),
    first_vanishing_lines_axis=Axis.PositiveX,
    second_vanishing_lines_axis=Axis.PositiveY,
    principalPointMode: Literal['Default', 'Manual', 'FromThirdVanishingPoint']='Default',
    quadModeEnabled: bool=False,
)->SolverResult:
    result = SolverResult()  # blank result to fill

    # Compute the two input vanishing points from the provided control points
    inputVanishingPoints = _compute_vanishing_points_from_control_points(
      image_width=image_width,
      image_height=image_height,
      vanishing_lines_for_multiple_axes=[first_vanishing_lines, second_vanishing_lines],
    )

    if not inputVanishingPoints or len(inputVanishingPoints) < 2:
        raise Exception("Failed to compute vanishing points")
    
    # TODO: principal point seem to be overcomplicated in fSpy. Why? Fix it!
    match principalPointMode:
        case 'Default':
            principal_point = _relative_to_image_plane_coords(glm.vec2(0.5, 0.5), image_width, image_height)

        case 'Manual':
            principal_point = _relative_to_image_plane_coords(principalPointCtrl, image_width, image_height)

        case 'FromThirdVanishingPoint':
            thirdVanishingPointArray = _compute_vanishing_points_from_control_points(
               image_width, image_height,
               [third_vanishing_lines],
            )

            if thirdVanishingPointArray:
                thirdVanishingPoint = thirdVanishingPointArray[0]
                principal_point = _triangleOrthoCenter(
                    inputVanishingPoints[0], 
                    inputVanishingPoints[1], 
                    thirdVanishingPoint
                )
            else:
                raise Exception("Failed to compute third vanishing point for principal point calculation")
        case _:
            raise Exception(f"Unsupported principal point mode: {principalPointMode}")
        
    # Check vanishing line sets for near-parallel lines
    for vanishing_lines in filter(lambda _:bool(_), [first_vanishing_lines, second_vanishing_lines, third_vanishing_lines]):
        for line1, line2 in itertools.combinations(vanishing_lines, 2):
            if are_lines_near_parallel(line1, line2):
                raise Exception("Near parallel lines detected between vanishing line sets")

    fRelative = _compute_focal_length_from_vanishing_points(
        inputVanishingPoints[0], 
        inputVanishingPoints[1], 
        principal_point
    )
    
    camera_parameters = _computeCameraParameters(
        origin=originPoint,
        firstVanishingPointAxis=first_vanishing_lines_axis,
        secondVanishingPointAxis=second_vanishing_lines_axis,
        principalPoint=principal_point,
        vp1=inputVanishingPoints[0],
        vp2=inputVanishingPoints[1],
        relativeFocalLength=fRelative,
        imageWidth=image_width,
        imageHeight=image_height
    )

    result.cameraParameters = camera_parameters
    return result
