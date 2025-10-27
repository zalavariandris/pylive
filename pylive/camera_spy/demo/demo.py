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
from pylive import imx
from pylive.glrenderer.utils.camera import Camera
from pylive.camera_spy import solver

# Configure logging to see shader compilation logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_axis_color(axis:solver.Axis, dim:bool=False) -> Tuple[float, float, float]:
    match axis:
        case solver.Axis.PositiveX | solver.Axis.NegativeX:
            return imx.colors.RED if not dim else imx.colors.RED_DIMMED
        case solver.Axis.PositiveY | solver.Axis.NegativeY:
            return imx.colors.GREEN if not dim else imx.colors.GREEN_DIMMED
        case solver.Axis.PositiveZ | solver.Axis.NegativeZ:
            return imx.colors.BLUE if not dim else imx.colors.BLUE_DIMMED
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
    PANEL_FLAGS = imgui.WindowFlags_.always_auto_resize | imgui.WindowFlags_.no_move | imgui.WindowFlags_.no_resize | imgui.WindowFlags_.no_collapse | imgui.WindowFlags_.no_title_bar
    
    side_panel_width = 300
    # imgui.set_next_window_pos((0,24))
    # imgui.set_next_window_size((side_panel_width, display_size.y))
    with imgui_ctx.begin("Parameters", None):
        _, gui.first_axis = imgui.combo("first axis",   gui.first_axis, solver.Axis._member_names_)
        _, gui.second_axis = imgui.combo("second axis", gui.second_axis, solver.Axis._member_names_)
        _, gui.scene_scale = imgui.slider_float("scene_scale", gui.scene_scale, 1.0, 100.0, "%.2f")
        _, gui.solver_mode = imgui.combo("mode", gui.solver_mode, SolverMode._member_names_)

        match gui.solver_mode:
            case SolverMode.OneVP:
                _, gui.fov_degrees = imgui.slider_float("fov°", gui.fov_degrees, 1.0, 179.0, "%.1f°")
            case SolverMode.TwoVP:
                _, gui.quad_mode = imgui.checkbox("quad", gui.quad_mode)

    with imgui_ctx.begin("MyPlotWindow", None):
        _, gui.my_point.x = imgui.slider_float("x", gui.my_point.x, 0, 100)
        _, gui.my_point.y = imgui.slider_float("y", gui.my_point.y, 0, 100)
        if imx.viewport.begin_viewport("my_plot", (100,100)):
            imx.viewport.setup_orthographic(0,0,100,100)
            _, gui.my_point = imx.viewport.point_handle("P1", gui.my_point)
        imx.viewport.end_viewport()

    # imgui.set_next_window_pos((side_panel_width,24))
    # imgui.set_next_window_size((display_size.x - side_panel_width*2, display_size.y))
    with imgui_ctx.begin("3d_viewport_child", None, PANEL_FLAGS):
        widget_size = imgui.get_content_region_avail()
        image_width, image_height = int(widget_size.x), int(widget_size.y)

        #######################
        # UI Viewport Handles #
        #######################
        match gui.solver_mode:
            case SolverMode.OneVP:
                ...
            case SolverMode.TwoVP:
                ...

        # with imgui_ctx.begin_drag_drop_target() as target:
        #     print(target)
            # payload = imgui.accept_drag_drop_payload("MY_PAYLOAD_TYPE")
            # if payload is not None:
                # print("Dropped payload:", payload.data.decode("utf-8"))

        try:
            # Control Points
            drag_line = imx.comp(imx.drag_point)
            drag_lines = imx.comp(drag_line)
            _, gui.first_vanishing_lines_pixel = drag_lines("Z", gui.first_vanishing_lines_pixel, color=get_axis_color(gui.first_axis))
            imx.draw.draw_lines(gui.first_vanishing_lines_pixel, "", get_axis_color(gui.first_axis))

            # _, principal_point_pixel = drag_point("principal_point", principal_point_pixel)
            principal_point_pixel = glm.vec2(widget_size.x / 2, widget_size.y / 2)
            _, gui.origin_pixel = imx.drag_point("origin", gui.origin_pixel)
 
            match gui.solver_mode:
                case SolverMode.OneVP: # 1VP
                    ######
                    # UI #
                    ######)
                    _, gui.second_vanishing_lines_pixel[0] = drag_line("X", gui.second_vanishing_lines_pixel[0], color=get_axis_color(gui.second_axis))  
                    imx.draw.draw_lines(gui.second_vanishing_lines_pixel[:1], "", get_axis_color(gui.second_axis))

                    ###############################
                    # 1. COMPUTE vanishing points #
                    ###############################
                    first_vanishing_point_pixel =  solver.least_squares_intersection_of_lines(
                        gui.first_vanishing_lines_pixel)
                    
                    # draw vanishing line to VP1
                    VP1 = first_vanishing_point_pixel
                    for A, B in gui.first_vanishing_lines_pixel:
                        P = sorted([A, B], key=lambda P: glm.distance2(P, VP1))[0]
                        imx.draw.draw_lines([(P, VP1)], "", get_axis_color(gui.first_axis, dim=True))

                    ###################
                    # 2. Solve Camera #
                    ###################
                    fovy = math.radians(gui.fov_degrees)
                    focal_length_pixel = solver.focal_length_from_fov(fovy, image_height)
                    camera_transform = solver.solve1vp(
                        image_width, 
                        image_height, 
                        first_vanishing_point_pixel,
                        gui.second_vanishing_lines_pixel[0],
                        focal_length_pixel,
                        principal_point_pixel,
                        gui.origin_pixel,
                        gui.first_axis,
                        gui.second_axis,
                        gui.scene_scale
                    )

                    # create camera
                    camera = Camera()
                    camera.setFoVY(fovy)
                    
                    camera.transform = camera_transform
                    camera.setAspectRatio(widget_size.x / widget_size.y)
                    camera.setFoVY(math.degrees(fovy))

                case SolverMode.TwoVP: # 2VP
                    
                    if gui.quad_mode:
                        VL = gui.first_vanishing_lines_pixel
                        gui.second_vanishing_lines_pixel = [
                            (VL[0][0], VL[1][0]), 
                            (VL[0][1], VL[1][1])
                        ]
                    else:
                        _, gui.second_vanishing_lines_pixel = drag_lines("X", gui.second_vanishing_lines_pixel, color=get_axis_color(gui.second_axis))
                    imx.draw.draw_lines(gui.second_vanishing_lines_pixel, "", get_axis_color(gui.second_axis, dim=True))
                    ###############################
                    # 1. COMPUTE vanishing points #
                    ###############################
                    first_vanishing_point_pixel =  solver.least_squares_intersection_of_lines(
                        gui.first_vanishing_lines_pixel)
                    
                    second_vanishing_point_pixel = solver.least_squares_intersection_of_lines(
                        gui.second_vanishing_lines_pixel)
                    
                    # draw vanishing line to VP1
                    VP1 = first_vanishing_point_pixel
                    for A, B in gui.first_vanishing_lines_pixel:
                        P = sorted([A, B], key=lambda P: glm.distance2(P, VP1))[0]
                        imx.draw.draw_lines([(P, VP1)], "", get_axis_color(gui.first_axis, dim=True))
                    VP2 = second_vanishing_point_pixel
                    for A, B in gui.second_vanishing_lines_pixel:
                        P = sorted([A, B], key=lambda P: glm.distance2(P, VP2))[0]
                        imx.draw.draw_lines([(P, VP2)], "", get_axis_color(gui.second_axis, dim=True))

                    ###################
                    # 2. Solve Camera #
                    ###################
                    fovy, camera_transform = solver.solve2vp(
                        image_width, 
                        image_height, 
                        first_vanishing_point_pixel,
                        second_vanishing_point_pixel,
                        principal_point_pixel,
                        gui.origin_pixel,
                        gui.first_axis,
                        gui.second_axis,
                        gui.scene_scale
                    )

                    # create camera
                    camera = Camera()
                    camera.setFoVY(fovy)
                    camera.transform = camera_transform
                    camera.setAspectRatio(widget_size.x / widget_size.y)
                    camera.setFoVY(math.degrees(fovy))            

        except Exception as e:
            imgui.push_style_color(imgui.Col_.text, (1.0, 0.2, 0.2, 1.0))
            imgui.text_wrapped(f"fspy error: {pformat(e)}")
            import traceback
            traceback.print_exc()
            imgui.pop_style_color()

        # Render Scene
        gl_size = widget_size * imgui.get_io().display_framebuffer_scale
        # render_target.resize(int(gl_size.x), int(gl_size.y))
        # with render_target:
        #     render_target.clear(0.1, 0.1, 0.1, 0.0)  # Clear with dark gray background
        #     scene_layer.render(camera)

        # # Display the framebuffer texture in ImGui
        # imgui.set_cursor_pos(imgui.ImVec2(0,0))
        # image_ref = imgui.ImTextureRef(int(render_target.color_texture.glo))
        # imgui.image(image_ref,imgui.ImVec2(widget_size.x, widget_size.y))

        # Draw 3D grid
        view = camera.viewMatrix()
        projection = glm.perspective(math.radians(camera.fovy), camera._aspect_ratio, 0.1, 100.0)
        viewport = (0, 0, int(widget_size.x), int(widget_size.y))
        imx.draw_grid3D(view, projection, viewport)

    imgui.set_next_window_pos((display_size.x - side_panel_width, 24))
    imgui.set_next_window_size((side_panel_width, display_size.y))
    with imgui_ctx.begin("Results", None, PANEL_FLAGS):
        x, y, z = solver.extract_euler_angle(camera.transform, order="ZXY")
        pos = camera.getPosition()
        imgui.input_text_multiline("results", "text",size=None, flags=imgui.InputTextFlags_.read_only)
        
        matrix = [camera.transform[j][i] for i in range(4) for j in range(4)]
        imgui.input_float4("matrix##row1", matrix[0:4], "%.3f", imgui.InputTextFlags_.read_only)
        imgui.input_float4("##matrixrow2", matrix[4:8], "%.3f", imgui.InputTextFlags_.read_only)
        imgui.input_float4("##matrixrow3", matrix[8:12], "%.3f", imgui.InputTextFlags_.read_only)
        imgui.input_float4("##matrixrow4", matrix[12:16], "%.3f", imgui.InputTextFlags_.read_only)

        

        imgui.input_text("translate", f"{pos.x:.2f}, {pos.y:.2f}, {pos.z:.2f}",                               flags=imgui.InputTextFlags_.read_only)
        imgui.input_text("rotate",    f"{math.degrees(x):.0f}, {math.degrees(y):.0f}, {math.degrees(z):.0f}", flags=imgui.InputTextFlags_.read_only)
        
        imgui.text(f"translate: {pos.x:.2f}, {pos.y:.2f}, {pos.z:.2f}")
        imgui.text(f"rotate:    {math.degrees(x):.0f}, {math.degrees(y):.0f}, {math.degrees(z):.0f}")

        imgui.input_float4("quaternion", (3,3,3,4), "%.3f", imgui.InputTextFlags_.read_only)
        imgui.input_float3("translate", camera.getPosition(), "%.3f", imgui.InputTextFlags_.read_only)
        imgui.input_float3("rotate", (x,y,z), "%.3f", imgui.InputTextFlags_.read_only)

        
    


if __name__ == "__main__":
    immapp.run(gui, window_title="Camera Spy", window_size=(1200, 512), with_implot3d=True)

