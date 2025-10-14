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
from pylive.render_engine.render_layers import GridLayer, RenderLayer, AxesLayer
import OpenGL.GL as gl
import glm


class SceneLayer(RenderLayer):
    def __init__(self):
        super().__init__()
        self.initialized = False
        self.grid = GridLayer()
        self.axes = AxesLayer()

    def setup(self, ctx:moderngl.Context):
        self.grid.setup(ctx)
        self.axes.setup(ctx)
        super().setup(ctx)

    def destroy(self):
        if self.grid:
            self.grid.destroy()
            self.grid = None
        if self.axes:
            self.axes.destroy()
            self.axes = None
        return super().destroy()
    
    def render(self, camera:Camera):
        self.grid.render(view=camera.viewMatrix(), projection=camera.projectionMatrix())
        self.axes.render(view=camera.viewMatrix(), projection=camera.projectionMatrix())
        super().render()


# ########### #
# GUI helpers #
# ########### #
from imgui_bundle import imgui, immapp
from gizmos import drag_line, drag_horizon
from utils.geo import closest_point_on_line_segment
from gizmos import window_to_screen, drag_point

# COLOR CONSTANTS
RED = imgui.color_convert_float4_to_u32((1,0,0, 1.0))
RED_DIMMED = imgui.color_convert_float4_to_u32((1,0,0, 0.2))
BLUE = imgui.color_convert_float4_to_u32((0,0,1, 1.0))
BLUE_DIMMED = imgui.color_convert_float4_to_u32((0,0,1, 0.2))
GREEN = imgui.color_convert_float4_to_u32((0,1,0, 1.0))
GREEN_DIMMED = imgui.color_convert_float4_to_u32((0,1,0, 0.2))
WHITE = imgui.color_convert_float4_to_u32((1,1,1, 1.0))
WHITE_DIMMED = imgui.color_convert_float4_to_u32((1,1,1, 0.2))

# ##### #
# TYPES #
# ##### #
from typing import Tuple, List, Optional
from typing import NewType, Callable, Dict

Radians = NewType("Radians", float)
Degrees = NewType("Degrees", float)

from typing import NamedTuple
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

from my_solver import solve_no_axis

import fspy_solver_functional as fspy

# Helper function to convert ImGui coordinates to relative [0,1] coordinates
def imgui_to_relative(imgui_point: imgui.ImVec2, image_width, image_height) -> glm.vec2:
    aspect_ratio = image_width / image_height
    return glm.vec2(
        imgui_point.x / image_width * aspect_ratio - (aspect_ratio-1) / 2,
        imgui_point.y / image_height
    )

# Convert vanishing lines from ImGui coordinates to relative coordinates
def vanishing_lines_to_relative(vanishing_lines: List[fspy.LineSegmentType], image_width, image_height) -> List[fspy.LineSegmentType]:
    relative_lines = []
    for line in vanishing_lines:
        relative_line = (
            imgui_to_relative(line[0], image_width, image_height),
            imgui_to_relative(line[1], image_width, image_height)
        )
        relative_lines.append(relative_line)
    return relative_lines
    

# ########## #
# INITIALIZE #
# ########## #

# ModernGL context and framebuffer
scene_renderer = SceneLayer()
moderngl_ctx: moderngl.Context|None = None
fbo: moderngl.Framebuffer|None = None


# Parameters
axis_names = ('X', 'Y', 'Z')
vanishing_lines: List[Tuple[fspy.LineSegmentType, ...]] = [
    [
        [imgui.ImVec2(280, 340), imgui.ImVec2(520, 360)],
        [imgui.ImVec2(230, 480), imgui.ImVec2(560, 460)]
    ],
    [
        [imgui.ImVec2(480, 500), imgui.ImVec2(580, 270)],
        [imgui.ImVec2(315, 505), imgui.ImVec2(220, 270)]
    ],
    [
        [imgui.ImVec2(280, 520), imgui.ImVec2(310, 300)],
        [imgui.ImVec2(520, 500), imgui.ImVec2(480, 330)]
    ]
]
use_vanishing_lines = [True, False, True]

horizon_height: float = 300.0
default_fov:Degrees = 60.0
screen_origin = imgui.ImVec2(400, 400)
principal_point_ctrl = imgui.ImVec2(400, 400)
DEFAULT_CAMERA_DISTANCE_SCALE = 5.0
scene_scale = DEFAULT_CAMERA_DISTANCE_SCALE
# ######### #
# MAIN LOOP #
# ######### #

camera = Camera()
def gui():
    global camera
    global moderngl_ctx, fbo
    # Camera Calibration parameters
    global screen_origin
    global horizon_height
    global default_fov
    global vanishing_lines, use_vanishing_lines
    global principal_point_ctrl
    global scene_scale

    imgui.text("Camera Spy")
    if imgui.begin_child("3d_viewport", imgui.ImVec2(0, 0)):
        # Get ImGui child window dimensions and position
        widget_size = imgui.get_content_region_avail()
        pos = imgui.get_cursor_screen_pos()
       
        
        # parameters
        
        camera.setAspectRatio(widget_size.x / widget_size.y)
        camera.setFoVY(default_fov)

        # Compute Camera from parameters
        for i, in_use in enumerate(use_vanishing_lines):
            _, use_vanishing_lines[i] = imgui.checkbox(f"use {axis_names[i]} axes", in_use)

        _, scene_scale = imgui.slider_float("scene_scale", scene_scale, 1.0, 100.0, "%.2f")
        match use_vanishing_lines:
            case (False, False, False):
                # parameters
                _, horizon_height = drag_horizon(horizon_height, WHITE_DIMMED)
                _, default_fov = imgui.slider_float("fov", default_fov, 20.0, 120.0, "%.2f")
                _, screen_origin = drag_point("origin###origin", screen_origin)
                principal_point_ctrl = imgui.ImVec2(widget_size.x / 2, widget_size.y / 2)

                # Solve no Axes
                camera_pitch, camera_pos_x, camera_pos_y, camera_pos_z = solve_no_axis(
                    horizon=horizon_height,
                    viewport_size=widget_size,
                    screen_origin=screen_origin,
                    fov=default_fov,
                    principal_point=imgui_to_relative(principal_point_ctrl, widget_size.x, widget_size.y),
                    distance=scene_scale,
                )

                camera.transform = _build_camera_transform(camera_pitch, camera_pos_x, camera_pos_y, camera_pos_z)

            case (False, False, True):
                # # parameters
                principal_point_ctrl = imgui.ImVec2(widget_size.x / 2, widget_size.y / 2)
                _, principal_point_ctrl = drag_point("principal_point###principal_point", principal_point_ctrl)
                for i, axis in enumerate(vanishing_lines[2]):
                    _, vanishing_lines[2][i] = drag_line(f"Z{i}", axis, BLUE)
                _, screen_origin = drag_point("origin###origin", screen_origin)
            

                # Create proper horizon direction from the horizon Y coordinate
                # Instead of two points on a horizontal line, create a direction vector
                horizon_start = glm.vec2(0.0, horizon_height / widget_size.y)
                horizon_end = glm.vec2(1.0, horizon_height / widget_size.y)
                
                # Debug: Print coordinate conversions
                imgui.text(f"Screen origin: ({screen_origin.x:.0f}, {screen_origin.y:.0f})")
                relative_screen_origin = imgui_to_relative(screen_origin, widget_size.x, widget_size.y)
                imgui.text(f"  relative : ({relative_screen_origin.x:.2f}, {relative_screen_origin.y:.2f})")
                imgui.text(f"Viewport size: ({widget_size.x:.0f}, {widget_size.y:.0f})")
                imgui.text(f"Horizon Y: {horizon_height:.1f}")
                imgui.text(f"FoV: {default_fov:.1f}°")
                imgui.separator()
                try:
                    result = fspy.solve1VP(
                        image_width =                 int(widget_size.x),
                        image_height =                int(widget_size.y),
                        # control points              
                        first_vanishing_lines =       vanishing_lines_to_relative(vanishing_lines[2], widget_size.x, widget_size.y),
                        horizon_line_ctrl =           (horizon_start, horizon_end),
                        principal_point_ctrl =        imgui_to_relative(principal_point_ctrl, widget_size.x, widget_size.y),
                        originPoint =                 imgui_to_relative(screen_origin, widget_size.x, widget_size.y),
                        # settings                    
                        fovy =                        math.radians(default_fov),
                        sensor_size =                 (36, 24),
                        first_vanishing_lines_axis =  fspy.Axis.PositiveZ,
                        second_vanishing_lines_axis = fspy.Axis.PositiveX,
                        principal_point_mode  =       'Default',
                        scale =                       scene_scale
                    )
                    
                    camera.transform = glm.inverse(result['view_transform'])
                    
                except Exception as e:
                    from textwrap import wrap
                    imgui.push_style_color(imgui.Col_.text, (1.0, 0.2, 0.2, 1.0))
                    imgui.text_wrapped(f"fspy error: {pformat(e)}")
                    import traceback
                    traceback.print_exc()
                    imgui.pop_style_color()

            case [True, False, True] | [True, True, True]:
                for i, axis in enumerate(vanishing_lines[0]):
                    _, vanishing_lines[0][i] = drag_line(f"X{i}", axis, RED)

                for i, axis in enumerate(vanishing_lines[2]):
                    _, vanishing_lines[2][i] = drag_line(f"Z{i}", axis, BLUE)

                _, screen_origin = drag_point("origin###origin", screen_origin)

                _, principal_point_ctrl = drag_point("principal_point###principal_point", principal_point_ctrl)

                # Convert the correct vanishing lines for each axis
                relative_vanishing_lines =        vanishing_lines_to_relative(vanishing_lines[2], widget_size.x, widget_size.y) # Z-axis (first VP)
                relative_second_vanishing_lines = vanishing_lines_to_relative(vanishing_lines[0], widget_size.x, widget_size.y) # X-axis (second VP)

                UseThirdAxisForPrincipalPoint = use_vanishing_lines[1]
                relative_third_vanishing_lines = []
                if UseThirdAxisForPrincipalPoint:
                    for i, axis in enumerate(vanishing_lines[1]):
                        _, vanishing_lines[1][i] = drag_line(f"Y{i}", axis, GREEN)
                    relative_third_vanishing_lines = vanishing_lines_to_relative(vanishing_lines[1], widget_size.x, widget_size.y)  # Y-axis (third VP)
                else:
                    principal_point_ctrl = imgui.ImVec2(widget_size.x / 2, widget_size.y / 2)
                    
                try:
                    result = fspy.solve2VP(
                        image_width =                 int(widget_size.x),
                        image_height =                int(widget_size.y),
                        # control points
                        origin_relative =                 imgui_to_relative(screen_origin, widget_size.x, widget_size.y),
                        first_vanishing_lines_relative =       relative_vanishing_lines,
                        second_vanishing_lines_relative =      relative_second_vanishing_lines,
                        third_vanishing_lines_relative =       relative_third_vanishing_lines, # Used to determine principal point if present
                        principal_point_relative =          glm.vec2(0.5, 0.5),  # Center in relative coords [0,1]
                        # settings
                        sensor_size =                 (36, 24),
                        first_vanishing_lines_axis =  fspy.Axis.PositiveZ,
                        second_vanishing_lines_axis = fspy.Axis.PositiveX,
                        principal_point_mode =        'Default' if not UseThirdAxisForPrincipalPoint else 'FromThirdVanishingPoint',
                        quad_mode_enabled =           False,
                        scale =                       scene_scale
                    )

                    camera.transform = glm.inverse(result['view_transform'])
                    camera.setFoVY(math.degrees(result['fovy']))

                except Exception as e:
                    from textwrap import wrap
                    imgui.push_style_color(imgui.Col_.text, (1.0, 0.2, 0.2, 1.0))
                    imgui.text_wrapped(f"fspy error: {pformat(e)}")
                    import traceback
                    traceback.print_exc()
                    imgui.pop_style_color()

            case _:
                imgui.text("Only Z axis supported for now")
                
        # camera.transform = camera_parameters.cameraTransform
        imgui.text_wrapped(f"camera.getPosition(): {pformat(camera.getPosition())}")

        ############################
        # Render 3D Scene in ImGui #
        ############################
        if moderngl_ctx is None:
            logger.info("Initializing ModernGL context...")
            moderngl_ctx = moderngl.create_context()
            
            scene_renderer.setup(moderngl_ctx)
            
        # Update GL viewport
        imgui.text_wrapped(f"widget size: {int(widget_size.x)}x{int(widget_size.y)}")
        dpi = imgui.get_io().display_framebuffer_scale
        imgui.text_wrapped(f"dpi: {dpi}")
        gl_size = widget_size * dpi
        imgui.text_wrapped(f"gl_size: {int(gl_size.x)}x{int(gl_size.y)}")
        moderngl_ctx.viewport = (0, 0, gl_size.x, gl_size.y)

        ## Create or resize framebuffer if needed
        dpi = imgui.get_io().display_framebuffer_scale
        fbo_width = int(widget_size.x * dpi.x)
        fbo_height = int(widget_size.y * dpi.y)
        
        if fbo is None or fbo.width != fbo_width or fbo.height != fbo_height:
            if fbo is not None:
                fbo.release()
            
            # Create color texture
            color_texture = moderngl_ctx.texture((fbo_width, fbo_height), 4, dtype='f1')
            color_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
            
            # Create depth renderbuffer
            depth_buffer = moderngl_ctx.depth_renderbuffer((fbo_width, fbo_height))
            
            # Create framebuffer
            fbo = moderngl_ctx.framebuffer(
                color_attachments=[color_texture],
                depth_attachment=depth_buffer
            )
            
            logger.info(f"Created framebuffer: {fbo_width}x{fbo_height}")
        imgui.text_wrapped(f"fbo size: {fbo_width}x{fbo_height}")

        # Render to framebuffer
        fbo.use()
        fbo.clear(0.1, 0.1, 0.1, 0.0)  # Clear with dark gray background
        moderngl_ctx.enable(moderngl.DEPTH_TEST)
        scene_renderer.render(camera)
        moderngl_ctx.screen.use() # Restore default framebuffer
        
        # Display the framebuffer texture in ImGui
        texture = fbo.color_attachments[0] # Get texture from framebuffer
        texture_ref = imgui.ImTextureRef(texture.glo)
        
        imgui.set_cursor_pos(imgui.ImVec2(0,0))
        imgui.image(
            texture_ref,  # OpenGL texture ID
            imgui.ImVec2(widget_size.x, widget_size.y),
            uv0=imgui.ImVec2(0, 1),  # Flip vertically (OpenGL texture is bottom-up)
            uv1=imgui.ImVec2(1, 0)
        )

    imgui.end_child()


if __name__ == "__main__":
    immapp.run(gui, window_title="ImGui Bundle - 2D Points & 3D Scene", window_size=(9*75, 9*75))