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
import OpenGL.GL as gl

# Configure logging to see shader compilation logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def begin_sidebar(name:str, p_open:bool|None=None, flags:int=0):
    SIDEBAR_FLAGS = imgui.WindowFlags_.always_auto_resize | imgui.WindowFlags_.no_move | imgui.WindowFlags_.no_resize | imgui.WindowFlags_.no_collapse
    
    style = imgui.get_style()
    imgui.push_style_var(imgui.StyleVar_.window_padding, imgui.ImVec2(style.window_padding.x, 0))
    # imgui.push_style_color(imgui.Col_.window_bg, (0.2, 0.2, 0.2, 0.0))
    # imgui.push_style_color(imgui.Col_.title_bg, (0.2, 0.2, 0.2, 0.0))
    # imgui.push_style_color(imgui.Col_.border   , (0.08, 0.08, 0.08, 0.00))
    return imgui.begin(name, None, SIDEBAR_FLAGS)

def end_sidebar():
    imgui.end()
    # imgui.pop_style_color(3)
    imgui.pop_style_var()

def begin_attribute_editor(str_id:str):
    imgui.set_next_item_width(200)
    if imgui.begin_table(str_id, 2):
        imgui.table_setup_column("name", imgui.TableColumnFlags_.width_fixed)
        imgui.table_setup_column("value", imgui.TableColumnFlags_.width_stretch | imgui.TableColumnFlags_.no_clip)
        return True
    return False

def end_attribute_editor():
    imgui.end_table()

def next_attribute(string:str=""):
    imgui.table_next_row()
    imgui.table_next_column()
    imgui.push_style_var(imgui.StyleVar_.selectable_text_align, imgui.ImVec2(1.0,0))
    imgui.push_style_color(imgui.Col_.header_hovered, (0, 0, 0, 0))
    imgui.push_style_color(imgui.Col_.header_active,  (0, 0, 0, 0))
    imgui.selectable(string, False)
    imgui.pop_style_var()
    imgui.pop_style_color(2)
    imgui.table_next_column()
    imgui.set_next_item_width(-1) # stretch item to fill cell

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

def setup_dark_theme():
    style = imgui.get_style()
    imgui.style_colors_dark(style)

    style.anti_aliased_lines = True
    style.anti_aliased_lines_use_tex = True
    style.anti_aliased_fill = True

    levels = [
        0.08,   # really deep
        0.09,   # deep
        0.11,   # medium
        0.15,   # shallow
    ]

    windows_dark_titlebar_color = [32/255, 32/255, 32/255, 1.0]
    windows_dark_text_color = [255/255, 255/255, 255/255, 1.0]
    windows_light_titlebar_color = [243/255.0]*3 + [1.0]
    windows_light_text_color = [25/255.0]*3 + [1.0]

    style.set_color_(imgui.Col_.text ,               windows_dark_text_color)
    style.set_color_(imgui.Col_.title_bg ,           imgui.ImVec4(*[levels[1]]*3,1.00))
    style.set_color_(imgui.Col_.title_bg_active ,    imgui.ImVec4(*[levels[1]]*3,1.00))
    style.set_color_(imgui.Col_.title_bg_collapsed , imgui.ImVec4(*[levels[1]]*3,1.00))
    style.set_color_(imgui.Col_.window_bg,           imgui.ImVec4(*[levels[1]]*3,1.00))
    style.set_color_(imgui.Col_.child_bg ,           imgui.ImVec4(*[levels[2]]*3,1.00))
    style.set_color_(imgui.Col_.frame_bg ,           imgui.ImVec4(*[levels[3]]*3,1.00))
    style.set_color_(imgui.Col_.button   ,           imgui.ImVec4(*[levels[3]]*3,1.00))

    # Remove the dark border by setting menu bar background to match the menu bar
    style.set_color_(imgui.Col_.menu_bar_bg,         windows_dark_titlebar_color)
    
    style.window_padding = imgui.ImVec2(12, 12)
    style.frame_padding = imgui.ImVec2(12, 6)
    style.item_spacing = imgui.ImVec2(12, 16)

    style.frame_border_size = 0

    style.child_border_size = 1
    style.window_border_size = 1
    style.set_color_(imgui.Col_.border   , imgui.ImVec4(*[levels[0]]*3,1.00))
    style.popup_border_size = 1

    style.grab_min_size = 4
    style.grab_rounding = 4
    style.frame_rounding = 4

    style.separator_text_align = imgui.ImVec2(0.0, 0.5)
    style.separator_text_border_size = 1

    style.window_title_align = imgui.ImVec2(0.5, 0.5)
    style.window_menu_button_position = imgui.Dir.right

    logger.info("✓ ImGui theme applied")


def setup_windows_dark_theme():
    style = imgui.get_style()
    imgui.style_colors_dark(style)

    style.anti_aliased_lines = True
    style.anti_aliased_lines_use_tex = True
    style.anti_aliased_fill = True

    levels = [
        0.08,   # really deep
        0.09,   # deep
        0.11,   # medium
        0.15,   # shallow
    ]

    windows_dark_titlebar_color = [ 32/255,  32/255, 32/255, 1.0]
    levels = [
        22/255,   # really deep
        32/255,   # deep
        43/255,   # medium
        57/255,   # shallow
    ]
    windows_dark_text_color =     [255/255, 255/255, 255/255, 1.0]

    windows_light_titlebar_color = [243/255.0]*3 + [1.0]
    windows_light_text_color = [25/255.0]*3 + [1.0]

    style.set_color_(imgui.Col_.text ,               windows_dark_text_color)
    style.set_color_(imgui.Col_.title_bg ,           imgui.ImVec4(*[levels[1]]*3,1.00))
    style.set_color_(imgui.Col_.title_bg_active ,    imgui.ImVec4(*[levels[1]]*3,1.00))
    style.set_color_(imgui.Col_.title_bg_collapsed , imgui.ImVec4(*[levels[1]]*3,1.00))
    style.set_color_(imgui.Col_.window_bg,           imgui.ImVec4(*[levels[1]]*3,1.00))
    style.set_color_(imgui.Col_.child_bg ,           imgui.ImVec4(*[levels[2]]*3,1.00))
    style.set_color_(imgui.Col_.frame_bg ,           imgui.ImVec4(*[levels[3]]*3,1.00))
    style.set_color_(imgui.Col_.button   ,           imgui.ImVec4(*[levels[3]]*3,1.00))
    style.set_color_(imgui.Col_.popup_bg ,           imgui.ImVec4(*[levels[1]]*3,1.00))

    # Remove the dark border by setting menu bar background to match the menu bar
    style.set_color_(imgui.Col_.menu_bar_bg,         windows_dark_titlebar_color)
    
    style.window_padding = imgui.ImVec2(12, 12)
    style.frame_padding = imgui.ImVec2(6, 6)
    style.item_spacing = imgui.ImVec2(12, 12)

    style.frame_border_size = 0

    style.child_border_size = 0
    style.window_border_size = 0
    style.set_color_(imgui.Col_.border   , imgui.ImVec4(*[levels[2]]*3,1.00))
    style.popup_border_size = 1

    style.grab_min_size = 4

    
    style.grab_rounding = 4
    style.frame_rounding = 4
    style.frame_rounding = 4
    style.popup_rounding = 4
    style.child_rounding = 4
    style.window_rounding = 4
    style.scrollbar_rounding = 4

    style.window_title_align = imgui.ImVec2(0.5, 0.5)
    style.window_menu_button_position = imgui.Dir.right

    logger.info("✓ ImGui theme applied")



def setup_light_theme():
    style = imgui.get_style()
    imgui.style_colors_light(style)

    style.anti_aliased_lines = True
    style.anti_aliased_lines_use_tex = True
    style.anti_aliased_fill = True

    levels = [
        1-0.08,   # really deep
       1-0.09,   # deep
       1-0.11,   # medium
       1-0.15,   # shallow
    ]

    style.set_color_(imgui.Col_.title_bg ,           imgui.ImVec4(*[levels[1]]*3,1.00))
    style.set_color_(imgui.Col_.title_bg_active ,    imgui.ImVec4(*[levels[1]]*3,1.00))
    style.set_color_(imgui.Col_.title_bg_collapsed , imgui.ImVec4(*[levels[1]]*3,1.00))
    style.set_color_(imgui.Col_.window_bg,           imgui.ImVec4(*[levels[1]]*3,1.00))
    style.set_color_(imgui.Col_.child_bg ,           imgui.ImVec4(*[levels[2]]*3,1.00))
    style.set_color_(imgui.Col_.frame_bg ,           imgui.ImVec4(*[levels[3]]*3,1.00))
    style.set_color_(imgui.Col_.button   ,           imgui.ImVec4(*[levels[3]]*3,1.00))

    style.window_padding = imgui.ImVec2(12, 12)
    style.frame_padding = imgui.ImVec2(12, 6)
    style.item_spacing = imgui.ImVec2(12, 16)

    style.frame_border_size = 0

    style.child_border_size = 1
    style.window_border_size = 1
    style.set_color_(imgui.Col_.border   , imgui.ImVec4(*[levels[0]]*3,1.00))
    style.popup_border_size = 1

    style.grab_min_size = 4
    style.grab_rounding = 4
    style.frame_rounding = 4

    style.window_title_align = imgui.ImVec2(0.5, 0.5)
    style.window_menu_button_position = imgui.Dir.right

    logger.info("✓ ImGui theme applied")


static = dict()

class App:
    def __init__(self):
        # content image
        self.content_size = imgui.ImVec2(1280,720)
        self.pan_and_zoom_matrix = glm.identity(glm.mat4)
        self.image_texture_ref:imgui.ImTextureRef|None = None
        self.image_texture_id: int|None = None
        self.dim_background: bool = True

        # control points
        self.first_vanishing_lines_pixel = [
            (glm.vec2(296, 417), glm.vec2(633, 291)),
            (glm.vec2(654, 660), glm.vec2(826, 344))
        ]
        self.second_vanishing_lines_pixel = [
            [glm.vec2(381, 363), glm.vec2(884, 451)],
            [glm.vec2(511, 311), glm.vec2(879, 356)]
        ]

        self.origin_pixel=self.content_size/2
        self.principal_point_pixel=self.content_size/2

        # solver params
        self.solver_mode=SolverMode.OneVP
        self.fov_degrees=60.0
        self.quad_mode=False
        self.scene_scale=5.0
        self.first_axis=solver.Axis.PositiveZ
        self.second_axis=solver.Axis.PositiveX

        # solver results
        self.first_vanishing_point_pixel:glm.vec2|None = None
        self.second_vanishing_point_pixel:glm.vec2|None = None
        self.camera:Camera|None = None

        # misc
        self.theme=hello_imgui.ImGuiTheme_.darcula_darker
        self.startup_end_time = None

    def gui(self):
        if self.startup_end_time is None:
            self.startup_end_time = time.time()
            logger.info(f"Startup time: {self.startup_end_time - startup_start_time:.2f} seconds")
        
        # Compute Camera
        self.camera = Camera()

        # Create main menu bar (independent of any window)
        menu_bar_height = 0
        
        # Push styling to eliminate border between title bar and menu bar
        # imgui.push_style_var(imgui.StyleVar_.window_border_size, 0.0)
        # imgui.push_style_var(imgui.StyleVar_.frame_border_size, 0.0)
        if imgui.begin_main_menu_bar():
            if imgui.begin_menu("File"):
                if imgui.menu_item_simple("Open Image", "Ctrl+O"):
                    self.open_image_file()
                
                imgui.separator()
                if imgui.menu_item_simple("Quit", "Ctrl+Q"):
                    # Exit the application
                    import sys
                    sys.exit(0)
                
                imgui.end_menu()

            if imgui.begin_menu("Help"):
                if imgui.menu_item_simple("Manual"):
                    ...
                if imgui.menu_item_simple("About"):
                    ...
                
                imgui.end_menu()
            
            # Get the actual height of the menu bar
            menu_bar_height = imgui.get_frame_height()
            imgui.end_main_menu_bar()
        
        # Pop the style variables we pushed
        # imgui.pop_style_var(2)

        # Parameters
        style = imgui.get_style()
        display_size = imgui.get_io().display_size

        imgui.set_next_window_pos(imgui.ImVec2(style.window_padding.x, display_size.y/2), imgui.Cond_.always, imgui.ImVec2(0.0, 0.5))
        if begin_sidebar("Parameters", None):
            self.show_parameters()
        end_sidebar()

        self.solve()

        # fullscreen viewer
        imgui.set_next_window_pos(imgui.ImVec2(0, menu_bar_height))
        imgui.set_next_window_size(imgui.ImVec2(display_size.x, display_size.y - menu_bar_height))       
        if imgui.begin("MainViewport", None, imgui.WindowFlags_.no_bring_to_front_on_focus | imgui.WindowFlags_.no_move | imgui.WindowFlags_.no_resize | imgui.WindowFlags_.no_collapse | imgui.WindowFlags_.no_title_bar):
            self.show_viewer()
        imgui.end()

        imgui.set_next_window_pos(imgui.ImVec2(display_size.x-style.window_padding.x, display_size.y/2), imgui.Cond_.always, imgui.ImVec2(1.0, 0.5))
        if begin_sidebar("Results"):
            self.show_results()
        end_sidebar()

        
        if imgui.begin("style editor"):
            imgui.show_style_editor()
        imgui.end()

        if imgui.begin("about"):
            imgui.text_wrapped("Camera Spy Demo\n\n"
                               "Drop an image file (jpg, png, etc) into the window to load it as background.\n\n"
                               "Define vanishing lines by dragging the control points.\n\n"
                               "Adjust parameters in the sidebar to compute the camera.\n\n"
                               "Developed with ❤ by András Zalavári\n"
                               "https://github.com/yourusername/camera-spy")

        imgui.end()
        
    def show_parameters(self):
        imgui.separator_text("Image")
        imgui.set_next_item_width(150)
        if self.image_texture_ref is None:
            if imgui.button("open image", size=imgui.ImVec2(-1,0)):
                self.open_image_file()
            imgui.set_next_item_width(150)
            _, value = imgui.input_int2("image size", [int(self.content_size.x), int(self.content_size.y)])
            if _:
                self.content_size = imgui.ImVec2(value[0], value[1])
        else:
            image_aspect = self.content_size.x / self.content_size.y
            width = imgui.get_content_region_avail().x-imgui.get_style().frame_padding.x*2
            if imgui.image_button("open", self.image_texture_ref, imgui.ImVec2(width, width/image_aspect)):
                self.open_image_file()
            imgui.set_next_item_width(150)
            imgui.input_int2("image size", [int(self.content_size.x), int(self.content_size.y)], imgui.InputTextFlags_.read_only)

        _, self.dim_background = imgui.checkbox("dim background", self.dim_background)

        # imgui.bullet_text("Warning: Font scaling will NOT be smooth, because\nImGuiBackendFlags_RendererHasTextures is not set!")
        imgui.separator_text("Solver Parameters")
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
                    self.second_vanishing_point_pixel = solver.least_squares_intersection_of_lines(
                        self.second_vanishing_lines_pixel)

                    fovy, camera_transform = solver.solve2vp(
                        self.content_size.x, 
                        self.content_size.y, 
                        self.first_vanishing_point_pixel,
                        self.second_vanishing_point_pixel,
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
        if ui.viewer.begin_viewer("viewer1", content_size=self.content_size, size=imgui.ImVec2(-1,-1), coordinate_system="top-left"):
            if self.image_texture_ref is not None:
                tl = ui.viewer._get_window_coords(imgui.ImVec2(0,0))
                br = ui.viewer._get_window_coords(imgui.ImVec2(self.content_size.x, self.content_size.y))
                image_size = br - tl
                imgui.set_cursor_pos(tl)
                if self.dim_background:
                    style = imgui.get_style()
            
                    # imgui.set_cursor_pos(style.window_padding)
                    # static.setdefault('bg_color',   [0.33,0.33,0.33,1.0])
                    # static.setdefault('tint_color', [0.33,0.33,0.33,1.0])

                    # _, static['bg_color'] = imgui.color_edit4("bg color", static['bg_color'], imgui.ColorEditFlags_.no_inputs | imgui.ColorEditFlags_.no_label | imgui.ColorEditFlags_.alpha_bar)
                    # _, static['tint_color'] = imgui.color_edit4("tint color", static['tint_color'], imgui.ColorEditFlags_.no_inputs | imgui.ColorEditFlags_.no_label | imgui.ColorEditFlags_.alpha_bar)
                    
                    imgui.image_with_bg(self.image_texture_ref, image_size, None, None, 
                                        bg_col=  (0.33,0.33,0.33,1.0),
                                        tint_col=(0.33,0.33,0.33,1.0)
                    )
                else:
                    imgui.image(self.image_texture_ref, image_size)
            else:
                io = imgui.get_io()
                center = io.display_size / 2
                
                # # imgui.set_cursor_pos(center)
                # imgui.set_next_window_pos(center, imgui.Cond_.always, imgui.ImVec2(0.5, 0.5))
                # imgui.push_style_var(imgui.StyleVar_.window_padding, imgui.ImVec2(20, 20))
                # imgui.push_style_color(imgui.Col_.window_bg, (0,0,0, 0.7))
                # if imgui.begin("##dropzone", None, imgui.WindowFlags_.always_auto_resize | imgui.WindowFlags_.no_title_bar | imgui.WindowFlags_.no_inputs | imgui.WindowFlags_.no_move | imgui.WindowFlags_.no_resize | imgui.WindowFlags_.no_scrollbar):
                #     imgui.push_style_color(imgui.Col_.text, imgui.get_style().color_(imgui.Col_.text_disabled))
                #     imgui.bullet_text("Drop an image file here to load it as background")
                #     imgui.pop_style_color()
                # imgui.end()
                # imgui.pop_style_color()
                # imgui.pop_style_var()

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
                    if self.quad_mode:
                        z0, z1 = self.first_vanishing_lines_pixel
                        self.second_vanishing_lines_pixel = [
                            (z0[0], z1[0]),
                            (z0[1], z1[1])
                        ]
                    else:
                        _, self.second_vanishing_lines_pixel = control_lines("x", self.second_vanishing_lines_pixel, color=get_axis_color(self.second_axis) )
                    
                    for line in self.second_vanishing_lines_pixel:
                        ui.viewer.guide(line[0], line[1], color=get_axis_color(self.second_axis))

            # draw vanishing lines to vanishing points
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
                        ui.viewer.guide(A, B)
                    ui.viewer.axes(length=1.0)
                    ui.viewer.horizon_line()

                ui.viewer.end_scene()





        ui.viewer.end_viewer()

    def show_results(self):
        def pretty_matrix(value:np.array, separator:str='\t') -> str:
            # Format with numpy's array2string for better control
            text = np.array2string(
                value,
                precision=3,
                suppress_small=True,
                separator=separator,  # Use double space as separator
                prefix='',
                suffix='',
                formatter={'float_kind': lambda x: f"{'+' if np.sign(x)>=0 else '-'}{abs(x):.3f}"}  # Right-aligned with 8 characters width
            )
            
            text = text.replace('[', ' ').replace(']', '')
            from textwrap import dedent
            text = dedent(text).strip()
            text = text.replace('+', ' ')
            return text
            
        if self.camera is not None:
            scale = glm.vec3()
            quat = glm.quat()  # This will be our quaternion
            translation = glm.vec3()
            skew = glm.vec3()
            perspective = glm.vec4()
            success = glm.decompose(self.camera.transform, scale, quat, translation, skew, perspective)

            pos = self.camera.getPosition()
            matrix = [self.camera.transform[j][i] for i in range(4) for j in range(4)]

            transform_text = pretty_matrix(np.array(matrix).reshape(4,4), separator="\t")
            position_text = pretty_matrix(np.array(translation), separator="\t")
            quat_text = pretty_matrix(np.array([quat.x, quat.y, quat.z, quat.w]), separator="\t")

            x, y, z = solver.extract_euler_angle(self.camera.transform, order="ZXY")
            euler_text = pretty_matrix(np.array([x, y, z]), separator="\t")

            if begin_attribute_editor("res props"):
                next_attribute("transform")
                style = imgui.get_style()
                transform_text_size = imgui.calc_text_size(transform_text) + style.frame_padding * 2
                imgui.input_text_multiline("##transform", transform_text, size=transform_text_size, flags=imgui.InputTextFlags_.read_only)

                next_attribute("position")
                imgui.input_text("##position", position_text, flags=imgui.InputTextFlags_.read_only)
                
                # imgui.begin_tooltip()
                next_attribute("quaternion (xyzw)")
                imgui.input_text("##quaternion", quat_text, flags=imgui.InputTextFlags_.read_only)
                imgui.set_item_tooltip("Quaternion representing camera rotation (x, y, z, w)")

                next_attribute("euler (ZXY)°")
                imgui.input_text("##euler", euler_text, flags=imgui.InputTextFlags_.read_only)
                imgui.set_item_tooltip("Euler angles in degrees (x,y,z).\nNote: Rotation is applied in order order: ZXY (Yaw, Pitch, Roll)")

                next_attribute("fov")
                imgui.input_text("##fov", f"{self.camera.fovy:.2f}°")
                end_attribute_editor()

    def open_image_file(self, path:str|None=None):
        from pathlib import Path
        try:
            if path is None:
                filters = [
                    "Image Files", "*.png *.jpg *.jpeg *.bmp *.tiff *.tif *.gif", 
                    "All Files", "*.*"
                ]
                open_file_dialog = pfd.open_file("Select Image", "", filters, pfd.opt.none)
                paths = open_file_dialog.result()
                print("results: ", paths)
                if len(paths)>0:
                    path = paths[0]
                else:
                    return

            if not Path(path).exists():
                logger.error(f"File not found: {Path(path).absolute()}")
                return
            else:
                logger.info(f"✓ Found file: {Path(path).absolute()}")

            # Load image with PIL
            img = Image.open(path)
            self.content_size = imgui.ImVec2(img.width, img.height)
            logger.info(f"✓ Loaded: {path} ({img.width}x{img.height})")
            
            if img.mode != 'RGBA':
                # Convert to RGBA if needed
                img = img.convert('RGBA')

            img_data = np.frombuffer(img.tobytes(), dtype=np.uint8)
            if self.image_texture_id is not None:
                gl.glDeleteTextures(1, [self.image_texture_id])
                self.image_texture_ref = None
                self.image_texture_id = None
            
            texture_id = gl.glGenTextures(1)
            gl.glBindTexture(gl.GL_TEXTURE_2D, texture_id)
            
            # Set texture parameters
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
            
            # Upload texture data
            gl.glTexImage2D(
                gl.GL_TEXTURE_2D, 0, gl.GL_RGBA,
                img.width, img.height, 0,
                gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, img_data
            )
            
            # Unbind texture
            gl.glBindTexture(gl.GL_TEXTURE_2D, 0)
            
            self.image_texture_id = texture_id
            self.image_texture_ref = imgui.ImTextureRef(texture_id)
            logger.info(f"✓ Created OpenGL texture: {texture_id}")
            
        except Exception as e:
            logger.error(f"Failed to load {path}: {e}")
            import traceback
            traceback.print_exc()

    def on_file_drop(self, window, paths):
        from pathlib import Path
        """GLFW drop callback - receives list of paths"""
        logger.info(f"Files dropped: {paths}")
        if len(paths) > 0:
            first_path = paths[0]
            self.open_image_file(first_path)

if __name__ == "__main__":
    from imgui_bundle import hello_imgui
    runner_params = hello_imgui.RunnerParams()
    runner_params.app_window_params.window_title = "Camera Spy"
    runner_params.imgui_window_params.menu_app_title = "Camera Spy"
    runner_params.app_window_params.window_geometry.size = (1200, 512)
    runner_params.app_window_params.restore_previous_geometry = True
    
    # Set background color to match menu bar to eliminate dark border
    windows_dark_titlebar_color = [32/255, 32/255, 32/255, 1.0]
    runner_params.imgui_window_params.background_color = windows_dark_titlebar_color

    # Enable DPI awareness
    runner_params.dpi_aware_params.dpi_window_size_factor = 1.0  # Auto-detect
    
    # Enable continuous rendering during window resize
    runner_params.fps_idling.enable_idling = True
    runner_params.app_window_params.repaint_during_resize_gotcha_reentrant_repaint = True

    def load_fonts():
        """Load FiraCode fonts"""
        from pathlib import Path
        try:
            # Get the fonts directory
            script_dir = Path(__file__).parent
            fonts_dir = Path("fonts/FiraCode")
            
            io = imgui.get_io()

            # Get DPI scale factor
            dpi_scale = hello_imgui.dpi_window_size_factor()
            # logger.info(f"DPI scale factor: {dpi_scale}")
            
            # Scale font sizes by DPI - increased base size to 40px for better readability
            base_size = 12.0*dpi_scale
            
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
    
    def setup_imgui_config():
        """Setup ImGui configuration before initialization"""
        io = imgui.get_io()
        # Disable docking completely
        io.config_flags &= ~imgui.ConfigFlags_.docking_enable
        io.config_flags &= ~imgui.ConfigFlags_.viewports_enable  # Also disable viewports

    def enable_windows_dark_mode(enable: bool | None = None):
        """Enable or disable Windows dark mode for the application window
        
        Args:
            enable: True for dark mode, False for light mode, None to detect system settings
        """
        import platform
        
        if platform.system() != "Windows":
            logger.info("Dark mode API only available on Windows")
            return
            
        try:
            import ctypes
            from ctypes import wintypes
            import winreg
            import glfw
            
            # Determine which mode to use
            if enable is None:
                # Auto-detect system dark mode setting
                def is_system_dark_mode():
                    try:
                        # Check registry for current theme
                        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize")
                        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                        winreg.CloseKey(key)
                        # Value is 0 for dark mode, 1 for light mode
                        return value == 0
                    except Exception:
                        # Fallback: assume light mode if we can't read registry
                        return False
                
                use_dark_mode_bool = is_system_dark_mode()
                logger.info(f"System dark mode detected: {use_dark_mode_bool}")
            else:
                # Use explicitly provided setting
                use_dark_mode_bool = bool(enable)
                source = "explicit setting" if enable is not None else "system detection"
                logger.info(f"Dark mode set to {use_dark_mode_bool} via {source}")
            
            # Get the GLFW window handle
            window = glfw.get_current_context()
            if not window:
                logger.warning("Could not get GLFW window for dark mode setup")
                return
                
            # Get the native Windows window handle (HWND)
            hwnd = glfw.get_win32_window(window)
            if not hwnd:
                logger.warning("Could not get Windows HWND")
                return
            
            # Define Windows constants for dark mode
            DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1 = 19
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            
            # Load DWM library
            dwmapi = ctypes.windll.dwmapi
            
            # Set up DwmSetWindowAttribute function
            dwmapi.DwmSetWindowAttribute.argtypes = [
                wintypes.HWND,      # hwnd
                wintypes.DWORD,     # dwAttribute  
                ctypes.c_void_p,    # pvAttribute
                wintypes.DWORD      # cbAttribute
            ]
            
            # Set dark mode based on determined setting
            use_dark_mode = wintypes.BOOL(use_dark_mode_bool)
            
            # Try the newer attribute first (Windows 10 build 20H1+)
            result = dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_USE_IMMERSIVE_DARK_MODE,
                ctypes.byref(use_dark_mode),
                ctypes.sizeof(use_dark_mode)
            )
            
            # If that fails, try the older attribute (Windows 10 earlier builds)
            if result != 0:
                result = dwmapi.DwmSetWindowAttribute(
                    hwnd,
                    DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1,
                    ctypes.byref(use_dark_mode),
                    ctypes.sizeof(use_dark_mode)
                )
            
            if result == 0:  # S_OK
                mode_str = "dark" if use_dark_mode_bool else "light"
                logger.info(f"✓ Windows {mode_str} mode applied to title bar")
            else:
                logger.warning(f"Failed to set window theme: DWM error {result}")
                
        except ImportError as e:
            logger.warning(f"Windows API not available: {e}")
        except Exception as e:
            logger.warning(f"Failed to setup window theme: {e}")
            import traceback
            traceback.print_exc()

    def post_init():
        setup_file_drop_callback(app.on_file_drop)
        enable_windows_dark_mode(True)

    # Completely disable docking at the hello_imgui level
    runner_params.docking_params.layout_condition = hello_imgui.DockingLayoutCondition.never
    
    runner_params.callbacks.setup_imgui_config = setup_imgui_config
    runner_params.callbacks.setup_imgui_style = setup_windows_dark_theme
    runner_params.callbacks.post_init = post_init
    runner_params.callbacks.show_gui = lambda: app.gui()
    runner_params.imgui_window_params.default_imgui_window_type = (
        hello_imgui.DefaultImGuiWindowType.no_default_window
        # hello_imgui.DefaultImGuiWindowType.provide_full_screen_dock_space
    )

    hello_imgui.run(runner_params)
    # immapp.run(app.gui, 
    #            window_title="Camera Spy", 
    #            window_size=(1200, 512), 
    #            with_implot3d=True
    # )

