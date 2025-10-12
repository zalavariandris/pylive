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
from utils.geo import closest_point_line_segment
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

#########################
# Coordinate Conversion #
#########################
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
    
def pixel_point_to_relative_coords(value: glm.vec2|fspy.LineSegmentType, image_width, image_height) -> glm.vec2:
    return glm.vec2(
        value.x / image_width,
        value.y / image_height
    )

def relative_point_to_image_plane_coords(
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
    
def pixel_point_to_image_plane_coords(
        P: glm.vec2, image_width: int, image_height: int) -> glm.vec2:
    return relative_point_to_image_plane_coords(pixel_point_to_relative_coords(P, image_width, image_height), image_width, image_height)

def pixel_line_to_relative_coords(line: fspy.LineSegmentType, image_width, image_height) -> fspy.LineSegmentType:
    return (
        pixel_point_to_relative_coords(glm.vec2(line[0].x, line[0].y), image_width, image_height),
        pixel_point_to_relative_coords(glm.vec2(line[1].x, line[1].y), image_width, image_height)
    )

def relative_line_to_image_plane_coords(
        line: fspy.LineSegmentType, image_width: int, image_height: int
    ) -> fspy.LineSegmentType:
    return (
        relative_point_to_image_plane_coords(line[0], image_width, image_height),
        relative_point_to_image_plane_coords(line[1], image_width, image_height)
    )

def pixel_line_to_image_plane_coords(
        line: fspy.LineSegmentType, image_width: int, image_height: int
    ) -> fspy.LineSegmentType:
    return (
        pixel_point_to_image_plane_coords(line[0], image_width, image_height),
        pixel_point_to_image_plane_coords(line[1], image_width, image_height)
    )

# ########## #
# INITIALIZE #
# ########## #

# ModernGL context and framebuffer
scene_renderer = SceneLayer()
moderngl_ctx: moderngl.Context|None = None
fbo: moderngl.Framebuffer|None = None


# Parameters
axis_names = ('Z', 'X', 'Y')


second_vanishing_lines_pixel:Tuple[fspy.LineSegmentType] = [
    [glm.vec2(280, 340), glm.vec2(520, 360)],
    [glm.vec2(230, 480), glm.vec2(560, 460)]
]

third_vanishing_lines_pixel:Tuple[fspy.LineSegmentType] = [
    [glm.vec2(480, 500), glm.vec2(580, 270)],
    [glm.vec2(315, 505), glm.vec2(220, 270)]
]

first_vanishing_lines_pixel:Tuple[fspy.LineSegmentType] = [
    [glm.vec2(280, 520), glm.vec2(310, 300)],
    [glm.vec2(520, 500), glm.vec2(480, 330)]
]


from enum import IntEnum
class PrincipalPointMode(IntEnum):
    Default = 0
    Manual = 1
    FromThirdVanishingPoint = 2

principal_point_mode: PrincipalPointMode = PrincipalPointMode.Default
horizon_height: float = 300.0
default_fov:Degrees = 60.0
origin_pixel = glm.vec2(400, 400)
principal_point_pixel = glm.vec2(400, 400)
first_vanishing_point_pixel = glm.vec2(100, 250)
second_vanishing_point_pixel = glm.vec2(800, 250)
DEFAULT_CAMERA_DISTANCE_SCALE = 5.0
scene_scale = DEFAULT_CAMERA_DISTANCE_SCALE
# ######### #
# MAIN LOOP #
# ######### #
first_axis = fspy.Axis.PositiveZ
second_axis = fspy.Axis.PositiveX
camera = Camera()
import itertools
def gui():
    global camera
    global moderngl_ctx, fbo
    # Camera Calibration parameters
    global first_axis, second_axis
    global principal_point_pixel, principal_point_mode
    global first_vanishing_point_pixel
    global second_vanishing_point_pixel
    global origin_pixel
    global horizon_height
    global default_fov
    global first_vanishing_lines_pixel
    global second_vanishing_lines_pixel
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
        _, scene_scale = imgui.slider_float("scene_scale", scene_scale, 1.0, 100.0, "%.2f")

        for i, axis in enumerate(second_vanishing_lines_pixel):
            changed, new_line = drag_line(f"X{i}", axis, RED)
            second_vanishing_lines_pixel[i] = new_line

        for i, axis in enumerate(first_vanishing_lines_pixel):
            changed, new_line = drag_line(f"Z{i}", axis, BLUE)
            first_vanishing_lines_pixel[i] = new_line

        _, principal_point_pixel = drag_point("principal_point", principal_point_pixel)
        principal_point_pixel = glm.vec2(widget_size.x / 2, widget_size.y / 2)
        _, first_vanishing_point_pixel = drag_point("first_vanishing_point", first_vanishing_point_pixel)
        _, second_vanishing_point_pixel = drag_point("second_vanishing_point", second_vanishing_point_pixel)
        _, origin_pixel = drag_point("origin", origin_pixel)

        _, first_axis = imgui.combo("first axis", first_axis, ["PositiveX", "NegativeX", "PositiveY", "NegativeY", "PositiveZ", "NegativeZ"])
        _, second_axis = imgui.combo("second axis", second_axis, ["PositiveX", "NegativeX", "PositiveY", "NegativeY", "PositiveZ", "NegativeZ"])
        
        # _, principal_point_mode = imgui.combo("principal point mode", principal_point_mode, ["Default", "Manual", "FromThirdVanishingPoint"])
        try:
            ## Validate
            # Check vanishing line sets for near-parallel lines
            for vanishing_line_set in filter(lambda _:bool(_), [first_vanishing_lines_pixel, second_vanishing_lines_pixel, third_vanishing_lines_pixel]):
                for line1, line2 in itertools.combinations(vanishing_line_set, 2):
                    if fspy.are_lines_near_parallel(line1, line2):
                        raise Exception("Near parallel lines detected between vanishing line sets")

            # settings
            # sensor_size =                 (36, 24),
            # first_vanishing_lines_axis =  first_axis,
            # second_vanishing_lines_axis = second_axis,
            # principal_point_mode =        'Manual', # 'Default' or 'FromThirVanishingPoint'
            # quad_mode_enabled =           False,
            # scale =                       scene_scale
            image_width =                 int(widget_size.x)
            image_height =                int(widget_size.y)

            ###############################
            # 1. COMPUTE vanishing points #
            ###############################
            first_vanishing_point_pixel =  fspy.my_compute_vanishing_point(first_vanishing_lines_pixel)
            second_vanishing_point_pixel = fspy.my_compute_vanishing_point(second_vanishing_lines_pixel)
            third_vanishing_point_pixel =  fspy.my_compute_vanishing_point(third_vanishing_lines_pixel)
            
            #############################
            # 2. COMPUTE Focal Length #
            ##############################
            focal_length_pixel = fspy._compute_focal_length_from_vanishing_points(
                Fu = first_vanishing_point_pixel, 
                Fv = second_vanishing_point_pixel, 
                P =  principal_point_pixel
            )

            #################################
            # 3. COMPUTE Camera Orientation #
            #################################
            
            camera_orientation_matrix:glm.mat3 = fspy._create_orientation_matrix_from_vanishing_points(
                Fu = first_vanishing_point_pixel, 
                Fv = second_vanishing_point_pixel, 
                f = focal_length_pixel, # math.tan(fovy / 2), # fovy is vertical fov in radians, 
                P =  principal_point_pixel
            )
            

            # validate if matrix is a purely rotational matrix
            determinant = glm.determinant(camera_orientation_matrix)
            if math.fabs(determinant - 1) > 1e-6:
                raise Exception(f'Invalid vanishing point configuration. Rotation determinant {determinant}')

            # apply axis assignment
            axis_assignment_matrix:glm.mat3 = fspy._createAxisAssignmentMatrix(first_axis, second_axis)
            camera_orientation_matrix:glm.mat3 = axis_assignment_matrix * camera_orientation_matrix
            view_orientation_matrix:glm.mat3 = glm.inverse(camera_orientation_matrix)
            if math.fabs(1 - glm.determinant(axis_assignment_matrix) ) > 1e-7:
                raise Exception("Invalid axis assignment")
            
            # convert to 4x4 matrix for transformations
            view_rotation_transform:glm.mat4 = glm.mat4(view_orientation_matrix)
            view_rotation_transform[3][3] = 1.0

            ##############################
            # 4. COMPUTE Camera Position #
            ##############################
            fovy =         math.atan(image_height/2 / focal_length_pixel) * 2
            imgui.text(f"fovy: {fovy}")

            projection_matrix = glm.perspective(
                fovy, # fovy in radians
                image_width/image_height, # aspect 
                0.1, # near
                100 # far
            )

            # 3. compute camera translation
            origin_3D = fspy._compute_camera_position_from_origin(
                view_rotation_transform = view_rotation_transform, 
                projection_matrix =       projection_matrix, 
                origin_pixel =            glm.vec2(origin_pixel.x, origin_pixel.y), # flip Y for image coords
                image_width =             image_width,
                image_height =            image_height, 
                scale =                   scene_scale
            )

            view_translate_transform = glm.translate(glm.mat4(1.0), -origin_3D)
            view_transform= view_rotation_transform * view_translate_transform
            camera.transform = glm.inverse(view_transform)
            camera.setFoVY(math.degrees(fovy))

        except Exception as e:
            from textwrap import wrap
            imgui.push_style_color(imgui.Col_.text, (1.0, 0.2, 0.2, 1.0))
            imgui.text_wrapped(f"fspy error: {pformat(e)}")
            import traceback
            traceback.print_exc()
            imgui.pop_style_color()

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
            imgui.ImVec2(widget_size.x, widget_size.y)
            # uv0=imgui.ImVec2(0, 1),  # Flip vertically (OpenGL texture is bottom-up)
            # uv1=imgui.ImVec2(1, 0)
        )

    imgui.end_child()


if __name__ == "__main__":
    immapp.run(gui, window_title="ImGui Bundle - 2D Points & 3D Scene", window_size=(9*75, 9*75))