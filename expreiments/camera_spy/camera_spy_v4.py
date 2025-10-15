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
from pylive.render_engine.render_target import RenderTarget

class SceneLayer(RenderLayer):
    def __init__(self):
        super().__init__()
        self.grid = GridLayer()
        self.axes = AxesLayer()
        self._initialized = False

    @property
    def initialized(self) -> bool:
        return self._initialized

    def setup(self):
        ctx = moderngl.get_context()
        if ctx is None:
            raise Exception("No current ModernGL context. Cannot setup SceneLayer.")
        self.grid.setup(ctx)
        self.axes.setup(ctx)
        super().setup(ctx)
        self._initialized = True

    def destroy(self):
        if self.grid:
            self.grid.destroy()
            self.grid = None
        if self.axes:
            self.axes.destroy()
            self.axes = None
        self._initialized = False
        return super().destroy()
    
    def render(self, camera:Camera):
        self.grid.render(view=camera.viewMatrix(), projection=camera.projectionMatrix())
        self.axes.render(view=camera.viewMatrix(), projection=camera.projectionMatrix())
        super().render()

# ModernGL context and framebuffer
scene_layer = SceneLayer()
render_target = RenderTarget(800, 800)

# ############## #
# GUI #
# ############## #
import fspy_solver_functional as fspy
from gizmos import draw
import widgets

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
import glm
import my_solver_v3 as solver

# ################# #
# Application State #
# ################# #

from dataclasses import dataclass
@dataclass
class State:
    origin_pixel: glm.vec2 =          glm.vec2(400, 400)
    principal_point_pixel: glm.vec2 = glm.vec2(400, 400)
    first_vanishing_lines_pixel: List[solver.LineSegmentType] = [
        [glm.vec2(190, 360), glm.vec2(450, 260)],
        [glm.vec2(340, 475), glm.vec2(550, 290)]
    ]
    second_vanishing_lines_pixel: List[solver.LineSegmentType] = [
        [glm.vec2(350, 260), glm.vec2(550, 330)],
        [glm.vec2(440, 480), glm.vec2(240, 300)]
    ]
    scene_scale:float =                5.0,
    first_axis:solver.Axis =           solver.Axis.PositiveZ,
    second_axis:solver.Axis =          solver.Axis.PositiveX,
    quad_mode:bool =                   False
    overrides = dict()
    settings = dict()

state = State()

# ######### #
# MAIN LOOP #
# ######### #
def gui():
    # Configure imgui
    style = imgui.get_style()
    style.anti_aliased_lines = True
    style.anti_aliased_lines_use_tex = True
    style.anti_aliased_fill = True

    # ModernGL renderer
    global render_target
    if not render_target.initialized:
        render_target.setup()
    if not scene_layer.initialized:
        scene_layer.setup()

    global overrides, settings, state

    # # Control Points
    # global origin_pixel
    # global principal_point_pixel
    # global second_vanishing_point_pixel
    # global second_vanishing_lines_pixel

    # # parameters
    # global focal_length_pixel
    # global scene_scale

    # # options
    # global first_axis, second_axis
    # global quad_mode
    
    # # Camera
    # global camera

    imgui.text("Camera Spy")    
    

    # Parameters
    _, state.first_axis = imgui.combo("first axis", state.first_axis, ["PositiveX", "NegativeX", "PositiveY", "NegativeY", "PositiveZ", "NegativeZ"])
    _, state.second_axis = imgui.combo("second axis", state.second_axis, ["PositiveX", "NegativeX", "PositiveY", "NegativeY", "PositiveZ", "NegativeZ"])
    _, state.scene_scale = imgui.slider_float("scene_scale", state.scene_scale, 1.0, 100.0, "%.2f")
    _, state.quad_mode = imgui.checkbox("quad mode", state.quad_mode)

    widget_size = imgui.get_content_region_avail()
    if imgui.begin_child("3d_viewport", widget_size):
        image_width, image_height = int(widget_size.x), int(widget_size.y)

        # Compute Camera
        camera = Camera()
        try:
            # Control Points
            from collections import defaultdict
            changes = defaultdict(bool)
            for i, axis in enumerate(state.first_vanishing_lines_pixel):
                changes[f"Z{i}"], new_line = widgets.zip(
                    drag_point(f"Z{i}A", axis[0], BLUE), 
                    drag_point(f"Z{i}B", axis[1], BLUE)
                )
                state.first_vanishing_lines_pixel[i] = new_line

            # if not quad_mode:
            for i, axis in enumerate(state.second_vanishing_lines_pixel):
                changes[f"X{i}"], new_line = widgets.zip(
                    drag_point(f"X{i}A", axis[0], RED), 
                    drag_point(f"X{i}B", axis[1], RED)
                )
                state.second_vanishing_lines_pixel[i] = new_line

            if state.quad_mode:
                state.second_vanishing_lines_pixel = [
                    (state.first_vanishing_lines_pixel[0][0], state.first_vanishing_lines_pixel[1][0]),
                    (state.first_vanishing_lines_pixel[0][1], state.first_vanishing_lines_pixel[1][1])
                ]

            draw.lines(state.second_vanishing_lines_pixel, "", RED)


            # _, principal_point_pixel = drag_point("principal_point", principal_point_pixel)
            principal_point_pixel = glm.vec2(widget_size.x / 2, widget_size.y / 2)
            _, state.origin_pixel = drag_point("origin", state.origin_pixel)

            ###############################
            # 1. COMPUTE vanishing points #
            ###############################
            first_vanishing_point_pixel =  solver.least_squares_intersection_of_lines(
                state.first_vanishing_lines_pixel)
            second_vanishing_point_pixel = solver.least_squares_intersection_of_lines(
                state.second_vanishing_lines_pixel)

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
            

            fovy, view_orientation, position = solver.solve2vp(
                image_width, 
                image_height, 
                principal_point_pixel,
                state.origin_pixel,
                first_vanishing_point_pixel,
                second_vanishing_point_pixel,
                state.first_axis,
                state.second_axis,
                state.scene_scale
            )

            # create camera
            view_translate_transform = glm.translate(glm.mat4(1.0), position)
            view_rotation_transform = glm.mat4(view_orientation)
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
            VL_Z = map(lambda line: (line[0]/2+line[1]/2, VP_Z), state.first_vanishing_lines_pixel)
            for corrected_line, current_line in zip(VL_Z, state.first_vanishing_lines_pixel):
                from utils.geo import closest_point_on_line
                P_corrected = closest_point_on_line(current_line[0], corrected_line)
                Q_corrected = closest_point_on_line(current_line[1], corrected_line)
                corrected_first_vanishing_lines.append((P_corrected, Q_corrected))

            corrected_second_vanishing_lines = []
            VL_X = map(lambda line: (line[0]/2+line[1]/2, VP_X), state.second_vanishing_lines_pixel)
            for corrected_line, current_line in zip(VL_X, state.second_vanishing_lines_pixel):
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
            for line, corrected in  zip(state.first_vanishing_lines_pixel, corrected_first_vanishing_lines):
                draw.lines([(line[0], corrected[0])], "", BLUE_DIMMED)
                draw.lines([(line[1], corrected[1])], "", BLUE_DIMMED)

            for line, corrected in  zip(state.second_vanishing_lines_pixel, corrected_second_vanishing_lines):
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
        gl_size = widget_size * imgui.get_io().display_framebuffer_scale
        render_target.resize(int(gl_size.x), int(gl_size.y))
        with render_target:
            render_target.clear(0.1, 0.1, 0.1, 0.0)  # Clear with dark gray background
            scene_layer.render(camera)

        # Display the framebuffer texture in ImGui
        imgui.set_cursor_pos(imgui.ImVec2(0,0))
        image_ref = imgui.ImTextureRef(int(render_target.color_texture.glo))
        imgui.image(image_ref,imgui.ImVec2(widget_size.x, widget_size.y))

        
    imgui.end_child()



if __name__ == "__main__":
    immapp.run(gui, window_title="ImGui Bundle - 2D Points & 3D Scene", window_size=(800, 800))

