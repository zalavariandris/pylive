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
import numpy as np
from imgui_bundle import imgui, immapp, imgui_ctx, hello_imgui, immvision, icons_fontawesome_4
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

class SolverMode(IntEnum):
    OneVP = 0
    TwoVP = 1

# ################# #
# Application State #
# ################# #)
class App:
    def __init__(self):
        self.first_vanishing_lines_pixel = [
            (glm.vec2(240, 408), glm.vec2(355, 305)),
            (glm.vec2(501, 462), glm.vec2(502, 325))
        ]
        self.second_vanishing_lines_pixel = [
            [glm.vec2(350, 260), glm.vec2(550, 330)],
            [glm.vec2(440, 480), glm.vec2(240, 300)]
        ]
        self.solver_mode=SolverMode.OneVP
        self.origin_pixel=glm.vec2(400, 300)
        self.principal_point_pixel=glm.vec2(400, 300)
        self.theme=hello_imgui.ImGuiTheme_.darcula_darker
        self.fov_degrees=60.0
        self.quad_mode=False
        self.scene_scale=5.0
        self.first_axis=solver.Axis.PositiveZ
        self.second_axis=solver.Axis.PositiveX
        self.startup_end_time = None
        self.my_point=imgui.ImVec2(50,50)
        self.image_texture_ref=None
        self.content_size = imgui.ImVec2(720,720)
        self.pan_and_zoom_matrix = glm.identity(glm.mat4)
        self.first_vanishing_point_pixel:glm.vec2|None = None
        self.second_vanishing_point_pixel:glm.vec2|None = None
        self.camera:Camera|None = None

    def gui(self):
        if self.startup_end_time is None:
            self.startup_end_time = time.time()
            logger.info(f"Startup time: {self.startup_end_time - startup_start_time:.2f} seconds")
        
        # Compute Camera
        self.camera = Camera()

        # Parameters
        style = imgui.get_style()
        display_size = imgui.get_io().display_size
        menu_bar_height = 0
        PANEL_FLAGS = imgui.WindowFlags_.always_auto_resize | imgui.WindowFlags_.no_move | imgui.WindowFlags_.no_resize | imgui.WindowFlags_.no_collapse | imgui.WindowFlags_.no_title_bar
        
        imgui.push_style_color(imgui.Col_.window_bg, (0.2, 0.2, 0.2, 0.0))
        imgui.set_next_window_pos(imgui.ImVec2(style.window_padding.x, display_size.y/2), imgui.Cond_.always, imgui.ImVec2(0.0, 0.5))
        if imgui.begin("Parameters", None, imgui.WindowFlags_.always_auto_resize | imgui.WindowFlags_.no_move | imgui.WindowFlags_.no_resize | imgui.WindowFlags_.no_collapse | imgui.WindowFlags_.no_title_bar):
            self.show_parameters()
        imgui.end()
        imgui.pop_style_color()

        self.solve()

        # fullscreen viewer
        imgui.set_next_window_pos(imgui.ImVec2(0, menu_bar_height))
        imgui.set_next_window_size(imgui.ImVec2(display_size.x, display_size.y - menu_bar_height))       
        if imgui.begin("Viewport3", None, imgui.WindowFlags_.no_bring_to_front_on_focus | imgui.WindowFlags_.no_move | imgui.WindowFlags_.no_resize | imgui.WindowFlags_.no_collapse | imgui.WindowFlags_.no_title_bar):
            self.show_viewer()
        imgui.end()

        imgui.push_style_color(imgui.Col_.window_bg, (0.2, 0.2, 0.2, 0.0))
        imgui.set_next_window_pos(imgui.ImVec2(display_size.x-style.window_padding.x, display_size.y/2), imgui.Cond_.always, imgui.ImVec2(1.0, 0.5))
        if imgui.begin("Results", None, imgui.WindowFlags_.always_auto_resize | imgui.WindowFlags_.no_move | imgui.WindowFlags_.no_resize | imgui.WindowFlags_.no_collapse | imgui.WindowFlags_.no_title_bar):
            self.show_results()
        imgui.end()
        imgui.pop_style_color()

        
        if imgui.begin("style editor"):
            imgui.show_style_editor()
        imgui.end()
        

    def show_parameters(self):
        imgui.set_next_item_width(150)
        _, self.solver_mode = imgui.combo("mode", self.solver_mode, SolverMode._member_names_)
        imgui.set_next_item_width(150)
        _, self.first_axis = imgui.combo("first axis",   self.first_axis, solver.Axis._member_names_)
        imgui.set_next_item_width(150)
        _, self.second_axis = imgui.combo("second axis", self.second_axis, solver.Axis._member_names_)
        imgui.set_next_item_width(150)
        _, self.scene_scale = imgui.slider_float("scene  scale", self.scene_scale, 1.0, 100.0, "%.2f")
        

        match self.solver_mode:
            case SolverMode.OneVP:
                imgui.set_next_item_width(150)
                _, self.fov_degrees = imgui.slider_float("fov°", self.fov_degrees, 1.0, 179.0, "%.1f°")
            case SolverMode.TwoVP:
                _, self.quad_mode = imgui.checkbox("quad", self.quad_mode)

    def solve(self):
        # Solve for camera
        self.first_vanishing_point_pixel:glm.vec2|None = None
        self.second_vanishing_point_pixel:glm.vec2|None = None
        self.camera:Camera|None = None

        self.principal_point_pixel = glm.vec2(self.content_size.x / 2, self.content_size.y / 2)
        match self.solver_mode:
            case SolverMode.OneVP:
                try:
                    ###############################
                    # 1. COMPUTE vanishing points #
                    ###############################
                    self.first_vanishing_point_pixel =  solver.least_squares_intersection_of_lines(self.first_vanishing_lines_pixel)
                    

                    ###################
                    # 2. Solve Camera #
                    ###################
                    fovy = math.radians(self.fov_degrees)
                    focal_length_pixel = solver.focal_length_from_fov(fovy, self.content_size.y)
                    camera_transform = solver.solve1vp(
                        self.content_size.x, 
                        self.content_size.y, 
                        self.first_vanishing_point_pixel,
                        self.second_vanishing_lines_pixel[0],
                        focal_length_pixel,
                        self.principal_point_pixel,
                        self.origin_pixel,
                        self.first_axis,
                        self.second_axis,
                        self.scene_scale
                    )

                    # create camera
                    self.camera = Camera()
                    self.camera.setFoVY(fovy)
                    self.camera.transform = camera_transform
                    self.camera.setAspectRatio(self.content_size.x / self.content_size.y)
                    self.camera.setFoVY(math.degrees(fovy))
                except Exception as e:
                    imgui.push_style_color(imgui.Col_.text, (1.0, 0.2, 0.2, 1.0))
                    imgui.text_wrapped(f"fspy error: {pformat(e)}")
                    import traceback
                    traceback.print_exc()
                    imgui.pop_style_color()

            case SolverMode.TwoVP:
                try:
                    # compute vanishing points
                    self.first_vanishing_point_pixel =  solver.least_squares_intersection_of_lines(
                        self.first_vanishing_lines_pixel)
                    second_vanishing_point_pixel = solver.least_squares_intersection_of_lines(
                        self.second_vanishing_lines_pixel)

                    fovy, camera_transform = solver.solve2vp(
                        self.content_size.x, 
                        self.content_size.y, 
                        self.first_vanishing_point_pixel,
                        second_vanishing_point_pixel,
                        self.principal_point_pixel,
                        self.origin_pixel,
                        self.first_axis,
                        self.second_axis,
                        self.scene_scale
                    )

                    # create camera
                    self.camera = Camera()
                    self.camera.setFoVY(fovy)
                    self.camera.transform = camera_transform
                    self.camera.setAspectRatio(self.content_size.x / self.content_size.y)
                    self.camera.setFoVY(math.degrees(fovy))
                except Exception as e:
                    imgui.push_style_color(imgui.Col_.text, (1.0, 0.2, 0.2, 1.0))
                    imgui.text_wrapped(f"fspy error: {pformat(e)}")
                    import traceback
                    traceback.print_exc()
                    imgui.pop_style_color()

    def show_viewer(self):
        if ui.viewer.begin_viewer("viewer3", content_size=self.content_size, size=imgui.ImVec2(-1,-1), coordinate_system="top-left"):
            # control points
            _, self.origin_pixel = ui.viewer.control_point("o", self.origin_pixel)
            control_line = ui.comp(ui.viewer.control_point)
            control_lines = ui.comp(control_line)
            _, self.first_vanishing_lines_pixel = control_lines("z", self.first_vanishing_lines_pixel, color=get_axis_color(self.first_axis) )
            for line in self.first_vanishing_lines_pixel:
                ui.viewer.guide(line[0], line[1], color=get_axis_color(self.first_axis))

            match self.solver_mode:
                case SolverMode.OneVP:
                    _, self.second_vanishing_lines_pixel[0] = control_line("x", self.second_vanishing_lines_pixel[0], color=get_axis_color(self.second_axis))  
                    ui.viewer.guide(self.second_vanishing_lines_pixel[0][0], self.second_vanishing_lines_pixel[0][1], color=get_axis_color(self.second_axis))
                
                case SolverMode.TwoVP:
                    _, self.second_vanishing_lines_pixel = control_lines("x", self.second_vanishing_lines_pixel, color=get_axis_color(self.second_axis) )
                    for line in self.second_vanishing_lines_pixel:
                        ui.viewer.guide(line[0], line[1], color=get_axis_color(self.second_axis))

            if self.first_vanishing_point_pixel is not None:
                for line in self.first_vanishing_lines_pixel:
                    P = sorted([line[0], line[1]], key=lambda P: glm.distance2(P, self.first_vanishing_point_pixel))[0]
                    ui.viewer.guide(P, self.first_vanishing_point_pixel, get_axis_color(self.first_axis, dim=True))

            if self.second_vanishing_point_pixel is not None:
                for line in self.second_vanishing_lines_pixel:
                    P = sorted([line[0], line[1]], key=lambda P: glm.distance2(P, self.second_vanishing_point_pixel))[0]
                    ui.viewer.guide(P, self.second_vanishing_point_pixel, get_axis_color(self.second_axis, dim=True))

            if self.camera is not None:
                if ui.viewer.begin_scene(glm.scale(self.camera.projectionMatrix(), glm.vec3(1.0, -1.0, 1.0)), self.camera.viewMatrix()):
                    # draw the grid
                    for A, B in ui.viewer.make_gridXZ_lines(step=1, size=10):
                        ui.viewer.guide(A, B, ui.colors.WHITE_DIMMED)
                    ui.viewer.axes(length=1.0)
                ui.viewer.end_scene()
        ui.viewer.end_viewer()

    def show_results(self):
        imgui.text(icons_fontawesome_4.ICON_FA_HEART+"Results")
        if self.camera is not None:
            x, y, z = solver.extract_euler_angle(self.camera.transform, order="ZXY")
            pos = self.camera.getPosition()
            matrix = [self.camera.transform[j][i] for i in range(4) for j in range(4)]

            matrix_text = ""
            for i in range(4):
                for j in range(4):
                    value = self.camera.transform[i][j]
                    # Round very small values to zero to avoid -0.000
                    if abs(value) < 0.0005:  # Half of the display precision
                        value = 0.0
                    
                    if value < 0:
                        matrix_text += f"{value:.3f}"
                    elif value > 0:
                        matrix_text += f" {value:.3f}"
                    else:
                        matrix_text += f" {value:.3f}"
                    if j < 3:
                        matrix_text += ", "
                matrix_text += "\n"
            
            # Calculate height for 4 lines of text
            line_height = imgui.get_text_line_height_with_spacing()
            text_height = line_height * 4
            
            imgui.input_text_multiline("results", matrix_text, size=imgui.ImVec2(-1, text_height), flags=imgui.InputTextFlags_.read_only)

            # imgui.input_float4("matrix##row1", matrix[0:4], "%.3f", imgui.InputTextFlags_.read_only)
            # imgui.input_float4("##matrixrow2", matrix[4:8], "%.3f", imgui.InputTextFlags_.read_only)
            # imgui.input_float4("##matrixrow3", matrix[8:12], "%.3f", imgui.InputTextFlags_.read_only)
            # imgui.input_float4("##matrixrow4", matrix[12:16], "%.3f", imgui.InputTextFlags_.read_only)
            imgui.input_float4("quaternion", (3,3,3,4), "%.3f", imgui.InputTextFlags_.read_only)
            imgui.input_float3("translate", self.camera.getPosition(), "%.3f", imgui.InputTextFlags_.read_only)
            imgui.input_float3("rotate", (x,y,z), "%.3f", imgui.InputTextFlags_.read_only)

    def on_file_drop(self, window, paths):
        """GLFW drop callback - receives list of paths"""
        logger.info(f"Files dropped: {paths}")
        for path in paths:
            try:
                img = Image.open(path)
                self.content_size = imgui.ImVec2(img.width, img.height)
                logger.info(f"✓ Loaded: {path} ({img.width}x{img.height})")

                # Convert to RGBA
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                # Get raw image bytes
                img_bytes = img.tobytes()
                
                # Use immapp to create texture from memory
                self.image_texture_ref = hello_imgui.im_texture_id_from_asset().texture_from_memory(
                    img_bytes, 
                    img.width, 
                    img.height
                )
                logger.info(f"✓ Created texture: {self.image_texture_ref}")
                
            except Exception as e:
                logger.error(f"Failed to load {path}: {e}")
                import traceback
                traceback.print_exc()
                
if __name__ == "__main__":
    

    from imgui_bundle import hello_imgui
    runner_params = hello_imgui.RunnerParams()
    runner_params.app_window_params.window_title = "Camera Spy"
    runner_params.imgui_window_params.menu_app_title = "Camera Spy"
    runner_params.app_window_params.window_geometry.size = (1200, 512)
    runner_params.app_window_params.restore_previous_geometry = True
    # Enable DPI awareness
    runner_params.dpi_aware_params.dpi_window_size_factor = 1.0  # Auto-detect
    
    # Enable continuous rendering during window resize
    # runner_params.fps_idling.enable_idling = False
    # runner_params.app_window_params.repaint_during_resize_gotcha_reentrant_repaint = True

    def setup_theme():
        style = imgui.get_style()
        style.anti_aliased_lines = True
        style.anti_aliased_lines_use_tex = True
        style.anti_aliased_fill = True


        style.set_color_(imgui.Col_.window_bg, imgui.ImVec4(0.09, 0.09, 0.09, 1.00))
        style.set_color_(imgui.Col_.child_bg , imgui.ImVec4(0.11, 0.11, 0.11, 1.00))
        style.set_color_(imgui.Col_.frame_bg , imgui.ImVec4(0.15, 0.15, 0.15, 1.00))
        style.set_color_(imgui.Col_.title_bg , imgui.ImVec4(0.09, 0.09, 0.09, 1.00))
        style.set_color_(imgui.Col_.title_bg_active , imgui.ImVec4(0.09, 0.09, 0.09, 1.00))
        style.set_color_(imgui.Col_.title_bg_collapsed , imgui.ImVec4(0.09, 0.09, 0.09, 1.00))
        style.set_color_(imgui.Col_.button   , imgui.ImVec4(0.15, 0.15, 0.15, 1.00))

        style.window_padding = imgui.ImVec2(12, 12)
        style.frame_padding = imgui.ImVec2(12, 8)
        style.item_spacing = imgui.ImVec2(12, 16)


        style.child_border_size = 0
        style.frame_border_size = 0
        style.window_border_size = 0
        style.popup_border_size = 0

        style.window_title_align = imgui.ImVec2(0.5, 0.5)
        style.window_menu_button_position = imgui.Dir.right



        logger.info("✓ ImGui theme applied")

    def load_fonts():
        """Load FiraCode fonts"""
        from pathlib import Path
        try:
            # Get the fonts directory
            script_dir = Path(__file__).parent
            fonts_dir = Path("fonts/FiraCode")
            
            io = imgui.get_io()

            # Get DPI scale factor
            # dpi_scale = hello_imgui.dpi_window_size_factor()
            # logger.info(f"DPI scale factor: {dpi_scale}")
            
            # Scale font sizes by DPI - increased base size to 40px for better readability
            base_size = 20.0
            
            # Check if FiraCode exists
            fira_regular = fonts_dir / "FiraCode-Regular.ttf"
            fira_bold = fonts_dir / "FiraCode-Bold.ttf"
            
            if fira_regular.exists():
                # Add FiraCode as default font (40px) - this will be the primary font
                io.fonts.add_font_from_file_ttf(str(fira_regular), base_size)
                logger.info(f"✓ Loaded FiraCode Regular from {fira_regular} at {base_size}px")
                
                if fira_bold.exists():
                    io.fonts.add_font_from_file_ttf(str(fira_bold), base_size)
                    logger.info(f"✓ Loaded FiraCode Bold from {fira_bold} at {base_size}px")
            else:
                logger.warning(f"FiraCode font not found at {fira_regular.absolute()}")
                # Fallback to default font
                io.fonts.add_font_default()
                
        except Exception as e:
            logger.error(f"Failed to load fonts: {e}")
            import traceback
            traceback.print_exc()

    # Use the proper callbacks
    runner_params.callbacks.load_additional_fonts = load_fonts

    def setup_file_drop_callback(callback):
        """Setup GLFW file drop callback"""
        try:
            import glfw
            # Method 2: Try getting current context window
            window = glfw.get_current_context()

            if not window:
                logger.warning("Could not get GLFW window handle")
                return

            glfw.set_drop_callback(window, callback)
            logger.info("✓ File drop callback installed successfully (method2)")
            return
                
        except ImportError:
            logger.warning("glfw module not available. Install with: pip install glfw")
        except Exception as e:
            logger.warning(f"Could not setup file drop: {e}")
            import traceback
            traceback.print_exc()

    app = App()
    def post_init():
        setup_file_drop_callback(app.on_file_drop)

    runner_params.callbacks.setup_imgui_style = setup_theme
    runner_params.callbacks.post_init = lambda: post_init()
    runner_params.callbacks.show_gui = lambda: app.gui()
    runner_params.imgui_window_params.default_imgui_window_type = (
        hello_imgui.DefaultImGuiWindowType.provide_full_screen_dock_space
    )

    hello_imgui.run(runner_params)
    # immapp.run(app.gui, 
    #            window_title="Camera Spy", 
    #            window_size=(1200, 512), 
    #            with_implot3d=True
    # )

