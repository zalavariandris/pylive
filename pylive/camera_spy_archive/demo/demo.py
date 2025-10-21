import math
from imgui_bundle import imgui, immapp
from pprint import pformat
from typing import Any, List, Tuple, Dict

# Configure logging to see shader compilation logs
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

import ui
from pylive.glrenderer.gllayers import GridLayer, RenderLayer, AxesLayer
from pylive.glrenderer.utils.render_target import RenderTarget
from pylive.glrenderer.utils.camera import Camera

import glm
from pylive.camera_spy import solver

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
        super().setup()
        self.grid.setup()
        self.axes.setup()
        self._initialized = True

    def release(self):
        if self.grid:
            self.grid.release()
            self.grid = None
        if self.axes:
            self.axes.release()
            self.axes = None
        self._initialized = False
        return super().release()
    
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


# ################# #
# Application State #
# ################# #

from enum import IntEnum
class SolverMode(IntEnum):
    OneVP = 0
    TwoVP = 1

class State:
    def __init__(self):
        # controlpoints
        self.origin_pixel: glm.vec2 =          glm.vec2(400, 400)
        self.principal_point_pixel: glm.vec2 = glm.vec2(400, 400)

        self.first_vanishing_lines_pixel: List[solver.LineSegmentType] = [
            (glm.vec2(240, 408), glm.vec2(355, 305)),
            (glm.vec2(501, 462), glm.vec2(502, 325))
        ]
        self.second_vanishing_lines_pixel: List[solver.LineSegmentType] = [
            [glm.vec2(350, 260), glm.vec2(550, 330)],
            [glm.vec2(440, 480), glm.vec2(240, 300)]
        ]

        # params
        self.scene_scale:float =                5.0
        self.first_axis:solver.Axis =           solver.Axis.PositiveZ
        self.second_axis:solver.Axis =          solver.Axis.PositiveX

        # options
        # self.quad_mode:bool =                   False
        self.overrides = dict()
        self.settings = dict()

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

    global state

    imgui.text("Camera Spy")    
    

    # Parameters
    _, state.first_axis = imgui.combo("first axis",   state.first_axis, solver.Axis._member_names_)
    _, state.second_axis = imgui.combo("second axis", state.second_axis, solver.Axis._member_names_)
    _, state.scene_scale = imgui.slider_float("scene_scale", state.scene_scale, 1.0, 100.0, "%.2f")
    _, state.settings["solver_mode"] = imgui.combo("mode", state.settings.get("solver_mode", SolverMode.OneVP), SolverMode._member_names_)
    # _, state.quad_mode = imgui.checkbox("quad mode", state.quad_mode)

    widget_size = imgui.get_content_region_avail()
    if imgui.begin_child("3d_viewport", widget_size):
        image_width, image_height = int(widget_size.x), int(widget_size.y)

        # Compute Camera
        camera = Camera()
        try:
            # Control Points
            from collections import defaultdict
            drag_line = ui.comp(ui.drag_point)
            drag_lines = ui.comp(drag_line)
            _, state.first_vanishing_lines_pixel = drag_lines("Z", state.first_vanishing_lines_pixel, color=ui.colors.BLUE)
            ui.draw.draw_lines(state.first_vanishing_lines_pixel, "", ui.colors.BLUE)
            

            # _, principal_point_pixel = drag_point("principal_point", principal_point_pixel)
            principal_point_pixel = glm.vec2(widget_size.x / 2, widget_size.y / 2)
            _, state.origin_pixel = ui.drag_point("origin", state.origin_pixel)

 
            match state.settings["solver_mode"]:
                case SolverMode.OneVP: # 1VP
                    ######
                    # UI #
                    ######)
                    _, state.settings["fov_degrees"] = imgui.slider_float("fov°", state.settings.get("fov_degrees", 60.0), 1.0, 179.0, "%.1f°")
                    _, state.second_vanishing_lines_pixel[0] = drag_line("X", state.second_vanishing_lines_pixel[0], color=ui.colors.RED)  
                    ui.draw.draw_lines(state.second_vanishing_lines_pixel[:1], "", ui.colors.RED)

                    ###############################
                    # 1. COMPUTE vanishing points #
                    ###############################
                    first_vanishing_point_pixel =  solver.least_squares_intersection_of_lines(
                        state.first_vanishing_lines_pixel)
                    
                    # draw vanishing line to VP1
                    VP1 = first_vanishing_point_pixel
                    for A, B in state.first_vanishing_lines_pixel:
                        P = sorted([A, B], key=lambda P: glm.distance2(P, VP1))[0]
                        ui.draw.draw_lines([(P, VP1)], "", ui.colors.BLUE_DIMMED)

                    ###################
                    # 2. Solve Camera #
                    ###################
                    fovy = math.radians(state.settings["fov_degrees"])
                    focal_length_pixel = solver.focal_length_from_fov(fovy, image_height)
                    view_orientation, position = solver.solve1vp(
                        image_width, 
                        image_height, 
                        first_vanishing_point_pixel,
                        focal_length_pixel,
                        principal_point_pixel,
                        state.origin_pixel,
                        state.first_axis,
                        state.second_axis,
                        state.scene_scale
                    )

                    view_translate_transform = glm.translate(glm.mat4(1.0), position)
                    view_rotation_transform = glm.mat4(view_orientation)
                    view_transform= view_rotation_transform * view_translate_transform

                    ###################
                    # 3. Adjust Camera Roll to match second vanishing lines
                    ###################
                    # Roll the camera based on the horizon line projected to 3D
                    roll_matrix = solver.compute_roll_matrix(
                        image_width, 
                        image_height, 
                        state.second_vanishing_lines_pixel[0],
                        projection_matrix=glm.perspective(fovy, image_width/image_height, 0.1, 100.0),
                        view_matrix=view_transform
                    )

                    view_transform = view_transform * roll_matrix

                    # create camera
                    camera = Camera()
                    camera.setFoVY(fovy)
                    camera.transform = glm.inverse(view_transform)
                    camera.setAspectRatio(widget_size.x / widget_size.y)
                    camera.setFoVY(math.degrees(fovy))

                case SolverMode.TwoVP: # 2VP
                    _, state.settings["quad_mode"] = imgui.checkbox("quad", state.settings.get("quad_mode", False))
                    if state.settings["quad_mode"]:
                        VL = state.first_vanishing_lines_pixel
                        state.second_vanishing_lines_pixel = [
                            (VL[0][0], VL[1][0]), 
                            (VL[0][1], VL[1][1])
                        ]
                    else:
                        _, state.second_vanishing_lines_pixel = drag_lines("X", state.second_vanishing_lines_pixel, color=ui.colors.RED)
                    ui.draw.draw_lines(state.second_vanishing_lines_pixel, "", ui.colors.RED)
                    ###############################
                    # 1. COMPUTE vanishing points #
                    ###############################
                    first_vanishing_point_pixel =  solver.least_squares_intersection_of_lines(
                        state.first_vanishing_lines_pixel)
                    
                    second_vanishing_point_pixel = solver.least_squares_intersection_of_lines(
                        state.second_vanishing_lines_pixel)
                    
                    # draw vanishing line to VP1
                    VP1 = first_vanishing_point_pixel
                    for A, B in state.first_vanishing_lines_pixel:
                        P = sorted([A, B], key=lambda P: glm.distance2(P, VP1))[0]
                        ui.draw.draw_lines([(P, VP1)], "", ui.colors.BLUE_DIMMED)
                    VP2 = second_vanishing_point_pixel
                    for A, B in state.second_vanishing_lines_pixel:
                        P = sorted([A, B], key=lambda P: glm.distance2(P, VP2))[0]
                        ui.draw.draw_lines([(P, VP2)], "", ui.colors.RED_DIMMED)

                    ###################
                    # 2. Solve Camera #
                    ###################
                    fovy, view_orientation, position = solver.solve2vp(
                        image_width, 
                        image_height, 
                        first_vanishing_point_pixel,
                        second_vanishing_point_pixel,
                        principal_point_pixel,
                        state.origin_pixel,
                        state.first_axis,
                        state.second_axis,
                        state.scene_scale
                    )

                    view_translate_transform = glm.translate(glm.mat4(1.0), position)
                    view_rotation_transform = glm.mat4(view_orientation)
                    view_transform= view_rotation_transform * view_translate_transform

                    # create camera
                    camera = Camera()
                    camera.setFoVY(fovy)
                    camera.transform = glm.inverse(view_transform)
                    camera.setAspectRatio(widget_size.x / widget_size.y)
                    camera.setFoVY(math.degrees(fovy))

            # ##############################
            # # Override Camera Parameters #
            # ##############################
            # imgui.text("Override Camera Parameters:")
            # state.overrides.setdefault('fov', None)
            # _, override_fov = imgui.checkbox("fov", state.overrides['fov'] is not None)
            # if _:
            #     state.overrides.setdefault('fov', math.degrees(fovy))
            #     _, new_fov_y_degrees = imgui.slider_float("fov_y (degrees)", math.degrees(fovy), 1.0, 179.0, "%.1f")
            #     state.overrides['fov'] = new_fov_y_degrees
            # else:
            #     imgui.text(f"fov_y (degrees): {math.degrees(fovy):.1f}")
            
            # if state.overrides['fov'] is not None:
            #     camera.setFoVY(state.overrides['fov'])

            # # Project vanishing Points
            # VP_X, VP_Y, VP_Z = solver.vanishing_points_from_camera(
            #     camera.viewMatrix(),
            #     camera.projectionMatrix(),
            #     (0,0,image_width,image_height)
            # )
            # # draw.points([VP_X, VP_Z], ["", ""], [RED, BLUE], shapes='x')

            # # calculate actual vanishing lines
            # VL_Z = map(lambda line: (line[0]/2+line[1]/2, VP_Z), state.first_vanishing_lines_pixel)
            # corrected_first_vanishing_lines = []
            # for corrected_line, current_line in zip(VL_Z, state.first_vanishing_lines_pixel):
            #     from utils.geo import closest_point_on_line
            #     P_corrected = closest_point_on_line(current_line[0], corrected_line)
            #     Q_corrected = closest_point_on_line(current_line[1], corrected_line)
            #     corrected_first_vanishing_lines.append((P_corrected, Q_corrected))

            
            # VL_X = map(lambda line: (line[0]/2+line[1]/2, VP_X), state.second_vanishing_lines_pixel)
            # corrected_second_vanishing_lines = []
            # for corrected_line, current_line in zip(VL_X, state.second_vanishing_lines_pixel):
            #     from utils.geo import closest_point_on_line
            #     P_corrected = closest_point_on_line(current_line[0], corrected_line)
            #     Q_corrected = closest_point_on_line(current_line[1], corrected_line)
            #     corrected_second_vanishing_lines.append((P_corrected, Q_corrected))

            # # Draw corrected lines
            # draw.lines(corrected_first_vanishing_lines, "", BLUE)
            # draw.lines(corrected_second_vanishing_lines, "", RED)
            # # extend to vp
            # draw.lines([(line[0], VP_Z) for line in corrected_first_vanishing_lines], "", BLUE_DIMMED)
            # draw.lines([(line[0], VP_X) for line in corrected_second_vanishing_lines], "", RED_DIMMED)

            # # draw control offsets
            # for line, corrected in  zip(state.first_vanishing_lines_pixel, corrected_first_vanishing_lines):
            #     draw.lines([(line[0], corrected[0])], "", BLUE_DIMMED)
            #     draw.lines([(line[1], corrected[1])], "", BLUE_DIMMED)

            # for line, corrected in  zip(state.second_vanishing_lines_pixel, corrected_second_vanishing_lines):
            #     draw.lines([(line[0], corrected[0])], "", RED_DIMMED)
            #     draw.lines([(line[1], corrected[1])], "", RED_DIMMED)
            

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

        # Draw 3D grid
        view = camera.viewMatrix()
        projection = glm.perspective(math.radians(camera.fovy), camera.aspect_ratio, 0.1, 100.0)
        viewport = (0, 0, int(widget_size.x), int(widget_size.y))
        ui.draw_grid3D(view, projection, viewport)

        
    imgui.end_child()


if __name__ == "__main__":
    immapp.run(gui, window_title="ImGui Bundle - 2D Points & 3D Scene", window_size=(800, 800))

