# Standard library imports
import time
startup_start_time = time.time()
import math
import logging
from pprint import pformat
from typing import Any, List, Tuple, Dict
from enum import IntEnum

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
# ################# #

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
    my_point=imgui.ImVec2(50,50))
def gui():
    if gui.startup_end_time is None:
        gui.startup_end_time = time.time()
        logger.info(f"Startup time: {gui.startup_end_time - startup_start_time:.2f} seconds")
    
    # Configure imgui
    style = imgui.get_style()
    style.anti_aliased_lines = True
    style.anti_aliased_lines_use_tex = True
    style.anti_aliased_fill = True

    # setup main docking space
    # Main viewport
    # viewport = imgui.get_main_viewport()

    # Setup main dockspace window
    # imgui.set_next_window_pos(viewport.pos)
    # imgui.set_next_window_size(viewport.size)
    # imgui.set_next_window_viewport(viewport.id_)
    # flags = (
    #     imgui.WindowFlags_.no_title_bar
    #     | imgui.WindowFlags_.no_collapse
    #     | imgui.WindowFlags_.no_resize
    #     | imgui.WindowFlags_.no_move
    #     | imgui.WindowFlags_.no_bring_to_front_on_focus
    #     | imgui.WindowFlags_.no_nav_focus
    #     | imgui.WindowFlags_.menu_bar
    # )
    # imgui.push_style_var(imgui.StyleVar_.window_rounding, 0)
    # imgui.push_style_var(imgui.StyleVar_.window_border_size, 0)
    # imgui.begin("MainDockSpace", True)
    # imgui.end()
    # imgui.pop_style_var(2)

    # dockspace_id = imgui.get_id("MyDockSpace")
    # imgui.dock_space(dockspace_id, (0.0, 0.0), imgui.DockNodeFlags_.none)
    
    # Compute Camera
    camera = Camera()

    if imgui.begin_main_menu_bar():
        if imgui.begin_menu("File", True):
            clicked_open, _ = imgui.menu_item("Open", "Ctrl+O", False, True)
            if clicked_open:
                file_object = pfd.open_file(
                    title="Open fspy file"
                )
                file_paths = file_object.result()
                print("Selected file:", file_paths)
            clicked_exit, _ = imgui.menu_item("Exit", "Alt+F4", False, True)
            if clicked_exit:
                print("Exiting...")
            imgui.end_menu()
        if imgui.begin_menu("View", True):
            for theme in hello_imgui.ImGuiTheme_:
                activated, toggle = imgui.menu_item(f"{theme}", "", gui.theme == theme, True)
                if activated:
                    gui.theme = theme
                    hello_imgui.apply_theme(gui.theme)
            imgui.end_menu()
        imgui.end_main_menu_bar()   

    # Parameters
    display_size = imgui.get_io().display_size
    menu_bar_height = 30
    PANEL_FLAGS = imgui.WindowFlags_.always_auto_resize | imgui.WindowFlags_.no_move | imgui.WindowFlags_.no_resize | imgui.WindowFlags_.no_collapse | imgui.WindowFlags_.no_title_bar
    
    side_panel_width = 550
    with imgui_ctx.begin("Parameters", None):
        # imgui.text("First Axis")
        # ui.radio_group("##1st axis", "X", ["X", "Y", "Z"])
        # imgui.same_line()
        # ui.radio_group("##1st axis sign", "+", ["+", "-"])
        # imgui.new_line()

        # imgui.text("Second Axis")
        # ui.radio_group("##2nd axis", "X", ["X", "Y", "Z"])
        # imgui.same_line()
        # ui.radio_group("##2nd axis sign", "+", ["+", "-"])

        # imgui.new_line()
        # imgui.text("Solver Mode")
        # ui.radio_group("##mode", "1VP", ["1VP", "2VP"])

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


    imgui.push_style_var(imgui.StyleVar_.window_padding, imgui.ImVec2(0, 0))
    imgui.begin("Viewport2", None)
    content_size = imgui.ImVec2(720,576)
    ui.viewport.begin_viewport("Viewport2", None, borders=False)
    ui.viewport.setup_orthographic(0,0,content_size.x,content_size.y)

    # origin CP
    _, gui.origin_pixel = ui.viewport.control_point("o", gui.origin_pixel)

    # vanishing line controls
    line_control = ui.comp(ui.viewport.control_point)
    lines_control = ui.comp(line_control)
    _, gui.first_vanishing_lines_pixel = lines_control("z", gui.first_vanishing_lines_pixel, color=get_axis_color(gui.first_axis) )
    for line in gui.first_vanishing_lines_pixel:
        ui.viewport.render_guide_line(line[0], line[1], color=get_axis_color(gui.first_axis))

    gui.principal_point_pixel = glm.vec2(content_size.x / 2, content_size.y / 2)
    match gui.solver_mode:
        case SolverMode.OneVP:
            _, gui.second_vanishing_lines_pixel[0] = line_control("x", gui.second_vanishing_lines_pixel[0], color=get_axis_color(gui.second_axis))  
            ui.viewport.render_guide_line(gui.second_vanishing_lines_pixel[0][0], gui.second_vanishing_lines_pixel[0][1], color=get_axis_color(gui.second_axis))
            try:
                ###############################
                # 1. COMPUTE vanishing points #
                ###############################
                first_vanishing_point_pixel =  solver.least_squares_intersection_of_lines(
                    gui.first_vanishing_lines_pixel)
                
                # draw vanishing line to VP1
                VP1 = first_vanishing_point_pixel
                for A, B in gui.first_vanishing_lines_pixel:
                    P = sorted([A, B], key=lambda P: glm.distance2(P, VP1))[0]
                    ui.viewport.render_guide_line(P, VP1, get_axis_color(gui.first_axis, dim=True))
                ###################
                # 2. Solve Camera #
                ###################
                fovy = math.radians(gui.fov_degrees)
                focal_length_pixel = solver.focal_length_from_fov(fovy, content_size.y)
                camera_transform = solver.solve1vp(
                    content_size.x, 
                    content_size.y, 
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
                camera.setAspectRatio(content_size.x / content_size.y)
                camera.setFoVY(math.degrees(fovy))
            except Exception as e:
                imgui.push_style_color(imgui.Col_.text, (1.0, 0.2, 0.2, 1.0))
                imgui.text_wrapped(f"fspy error: {pformat(e)}")
                import traceback
                traceback.print_exc()
                imgui.pop_style_color()
        case SolverMode.TwoVP:
            _, gui.second_vanishing_lines_pixel = lines_control("x", gui.second_vanishing_lines_pixel, color=get_axis_color(gui.second_axis))
            for line in gui.second_vanishing_lines_pixel:
                ui.viewport.render_guide_line(line[0], line[1], color=get_axis_color(gui.second_axis, dim=True))
    
    # 3D scene
    # setup overscan perspective projection
    content_aspect = content_size.x / content_size.y
    widget_aspect = imgui.get_window_size().x / imgui.get_window_size().y
    overscan_fovy = 2 * glm.atan(glm.tan(fovy / 2) * content_aspect/widget_aspect )
    ui.viewport.setup_perspective(camera.viewMatrix(), max(fovy, overscan_fovy), widget_aspect, 0.1, 100.0)

    # draw grid and axes
    ui.viewport.render_grid_plane()
    ui.viewport.render_axes()

    # Render margins
    ui.viewport.setup_orthographic(0,0,content_size.x,content_size.y)
    ui.viewport.render_margins(imgui.ImVec2(0,0), imgui.ImVec2(content_size.x,content_size.y))
    ui.viewport.end_viewport()
    imgui.end()
    imgui.pop_style_var()  # WindowPadding

    # imgui.set_next_window_pos((display_size.x - side_panel_width, menu_bar_height))
    # imgui.set_next_window_size((side_panel_width, display_size.y))
    with imgui_ctx.begin("Results", None):
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

        
    


if __name__ == "__main__":
    from imgui_bundle import hello_imgui
    runner_params = hello_imgui.RunnerParams()
    runner_params.app_window_params.window_title = "Camera Spy"
    runner_params.imgui_window_params.menu_app_title = "Camera Spy"
    runner_params.app_window_params.window_geometry.size = (1200, 512)
    runner_params.app_window_params.restore_previous_geometry = True
    # runner_params.app_window_params.borderless = True
    # runner_params.app_window_params.borderless_movable = True
    # runner_params.app_window_params.borderless_resizable = True
    # runner_params.app_window_params.borderless_closable = True
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

