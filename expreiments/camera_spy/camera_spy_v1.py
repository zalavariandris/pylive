import logging
import string
logger = logging.getLogger(__name__)

import math
import numpy as np
from pylive.render_engine.camera import Camera


# ############## #
# Graphics Layer #
# ############## #
import moderngl
from pylive.render_engine.render_layers import GridLayer, RenderLayer
import OpenGL.GL as gl
import glm


class SceneLayer(RenderLayer):
    def __init__(self):
        self.initialized = False
        self.grid = GridLayer()

    def setup(self, ctx:moderngl.Context):
        self.grid.setup(ctx)
        super().setup(ctx)

    def destroy(self):
        if self.grid:
            self.grid.destroy()
            self.grid = None
        return super().destroy()
    
    def render(self, camera:Camera):
        self.grid.render(view=camera.viewMatrix(), projection=camera.projectionMatrix())
        super().render()


# ########### #
# GUI helpers #
# ########### #
from imgui_bundle import imgui, immapp
from gizmos import drag_axes, drag_horizon
from utils.geo import closest_point_line_segment
from gizmos import window_to_screen, drag_point

# COLOR CONSTANTS
BLUE = imgui.color_convert_float4_to_u32((0,0,1, 1.0))
BLUE_DIMMED = imgui.color_convert_float4_to_u32((0,0,1, 0.2))
GREEN = imgui.color_convert_float4_to_u32((0,1,0, 1.0))
GREEN_DIMMED = imgui.color_convert_float4_to_u32((0,1,0, 0.2))
WHITE = imgui.color_convert_float4_to_u32((1,1,1, 1.0))
WHITE_DIMMED = imgui.color_convert_float4_to_u32((1,1,1, 0.2))

# ##### #
# TYPES #
# ##### #
from core import LineSegment, Point2D
from dataclasses import dataclass, field
from typing import Tuple, List, Optional
from typing import NewType, Callable, Dict
from typing import NewType
Point2D = NewType("Point2D", Tuple[float, float])
LineSegment = NewType("LineSegment", Tuple[Point2D, Point2D])
Radians = NewType("Radians", float)
Degrees = NewType("Degrees", float)

from typing import NamedTuple
class CameraEstimate(NamedTuple):
    position: Tuple[float, float, float]  # (x, y, z)
    pitch: float  # radians
    yaw: float    # radians
    roll: float   # radians
    fov: Optional[float] = None  # degrees, None if not estimable


Width = NewType("Width", int)
Height = NewType("Height", int)
Size = NewType("Size", Tuple[Width, Height])

class Rect(NamedTuple):
    x: int
    y: int
    width: Width
    height: Height


# ################ #
# SOLVER FUNCTIONS #
# ################ #

from expreiments.camera_spy.solver import compute_vanishing_point, estimate_focal_length, compute_camera_orientation

def _compute_camera_position(*,viewport_size:imgui.ImVec2, screen_origin:imgui.ImVec2, principal_point:imgui.ImVec2, camera_pitch:float, distance:float):
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
        screen_origin=screen_origin,
        principal_point=principal_point,
        camera_pitch=camera_pitch,
        distance=distance
    )

    return camera_pitch, camera_pos_x, camera_pos_y, camera_pos_z

from enum import StrEnum, IntEnum
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

ControlPointPairState = NewType('ControlPointPairState', Tuple[ControlPointState, ControlPointState])

# // TODO: Rename to BinaryIndex or something? Or remove if it doesnt provide type info
class ControlPointPairIndex(IntEnum):
    First = 0
    Second = 1

class ReferenceDistanceUnit(StrEnum):
  None = 'No unit',
  Millimeters = 'Millimeters',
  Centimeters = 'Centimeters',
  Meters = 'Meters',
  Kilometers = 'Kilometers',
  Inches = 'Inches',
  Feet = 'Feet',
  Miles = 'Miles'

@dataclass
class VanishingPointControlState:
    lineSegments: List[ControlPointPairState, ControlPointPairState]

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

def _relative_to_image_coords(vp:glm.vec2, imageWidth:int, imageHeight:int)->glm.vec2:
    return glm.vec2(
        vp.x * imageWidth,
        (1.0 - vp.y) * imageHeight
    )

def _computeVanishingPointsFromControlPoints(
    image_width:int,
    image_height:int, 
    controlPointStates: List[VanishingPointControlState], 
    errors
)->List[glm.vec2] | None:
    results: List[glm.vec2] = []
    for vanishingPointState in controlPointStates:
        vanishingPoint = compute_vanishing_point(vanishingPointState)
        image_coords_vanishing_point = _relative_to_image_coords(vanishingPoint, image_width, image_height)
        results.append(image_coords_vanishing_point)

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
    if abs(denominator) < 1e-9:
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

def _computeCameraRotationMatrix(Fu: glm.vec2, Fv: glm.vec2, f: float, P: Point2D)->glm.mat4:
    OFu = glm.vec3(Fu.x - P.x, Fu.y - P.y, -f)
    OFv = glm.vec3(Fv.x - P.x, Fv.y - P.y, -f)

    s1 = glm.length(OFu)
    upRc = glm.length(OFu)

    s2 = glm.length(OFv)
    vpRc = glm.normalize(OFv)

    wpRc = glm.cross(upRc, vpRc)

    M = glm.mat4()
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

DEFAULT_CAMERA_DISTANCE_SCALE = 5.0
def _computeTranslationVector(
    origin:glm.vec2, # probably relative coords?
    imageWidth: float,
    imageHeight: float,
    horizontalFieldOfView: float,
    principalPoint: glm.vec2 # probably relative coords?
  )->glm.vec3:
    # The 3D origin in image plane coordinates
    origin = _relative_to_image_coords(origin, imageWidth, imageHeight)

    k = math.tan(0.5 * horizontalFieldOfView)
    origin3D = glm.vec3(
      k * (origin.x - principalPoint.x),
      k * (origin.y - principalPoint.y),
      -1
    ) * DEFAULT_CAMERA_DISTANCE_SCALE

    return origin3D

def _computeCameraParameters(
    result: SolverResult,
    controlPoints: ControlPointsStateBase,
    settings: CalibrationSettingsBase,
    principalPoint: Point2D,
    vp1: Point2D,
    vp2: Point2D,
    relativeFocalLength: float,
    imageWidth: float,
    imageHeight: float
  )->CameraParameters | None:

    cameraParameters = CameraParameters(
      principalPoint=glm.vec2(0,0),
      viewTransform= glm.identity(4),
      cameraTransform = glm.identity(4),
      horizontalFieldOfView= 0.0,
      verticalFieldOfView= 0.0,
      vanishingPoints= [glm.vec2(0,0), glm.vec2(0,0), glm.vec2(0,0)],
      vanishingPointAxes= [Axis.NegativeX, Axis.NegativeX, Axis.NegativeX],
      relativeFocalLength= 0.0,
      imageWidth=imageWidth,
      imageHeight=imageHeight
    )

    # Assing vanishing point axes
    axisAssignmentMatrix = glm.eye(4)
    row1 = _axisVector(settings.firstVanishingPointAxis)
    row2 = _axisVector(settings.secondVanishingPointAxis)
    row3 = row1.cross(row2)
    axisAssignmentMatrix[0][0] = row1.x
    axisAssignmentMatrix[0][1] = row1.y
    axisAssignmentMatrix[0][2] = row1.z
    axisAssignmentMatrix[1][0] = row2.x
    axisAssignmentMatrix[1][1] = row2.y
    axisAssignmentMatrix[1][2] = row2.z
    axisAssignmentMatrix[2][0] = row3.x
    axisAssignmentMatrix[2][1] = row3.y
    axisAssignmentMatrix[2][2] = row3.z

    if math.abs(1 - axisAssignmentMatrix.determinant) > 1e-7:
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
    if math.abs(glm.determinant(cameraRotationMatrix) - 1) > 1e-7:
      raise Exception('Invalid vanishing point configuration. Rotation determinant ' + cameraRotationMatrix.determinant.toFixed(5))

    cameraParameters.viewTransform = axisAssignmentMatrix * cameraRotationMatrix
    
    origin3D = _computeTranslationVector(
      controlPoints.origin,
      settings,
      imageWidth,
      imageHeight,
      cameraParameters.horizontalFieldOfView,
      cameraParameters.principalPoint
    )

    # TODO: get rid of camera parameters altogether. either replace with Camera or use attributes directly
    cameraParameters.viewTransform[0][3] = origin3D.x
    cameraParameters.viewTransform[1][3] = origin3D.y
    cameraParameters.viewTransform[2][3] = origin3D.z

    cameraParameters.cameraTransform = glm.inverse(cameraParameters.viewTransform)

    return cameraParameters

def _computeSecondVanishingPoint(
        Fu: Point2D, 
        f: float, 
        P: Point2D, 
        horizonDir: Point2D
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

    Fup = glm.vec2(Fu.x - P.x, Fu.y - P.y)

    k = -(Fup.x * Fup.x + Fup.y * Fup.y + f * f) / (Fup.x * horizonDir.x + Fup.y * horizonDir.y)
    Fv = glm.vec2(
        x=Fup.x + k * horizonDir.x + P.x,
        y=Fup.y + k * horizonDir.y + P.y
    )
    return Fv

def solve1VP(
        absoluteFocalLength, 
        sensorWidth, 
        sensorHeight, 
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
    sensorAspectRatio = sensorWidth / sensorHeight
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

    # Get the principal point
    principalPoint = glm.vec2(0,0)
    # TODO: Implement principal point calculation if manually set
    # ...
    # is principal point in image coordinates?

    #/Compute the horizon direction
    horizonDirection = glm.vec2(1, 0) # flat by default
    horizonStart = _relative_to_image_coords(horizonDirection, image_width, image_height)

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
      inputVanishingPoints![0],
      secondVanishingPoint,
      relativeFocalLength,
      imageWidth,
      imageHeight
    )

# ########## #
# INITIALIZE #
# ########## #

# ModernGL context and framebuffer
scene_renderer = SceneLayer()
ctx: moderngl.Context|None = None
fbo: moderngl.Framebuffer|None = None

# Parameters
horizon = 300.0
vanishing_lines = [
        [

    ],[

    ],[
        [imgui.ImVec2(145, 480), imgui.ImVec2(330, 330)],
        [imgui.ImVec2(650, 460), imgui.ImVec2(508, 343)]
    ]
]

use_vanishing_lines = [False, False, False]
axis_names = ('X', 'Y', 'Z')
screen_origin = imgui.ImVec2(400, 400)
fov:Degrees = 60.0
distance = 5.0

# ######### #
# MAIN LOOP #
# ######### #
def gui():
    global ctx, fbo
    # Camera Calibration parameters
    global distance
    global screen_origin
    global horizon
    global fov
    global vanishing_lines, use_vanishing_lines

    imgui.text("Camera Spy")
    if imgui.begin_child("3d_viewport", imgui.ImVec2(0, 0)):
        # Get ImGui child window dimensions and position
        size = imgui.get_content_region_avail()
        pos = imgui.get_cursor_screen_pos()

        if ctx is None:
            logger.info("Initializing ModernGL context...")
            ctx = moderngl.create_context()
            
            scene_renderer.setup(ctx)
        
        ## Create or resize framebuffer if needed
        dpi = imgui.get_io().display_framebuffer_scale
        fb_width = int(size.x * dpi.x)
        fb_height = int(size.y * dpi.y)
        
        
        if fbo is None or fbo.width != fb_width or fbo.height != fb_height:
            if fbo is not None:
                fbo.release()
            
            # Create color texture
            color_texture = ctx.texture((fb_width, fb_height), 4, dtype='f1')
            color_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
            
            # Create depth renderbuffer
            depth_buffer = ctx.depth_renderbuffer((fb_width, fb_height))
            
            # Create framebuffer
            fbo = ctx.framebuffer(
                color_attachments=[color_texture],
                depth_attachment=depth_buffer
            )
            
            logger.info(f"Created framebuffer: {fb_width}x{fb_height}")
        
        
        # parameters
        camera = Camera()
        camera.setAspectRatio(size.x / size.y)
        camera.setFOV(fov)

        # Compute Camera from parameters
        for i, in_use in enumerate(use_vanishing_lines):
            _, use_vanishing_lines[i] = imgui.checkbox(f"use {axis_names[i]} axes", in_use)

        match use_vanishing_lines:
            case (False, False, False):
                # parameters
                _, horizon = drag_horizon(horizon, WHITE_DIMMED)
                _, fov = imgui.slider_float("fov", fov, 20.0, 120.0, "%.2f")
                _, distance = imgui.drag_float("distance", distance, 0.1, 0.1, 20.0, "%.2f")
                _, screen_origin = drag_point("origin###origin", screen_origin)
                principal_point = imgui.ImVec2(size.x / 2, size.y / 2)

                # Solve no Axes
                camera_pitch, camera_pos_x, camera_pos_y, camera_pos_z = solve_no_axis(
                    horizon=horizon,
                    viewport_size=size,
                    screen_origin=screen_origin,
                    fov=fov,
                    principal_point=principal_point,
                    distance=distance,
                )

                camera.transform = _build_camera_transform(camera_pitch, camera_pos_x, camera_pos_y, camera_pos_z)

            case (False, False, True):
                # parameters
                principal_point = imgui.ImVec2(size.x / 2, size.y / 2)
                _, vanishing_lines[2] = drag_axes("Z", vanishing_lines[2], BLUE)

                # calculate vanishing point
                vp_z = imgui.ImVec2(compute_vanishing_point([axis for axis in vanishing_lines[2]]))
                
                # draw vanishing point
                draw_list = imgui.get_window_draw_list()
                draw_list.add_circle_filled(window_to_screen(vp_z), 5, BLUE)
                draw_list.add_text(window_to_screen(vp_z) + imgui.ImVec2(5, -5),  BLUE, f"VP{2} ({vp_z.x:.0f},{vp_z.y:.0f})")

                # draw lines to vanishing point
                for axis in vanishing_lines[2]:
                    closest_point = closest_point_line_segment(vp_z, axis)
                    imgui.get_window_draw_list().add_line(window_to_screen(closest_point), window_to_screen(vp_z), BLUE_DIMMED, 1)

                # calc yaw from y axes.
                horizon = vp_z.y

                camera_pitch = _estimate_pitch_from_horizon(horizon, principal_point=principal_point, size=size, fov=fov)
                
                # compute yaw from vanishing point?
                vp_z_ndc_x = (vp_z.x - principal_point.x) / (size.x / 2.0)
                aspect = size.x / size.y
                tan_half_fov = math.tan(math.radians(fov) / 2.0)
                tan_half_fov_x = tan_half_fov * aspect
                camera_yaw = math.atan(vp_z_ndc_x * tan_half_fov_x)
                imgui.text(f"Camera yaw: {math.degrees(camera_yaw):.2f}° (from Z VP)")

                # compute camera position
                camera_pos_x, camera_pos_y, camera_pos_z = _compute_camera_position(
                    viewport_size=size,
                    screen_origin=screen_origin,
                    principal_point=principal_point,
                    camera_pitch=camera_pitch,
                    distance=distance
                )

                # build transform
                camera.transform = _build_camera_transform(camera_pitch, camera_pos_x, camera_pos_y, camera_pos_z)
                

            case _:
                imgui.text("Only Z axis supported for now")
                return
            

        # Update GL viewport
        display_size = imgui.get_io().display_size
        dpi = imgui.get_io().display_framebuffer_scale
        gl_size = display_size * dpi
        ctx.viewport = (0, 0, gl_size.x, gl_size.y)

        # Render to framebuffer
        fbo.use()
        fbo.clear(0.1, 0.1, 0.1, 0.0)  # Clear with dark gray background
        ctx.enable(moderngl.DEPTH_TEST)
        scene_renderer.render(camera)
        ctx.screen.use() # Restore default framebuffer
        
        # Display the framebuffer texture in ImGui
        texture = fbo.color_attachments[0] # Get texture from framebuffer
        texture_ref = imgui.ImTextureRef(texture.glo)
        
        imgui.set_cursor_pos(imgui.ImVec2(0,0))
        imgui.image(
            texture_ref,  # OpenGL texture ID
            imgui.ImVec2(size.x, size.y),
            uv0=imgui.ImVec2(0, 1),  # Flip vertically (OpenGL texture is bottom-up)
            uv1=imgui.ImVec2(1, 0)
        )

    imgui.end_child()

    
    # camera.setPosition(glm.vec3(5, 5, 5))
    # camera.lookAt(glm.vec3(0,0,0))
    # scene_renderer.render(camera)


if __name__ == "__main__":
    immapp.run(gui, window_title="ImGui Bundle - 2D Points & 3D Scene", window_size=(800, 800))