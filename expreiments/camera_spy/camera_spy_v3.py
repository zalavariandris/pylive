import logging
import string

logger = logging.getLogger(__name__)

import math
import numpy as np
from pylive.render_engine.camera import Camera
from pprint import pformat

from imgui_bundle import imgui, immapp
from gizmos import drag_line, drag_horizon
from utils.geo import closest_point_line_segment
from gizmos import window_to_screen, drag_point

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

def render_scene_to_image_ref(moderngl_ctx, camera:Camera, scene_layer:RenderLayer, fbo: moderngl.Framebuffer, widget_size: glm.vec2) -> imgui.ImTextureRef:
    ############################
    # Render 3D Scene in ImGui #
    ############################
        
    # Update GL viewport
    dpi = imgui.get_io().display_framebuffer_scale
    gl_size = widget_size * dpi
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
    scene_layer.render(camera)
    moderngl_ctx.screen.use() # Restore default framebuffer
    
    # Display the framebuffer texture in ImGui
    texture = fbo.color_attachments[0] # Get texture from framebuffer
    texture_ref = imgui.ImTextureRef(texture.glo)
    return texture_ref


# ########### #
# GUI helpers #
# ########### #

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

# ########## #
# INITIALIZE #
# ########## #

# ModernGL context and framebuffer
scene_layer = SceneLayer()
moderngl_ctx: moderngl.Context|None = None
fbo: moderngl.Framebuffer|None = None

# ########## #
# Parameters #
# ########## #

# Control Points
origin_pixel = glm.vec2(400, 400)
principal_point_pixel = glm.vec2(400, 400)
first_vanishing_point_pixel = glm.vec2(100, 250)
second_vanishing_point_pixel = glm.vec2(800, 250)

axis_names = ('Z', 'X', 'Y')

# Z axis by defaul
first_vanishing_lines_pixel:Tuple[fspy.LineSegmentType] = [
    [glm.vec2(280, 520), glm.vec2(310, 300)],
    [glm.vec2(520, 500), glm.vec2(480, 330)]
]

# X axis by default
second_vanishing_lines_pixel:Tuple[fspy.LineSegmentType] = [
    [glm.vec2(280, 340), glm.vec2(520, 360)],
    [glm.vec2(230, 480), glm.vec2(560, 460)]
]

# Y axis by default
third_vanishing_lines_pixel:Tuple[fspy.LineSegmentType] = [
    [glm.vec2(480, 500), glm.vec2(580, 270)],
    [glm.vec2(315, 505), glm.vec2(220, 270)]
]

# parameers
scene_scale = 5.0
# fovy:Radians = Radians(60.0 * math.pi / 180.0) # vertical fov in radians
focal_length_pixel = 500.0
# Options
from enum import IntEnum
class PrincipalPointMode(IntEnum):
    Default = 0
    Manual = 1
    FromThirdVanishingPoint = 2
principal_point_mode: PrincipalPointMode = PrincipalPointMode.Default
first_axis = fspy.Axis.PositiveZ
second_axis = fspy.Axis.PositiveX
quad_mode:bool = False
horizon_roll:float = 0.0

# Camera
camera = Camera()

class SolverMode(IntEnum):
    OneVP = 0
    TwoVP = 1

SOLVER_MODE = SolverMode.OneVP

# ######### #
# MAIN LOOP #
# ######### #
import itertools
def gui():
    # renderer
    global moderngl_ctx, fbo

    # solver mode
    global SOLVER_MODE

    # Control Points
    global origin_pixel
    global principal_point_pixel
    global first_vanishing_point_pixel
    global second_vanishing_point_pixel

    global first_vanishing_lines_pixel
    global second_vanishing_lines_pixel
    global third_vanishing_lines_pixel

    # parameters
    global focal_length_pixel
    global scene_scale
    global horizon_roll
    
    # options
    global principal_point_mode
    global first_axis, second_axis
    global quad_mode
    
    # Camera
    global camera

    imgui.text("Camera Spy")
    _, SOLVER_MODE = imgui.combo("Solver Mode", SOLVER_MODE, ["1VP", "2VP"])
    
    import my_solver_v3 as my_solver
    from gizmos import draw


    match SOLVER_MODE:
        case SolverMode.OneVP:
            widget_size = imgui.get_content_region_avail()
            image_width, image_height = int(widget_size.x), int(widget_size.y)
            # Parameters
            _, first_axis = imgui.combo("first axis", first_axis, ["PositiveX", "NegativeX", "PositiveY", "NegativeY", "PositiveZ", "NegativeZ"])
            _, scene_scale = imgui.slider_float("scene_scale", scene_scale, 1.0, 100.0, "%.2f")
            _, focal_length_pixel = imgui.slider_float("focal_length_pixel", focal_length_pixel, 1.0, image_height, "%.2f")

            _, horizon_roll = imgui.slider_float("horizon roll", horizon_roll, 1.0, image_height, "%.2f")

            
            if imgui.begin_child("3d_viewport", widget_size):
                # Control Points
                for i, axis in enumerate(first_vanishing_lines_pixel):
                    changed, new_line = drag_line(f"Z{i}", axis, BLUE)
                    first_vanishing_lines_pixel[i] = new_line

                changed, second_vanishing_lines_pixel[0] = drag_line(f"Horizon{i}", second_vanishing_lines_pixel[0], RED)

                _, principal_point_pixel = drag_point("principal_point", principal_point_pixel)
                principal_point_pixel = glm.vec2(widget_size.x / 2, widget_size.y / 2)
                # _, first_vanishing_point_pixel = drag_point("first_vanishing_point", first_vanishing_point_pixel)
                _, origin_pixel = drag_point("origin", origin_pixel)

                try:
                    from my_solver_v3 import solve1vp
                    view_orientation_matrix, position = solve1vp(
                        image_width=int(widget_size.x),
                        image_height=int(widget_size.y),
                        principal_point_pixel=principal_point_pixel,
                        origin_pixel=origin_pixel,
                        first_vanishing_lines_pixel=first_vanishing_lines_pixel,
                        second_vanishing_line_pixel=second_vanishing_lines_pixel[0],
                        focal_length_pixel=focal_length_pixel,
                        first_axis=first_axis,
                        second_axis=second_axis,
                        scene_scale=scene_scale
                    )

                    view_translate_transform = glm.translate(glm.mat4(1.0), position)
                    view_rotation_transform = glm.mat4(view_orientation_matrix)
                    view_transform= view_rotation_transform * view_translate_transform
                    camera.transform = glm.inverse(view_transform)
                    camera.setAspectRatio(widget_size.x / widget_size.y)
                    fovy = math.atan(image_height / 2 / focal_length_pixel) * 2
                    camera.setFoVY(math.degrees(fovy))

                    # Roll the camera based on the horizon line projected to 3D
                    roll_matrix = my_solver.compute_roll_matrix(
                        image_width, 
                        image_height, 
                        second_vanishing_lines_pixel[0],
                        projection_matrix=camera.projectionMatrix(),
                        view_matrix=camera.viewMatrix()
                    )
                    camera.transform = glm.inverse(roll_matrix) * camera.transform  


                except Exception as e:
                    from textwrap import wrap
                    imgui.push_style_color(imgui.Col_.text, (1.0, 0.2, 0.2, 1.0))
                    imgui.text_wrapped(f"fspy error: {pformat(e)}")
                    import traceback
                    traceback.print_exc()
                    imgui.pop_style_color()

                # Render Scene
                if moderngl_ctx is None:
                    logger.info("Initializing ModernGL context...")
                    moderngl_ctx = moderngl.create_context()
                    scene_layer.setup(moderngl_ctx)
                image_ref = render_scene_to_image_ref(moderngl_ctx, camera, scene_layer, fbo, widget_size)
                imgui.set_cursor_pos(imgui.ImVec2(0,0))
                imgui.image(image_ref,imgui.ImVec2(widget_size.x, widget_size.y))

            imgui.end_child()

        case SolverMode.TwoVP:
            # Parameters
            _, first_axis = imgui.combo("first axis", first_axis, ["PositiveX", "NegativeX", "PositiveY", "NegativeY", "PositiveZ", "NegativeZ"])
            _, second_axis = imgui.combo("second axis", second_axis, ["PositiveX", "NegativeX", "PositiveY", "NegativeY", "PositiveZ", "NegativeZ"])
            _, scene_scale = imgui.slider_float("scene_scale", scene_scale, 1.0, 100.0, "%.2f")
            _, principal_point_mode = imgui.combo("principal point mode", principal_point_mode, ["Default", "Manual", "FromThirdVanishingPoint"])

            widget_size = imgui.get_content_region_avail()
            if imgui.begin_child("3d_viewport", widget_size):
                # Control Points
                for i, axis in enumerate(first_vanishing_lines_pixel):
                    changed, new_line = drag_line(f"Z{i}", axis, BLUE)
                    first_vanishing_lines_pixel[i] = new_line

                for i, axis in enumerate(second_vanishing_lines_pixel):
                    changed, new_line = drag_line(f"X{i}", axis, RED)
                    second_vanishing_lines_pixel[i] = new_line

                _, principal_point_pixel = drag_point("principal_point", principal_point_pixel)
                principal_point_pixel = glm.vec2(widget_size.x / 2, widget_size.y / 2)
                _, origin_pixel = drag_point("origin", origin_pixel)

                # Compute Camera
                try:
                    from my_solver_v3 import solve2vp
                    # solve camera
                    fovy, view_orientation_matrix, position = solve2vp(
                        image_width=int(widget_size.x),
                        image_height=int(widget_size.y),
                        principal_point_pixel=principal_point_pixel,
                        origin_pixel=origin_pixel,
                        first_vanishing_lines_pixel=first_vanishing_lines_pixel,
                        second_vanishing_lines_pixel=second_vanishing_lines_pixel,
                        first_axis=first_axis,
                        second_axis=second_axis,
                        scene_scale=scene_scale
                    )
                    
                    view_translate_transform = glm.translate(glm.mat4(1.0), position)
                    view_rotation_transform = glm.mat4(view_orientation_matrix)
                    view_transform= view_rotation_transform * view_translate_transform
                    camera.transform = glm.inverse(view_transform)
                    camera.setAspectRatio(widget_size.x / widget_size.y)
                    camera.setFoVY(math.degrees(fovy))
                    
                except Exception as e:
                    from textwrap import wrap
                    imgui.push_style_color(imgui.Col_.text, (1.0, 0.2, 0.2, 1.0))
                    imgui.text_wrapped(f"fspy error: {pformat(e)}")
                    import traceback
                    traceback.print_exc()
                    imgui.pop_style_color()

                # Render Scene
                if moderngl_ctx is None:
                    logger.info("Initializing ModernGL context...")
                    moderngl_ctx = moderngl.create_context()
                    scene_layer.setup(moderngl_ctx)
                image_ref = render_scene_to_image_ref(moderngl_ctx, camera, scene_layer, fbo, widget_size)
                imgui.set_cursor_pos(imgui.ImVec2(0,0))
                imgui.image(image_ref,imgui.ImVec2(widget_size.x, widget_size.y))
            imgui.end_child()

        case _:
            imgui.push_style_color(imgui.Col_.text, (1.0, 0.2, 0.2, 1.0))
            imgui.text(f"Unsupported solver mode {SOLVER_MODE}")
            imgui.pop_style_color()


if __name__ == "__main__":
    immapp.run(gui, window_title="ImGui Bundle - 2D Points & 3D Scene", window_size=(800, 800))

