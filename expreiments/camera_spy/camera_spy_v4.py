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


# COLOR CONSTANTS
dimmed_alpha = 0.4
RED = imgui.color_convert_float4_to_u32((1,0,0, 1.0))
RED_DIMMED = imgui.color_convert_float4_to_u32((1,0,0, dimmed_alpha))
BLUE = imgui.color_convert_float4_to_u32((0.3,0.3,1, 1.0))
BLUE_DIMMED = imgui.color_convert_float4_to_u32((0.3,.3,1, dimmed_alpha))
GREEN = imgui.color_convert_float4_to_u32((0,1,0, 1.0))
GREEN_DIMMED = imgui.color_convert_float4_to_u32((0,1,0, dimmed_alpha))
WHITE = imgui.color_convert_float4_to_u32((1,1,1, 1.0))
WHITE_DIMMED = imgui.color_convert_float4_to_u32((1,1,1, dimmed_alpha))
PINK = imgui.color_convert_float4_to_u32((1,0,1, 1.0))
PINK_DIMMED = imgui.color_convert_float4_to_u32((1,0,1, dimmed_alpha))

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
axis_names = ('Z', 'X', 'Y')

# Z axis default points
first_vanishing_lines_pixel:Tuple[fspy.LineSegmentType] = [
    [glm.vec2(190, 360), glm.vec2(450, 260)],
    [glm.vec2(340, 475), glm.vec2(550, 290)]
]

# X axis by default
second_vanishing_lines_pixel:Tuple[fspy.LineSegmentType] = [
    [glm.vec2(350, 260), glm.vec2(550, 330)],
    [glm.vec2(440, 480), glm.vec2(240, 300)]
]

# parameers
scene_scale = 5.0
first_axis = fspy.Axis.PositiveZ
second_axis = fspy.Axis.PositiveX
quad_mode:bool = False


# ######### #
# MAIN LOOP #
# ######### #
overrides = dict()
settings = dict()


import my_solver_v3 as solver

import widgets

def gui():
    # Configure antialiasing
    style = imgui.get_style()
    style.anti_aliased_lines = True
    style.anti_aliased_lines_use_tex = True
    style.anti_aliased_fill = True

    global overrides
    # renderer
    global moderngl_ctx, fbo

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
    

    # Parameters
    _, first_axis = imgui.combo("first axis", first_axis, ["PositiveX", "NegativeX", "PositiveY", "NegativeY", "PositiveZ", "NegativeZ"])
    _, second_axis = imgui.combo("second axis", second_axis, ["PositiveX", "NegativeX", "PositiveY", "NegativeY", "PositiveZ", "NegativeZ"])
    _, scene_scale = imgui.slider_float("scene_scale", scene_scale, 1.0, 100.0, "%.2f")
    _, quad_mode = imgui.checkbox("quad mode", quad_mode)

    widget_size = imgui.get_content_region_avail()
    if imgui.begin_child("3d_viewport", widget_size):
        image_width, image_height = int(widget_size.x), int(widget_size.y)


        # Compute Camera
        camera = Camera()
        try:
            # Control Points
            from collections import defaultdict
            changes = defaultdict(bool)
            for i, axis in enumerate(first_vanishing_lines_pixel):
                changes[f"Z{i}"], new_line = widgets.zip(
                    drag_point(f"Z{i}A", axis[0], BLUE), 
                    drag_point(f"Z{i}B", axis[1], BLUE)
                )
                first_vanishing_lines_pixel[i] = new_line

            # if not quad_mode:
            for i, axis in enumerate(second_vanishing_lines_pixel):
                changes[f"X{i}"], new_line = widgets.zip(
                    drag_point(f"X{i}A", axis[0], RED), 
                    drag_point(f"X{i}B", axis[1], RED)
                )
                second_vanishing_lines_pixel[i] = new_line

            if quad_mode:
                second_vanishing_lines_pixel = [
                    (first_vanishing_lines_pixel[0][0], first_vanishing_lines_pixel[1][0]),
                    (first_vanishing_lines_pixel[0][1], first_vanishing_lines_pixel[1][1])
                ]

            draw.lines(second_vanishing_lines_pixel, "", RED)


            # _, principal_point_pixel = drag_point("principal_point", principal_point_pixel)
            principal_point_pixel = glm.vec2(widget_size.x / 2, widget_size.y / 2)
            _, origin_pixel = drag_point("origin", origin_pixel)

            ###############################
            # 1. COMPUTE vanishing points #
            ###############################
            first_vanishing_point_pixel =  solver.least_squares_intersection_of_lines(first_vanishing_lines_pixel)
            second_vanishing_point_pixel = solver.least_squares_intersection_of_lines(second_vanishing_lines_pixel)

            ## Drag vanishing points to adjust lines
            # old_first_vp = first_vanishing_point_pixel
            # changes[f"vp1"], first_vanishing_point_pixel = drag_point("vp1", first_vanishing_point_pixel, BLUE)
            # if changes[f"vp1"]:
            #     first_vanishing_lines_pixel = solver.adjust_vanishing_lines(
            #         old_first_vp, first_vanishing_point_pixel, first_vanishing_lines_pixel
            #     )
            # old_second_vp = second_vanishing_point_pixel
            # changes[f"vp2"], second_vanishing_point_pixel = drag_point("vp2", second_vanishing_point_pixel,RED)
            # if changes[f"vp2"]:
            #     second_vanishing_lines_pixel = solver.adjust_vanishing_lines(
            #         old_second_vp, second_vanishing_point_pixel, second_vanishing_lines_pixel
            #     )
            
            # # adjust controlpoints if override is active
            # if overrides.get('fov') is not None:
            #     if changes[f"vp1"] or changes["Z0"] or changes["Z1"]:
            #         old_second_vp = second_vanishing_point_pixel
            #         current_horizon_direction = glm.normalize(old_second_vp - old_first_vp)
            #         second_vanishing_point_pixel = solver.second_vanishing_point_from_focal_length(
            #             first_vanishing_point_pixel,
            #             focal_length_pixel,
            #             principal_point_pixel,
            #             current_horizon_direction
            #         )
            #         second_vanishing_lines_pixel = solver.adjust_vanishing_lines(
            #             old_second_vp, second_vanishing_point_pixel, second_vanishing_lines_pixel
            #         )

            #     if changes[f"vp2"] or changes["X0"] or changes["X1"]:
            #         old_first_vp = first_vanishing_point_pixel
            #         current_horizon_direction = glm.normalize(old_second_vp - old_first_vp)
            #         first_vanishing_point_pixel = solver.second_vanishing_point_from_focal_length(
            #             second_vanishing_point_pixel,
            #             focal_length_pixel,
            #             principal_point_pixel,
            #             -current_horizon_direction
            #         )
            #         first_vanishing_lines_pixel = solver.adjust_vanishing_lines(
            #             old_first_vp, first_vanishing_point_pixel, first_vanishing_lines_pixel
            #         )
            
            ###########################
            # 2. COMPUTE Focal Length #
            ###########################
            focal_length_pixel = solver.compute_focal_length_from_vanishing_points(
                Fu = first_vanishing_point_pixel, 
                Fv = second_vanishing_point_pixel, 
                P =  principal_point_pixel
            )

            #################################
            # 3. COMPUTE Camera Orientation #
            #################################
            forward = glm.normalize(glm.vec3(first_vanishing_point_pixel-principal_point_pixel,  -focal_length_pixel))
            right =   glm.normalize(glm.vec3(second_vanishing_point_pixel-principal_point_pixel, -focal_length_pixel))
            up = glm.cross(forward, right)
            view_orientation_matrix = glm.mat3(forward, right, up)

            # validate if matrix is a purely rotational matrix
            determinant = glm.determinant(view_orientation_matrix)
            if math.fabs(determinant - 1) > 1e-6:
                raise Exception(f'Invalid vanishing point configuration. Rotation determinant {determinant}')

            # apply axis assignment
            axis_assignment_matrix:glm.mat3 = solver.create_axis_assignment_matrix(first_axis, second_axis)            
            view_orientation_matrix:glm.mat3 = view_orientation_matrix * glm.inverse(axis_assignment_matrix)

            # convert to 4x4 matrix for transformations
            view_rotation_transform:glm.mat4 = glm.mat4(view_orientation_matrix)
            view_rotation_transform[3][3] = 1.0

            ##############################
            # 4. COMPUTE Camera Position #
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

            origin_3D = glm.unProject(
                glm.vec3(
                    origin_pixel.x, 
                    origin_pixel.y, 
                    solver._world_depth_to_ndc_z(scene_scale*focal_length_pixel/image_height, near, far)
                ),
                view_rotation_transform, 
                projection_matrix, 
                glm.vec4(0,0,image_width,image_height)
            )

            # create camera
            view_translate_transform = glm.translate(glm.mat4(1.0), -origin_3D)
            view_rotation_transform = glm.mat4(view_orientation_matrix)
            view_transform= view_rotation_transform * view_translate_transform
            camera.transform = glm.inverse(view_transform)
            camera.setAspectRatio(widget_size.x / widget_size.y)
            camera.setFoVY(math.degrees(fovy))

            ##############################
            # Override Camera Parameters #
            ##############################
            imgui.text("Override Camera Parameters:")
            overrides.setdefault('fov', None)
            _, override_fov = imgui.checkbox("fov", overrides['fov'] is not None)
            if _:
                overrides.setdefault('fov', math.degrees(fovy))
                _, new_fov_y_degrees = imgui.slider_float("fov_y (degrees)", math.degrees(fovy), 1.0, 179.0, "%.1f")
                overrides['fov'] = new_fov_y_degrees
            else:
                imgui.text(f"fov_y (degrees): {math.degrees(fovy):.1f}")
            
            if overrides['fov'] is not None:
                camera.setFoVY(overrides['fov'])

            # Project vanishing Points
            VP_X, VP_Y, VP_Z = solver.vanishing_points_from_camera(
                camera.viewMatrix(),
                camera.projectionMatrix(),
                (0,0,image_width,image_height)
            )
            # draw.points([VP_X, VP_Z], ["", ""], [RED, BLUE], shapes='x')

            # calculate actual vanishing lines
            corrected_first_vanishing_lines = []
            VL_Z = map(lambda line: (line[0]/2+line[1]/2, VP_Z), first_vanishing_lines_pixel)
            for corrected_line, current_line in zip(VL_Z, first_vanishing_lines_pixel):
                from utils.geo import closest_point_on_line
                P_corrected = closest_point_on_line(current_line[0], corrected_line)
                Q_corrected = closest_point_on_line(current_line[1], corrected_line)
                corrected_first_vanishing_lines.append((P_corrected, Q_corrected))

            corrected_second_vanishing_lines = []
            VL_X = map(lambda line: (line[0]/2+line[1]/2, VP_X), second_vanishing_lines_pixel)
            for corrected_line, current_line in zip(VL_X, second_vanishing_lines_pixel):
                from utils.geo import closest_point_on_line
                P_corrected = closest_point_on_line(current_line[0], corrected_line)
                Q_corrected = closest_point_on_line(current_line[1], corrected_line)
                corrected_second_vanishing_lines.append((P_corrected, Q_corrected))

            # Draw corrected lines
            draw.lines(corrected_first_vanishing_lines, "", BLUE)
            draw.lines(corrected_second_vanishing_lines, "", RED)
            # extend to vp
            draw.lines([(line[0], VP_Z) for line in corrected_first_vanishing_lines], "", BLUE_DIMMED)
            draw.lines([(line[0], VP_X) for line in corrected_second_vanishing_lines], "", RED_DIMMED)

            # draw control offsets
            for line, corrected in  zip(first_vanishing_lines_pixel, corrected_first_vanishing_lines):
                draw.lines([(line[0], corrected[0])], "", BLUE_DIMMED)
                draw.lines([(line[1], corrected[1])], "", BLUE_DIMMED)
            
            for line, corrected in  zip(second_vanishing_lines_pixel, corrected_second_vanishing_lines):
                draw.lines([(line[0], corrected[0])], "", RED_DIMMED)
                draw.lines([(line[1], corrected[1])], "", RED_DIMMED)
            

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



if __name__ == "__main__":
    immapp.run(gui, window_title="ImGui Bundle - 2D Points & 3D Scene", window_size=(800, 800))

