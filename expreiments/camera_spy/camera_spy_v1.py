import logging
import string
logger = logging.getLogger(__name__)

import math
import numpy as np
from pylive.render_engine.camera import Camera
from pprint import pformat

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

from my_solver import (
    compute_vanishing_point, 
    estimate_focal_length, 
    compute_camera_orientation, 
    _build_camera_transform,
    _estimate_pitch_from_horizon,
    _compute_camera_position
)

from fspy_solver import solve1VP
from my_solver import solve_no_axis

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
camera = Camera()
def gui():
    global camera
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
                # # parameters
                # principal_point = imgui.ImVec2(size.x / 2, size.y / 2)
                _, vanishing_lines[2] = drag_axes("Z", vanishing_lines[2], BLUE)
                _, screen_origin = drag_point("origin###origin", screen_origin)

                import fspy_solver as fspy
                def fov_to_focal_length(fov_x, *, sensor:tuple[float, float]) -> float:
                    # Return focal length in millimetres for a given horizontal FOV (degrees)
                    # sensor is (sensor_width_mm, sensor_height_mm)
                    # TODO: add a flag if fov is vertical or horizontal
                    return (0.5 * sensor[0]) / math.tan(math.radians(fov_x) / 2.0)
                
                # Helper function to convert ImGui coordinates to relative [0,1] coordinates
                def imgui_to_relative(imgui_point: imgui.ImVec2, viewport_size: imgui.ImVec2) -> glm.vec2:
                    return glm.vec2(
                        imgui_point.x / viewport_size.x,
                        imgui_point.y / viewport_size.y
                    )
                
                # Convert vanishing lines from ImGui coordinates to relative coordinates
                relative_vanishing_lines = []
                for line in vanishing_lines[2]:
                    relative_line = [
                        imgui_to_relative(line[0], size),
                        imgui_to_relative(line[1], size)
                    ]
                    relative_vanishing_lines.append(relative_line)
                
                # Create proper horizon direction from the horizon Y coordinate
                # Instead of two points on a horizontal line, create a direction vector
                horizon_start = glm.vec2(0.0, horizon / size.y)
                horizon_end = glm.vec2(1.0, horizon / size.y)
                
                focal_length = fov_to_focal_length(fov, sensor=(36, 24))  # Use actual fov variable
                
                # Debug: Print coordinate conversions
                imgui.text(f"Screen origin: ({screen_origin.x:.1f}, {screen_origin.y:.1f})")
                imgui.text(f"Viewport size: ({size.x:.1f}, {size.y:.1f})")
                origin_relative = imgui_to_relative(screen_origin, size)
                imgui.text(f"Origin relative: ({origin_relative.x:.3f}, {origin_relative.y:.3f})")
                imgui.text(f"Horizon Y: {horizon:.1f} -> relative: {horizon / size.y:.3f}")
                imgui.text(f"FOV: {fov:.1f}° -> focal length: {focal_length:.1f}mm")
                imgui.separator()
                try:
                    result:fspy.SolverResult = fspy.solve1VP(
                        settingsBase=fspy.CalibrationSettingsBase(
                            referenceDistanceUnit=fspy.ReferenceDistanceUnit.Meters,
                            referenceDistance=1.0,
                            referenceDistanceAxis=fspy.Axis.PositiveZ,
                            cameraData=fspy.CameraData(
                                customSensorWidth=36,
                                customSensorHeight=24
                            ),
                            firstVanishingPointAxis=fspy.Axis.PositiveZ,
                            secondVanishingPointAxis=fspy.Axis.PositiveX,
                        ),
                        settings1VP=fspy.CalibrationSettings1VP(
                            principalPointMode=fspy.PrincipalPointMode1VP.Default,
                            absoluteFocalLength=focal_length, # Use calculated focal length from actual fov
                        ),
                        controlPointsBase=fspy.ControlPointsStateBase(
                            principalPoint=glm.vec2(0.5, 0.5),  # Center in relative coords [0,1]
                            origin=imgui_to_relative(screen_origin, size),  # Convert to relative coords
                            referenceDistanceAnchor=imgui_to_relative(imgui.ImVec2(screen_origin.x + 100, screen_origin.y), size),
                            firstVanishingPoint=fspy.VanishingPointControlState(
                                lineSegments=relative_vanishing_lines  # Use converted relative coordinates
                            ),
                            referenceDistanceHandleOffsets=(0,0)
                        ),
                        controlPoints1VP=fspy.ControlPointsState1VP(
                            horizon=(horizon_start, horizon_end)  # Use properly defined horizon points
                        ),
                        image_width=int(size.x),
                        image_height=int(size.y)
                    )
                    camera.transform = result.cameraParameters.cameraTransform
                    
                except Exception as e:
                    from textwrap import wrap
                    imgui.push_style_color(imgui.Col_.text, (1.0, 0.2, 0.2, 1.0))
                    imgui.text_wrapped(f"fspy error: {pformat(e)}")
                    imgui.pop_style_color()

            case _:
                imgui.text("Only Z axis supported for now")
                
        # camera.transform = camera_parameters.cameraTransform
        imgui.text_wrapped(f"camera.getPosition(): {pformat(camera.getPosition())}")
            
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