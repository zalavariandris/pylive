import logging
import time
import string

# Configure logging to see shader compilation logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

import math
import numpy as np
from pylive.render_engine.camera import Camera
from pprint import pformat

from imgui_bundle import imgui, immapp
from gizmos import drag_line, drag_horizon
from utils.geo import closest_point_on_line_segment
from gizmos import window_to_screen, drag_point

from typing import Any, List, Tuple, Dict

class Cache:
    def __init__(self):
        self._data:Dict[str, Any] = dict()

    def set_default(self, name:str, value:Any) -> Any:
        if name not in self._data:
            self._data[name] = value
        return self._data[name]

    def __setattr__(self, name:str, value:Any):
        if name.startswith("_"):
            super().__setattr__(name, value)
        else:
            self._data[name] = value

    def __getattr__(self, name:str) -> Any:
        if name.startswith("_"):
            return super().__getattr__(name)
        else:
            return self._data.get(name, None)
        
settings = Cache()



# ############## #
# Graphics Layer #
# ############## #
import moderngl
from pylive.render_engine.render_layers import GridLayer, RenderLayer, AxesLayer
import glm

import fspy_solver_functional as fspy
import my_solver_v3 as my_solver
from gizmos import draw


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


def render_scene_to_image_ref(moderngl_ctx, camera:Camera, scene_layer:RenderLayer, widget_size: glm.vec2) -> imgui.ImTextureRef:
    ############################
    # Render 3D Scene in ImGui #
    ############################
    global fbo
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
        # TODO: IMPORTANT: Make sure new fbo is created only when size changes
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
BLUE = imgui.color_convert_float4_to_u32((0.3,0.3,1, 1.0))
BLUE_DIMMED = imgui.color_convert_float4_to_u32((0.3,.3,1, 0.5))
GREEN = imgui.color_convert_float4_to_u32((0,1,0, 1.0))
GREEN_DIMMED = imgui.color_convert_float4_to_u32((0,1,0, 0.2))
WHITE = imgui.color_convert_float4_to_u32((1,1,1, 1.0))
WHITE_DIMMED = imgui.color_convert_float4_to_u32((1,1,1, 0.2))
PINK = imgui.color_convert_float4_to_u32((1,0,1, 1.0))
PINK_DIMMED = imgui.color_convert_float4_to_u32((1,0,1, 0.2))

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
    Advanced = 2
    FSpy = 3
    SolverModel = 4

SOLVER_MODE = SolverMode.TwoVP

from dataclasses import dataclass

from typing import Literal

class OriginPointMode(IntEnum):
    Center = 0
    Manual = 1

class FirstVanishingPointMode(IntEnum):
    Manual = 0
    FromVanishingLines = 1

class SecondVanishingPointMode(IntEnum):
    Default = 0
    Manual = 1
    FromVanishingLines = 2

class FieldOfViewMode(IntEnum):
    Auto = 0
    Manual = 1
    Force = 2
    FromSecondVanishingLine = 3

class RollMode(IntEnum):
    Horizontal = 0 # by default horizon is horizontal
    FromFirstAndSecondVanishingPoints = 1 # if both vanishing points are specified, roll is computed from them, unless forced not to...
    FromSecondVanishingLine = 2 # if a single second vanishing line is available, roll can be computed from it
    
@dataclass
class AdvancedSettings:
    principal_point_mode: PrincipalPointMode = PrincipalPointMode.Manual
    origin_point_mode: OriginPointMode = OriginPointMode.Center

    use_first_vanishing_lines_to_compute_first_vanishing_point: bool = True
    use_second_vanishing_lines_to_compute_second_vanishing_point: bool = True

    use_second_vanishing_line_to_compute_roll: bool = True
    use_second_vanishing_line_to_compute_focal_length: bool = True
    # first_vanishing_point_mode: FirstVanishingPointMode = FirstVanishingPointMode.FromVanishingLines
    # field_of_view_mode: FieldOfViewMode = FieldOfViewMode.FromSecondVanishingLine
    # second_vanishing_point_mode: SecondVanishingPointMode = SecondVanishingPointMode.Default
    # roll_mode: RollMode = RollMode.Horizontal
    


advanced_settings = AdvancedSettings(
    # origin_point_mode=OriginPointMode.Manual
)

advanced_settings = dict()

# ######### #
# MAIN LOOP #
# ######### #
settings = Cache()

@dataclass
class CameraParameters:
    forward: glm.vec3|None
    right: glm.vec3|None
    up: glm.vec3|None
    f: float|None # focal length in pixels
    position: glm.vec3|None

import itertools
from my_solver_v3 import SolverModel
solver_model = SolverModel(dimensions=(0, 0))
solver_model.first_vanishing_lines_pixel = first_vanishing_lines_pixel
solver_model.second_vanishing_lines_pixel = second_vanishing_lines_pixel
def gui():
    global settings
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
    _, SOLVER_MODE = imgui.combo("Solver Mode", SOLVER_MODE, SolverMode._member_names_)
    
    def radio_buttons(label:str, current_value:int, options:List[str]) -> int:
        imgui.text(f"{label}:")
        imgui.same_line()
        changed = False
        new_value = current_value
        imgui.push_id(label)
        for i, option in enumerate(options):
            changed = imgui.radio_button(option, current_value == i)
            if changed:
                new_value = i
            if i < len(options) - 1:
                imgui.same_line()
        imgui.pop_id()
        return changed, new_value


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
                    context_start = time.time()
                    moderngl_ctx = moderngl.create_context()
                    context_time = time.time() - context_start
                    logger.info(f"ModernGL context created in {context_time:.3f}s")
                    
                    logger.info("Setting up scene layers...")
                    setup_start = time.time()
                    scene_layer.setup(moderngl_ctx)
                    setup_time = time.time() - setup_start
                    logger.info(f"Scene layer setup completed in {setup_time:.3f}s")
                image_ref = render_scene_to_image_ref(moderngl_ctx, camera, scene_layer, widget_size)
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

                    from my_solver_v3 import vanishing_points_from_camera
                    vp1, vp2 = vanishing_points_from_camera(
                        camera.viewMatrix(), 
                        camera.projectionMatrix(), 
                        (0, 0, widget_size.x, widget_size.y)
                    )

                    imgui.text(f"vp1: {vp1}, vp2: {vp2}")
                
                    draw.points([vp1, vp2], ["VP", "VP"], [PINK, PINK])
                    
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
                    context_start = time.time()
                    moderngl_ctx = moderngl.create_context()
                    context_time = time.time() - context_start
                    logger.info(f"ModernGL context created in {context_time:.3f}s")
                    
                    logger.info("Setting up scene layers...")
                    setup_start = time.time()
                    scene_layer.setup(moderngl_ctx)
                    setup_time = time.time() - setup_start
                    logger.info(f"Scene layer setup completed in {setup_time:.3f}s")
                image_ref = render_scene_to_image_ref(moderngl_ctx, camera, scene_layer, widget_size)



                imgui.set_cursor_pos(imgui.ImVec2(0,0))
                imgui.image(image_ref,imgui.ImVec2(widget_size.x, widget_size.y))

                
            imgui.end_child()

        case SolverMode.Advanced:
            _, advanced_settings.origin_point_mode = radio_buttons("Origin Point Mode", advanced_settings.origin_point_mode, OriginPointMode._member_names_)
            # _, advanced_settings.principal_point_mode = radio_buttons("Principal Point Mode", advanced_settings.principal_point_mode, PrincipalPointMode._member_names_)
            _, advanced_settings.first_vanishing_point_mode = radio_buttons("First Vanishing Point Mode", advanced_settings.first_vanishing_point_mode, FirstVanishingPointMode._member_names_)
            _, advanced_settings.field_of_view_mode = radio_buttons("Field of View Mode", advanced_settings.field_of_view_mode, FieldOfViewMode._member_names_)

            if advanced_settings.field_of_view_mode == FieldOfViewMode.Auto:
                imgui.begin_disabled()
            _, focal_length_pixel = imgui.slider_float("focal_length_pixel", focal_length_pixel, 1.0, 2000.0, "%.2f")
            if advanced_settings.field_of_view_mode == FieldOfViewMode.Auto:
                imgui.end_disabled()

            _, advanced_settings.second_vanishing_point_mode = radio_buttons("Second Vanishing Point Mode", advanced_settings.second_vanishing_point_mode, SecondVanishingPointMode._member_names_)

            widget_size = imgui.get_content_region_avail()
            image_width, image_height = int(widget_size.x), int(widget_size.y)
            if imgui.begin_child("3d_viewport", widget_size):
                try:
                    principal_point_pixel = glm.vec2(widget_size.x / 2, widget_size.y / 2)
                    draw.points([principal_point_pixel], ["principal point"])



                    # if advanced_settings.first_vanishing_point_mode == FirstVanishingPointMode.FromVanishingLines:
                    #     for i, axis in enumerate(first_vanishing_lines_pixel):
                    #         changed, new_line = drag_line(f"Z{i}", axis, BLUE)
                    #         first_vanishing_lines_pixel[i] = new_line
                    #     first_vanishing_point_pixel = my_solver.least_squares_intersection_of_lines(first_vanishing_lines_pixel)
                    #     draw.points([first_vanishing_point_pixel], ["vp1"])
                    # else:
                    #     _, first_vanishing_point_pixel = drag_point("vp1", first_vanishing_point_pixel)

                    # draw.lines([(origin_pixel, first_vanishing_point_pixel)], [""], [BLUE_DIMMED])

                    # match advanced_settings.second_vanishing_point_mode:
                    #     case SecondVanishingPointMode.Default:
                    #         ...
                    #     case  SecondVanishingPointMode.Manual:
                    #         _, second_vanishing_point_pixel = drag_point("vp2", second_vanishing_point_pixel)
                    #         draw.points([second_vanishing_point_pixel], ["vp2"])
                    #     case SecondVanishingPointMode.FromVanishingLines:
                    #         for i, axis in enumerate(second_vanishing_lines_pixel):
                    #             changed, new_line = drag_line(f"X{i}", axis, RED)
                    #             second_vanishing_lines_pixel[i] = new_line
                    #         second_vanishing_point_pixel = my_solver.least_squares_intersection_of_lines(second_vanishing_lines_pixel)
                    #         draw.points([second_vanishing_point_pixel], ["vp2"])

                    # if advanced_settings.second_vanishing_point_mode != SecondVanishingPointMode.Default:
                    #     focal_length_pixel = my_solver.compute_focal_length_from_vanishing_points(
                    #         Fu = first_vanishing_point_pixel, 
                    #         Fv = second_vanishing_point_pixel, 
                    #         P =  principal_point_pixel
                    #     )
                    #     advanced_settings.field_of_view_mode = FieldOfViewMode.Auto
                    #     forward = glm.normalize(glm.vec3(first_vanishing_point_pixel-principal_point_pixel,  -focal_length_pixel))
                    #     right =   glm.normalize(glm.vec3(second_vanishing_point_pixel-principal_point_pixel, -focal_length_pixel))
                    #     up = glm.cross(forward, right)
                    #     view_orientation_matrix = glm.mat3(forward, right, up)
                    #     draw.lines([(origin_pixel, second_vanishing_point_pixel)], [""], [RED_DIMMED])
                    # else:
                    #     forward = glm.normalize(glm.vec3(first_vanishing_point_pixel-principal_point_pixel, -focal_length_pixel))
                    #     up = glm.normalize(glm.cross(forward, glm.vec3(1,0,0)))
                    #     right = glm.cross(forward, up)
                    #     view_orientation_matrix = glm.mat3(forward, right, up)

                    glm.determinant(view_orientation_matrix)
                    if 1-math.fabs(glm.determinant(view_orientation_matrix)) > 1e-5:
                        raise Exception(f'Invalid vanishing point configuration. Rotation determinant {glm.determinant(view_orientation_matrix)}')

                    # apply axis assignment
                    axis_assignment_matrix:glm.mat3 = my_solver.create_axis_assignment_matrix(first_axis, second_axis)            
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
    

                    if advanced_settings.origin_point_mode == OriginPointMode.Center:
                        origin_pixel = principal_point_pixel
                    else:
                        _, origin_pixel = drag_point("origin", origin_pixel)
                    origin_3D = glm.unProject(
                        glm.vec3(
                            origin_pixel.x, 
                            origin_pixel.y, 
                            my_solver._world_depth_to_ndc_z(scene_scale, near, far)
                        ),
                        view_rotation_transform, 
                        projection_matrix, 
                        glm.vec4(0,0,image_width,image_height)
                    )
                    # match advanced_settings.principal_point_mode:
                    #     case PrincipalPointMode.Manual:
                    #         _, principal_point_pixel = drag_point("principal_point", principal_point_pixel)
                    #     case PrincipalPointMode.Default:
                    #         principal_point_pixel = glm.vec2(widget_size.x / 2, widget_size.y / 2)
                    #         draw.points([principal_point_pixel], ["principal point"])
                    # _, origin_pixel = drag_point("origin", origin_pixel)
                    # create transformation

                    view_translate_transform = glm.translate(glm.mat4(1.0), -origin_3D)
                    view_rotation_transform = glm.mat4(view_orientation_matrix)
                    view_transform= view_rotation_transform * view_translate_transform
                    camera.transform = glm.inverse(view_transform)
                    camera.setAspectRatio(widget_size.x / widget_size.y)
                    fovy = math.atan(image_height / 2 / focal_length_pixel) * 2
                    camera.setFoVY(math.degrees(fovy))

                    # Roll the camera based on the horizon line projected to 3D
                    # roll_matrix = my_solver.compute_roll_matrix(
                    #     image_width, 
                    #     image_height, 
                    #     second_vanishing_lines_pixel[0],
                    #     projection_matrix=camera.projectionMatrix(),
                    #     view_matrix=camera.viewMatrix()
                    # )
                    camera.transform = camera.transform
                except Exception as e:
                    logger.error(f"Error occurred while setting up camera: {e}")
                # Render Scene
                if moderngl_ctx is None:
                    logger.info("Initializing ModernGL context...")
                    context_start = time.time()
                    moderngl_ctx = moderngl.create_context()
                    context_time = time.time() - context_start
                    logger.info(f"ModernGL context created in {context_time:.3f}s")
                    
                    logger.info("Setting up scene layers...")
                    setup_start = time.time()
                    scene_layer.setup(moderngl_ctx)
                    setup_time = time.time() - setup_start
                    logger.info(f"Scene layer setup completed in {setup_time:.3f}s")
                image_ref = render_scene_to_image_ref(moderngl_ctx, camera, scene_layer, widget_size)
                imgui.set_cursor_pos(imgui.ImVec2(0,0))
                imgui.image(image_ref,imgui.ImVec2(widget_size.x, widget_size.y))
            imgui.end_child()

        case SolverMode.FSpy:
            import my_solver_v3 as solver
            widget_size = imgui.get_content_region_avail()
            image_width, image_height = int(widget_size.x), int(widget_size.y)

            if imgui.begin_child("3d_viewport", widget_size):
                ############
                # Settings #
                ############
                # First axis
                settings.set_default("first_axis", fspy.Axis.PositiveZ)
                imgui.text("First Axis:")
                for i, (name, axis) in enumerate(fspy.Axis._member_map_.items()):
                    if i%2 == 1:
                        imgui.same_line()
                    if imgui.radio_button(f"{name}##first", settings.first_axis == axis):
                        settings.first_axis = axis

                # Second axis
                imgui.text("Second Axis:")
                settings.set_default("use_second_axis", 'SecondAxisForBoth')
                if imgui.radio_button("No Second Axis", settings.use_second_axis == "NoSecondAxis"):
                    settings.use_second_axis = "NoSecondAxis"
                if imgui.radio_button("Use Single Second Axis for Roll", settings.use_second_axis == 'SecondAxisForRoll'):
                    settings.use_second_axis = 'SecondAxisForRoll'
                if imgui.radio_button("Use Single Second Axis for FOV", settings.use_second_axis == 'SecondAxisForFOV'):
                    settings.use_second_axis = 'SecondAxisForFOV'
                if imgui.radio_button("Use Multiple Second Axis for Both", settings.use_second_axis == 'SecondAxisForBoth'):
                    settings.use_second_axis = 'SecondAxisForBoth'

                if settings.use_second_axis != "NoSecondAxis":
                    settings.set_default("second_axis", fspy.Axis.PositiveX)
                    for i, (name, axis) in enumerate(fspy.Axis._member_map_.items()):
                        if i%2 == 1:
                            imgui.same_line()
                        if imgui.radio_button(f"{name}##second", settings.second_axis == axis):
                            settings.second_axis = axis

                # Control Points
                for i, axis in enumerate(first_vanishing_lines_pixel):
                    _, new_line = drag_line(f"Z{i}", axis, BLUE)
                    first_vanishing_lines_pixel[i] = new_line
                
                match settings.use_second_axis:
                    case "NoSecondAxis":
                        pass
                    case "SecondAxisForRoll" | "SecondAxisForFOV":
                        _, new_line = drag_line(f"Horizon{i}", second_vanishing_lines_pixel[0], RED)
                        second_vanishing_lines_pixel[0] = new_line
                    case "SecondAxisForBoth":
                        for i, axis in enumerate(second_vanishing_lines_pixel):
                            _, new_line = drag_line(f"Horizon{i}", axis, RED)
                            second_vanishing_lines_pixel[i] = new_line

                _, principal_point_pixel = drag_point("principal_point", principal_point_pixel)
                principal_point_pixel = glm.vec2(widget_size.x / 2, widget_size.y / 2)
                

                # Drag vaishing points
                old_first_vanishing_point_pixel = first_vanishing_point_pixel
                changed, first_vanishing_point_pixel = drag_point("vp1", first_vanishing_point_pixel)
                if changed:
                    first_vanishing_lines_pixel = solver.adjust_vanishing_lines(old_first_vanishing_point_pixel, first_vanishing_point_pixel, first_vanishing_lines_pixel)
                
                if settings.use_second_axis != "NoSecondAxis":
                    old_second_vanishing_point_pixel = second_vanishing_point_pixel
                    changed, second_vanishing_point_pixel = drag_point("vp2", second_vanishing_point_pixel)
                    if changed:
                        second_vanishing_lines_pixel = solver.adjust_vanishing_lines(old_second_vanishing_point_pixel, second_vanishing_point_pixel, second_vanishing_lines_pixel)

                try:
                    

                    # Compute Camera
                    ###############################
                    # 1. COMPUTE vanishing points #
                    ###############################
                    # Use the manually adjusted vanishing point instead of computing from lines
                    first_vanishing_point_pixel =  solver.least_squares_intersection_of_lines(first_vanishing_lines_pixel)

                    #################################
                    # 2. COMPUTE Camera Orientation #
                    #################################
                    match settings.use_second_axis:
                        case "NoSecondAxis" | 'SecondAxisForRoll'|"SecondAxisForFOV":
                            forward = glm.normalize(glm.vec3(first_vanishing_point_pixel-principal_point_pixel, -focal_length_pixel))
                            up = glm.normalize(glm.cross(forward, glm.vec3(1,0,0)))
                            right = glm.cross(forward, up)
                            # SecondAxisForRoll: see below: roll is applied after camera transform is computed
                            # SecondAxisForFOV: TODO: is not supported yet

                        case "SecondAxisForBoth":
                            # compute second vanishing point from lines
                            second_vanishing_point_pixel = solver.least_squares_intersection_of_lines(second_vanishing_lines_pixel)

                            # compute fov
                            focal_length_pixel = solver.compute_focal_length_from_vanishing_points(
                                Fu = first_vanishing_point_pixel, 
                                Fv = second_vanishing_point_pixel, 
                                P =  principal_point_pixel
                            )

                            # compute orientation
                            forward = glm.normalize(glm.vec3(first_vanishing_point_pixel-principal_point_pixel,  -focal_length_pixel))
                            right =   glm.normalize(glm.vec3(second_vanishing_point_pixel-principal_point_pixel, -focal_length_pixel))
                            up = glm.cross(forward, right)

                    view_orientation_matrix = glm.mat3(forward, right, up)

                    glm.determinant(view_orientation_matrix)
                    if 1-math.fabs(glm.determinant(view_orientation_matrix)) > 1e-5:
                        raise Exception(f'Invalid vanishing point configuration. Rotation determinant {glm.determinant(view_orientation_matrix)}')

                    # apply axis assignment
                    axis_assignment_matrix:glm.mat3 = solver.create_axis_assignment_matrix(first_axis, second_axis)            
                    view_orientation_matrix:glm.mat3 = view_orientation_matrix * glm.inverse(axis_assignment_matrix)

                    # convert to 4x4 matrix for transformations
                    view_rotation_transform:glm.mat4 = glm.mat4(view_orientation_matrix)
                    view_rotation_transform[3][3] = 1.0

                    ##############################
                    # 3. COMPUTE Camera Position #
                    ##############################
                    _, origin_pixel = drag_point("origin", origin_pixel)
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
                            solver._world_depth_to_ndc_z(scene_scale, near, far)
                        ),
                        view_rotation_transform, 
                        projection_matrix, 
                        glm.vec4(0,0,image_width,image_height)
                    )

                    view_translate_transform = glm.translate(glm.mat4(1.0), -origin_3D)
                    view_rotation_transform = glm.mat4(view_orientation_matrix)
                    view_transform= view_rotation_transform * view_translate_transform
                    camera.transform = glm.inverse(view_transform)
                    camera.setAspectRatio(widget_size.x / widget_size.y)
                    fovy = math.atan(image_height / 2 / focal_length_pixel) * 2
                    camera.setFoVY(math.degrees(fovy))
                    camera.transform = camera.transform 

                    # Roll the camera based on the horizon line projected to 3D
                    if settings.use_second_axis == "SecondAxisForRoll":
                        roll_matrix = solver.compute_roll_matrix(
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
                    context_start = time.time()
                    moderngl_ctx = moderngl.create_context()
                    context_time = time.time() - context_start
                    logger.info(f"ModernGL context created in {context_time:.3f}s")
                    
                    logger.info("Setting up scene layers...")
                    setup_start = time.time()
                    scene_layer.setup(moderngl_ctx)
                    setup_time = time.time() - setup_start
                    logger.info(f"Scene layer setup completed in {setup_time:.3f}s")
                image_ref = render_scene_to_image_ref(moderngl_ctx, camera, scene_layer, widget_size)
                imgui.set_cursor_pos(imgui.ImVec2(0,0))
                imgui.image(image_ref,imgui.ImVec2(widget_size.x, widget_size.y))

            imgui.end_child()

        case SolverMode.SolverModel:
            widget_size = imgui.get_content_region_avail()
            image_width, image_height = int(widget_size.x), int(widget_size.y)

            solver_model.dimensions = image_width, image_height
            

            if imgui.begin_child("3d_viewport", widget_size):
                try:
                    # First axis
                    imgui.text("First Axis:")
                    for i, (name, axis) in enumerate(fspy.Axis._member_map_.items()):
                        if i%2 == 1:
                            imgui.same_line()
                        if imgui.radio_button(f"{name}##first", solver_model.first_axis == axis):
                            solver_model.first_axis = axis

                    # Second axis
                    imgui.text("Second Axis:")
                    for i, (name, axis) in enumerate(fspy.Axis._member_map_.items()):
                        if i%2 == 1:
                            imgui.same_line()
                        if imgui.radio_button(f"{name}##second", solver_model.second_axis == axis):
                            solver_model.second_axis = axis

                    # Control Points
                    if solver_model.first_vanishing_lines_pixel:
                        for i, axis in enumerate(solver_model.first_vanishing_lines_pixel):
                            _, new_line = drag_line(f"Z{i}", axis, BLUE)
                            solver_model.first_vanishing_lines_pixel[i] = new_line
                        
                        # _, solver_model.first_vanishing_point_pixel  = drag_point("vp1", solver_model.first_vanishing_point_pixel)
                    
                    if solver_model.second_vanishing_lines_pixel:
                        for i, axis in enumerate(solver_model.second_vanishing_lines_pixel):
                            _, new_line = drag_line(f"X{i}", axis, RED)
                            solver_model.second_vanishing_lines_pixel[i] = new_line
                        
                        # _, solver_model.second_vanishing_point_pixel = drag_point("vp2", solver_model.second_vanishing_point_pixel)

                    settings.set_default("manual_principal_point", False)
                    _, settings.manual_principal_point = imgui.checkbox("Manual Principal Point", settings.manual_principal_point)
                    if settings.manual_principal_point:
                        _, solver_model.principal_point_pixel = drag_point("principal_point", solver_model.principal_point_pixel)
                    else:
                        solver_model.principal_point_pixel = None
                        draw.points([solver_model.principal_point_pixel], ["principal point"])

                    # Drag vanishing points
                    _, solver_model.origin_pixel = drag_point("origin", solver_model.origin_pixel)

                    draw.points([
                        solver_model.first_vanishing_point_pixel, 
                        solver_model.second_vanishing_point_pixel
                    ], ["vp1", "vp2"])

                    
                    camera = solver_model.camera()


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
                    context_start = time.time()
                    moderngl_ctx = moderngl.create_context()
                    context_time = time.time() - context_start
                    logger.info(f"ModernGL context created in {context_time:.3f}s")
                    
                    logger.info("Setting up scene layers...")
                    setup_start = time.time()
                    scene_layer.setup(moderngl_ctx)
                    setup_time = time.time() - setup_start
                    logger.info(f"Scene layer setup completed in {setup_time:.3f}s")
                image_ref = render_scene_to_image_ref(moderngl_ctx, camera, scene_layer, widget_size)
                imgui.set_cursor_pos(imgui.ImVec2(0,0))
                imgui.image(image_ref,imgui.ImVec2(widget_size.x, widget_size.y))

            imgui.end_child()
        case _:
            imgui.push_style_color(imgui.Col_.text, (1.0, 0.2, 0.2, 1.0))
            imgui.text(f"Unsupported solver mode {SOLVER_MODE}")
            imgui.pop_style_color()


if __name__ == "__main__":
    immapp.run(gui, window_title="ImGui Bundle - 2D Points & 3D Scene", window_size=(800, 800))

