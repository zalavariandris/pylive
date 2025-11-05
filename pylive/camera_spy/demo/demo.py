# Standard library imports
import time
startup_start_time = time.time()
import math
import logging
from pprint import pformat
from typing import Any, List, Tuple, Dict
from enum import IntEnum
from PIL import Image

# Third-party imports
import glm
from imgui_bundle import imgui, immapp, imgui_ctx, hello_imgui
from imgui_bundle import portable_file_dialogs as pfd

# Local application imports
from pylive.glrenderer.utils.camera import Camera
from pylive.camera_spy import solver

import ui

# Configure logging to see shader compilation logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_axis_color(axis:solver.Axis, dim:bool=False) -> Tuple[float, float, float]:
    match axis:
        case solver.Axis.PositiveX | solver.Axis.NegativeX:
            return ui.colors.RED if not dim else ui.colors.RED_DIMMED
        case solver.Axis.PositiveY | solver.Axis.NegativeY:
            return ui.colors.GREEN if not dim else ui.colors.GREEN_DIMMED
        case solver.Axis.PositiveZ | solver.Axis.NegativeZ:
            return ui.colors.BLUE if not dim else ui.colors.BLUE_DIMMED
        case _:
            return (1.0, 1.0, 1.0)

# ################# #
# Application State #
# ################# #)


class Rect:
    def __init__(self, left:float, right:float, top:float, bottom:float):
        self.left = left
        self.right = right
        self.top = top
        self.bottom = bottom

    @property
    def width(self) -> float:
        return self.right - self.left
    
    @property
    def height(self) -> float:
        return self.bottom - self.top

    @property
    def center(self) -> Tuple[float, float]:
        return (self.left + self.right) / 2, (self.top + self.bottom) / 2

    @property
    def topleft(self) -> Tuple[float, float]:
        return self.left, self.top

    @property
    def topright(self) -> Tuple[float, float]:
        return self.right, self.top

    @property
    def bottomleft(self) -> Tuple[float, float]:
        return self.left, self.bottom

    @property
    def bottomright(self) -> Tuple[float, float]:
        return self.right, self.bottom

class SolverMode(IntEnum):
    OneVP = 0
    TwoVP = 1


@immapp.static(
    first_vanishing_lines_pixel = [
        (glm.vec2(240, 408), glm.vec2(355, 305)),
        (glm.vec2(501, 462), glm.vec2(502, 325))
    ],
    second_vanishing_lines_pixel = [
        [glm.vec2(350, 260), glm.vec2(550, 330)],
        [glm.vec2(440, 480), glm.vec2(240, 300)]
    ],
    solver_mode=SolverMode.OneVP,
    origin_pixel=glm.vec2(400, 300),
    principal_point_pixel=glm.vec2(400, 300),
    theme=hello_imgui.ImGuiTheme_.darcula_darker,
    fov_degrees=60.0,
    quad_mode=False,
    scene_scale=5.0,
    first_axis=solver.Axis.PositiveZ,
    second_axis=solver.Axis.PositiveX,
    startup_end_time = None,
    my_point=imgui.ImVec2(50,50),
    image_texture_ref=None,
    content_size = imgui.ImVec2(720,720),
    pan_and_zoom_matrix = glm.identity(glm.mat4))
def gui():
    if gui.startup_end_time is None:
        gui.startup_end_time = time.time()
        logger.info(f"Startup time: {gui.startup_end_time - startup_start_time:.2f} seconds")
    
    # Configure imgui
    style = imgui.get_style()
    style.anti_aliased_lines = True
    style.anti_aliased_lines_use_tex = True
    style.anti_aliased_fill = True
    
    # Compute Camera
    camera = Camera()

    # if imgui.begin_main_menu_bar():
    #     if imgui.begin_menu("File", True):
    #         clicked_open, _ = imgui.menu_item("Open", "Ctrl+O", False, True)
    #         if clicked_open:
    #             file_object = pfd.open_file(
    #                 title="Open fspy file"
    #             )
    #             file_paths = file_object.result()
    #             if file_paths:
    #                 image_path = file_paths[0]
    #                 try:
    #                     # load image data
    #                     image = Image.open(image_path).convert("RGBA")
    #                     width, height = image.size
    #                     image_data = image.tobytes()

    #                     # Create OpenGL texture from image  
    #                     # Add at the top of your file
    #                     from OpenGL.GL import glGenTextures, glBindTexture, glTexImage2D, glTexParameteri, GL_TEXTURE_2D, GL_RGBA, GL_UNSIGNED_BYTE, GL_LINEAR

    #                     def create_texture_rgba(image_data, width, height):
    #                         tex_id = glGenTextures(1)
    #                         glBindTexture(GL_TEXTURE_2D, tex_id)
    #                         glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, image_data)
    #                         glTexParameteri(GL_TEXTURE_2D, 0x2801, GL_LINEAR)  # GL_TEXTURE_MIN_FILTER
    #                         glTexParameteri(GL_TEXTURE_2D, 0x2800, GL_LINEAR)  # GL_TEXTURE_MAG_FILTER
    #                         return tex_id
    #                     texture_id = create_texture_rgba(image_data, width, height)
    #                     gui.content_size = imgui.ImVec2(width, height)
    #                     gui.image_texture_ref = imgui.ImTextureRef(texture_id)


    #                 except Exception as e:
    #                     imgui.open_popup("Error##fspy_open")
    #         clicked_exit, _ = imgui.menu_item("Exit", "Alt+F4", False, True)
    #         if clicked_exit:
    #             print("Exiting...")
    #         imgui.end_menu()
    #     if imgui.begin_menu("View", True):
    #         for theme in hello_imgui.ImGuiTheme_:
    #             activated, toggle = imgui.menu_item(f"{theme}", "", gui.theme == theme, True)
    #             if activated:
    #                 gui.theme = theme
    #                 hello_imgui.apply_theme(gui.theme)
    #         imgui.end_menu()
    #     imgui.end_main_menu_bar()   

    # Parameters
    display_size = imgui.get_io().display_size
    menu_bar_height = 30
    PANEL_FLAGS = imgui.WindowFlags_.always_auto_resize | imgui.WindowFlags_.no_move | imgui.WindowFlags_.no_resize | imgui.WindowFlags_.no_collapse | imgui.WindowFlags_.no_title_bar
    side_panel_width = 550
    with imgui_ctx.begin("Parameters", None):
        imgui.set_next_item_width(150)
        _, gui.solver_mode = imgui.combo("mode", gui.solver_mode, SolverMode._member_names_)
        imgui.set_next_item_width(150)
        _, gui.first_axis = imgui.combo("first axis",   gui.first_axis, solver.Axis._member_names_)
        imgui.set_next_item_width(150)
        _, gui.second_axis = imgui.combo("second axis", gui.second_axis, solver.Axis._member_names_)
        imgui.set_next_item_width(150)
        _, gui.scene_scale = imgui.slider_float("scene_scale", gui.scene_scale, 1.0, 100.0, "%.2f")
        

        match gui.solver_mode:
            case SolverMode.OneVP:
                imgui.set_next_item_width(150)
                _, gui.fov_degrees = imgui.slider_float("fov°", gui.fov_degrees, 1.0, 179.0, "%.1f°")
            case SolverMode.TwoVP:
                _, gui.quad_mode = imgui.checkbox("quad", gui.quad_mode)

    # draw image
    if gui.image_texture_ref is not None:
        tl = ui.viewport._project((0,0))
        br = ui.viewport._project((gui.content_size.x, gui.content_size.y))
        imgui.set_cursor_screen_pos(tl)
        imgui.image(gui.image_texture_ref, imgui.ImVec2(br.x - tl.x, br.y - tl.y))

    # Solve for camera
    first_vanishing_point_pixel:glm.vec2|None = None
    second_vanishing_point_pixel:glm.vec2|None = None
    camera:Camera|None = None

    gui.principal_point_pixel = glm.vec2(gui.content_size.x / 2, gui.content_size.y / 2)
    match gui.solver_mode:
        case SolverMode.OneVP:
            try:
                ###############################
                # 1. COMPUTE vanishing points #
                ###############################
                first_vanishing_point_pixel =  solver.least_squares_intersection_of_lines(gui.first_vanishing_lines_pixel)
                

                ###################
                # 2. Solve Camera #
                ###################
                fovy = math.radians(gui.fov_degrees)
                focal_length_pixel = solver.focal_length_from_fov(fovy, gui.content_size.y)
                camera_transform = solver.solve1vp(
                    gui.content_size.x, 
                    gui.content_size.y, 
                    first_vanishing_point_pixel,
                    gui.second_vanishing_lines_pixel[0],
                    focal_length_pixel,
                    gui.principal_point_pixel,
                    gui.origin_pixel,
                    gui.first_axis,
                    gui.second_axis,
                    gui.scene_scale
                )

                # create camera
                camera = Camera()
                camera.setFoVY(fovy)
                
                camera.transform = camera_transform
                camera.setAspectRatio(gui.content_size.x / gui.content_size.y)
                camera.setFoVY(math.degrees(fovy))
            except Exception as e:
                imgui.push_style_color(imgui.Col_.text, (1.0, 0.2, 0.2, 1.0))
                imgui.text_wrapped(f"fspy error: {pformat(e)}")
                import traceback
                traceback.print_exc()
                imgui.pop_style_color()

        case SolverMode.TwoVP:
            try:
                # compute vanishing points
                first_vanishing_point_pixel =  solver.least_squares_intersection_of_lines(
                    gui.first_vanishing_lines_pixel)
                second_vanishing_point_pixel = solver.least_squares_intersection_of_lines(
                    gui.second_vanishing_lines_pixel)

                fovy, camera_transform = solver.solve2vp(
                    gui.content_size.x, 
                    gui.content_size.y, 
                    first_vanishing_point_pixel,
                    second_vanishing_point_pixel,
                    gui.principal_point_pixel,
                    gui.origin_pixel,
                    gui.first_axis,
                    gui.second_axis,
                    gui.scene_scale
                )

                # create camera
                camera = Camera()
                camera.setFoVY(fovy)
                camera.transform = camera_transform
                camera.setAspectRatio(gui.content_size.x / gui.content_size.y)
                camera.setFoVY(math.degrees(fovy))
            except Exception as e:
                imgui.push_style_color(imgui.Col_.text, (1.0, 0.2, 0.2, 1.0))
                imgui.text_wrapped(f"fspy error: {pformat(e)}")
                import traceback
                traceback.print_exc()
                imgui.pop_style_color()

    if imgui.begin("Viewport3"):
        if ui.viewer.begin_viewer("viewer3", content_size=gui.content_size, size=imgui.ImVec2(-1,-1), coordinate_system="top-left"):
            # control points
            _, gui.origin_pixel = ui.viewer.control_point("o", gui.origin_pixel)
            control_line = ui.comp(ui.viewer.control_point)
            control_lines = ui.comp(control_line)
            _, gui.first_vanishing_lines_pixel = control_lines("z", gui.first_vanishing_lines_pixel, color=get_axis_color(gui.first_axis) )
            for line in gui.first_vanishing_lines_pixel:
                ui.viewer.guide(line[0], line[1], color=get_axis_color(gui.first_axis))

            match gui.solver_mode:
                case SolverMode.OneVP:
                    _, gui.second_vanishing_lines_pixel[0] = control_line("x", gui.second_vanishing_lines_pixel[0], color=get_axis_color(gui.second_axis))  
                    ui.viewer.guide(gui.second_vanishing_lines_pixel[0][0], gui.second_vanishing_lines_pixel[0][1], color=get_axis_color(gui.second_axis))
                
                case SolverMode.TwoVP:
                    _, gui.second_vanishing_lines_pixel = control_lines("x", gui.second_vanishing_lines_pixel, color=get_axis_color(gui.second_axis) )
                    for line in gui.second_vanishing_lines_pixel:
                        ui.viewer.guide(line[0], line[1], color=get_axis_color(gui.second_axis))

            if first_vanishing_point_pixel is not None:
                for line in gui.first_vanishing_lines_pixel:
                    P = sorted([line[0], line[1]], key=lambda P: glm.distance2(P, first_vanishing_point_pixel))[0]
                    ui.viewer.guide(P, first_vanishing_point_pixel, get_axis_color(gui.first_axis, dim=True))

            if second_vanishing_point_pixel is not None:
                for line in gui.second_vanishing_lines_pixel:
                    P = sorted([line[0], line[1]], key=lambda P: glm.distance2(P, second_vanishing_point_pixel))[0]
                    ui.viewer.guide(P, second_vanishing_point_pixel, get_axis_color(gui.second_axis, dim=True))

            if camera is not None:
                if ui.viewer.begin_scene(glm.scale(camera.projectionMatrix(), glm.vec3(1.0, -1.0, 1.0)), camera.viewMatrix()):
                    # draw the grid
                    for A, B in ui.viewer.make_gridXZ_lines(step=1, size=10):
                        ui.viewer.guide(A, B, ui.colors.WHITE_DIMMED)
                    ui.viewer.axes(length=1.0)
                ui.viewer.end_scene()
        ui.viewer.end_viewer()

    imgui.end()

    # imgui.set_next_window_pos((display_size.x - side_panel_width, menu_bar_height))
    # imgui.set_next_window_size((side_panel_width, display_size.y))
    if imgui.begin("Results", None):
        if camera is not None:
            x, y, z = solver.extract_euler_angle(camera.transform, order="ZXY")
            pos = camera.getPosition()
            matrix = [camera.transform[j][i] for i in range(4) for j in range(4)]
            imgui.input_text_multiline("results", f"{",\n".join([", ".join([f"{v:.3f}" for v in row]) for row in camera.transform])}", size=None, flags=imgui.InputTextFlags_.read_only)
            imgui.input_float4("matrix##row1", matrix[0:4], "%.3f", imgui.InputTextFlags_.read_only)
            imgui.input_float4("##matrixrow2", matrix[4:8], "%.3f", imgui.InputTextFlags_.read_only)
            imgui.input_float4("##matrixrow3", matrix[8:12], "%.3f", imgui.InputTextFlags_.read_only)
            imgui.input_float4("##matrixrow4", matrix[12:16], "%.3f", imgui.InputTextFlags_.read_only)
            imgui.input_float4("quaternion", (3,3,3,4), "%.3f", imgui.InputTextFlags_.read_only)
            imgui.input_float3("translate", camera.getPosition(), "%.3f", imgui.InputTextFlags_.read_only)
            imgui.input_float3("rotate", (x,y,z), "%.3f", imgui.InputTextFlags_.read_only)

            if gui.image_texture_ref is not None:
                imgui.image(gui.image_texture_ref, imgui.ImVec2(128, 128))
    imgui.end()

if __name__ == "__main__":
    from imgui_bundle import hello_imgui
    runner_params = hello_imgui.RunnerParams()
    runner_params.app_window_params.window_title = "Camera Spy"
    runner_params.imgui_window_params.menu_app_title = "Camera Spy"
    runner_params.app_window_params.window_geometry.size = (1200, 512)
    runner_params.app_window_params.restore_previous_geometry = True
    
    # Enable continuous rendering during window resize
    runner_params.fps_idling.enable_idling = False
    runner_params.app_window_params.repaint_during_resize_gotcha_reentrant_repaint = True

    # Use the proper callbacks
    # runner_params.callbacks.load_additional_fonts = load_fonts
    # runner_params.callbacks.setup_imgui_style = setup_theme  # This is the correct callback for styling
    runner_params.callbacks.show_gui = gui
    runner_params.imgui_window_params.default_imgui_window_type = (
        hello_imgui.DefaultImGuiWindowType.provide_full_screen_dock_space
    )
    hello_imgui.run(runner_params)
    # immapp.run(gui, 
    #            window_title="Camera Spy", 
    #            window_size=(1200, 512), 
    #            with_implot3d=True
    # )

