import glm
from typing import *
from enum import StrEnum, IntEnum
from dataclasses import dataclass, field
from my_solver import compute_vanishing_point
import math
from imgui_bundle import imgui

class Axis(StrEnum):
  PositiveX = 'xPositive'
  NegativeX = 'xNegative'
  PositiveY = 'yPositive'
  NegativeY = 'yNegative'
  PositiveZ = 'zPositive'
  NegativeZ = 'zNegative'

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

@dataclass
class ControlPointState:
    x: float # Relative image coordinates [0, 1]
    y: float # Relative image coordinates [0, 1]

ControlPointPairState = Tuple[ControlPointState, ControlPointState]

# // TODO: Rename to BinaryIndex or something? Or remove if it doesnt provide type info
class ControlPointPairIndex(IntEnum):
    First = 0
    Second = 1

class ReferenceDistanceUnit(StrEnum):
  NoUnit = 'No unit',
  Millimeters = 'Millimeters',
  Centimeters = 'Centimeters',
  Meters = 'Meters',
  Kilometers = 'Kilometers',
  Inches = 'Inches',
  Feet = 'Feet',
  Miles = 'Miles'

@dataclass
class VanishingPointControlState:
    lineSegments: List[ControlPointPairState]

@dataclass
class ControlPointsStateBase:
    principalPoint: ControlPointState
    origin: ControlPointState
    referenceDistanceAnchor: ControlPointState
    firstVanishingPoint: VanishingPointControlState
    #   // The offsets are the distances in relative image coordinates
    #   // along the axis from the anchor to the vanishing point corresponding
    #   // to the selected reference axis
    referenceDistanceHandleOffsets: Tuple[float, float]

@dataclass
class CameraData:
  customSensorWidth: int
  customSensorHeight: int

class PrincipalPointMode1VP(StrEnum):
  Default = 'Default',
  Manual = 'Manual'


class PrincipalPointMode2VP(StrEnum):
  Default = 'Default',
  Manual = 'Manual',
  FromThirdVanishingPoint = 'FromThirdVanishingPoint'

@dataclass
class CalibrationSettings1VP:
  principalPointMode: PrincipalPointMode1VP
  absoluteFocalLength: float

@dataclass
class CalibrationSettingsBase:
  referenceDistanceUnit: ReferenceDistanceUnit
  referenceDistance: float
  referenceDistanceAxis: Axis | None
  cameraData: CameraData
  firstVanishingPointAxis: Axis
  secondVanishingPointAxis: Axis

@dataclass
class ControlPointsState1VP:
  horizon: ControlPointPairState

@dataclass
class ControlPointsState2VP:
  secondVanishingPoint: VanishingPointControlState
  thirdVanishingPoint: VanishingPointControlState

def _relative_to_image_plane_coords(vp:glm.vec2, imageWidth:int, imageHeight:int)->glm.vec2:
    """Convert relative [0,1] coordinates to ImagePlane coordinates (normalized, Y-up)"""
    aspect_ratio = imageWidth / imageHeight
    if aspect_ratio <= 1:
        # tall image: [0,1] → [-aspect, aspect] x [-1, 1]
        return glm.vec2(
            (-1 + 2 * vp.x) * aspect_ratio,
            1 - 2 * vp.y  # Y-flip: relative Y-down → ImagePlane Y-up
        )
    else:
        # wide image: [0,1] → [-1, 1] x [-1/aspect, 1/aspect]
        return glm.vec2(
            -1 + 2 * vp.x,
            (1 - 2 * vp.y) / aspect_ratio
        )

def _computeVanishingPointsFromControlPoints(
    image_width:int,
    image_height:int, 
    controlPointStates: List[VanishingPointControlState], 
    errors
)->List[glm.vec2] | None:
    results: List[glm.vec2] = []
    for vanishingPointState in controlPointStates:
        # Convert ControlPointPairState to the format expected by compute_vanishing_point
        line_segments = []
        for pair in vanishingPointState.lineSegments:
            if isinstance(pair[0], glm.vec2):
                # Handle glm.vec2 pairs (from your current usage)
                line_segments.append(pair)
            else:
                # Handle ControlPointState pairs (proper fSpy format)
                line_segments.append([
                    (pair[0].x, pair[0].y),
                    (pair[1].x, pair[1].y)
                ])
        
        vanishingPoint = compute_vanishing_point(line_segments)
        image_plane_vanishing_point = _relative_to_image_plane_coords(vanishingPoint, image_width, image_height)
        results.append(image_plane_vanishing_point)

    return results

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

def _computeFieldOfView(
    imageWidth: float,
    imageHeight: float,
    fRelative: float,
    vertical: bool
  )->float:
    aspectRatio = imageWidth / imageHeight
    d = 1 / aspectRatio if vertical else 1
    return 2 * math.atan(d / fRelative)

def _computeCameraRotationMatrix(Fu: glm.vec2, Fv: glm.vec2, f: float, P: glm.vec2)->glm.mat4:
    # Use higher precision by working with normalized vectors from the start
    OFu = glm.vec3(Fu.x - P.x, Fu.y - P.y, -f)
    OFv = glm.vec3(Fv.x - P.x, Fv.y - P.y, -f)

    # Compute lengths with higher precision
    s1 = glm.length(OFu)
    s2 = glm.length(OFv)
    
    # Ensure we don't divide by very small numbers
    if s1 < 1e-12 or s2 < 1e-12:
        raise Exception("Vanishing points too close to principal point")
    
    # Normalize vectors with higher precision
    u = OFu / s1  # First basis vector
    v_unnormalized = OFv / s2  # Second vector (not yet orthogonal)

    # Apply Gram-Schmidt orthogonalization for better numerical stability
    # Make v orthogonal to u: v = v - (v·u)u
    dot_vu = glm.dot(v_unnormalized, u)
    v = v_unnormalized - dot_vu * u
    
    # Normalize the orthogonalized v
    v_length = glm.length(v)
    if v_length < 1e-12:
        raise Exception("Vanishing points are parallel - cannot form rotation matrix")
    v = v / v_length
    
    # Compute the third orthogonal vector using cross product
    w = glm.cross(u, v)
    
    # Ensure w is normalized (should be for orthogonal unit vectors, but be safe)
    w_length = glm.length(w)
    if w_length < 1e-12:
        raise Exception("Failed to compute orthogonal basis")
    w = w / w_length

    # Construct rotation matrix using orthonormal basis vectors
    M = glm.identity(glm.mat4)
    M[0][0] = u.x
    M[0][1] = v.x
    M[0][2] = w.x

    M[1][0] = u.y
    M[1][1] = v.y
    M[1][2] = w.y

    M[2][0] = u.z
    M[2][1] = v.z
    M[2][2] = w.z

    return M

DEFAULT_CAMERA_DISTANCE_SCALE = 5.0
def _computeTranslationVector(
    origin:glm.vec2, # relative coords [0,1]
    imageWidth: float,
    imageHeight: float,
    horizontalFieldOfView: float,
    principalPoint: glm.vec2 # ImagePlane coordinates
    
  )->glm.vec3:
    # The 3D origin in image plane coordinates
    origin_image_plane = _relative_to_image_plane_coords(origin, imageWidth, imageHeight)

    k = math.tan(0.5 * horizontalFieldOfView)
    origin3D = glm.vec3(
      k * (origin_image_plane.x - principalPoint.x),
      k * (origin_image_plane.y - principalPoint.y),
      -1
    ) * DEFAULT_CAMERA_DISTANCE_SCALE

    return origin3D

def _computeCameraParameters(
    result: SolverResult,
    controlPoints: ControlPointsStateBase,
    settings: CalibrationSettingsBase,
    principalPoint: glm.vec2,
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

    # Assing vanishing point axes
    axisAssignmentMatrix = glm.identity(glm.mat4)
    row1 = _axisVector(settings.firstVanishingPointAxis)
    row2 = _axisVector(settings.secondVanishingPointAxis)
    row3 = glm.cross(row1, row2)
    axisAssignmentMatrix[0][0] = row1.x
    axisAssignmentMatrix[0][1] = row1.y
    axisAssignmentMatrix[0][2] = row1.z
    axisAssignmentMatrix[1][0] = row2.x
    axisAssignmentMatrix[1][1] = row2.y
    axisAssignmentMatrix[1][2] = row2.z
    axisAssignmentMatrix[2][0] = row3.x
    axisAssignmentMatrix[2][1] = row3.y
    axisAssignmentMatrix[2][2] = row3.z

    if math.fabs(1 - glm.determinant(axisAssignmentMatrix) ) > 1e-7:
      raise Exception("Invalid axis assignment")
    
    cameraParameters.vanishingPointAxes = [
      settings.firstVanishingPointAxis,
      settings.secondVanishingPointAxis,
      _vectorAxis(row3)
    ]

    # principal point
    cameraParameters.principalPoint = principalPoint
    # focal length
    cameraParameters.relativeFocalLength = relativeFocalLength
    # vanishing points
    cameraParameters.vanishingPoints = [
      vp1,
      vp2,
      _thirdTriangleVertex(
        vp1,
        vp2,
        principalPoint
      )
    ]
    # horizontal field of view
    cameraParameters.horizontalFieldOfView = _computeFieldOfView(
      imageWidth,
      imageHeight,
      relativeFocalLength,
      False
    )

    # vertical field of view
    cameraParameters.verticalFieldOfView = _computeFieldOfView(
      imageWidth,
      imageHeight,
      relativeFocalLength,
      True
    )

    # compute camera rotation matrix
    cameraRotationMatrix = _computeCameraRotationMatrix(
      vp1, vp2, relativeFocalLength, principalPoint
    )
    # Check determinant with very forgiving tolerance for floating-point precision
    determinant = glm.determinant(cameraRotationMatrix)
    if math.fabs(determinant - 1) > 1e-5:  # Much more relaxed: 1e-5 (100x more forgiving than original)
        raise Exception(f'Invalid vanishing point configuration. Rotation determinant {determinant}')

    cameraParameters.viewTransform = axisAssignmentMatrix * cameraRotationMatrix
    
    origin3D = _computeTranslationVector(
      origin=controlPoints.origin,
      imageWidth=imageWidth,
      imageHeight=imageHeight,
      horizontalFieldOfView=cameraParameters.horizontalFieldOfView,
      principalPoint=cameraParameters.principalPoint
    )

    # TODO: get rid of camera parameters altogether. either replace with Camera or use attributes directly
    cameraParameters.viewTransform[0][3] = origin3D.x
    cameraParameters.viewTransform[1][3] = origin3D.y
    cameraParameters.viewTransform[2][3] = origin3D.z

    imgui.text(f"Camera origin 3D: {origin3D}")

    # FIXED: Properly compute camera transform from view transform
    # The naive inversion loses the correct translation component
    # We need to manually construct the camera transform
    
    # Extract rotation part (3x3 upper-left)
    view_rotation = glm.mat3(cameraParameters.viewTransform)
    
    # Camera rotation is the transpose of view rotation
    camera_rotation = glm.transpose(view_rotation)
    
    # Camera position is -R^T * t, where R is view rotation and t is view translation
    view_translation = glm.vec3(
        cameraParameters.viewTransform[0][3],
        cameraParameters.viewTransform[1][3], 
        cameraParameters.viewTransform[2][3]
    )
    camera_position = -camera_rotation * view_translation
    
    # Construct the camera transform matrix (GLM uses column-major)
    # Each column represents: [right, up, forward, position]
    cameraParameters.cameraTransform = glm.mat4(
        # Column 0 (right vector)
        camera_rotation[0][0], camera_rotation[1][0], camera_rotation[2][0], 0.0,
        # Column 1 (up vector)  
        camera_rotation[0][1], camera_rotation[1][1], camera_rotation[2][1], 0.0,
        # Column 2 (forward vector)
        camera_rotation[0][2], camera_rotation[1][2], camera_rotation[2][2], 0.0,
        # Column 3 (position)
        camera_position.x, camera_position.y, camera_position.z, 1.0
    )
    
    # Debug: Print the camera position to verify it's correct
    imgui.text(f"Camera position: ({camera_position.x:.3f}, {camera_position.y:.3f}, {camera_position.z:.3f})")

    return cameraParameters

def _computeSecondVanishingPoint(
        Fu: glm.vec2, 
        f: float, 
        P: glm.vec2, 
        horizonDir: glm.vec2
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

def solve1VP(
        settingsBase: CalibrationSettingsBase,
        settings1VP: CalibrationSettings1VP,
        controlPointsBase: ControlPointsStateBase,
        controlPoints1VP: ControlPointsState1VP,
        image_width=800, 
        image_height=800
    ) -> SolverResult:
    result = SolverResult()

    # TODO: validate image dimensions
    # ...

    # Compute relative focal length
    relativeFocalLength = 0.0
    absoluteFocalLength = settings1VP.absoluteFocalLength
    sensorWidth = settingsBase.cameraData.customSensorWidth
    sensorHeight = settingsBase.cameraData.customSensorHeight
    sensorAspectRatio = settingsBase.cameraData.customSensorWidth / settingsBase.cameraData.customSensorHeight
    # // TODO: verify factor 2
    if sensorAspectRatio > 1:
        # wide sensor
        relativeFocalLength = 2 * absoluteFocalLength / sensorWidth
    else:
        # tall sensor
        relativeFocalLength = 2 * absoluteFocalLength / sensorHeight

    # TODO: validate sensor match image dimensions

    # Compute the input vanishing point in image plane coordinates
    vanishingPointStates = controlPointsBase.firstVanishingPoint
    input_vanishing_points = _computeVanishingPointsFromControlPoints(
        image_width=image_width,
        image_height=image_height,
        controlPointStates=[vanishingPointStates],
        errors=result.errors
    )

    # TODO: validate vanishing points accuracy
    # ...

    # Get the principal point in ImagePlane coordinates
    principalPoint = glm.vec2(0,0)  # Default to center in ImagePlane coordinates
    # Note: controlPointsBase.principalPoint should be in relative coordinates [0,1]
    # We need to convert it to ImagePlane coordinates for calculations
    if hasattr(controlPointsBase, 'principalPoint') and controlPointsBase.principalPoint:
        if isinstance(controlPointsBase.principalPoint, glm.vec2):
            # If it's a glm.vec2, assume it's already in relative coordinates
            principalPoint = _relative_to_image_plane_coords(controlPointsBase.principalPoint, image_width, image_height)
        else:
            # If it's a ControlPointState, extract x,y
            rel_point = glm.vec2(controlPointsBase.principalPoint.x, controlPointsBase.principalPoint.y)
            principalPoint = _relative_to_image_plane_coords(rel_point, image_width, image_height)

    #/Compute the horizon direction
    horizonDirection = glm.vec2(1, 0) # flat by default
    # Convert horizon points from relative coordinates to ImagePlane coordinates
    if isinstance(controlPoints1VP.horizon[0], glm.vec2):
        # Handle glm.vec2 format (current usage)
        horizonStart = _relative_to_image_plane_coords(controlPoints1VP.horizon[0], image_width, image_height)
        horizonEnd = _relative_to_image_plane_coords(controlPoints1VP.horizon[1], image_width, image_height)
    else:
        # Handle ControlPointState format (proper fSpy)
        horizonStart = _relative_to_image_plane_coords(
            glm.vec2(controlPoints1VP.horizon[0].x, controlPoints1VP.horizon[0].y), 
            image_width, image_height
        )
        horizonEnd = _relative_to_image_plane_coords(
            glm.vec2(controlPoints1VP.horizon[1].x, controlPoints1VP.horizon[1].y), 
            image_width, image_height
        )
    horizonDirection = glm.normalize(horizonEnd - horizonStart)

    second_vanishing_point = _computeSecondVanishingPoint(
        input_vanishing_points[0],
        relativeFocalLength,
        principalPoint,
        horizonDirection
    )


    camera_parameters = _computeCameraParameters(result,
        controlPointsBase,
        settingsBase,
        principalPoint,
        input_vanishing_points[0],
        second_vanishing_point,
        relativeFocalLength,
        image_width,
        image_height
    )


    result.cameraParameters = camera_parameters
    return result