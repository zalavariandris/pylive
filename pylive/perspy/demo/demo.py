# Standard library imports
import math
from pathlib import Path
from pprint import pformat
import threading
from typing import Any, List, Tuple, Dict
from enum import IntEnum
import json
import base64
import logging

# Third-party imports
from PIL import Image
import OpenGL.GL as gl
import glfw
import glm
import numpy as np
from imgui_bundle import imgui, icons_fontawesome_4
from imgui_bundle import portable_file_dialogs as pfd

# Local application imports
from pylive.glrenderer.utils.camera import Camera
from pylive.perspy import solver
import ui
from document import PerspyDocument, SolverMode
import pyperclip

# ############ #
# Hot Reloader #
# ############ #
import watchfiles
import importlib
class ModuleHotReloader:
    def __init__(self, modules_to_watch: list = []):
        self.modules_to_watch = modules_to_watch
        self.watcher_threads = []

    def watch_module_file(self, module):
        import watchfiles, importlib
        path = module.__file__
        for changes in watchfiles.watch(path):
            print(f"File changed: {changes}")
            try:
                importlib.reload(module)
                print(f"Reloaded {module.__name__}")
            except Exception as e:
                print(f"Error reloading {module.__name__}: {e}")

    def start_file_watchers(self):
        import threading
        for module in self.modules_to_watch:
            t = threading.Thread(
                target=self.watch_module_file,
                args=(module,),
                daemon=True
            )
            t.start()
            self.watcher_threads.append(t)

ModuleHotReloader([solver, ui.viewer]).start_file_watchers()


# Configure logging to see shader compilation logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_axis_color(axis:solver.Axis) -> Tuple[float, float, float]:
    match axis:
        case solver.Axis.PositiveX | solver.Axis.NegativeX:
            return ui.viewer.get_viewer_style().AXIS_COLOR_X
        case solver.Axis.PositiveY | solver.Axis.NegativeY:
            return ui.viewer.get_viewer_style().AXIS_COLOR_Y
        case solver.Axis.PositiveZ | solver.Axis.NegativeZ:
            return ui.viewer.get_viewer_style().AXIS_COLOR_Z
        case _:
            return (1.0, 1.0, 1.0)
        
# ########### #
# Application #
# ########### #
class PerspyApp():
    def __init__(self):
        super().__init__()

        self.doc = PerspyDocument()

        # stored texture
        self.image_texture_ref:imgui.ImTextureRef|None = None
        self.image_texture_id: int|None = None

        # ui state
        self.pan_and_zoom_matrix = glm.identity(glm.mat4)
        self.dim_background: bool = True

        # - manage windows
        self.show_about_popup: bool = False
        self.show_emoji_window: bool = False
        self.show_fontawesome_window: bool = False
        self.show_data_window: bool = False
        self.show_styleeditor_window: bool = False

        # - manage view
        self.view_grid: bool = True
        self.view_horizon: bool = True
        self.view_axes: bool = True

        # solver results
        self.camera:Camera|None = None
        self.current_euler_order = solver.EulerOrder.ZXY
        self.first_vanishing_point:glm.vec2|None = None
        self.second_vanishing_point:glm.vec2|None = None
        self.solver_results:solver.SolverResults|None = None
        
        # misc
        """
        Can be used to define inline variables, similarly how static vars used in C/C++ with imgui.
        
        Example:
        self.misc.setdefault('my_var', 0)
        _, self.misc['my_var'] = imgui.slider_float("my var", self.misc['my_var'], 0.0, 1.0)
        """
        self.misc:Dict[str, Any] = dict() # miscellaneous state variables for development. 

    def update_os_window_title(self):
        # Change the window title at runtime
        try:
            glfw_window = glfw.get_current_context()
            title = f"Perspy"
            if self.doc._file_path:
                title += " - "
                if self.doc.isModified():
                    title += " *"
                title += f"{Path(self.doc._file_path).stem}"
                title += f" [{self.doc._file_path}]"
            glfw.set_window_title(glfw_window, title)
        except Exception as e:
            logger.warning(f"Could not set window title: {e}")

    # Windows
    def gui(self):
        # Create main menu bar (independent of any window)
        self.show_main_menu_bar()
        menu_bar_height = imgui.get_frame_height()

        if self.show_about_popup:
            imgui.set_next_window_pos(imgui.ImVec2(0,0), imgui.Cond_.always)
            imgui.set_next_window_size(imgui.get_io().display_size, imgui.Cond_.always)
            imgui.set_next_window_bg_alpha(0.75)
            # imgui.set_next_window_focus()
            if imgui.begin("about##modal", None, imgui.WindowFlags_.no_title_bar | imgui.WindowFlags_.no_scrollbar | imgui.WindowFlags_.no_collapse | imgui.WindowFlags_.no_move | imgui.WindowFlags_.no_resize | imgui.WindowFlags_.no_collapse):
                modal_window_pos = imgui.get_window_pos()
                modal_window_size = imgui.get_window_size()
                imgui.set_next_window_pos(modal_window_size/2+modal_window_pos, imgui.Cond_.always, imgui.ImVec2(0.5,0.5))
                style = imgui.get_style()
                imgui.push_style_color(imgui.Col_.child_bg, style.color_(imgui.Col_.window_bg))
                if imgui.begin_child("about##content", None, imgui.ChildFlags_.always_use_window_padding | imgui.ChildFlags_.always_auto_resize | imgui.ChildFlags_.auto_resize_x | imgui.ChildFlags_.auto_resize_y):
                    self.show_about()
                    # if imgui.button("Close", imgui.ImVec2(0, 0)):
                    #     self.show_about_popup = False
                imgui.end_child()
                imgui.pop_style_color()

                # Close popup on Escape or outside click
                if imgui.is_key_pressed(imgui.Key.escape):
                    self.show_about_popup = False
                if not imgui.is_any_item_active() and imgui.get_io().mouse_clicked[0]:
                    self.show_about_popup = False
                
            imgui.end()

        # Emoji Test Window
        if self.show_emoji_window:
            expanded, self.show_emoji_window = imgui.begin("Emoji Test Window", self.show_emoji_window)
            if expanded:
                self.show_emoji_test()
            imgui.end()

        # FontAwesome Test Window
        if self.show_fontawesome_window:
            expanded, self.show_fontawesome_window = imgui.begin("FontAwesome Icons", self.show_fontawesome_window, imgui.WindowFlags_.always_auto_resize)
            if expanded:
                self.show_fontawesome_test()
            imgui.end()

        # Parameters Window
        if ui.begin_sidebar("Parameters", align="left"):
            self.show_parameters()
        ui.end_sidebar()

        # Solve the camera
        try:
            self.solve()
            error_msg = None
        except Exception as e:
            error_msg = e
            import traceback
            traceback.print_exc()

        # fullscreen viewer Window
        # style = imgui.get_style()
        display_size = imgui.get_io().display_size
        imgui.set_next_window_pos(imgui.ImVec2(0, menu_bar_height))
        imgui.set_next_window_size(imgui.ImVec2(display_size.x, display_size.y - menu_bar_height))       
        if imgui.begin("MainViewport", None, imgui.WindowFlags_.no_bring_to_front_on_focus | imgui.WindowFlags_.no_move | imgui.WindowFlags_.no_resize | imgui.WindowFlags_.no_collapse | imgui.WindowFlags_.no_title_bar):
            self.show_viewer()
        imgui.end()

        # Results Window
        
        if ui.begin_sidebar("Results", align="right"):
            if error_msg is not None:
                imgui.push_style_color(imgui.Col_.text, (1.0, 0.2, 0.2, 1.0))
                imgui.text_wrapped(f"{error_msg}")
                imgui.pop_style_color()
            else:
                self.show_results()
        ui.end_sidebar()

        if self.show_data_window:
            expanded, self.show_data_window = imgui.begin("data window", self.show_data_window)
            if expanded:
                self.show_data()
            imgui.end()

        # Style Editor Window
        if self.show_styleeditor_window:
            expanded, self.show_styleeditor_window = imgui.begin("style editor", self.show_styleeditor_window)
            if expanded:
                imgui.show_style_editor()
            imgui.end()

    def show_main_menu_bar(self):
        # Push styling to eliminate border between title bar and menu bar
        # imgui.push_style_var(imgui.StyleVar_.window_border_size, 0.0)
        # imgui.push_style_var(imgui.StyleVar_.frame_border_size, 0.0)
        style = imgui.get_style()
        # imgui.push_style_var(imgui.StyleVar_.frame_padding, imgui.ImVec2(style.frame_padding.x, 12))
        if imgui.begin_main_menu_bar():
            if imgui.begin_menu("File"):
                folder_icon = getattr(icons_fontawesome_4, 'ICON_FA_FOLDER_OPEN', getattr(icons_fontawesome_4, 'ICON_FA_FOLDER', ''))
                save_icon = getattr(icons_fontawesome_4, 'ICON_FA_SAVE', getattr(icons_fontawesome_4, 'ICON_FA_FLOPPY_O', ''))
                quit_icon = getattr(icons_fontawesome_4, 'ICON_FA_TIMES', getattr(icons_fontawesome_4, 'ICON_FA_CLOSE', ''))
                
                if imgui.menu_item_simple(f"{folder_icon} New", "Ctrl+N"):
                    ...
                
                if imgui.menu_item_simple(f"{folder_icon} Open", "Ctrl+O"):
                    self.doc.open()
                    if self.doc.image_path:
                        # Create OpenGL texture
                        self._upload_image_texture(self.image)

                if imgui.menu_item_simple(f"{save_icon} Save", "Ctrl+S"):
                    self.doc.save()
                
                if imgui.menu_item_simple(f"{save_icon} Save As...", "Ctrl+Shift+S"):
                    self.doc.save_as()

                imgui.separator()

                if imgui.menu_item_simple(f"{folder_icon} Load Image", "Ctrl+O"):
                    self.load_image_file()

                imgui.separator()

                if imgui.begin_menu("Export results"):
                    if imgui.menu_item_simple("JSON"):
                        self._export_text_to_file(
                            default_name="perspy_camera_factory.py",
                            content=json.dumps(self.results_to_dict(), indent=4),
                            file_type="JSON",
                            extension=".json"
                        )

                    if imgui.menu_item_simple("blender script"):
                        self._export_text_to_file(
                            default_name="perspy_camera_factory.py",
                            content=self.results_to_blender_script(),
                            file_type="Blender Python Script",
                            extension=".py"
                        )

                    imgui.end_menu()
                
                if imgui.begin_menu("Copy results to clipboard"):
                    if imgui.menu_item_simple("JSON"):
                        pyperclip.copy(json.dumps(self.results_to_dict(), indent=4))

                    if imgui.menu_item_simple("blender script"):
                        pyperclip.copy(self.results_to_blender_script())

                    imgui.end_menu()

                if imgui.begin_menu("Copy document to clipboard"):
                    if imgui.menu_item_simple("Python code"):
                        pyperclip.copy(self.doc.document_to_python())

                    imgui.end_menu()
                
                
                imgui.separator()
                if imgui.menu_item_simple(f"{quit_icon} Quit", "Ctrl+Q"):
                    # Exit the application
                    import sys
                    sys.exit(0)

                
                imgui.end_menu()

            if imgui.begin_menu("View"):

                if imgui.menu_item_simple(f"dim background", None, self.dim_background):
                    self.dim_background = not self.dim_background

                if imgui.menu_item_simple(f"grid", None, self.view_grid):
                    self.view_grid = not self.view_grid

                if imgui.menu_item_simple(f"horizon", None, self.view_horizon):
                    self.view_horizon = not self.view_horizon

                if imgui.menu_item_simple(f"axes", None, self.view_axes):
                    self.view_axes = not self.view_axes

                # global sidebar_opacity
                # _, sidebar_opacity = imgui.slider_float("sidebar opacity", sidebar_opacity, 0.0, 1.0, "%.2f")

                imgui.end_menu()
            
            if imgui.begin_menu("Windows"):
                smile_icon = getattr(icons_fontawesome_4, 'ICON_FA_SMILE_O', getattr(icons_fontawesome_4, 'ICON_FA_SMILE', ''))
                star_icon = getattr(icons_fontawesome_4, 'ICON_FA_STAR', '')

                if imgui.menu_item_simple(f"{smile_icon} Emoji Test", None, self.show_emoji_window):
                    self.show_emoji_window = not self.show_emoji_window

                if imgui.menu_item_simple(f"{star_icon} FontAwesome Icons", None, self.show_fontawesome_window):
                    self.show_fontawesome_window = not self.show_fontawesome_window

                if imgui.menu_item_simple("Style Window", None, self.show_styleeditor_window):
                    self.show_styleeditor_window = not self.show_styleeditor_window

                if imgui.menu_item_simple("Data Window", None, self.show_data_window):
                    self.show_data_window = not self.show_data_window
                imgui.end_menu()

            # center title horizontally
            if self.doc._file_path:
                text = f"— {Path(self.doc._file_path).stem} —"
                title_size = imgui.calc_text_size(text)
                center_cursor_pos = (imgui.get_window_width() - title_size.x) * 0.5
                if center_cursor_pos > imgui.get_cursor_pos_x():
                    imgui.set_cursor_pos_x(center_cursor_pos)
                imgui.text(text)                
                imgui.text_colored(style.color_(imgui.Col_.text_disabled), f"[{self.doc._file_path}]")
            else:
                text = '— Untitled —'
                title_size = imgui.calc_text_size(text)
                center_cursor_pos = (imgui.get_window_width() - title_size.x) * 0.5
                if center_cursor_pos > imgui.get_cursor_pos_x():
                    imgui.set_cursor_pos_x(center_cursor_pos)
                imgui.text(text)

            # alignt menu to right
            right_cursor_pos = imgui.get_window_width() - style.window_padding.x*2 - imgui.calc_text_size("Help").x
            if right_cursor_pos > imgui.get_cursor_pos_x():
                imgui.set_cursor_pos_x(right_cursor_pos)
            if imgui.begin_menu("Help"):
                # Use safe icon access with fallback
                book_icon = getattr(icons_fontawesome_4, 'ICON_FA_BOOK', '')
                info_icon = getattr(icons_fontawesome_4, 'ICON_FA_INFO_CIRCLE', getattr(icons_fontawesome_4, 'ICON_FA_INFO', ''))
                
                if imgui.menu_item_simple(f"{book_icon} Manual"):
                    ...
                if imgui.menu_item_simple(f"{info_icon} About"):
                    self.show_about_popup = True

                imgui.end_menu()

            imgui.end_main_menu_bar()
        # imgui.pop_style_var()

    def show_about(self):
        imgui.text("Camera Spy Demo")
        imgui.separator()
        imgui.text("Drop an image file (jpg, png, etc) into the window to load it as background.")
        imgui.text("Define vanishing lines by dragging the control points.")
        imgui.text("Adjust parameters in the sidebar to compute the camera.")
        imgui.separator()
        imgui.text("Developed with ❤ by András Zalavári")
        imgui.text_link_open_url("https://github.com/yourusername/camera-spy")

    def show_parameters(self):
        buttons_width = 120
        imgui.separator_text("Image")
        imgui.set_next_item_width(buttons_width)
        if self.image_texture_ref is None:
            if imgui.button("open image", size=imgui.ImVec2(-1,0)):
                self.load_image_file()
            imgui.set_next_item_width(buttons_width)
            _, value = imgui.input_int2("image size", [int(self.doc.content_size.x), int(self.doc.content_size.y)])
            if _:
                self.doc.content_size = imgui.ImVec2(value[0], value[1])
        else:
            image_aspect = self.doc.content_size.x / self.doc.content_size.y
            width = imgui.get_content_region_avail().x-imgui.get_style().frame_padding.x*2
            if imgui.image_button("open", self.image_texture_ref, imgui.ImVec2(width, width/image_aspect)):
                self.load_image_file()
            imgui.set_next_item_width(buttons_width)
            imgui.input_int2("image size", [int(self.doc.content_size.x), int(self.doc.content_size.y)], imgui.InputTextFlags_.read_only)

        _, self.dim_background = imgui.checkbox("dim background", self.dim_background)

        # imgui.bullet_text("Warning: Font scaling will NOT be smooth, because\nImGuiBackendFlags_RendererHasTextures is not set!")
        imgui.separator_text("Solver Parameters")
        imgui.set_next_item_width(buttons_width)
        _, self.doc.solver_mode = imgui.combo("mode", self.doc.solver_mode, SolverMode._member_names_)

        imgui.set_next_item_width(buttons_width)
        _, self.doc.scene_scale = imgui.slider_float("scene  scale", self.doc.scene_scale, 1.0, 100.0, "%.2f")

        # solver specific parameters
        match self.doc.solver_mode:
            case SolverMode.OneVP:
                imgui.set_next_item_width(buttons_width)
                _, self.doc.fov_degrees = imgui.slider_float("fov°", self.doc.fov_degrees, 1.0, 179.0, "%.1f°")

            case SolverMode.TwoVP:
                _, self.doc.enable_auto_principal_point = imgui.checkbox("auto principal point", self.doc.enable_auto_principal_point)
                _, self.doc.quad_mode = imgui.checkbox("quad", self.doc.quad_mode)

        imgui.separator_text("Axes")
        axes_presets = {
            "default": 0,
            'blender':1,
            'maya':2
        }
        self.misc.setdefault('axes_preset', 0)
        imgui.set_next_item_width(buttons_width)
        _, self.misc['axes_preset'] = imgui.combo("axes_preset", self.misc['axes_preset'], list(axes_presets.keys()))
        if _:
            preset = list(axes_presets.keys())[self.misc['axes_preset']]
            match preset:
                case "default":
                    """
                    right-handed
                    x: front/back axis
                    y: left/right axis
                    z: up/down axis
                    """
                    self.doc.first_axis, self.doc.second_axis = solver.Axis.PositiveX, solver.Axis.PositiveY
                case "blender":
                    """
                    right-handed
                    X is the left/right axis
                    Y is the front/back axis, 
                    Z is the up/down axis.
                    """
                    self.doc.first_axis, self.doc.second_axis = solver.Axis.PositiveY, solver.Axis.NegativeX
                case "maya":
                    self.doc.first_axis, self.doc.second_axis = solver.Axis.PositiveZ, solver.Axis.NegativeX
        
        try:
            axis_matrix = solver.create_axis_assignment_matrix(self.doc.first_axis, self.doc.second_axis)
        except Exception as e:
            self.doc.first_axis, self.doc.second_axis = solver.Axis.PositiveZ, solver.Axis.PositiveX
            axis_matrix = solver.create_axis_assignment_matrix(self.doc.first_axis, self.doc.second_axis)
            imgui.text(f"Error: {e}")
        
        axes_short_names = {
            solver.Axis.PositiveX: "X+",
            solver.Axis.NegativeX: "X-",
            solver.Axis.PositiveY: "Y+",
            solver.Axis.NegativeY: "Y-",
            solver.Axis.PositiveZ: "Z+",
            solver.Axis.NegativeZ: "Z-"
        }
        style = imgui.get_style()
        imgui.set_next_item_width(buttons_width/2-style.frame_padding.x)
        _, self.doc.first_axis = imgui.combo("##first axis",   self.doc.first_axis, list(axes_short_names.values()))
        imgui.set_item_tooltip(f"First axis (ground plane axis 1)")
        imgui.same_line()
        imgui.set_next_item_width(buttons_width/2-style.frame_padding.x)
        _, self.doc.second_axis = imgui.combo("##second axis", self.doc.second_axis, list(axes_short_names.values()))
        imgui.set_item_tooltip(f"Second axis (ground plane axis 2)")
        
    def show_viewer(self):
        if ui.viewer.begin_viewer("viewer1", content_size=self.doc.content_size, size=imgui.ImVec2(-1,-1)):
            # background image
            if self.image_texture_ref is not None:
                tl = ui.viewer._get_window_coords(imgui.ImVec2(0,0))
                br = ui.viewer._get_window_coords(imgui.ImVec2(self.doc.content_size.x, self.doc.content_size.y))
                image_size = br - tl
                imgui.set_cursor_pos(tl)
                if self.dim_background:
                    imgui.image_with_bg(self.image_texture_ref, image_size, None, None, 
                                        bg_col=  (0.33,0.33,0.33,1.0),
                                        tint_col=(0.33,0.33,0.33,1.0)
                    )
                else:
                    imgui.image(self.image_texture_ref, image_size)

            # control points
            _, self.doc.origin = ui.viewer.control_point("o", self.doc.origin)
            control_line = ui.comp(ui.viewer.control_point)
            control_lines = ui.comp(control_line)
            _, self.doc.first_vanishing_lines = control_lines("z", self.doc.first_vanishing_lines, color=get_axis_color(self.doc.first_axis) )
            for line in self.doc.first_vanishing_lines:
                ui.viewer.guide(line[0], line[1], get_axis_color(self.doc.first_axis), '>')

            ui.viewer.axes(length=10)

            match self.doc.solver_mode:
                case SolverMode.OneVP:
                    _, self.doc.second_vanishing_lines[0] = control_line("x", self.doc.second_vanishing_lines[0], color=get_axis_color(self.doc.second_axis))  
                    ui.viewer.guide(self.doc.second_vanishing_lines[0][0], self.doc.second_vanishing_lines[0][1], get_axis_color(self.doc.second_axis), '>')
                
                case SolverMode.TwoVP:
                    _, self.doc.principal_point = ui.viewer.control_point("p", self.doc.principal_point)
                    if self.doc.quad_mode:
                        z0, z1 = self.doc.first_vanishing_lines
                        self.doc.second_vanishing_lines = [
                            (z0[0], z1[0]),
                            (z0[1], z1[1])
                        ]
                    else:
                        _, self.doc.second_vanishing_lines = control_lines("x", self.doc.second_vanishing_lines, color=get_axis_color(self.doc.second_axis) )
                    
                    for line in self.doc.second_vanishing_lines:
                        ui.viewer.guide(line[0], line[1], get_axis_color(self.doc.second_axis), '>')

            # draw vanishing lines to vanishing points
            if self.first_vanishing_point is not None:
                for line in self.doc.first_vanishing_lines:
                    P = sorted([line[0], line[1]], key=lambda P: glm.distance2(P, self.first_vanishing_point))[0]
                    first_axis_color = get_axis_color(self.doc.first_axis)
                    ui.viewer.guide(P, self.first_vanishing_point, imgui.ImVec4(first_axis_color[0], first_axis_color[1], first_axis_color[2], 0.4))

            if self.second_vanishing_point is not None:
                for line in self.doc.second_vanishing_lines:
                    P = sorted([line[0], line[1]], key=lambda P: glm.distance2(P, self.second_vanishing_point))[0]
                    second_axis_color = get_axis_color(self.doc.second_axis)
                    ui.viewer.guide(P, self.second_vanishing_point, imgui.ImVec4(second_axis_color[0], second_axis_color[1], second_axis_color[2], 0.4))

            if self.camera is not None:
                if ui.viewer.begin_scene(glm.scale(self.camera.projectionMatrix(), glm.vec3(1.0, -1.0, 1.0)), self.camera.viewMatrix()):
                    axes_name = {
                        solver.Axis.PositiveX: "X",
                        solver.Axis.NegativeX: "X",
                        solver.Axis.PositiveY: "Y",
                        solver.Axis.NegativeY: "Y",
                        solver.Axis.PositiveZ: "Z",
                        solver.Axis.NegativeZ: "Z"
                    }
                    ground_axes = set([axes_name[self.doc.first_axis], axes_name[self.doc.second_axis]])
                    if self.view_grid:
                        # draw the grid
                        if ground_axes == {'X', 'Y'}:
                            for A, B in ui.viewer.make_gridXY_lines(step=1, size=10):
                                ui.viewer.guide(A, B)
                        elif ground_axes == {'X', 'Z'}:
                            for A, B in ui.viewer.make_gridXZ_lines(step=1, size=10):
                                ui.viewer.guide(A, B)
                        elif ground_axes == {'Y', 'Z'}:
                            for A, B in ui.viewer.make_gridYZ_lines(step=1, size=10):
                                ui.viewer.guide(A, B)
                        else:
                            logger.warning(f"Cannot draw grid for the selected axes. {solver.Axis(self.doc.first_axis).name}, {solver.Axis(self.doc.second_axis).name}")
                    
                    if self.view_axes:
                        ui.viewer.axes(length=1.0)

                    if self.view_horizon:
                        # draw the horizon line
                        if ground_axes == {'X', 'Y'}:
                            ui.viewer.horizon_line(ground='xy')
                        elif ground_axes == {'X', 'Z'}:
                            ui.viewer.horizon_line(ground='xz')
                        elif ground_axes == {'Y', 'Z'}:
                            ui.viewer.horizon_line(ground='yz')
                        else:
                            logger.warning(f"Cannot draw horizon line for the selected axes. {solver.Axis(self.doc.first_axis).name}, {solver.Axis(self.doc.second_axis).name}")
                    

                ui.viewer.end_scene()
        ui.viewer.end_viewer()

    def show_results(self):            
        if self.camera is not None:
            scale = glm.vec3()
            quat = glm.quat()  # This will be our quaternion
            translation = glm.vec3()
            skew = glm.vec3()
            perspective = glm.vec4()
            success = glm.decompose(self.camera.transform, scale, quat, translation, skew, perspective)
            if not success:
                imgui.text("Error: Could not decompose camera transform matrix.")
                return

            transform = [self.camera.transform[j][i] for i in range(4) for j in range(4)]
            euler = solver.extract_euler(self.camera.transform, order=self.current_euler_order)

            transform_text = solver.pretty_matrix(np.array(transform).reshape(4,4), separator=" ")
            position_text =  solver.pretty_matrix(np.array(translation), separator=" ")
            quat_text =      solver.pretty_matrix(np.array([quat.x, quat.y, quat.z, quat.w]), separator=" ")
            euler_text =     solver.pretty_matrix(np.array([math.degrees(radians) for radians in euler]), separator=" ")

            if ui.begin_attribute_editor("res props"):
                ui.next_attribute("transform")
                style = imgui.get_style()
                transform_text_size = imgui.calc_text_size(transform_text) + style.frame_padding * 2+imgui.ImVec2(50, 0)
                imgui.input_text_multiline("##transform", transform_text, size=transform_text_size, flags=imgui.InputTextFlags_.read_only)

                ui.next_attribute("position")
                imgui.input_text("##position", position_text, flags=imgui.InputTextFlags_.read_only)
                
                # imgui.begin_tooltip()

                ui.next_attribute("quaternion (xyzw)")
                imgui.input_text("##quaternion", quat_text, flags=imgui.InputTextFlags_.read_only)
                imgui.set_item_tooltip("Quaternion representing camera rotation (x, y, z, w)")

                # next_attribute("euler order")
                
                ui.next_attribute(f"euler")
                imgui.push_style_var(imgui.StyleVar_.item_spacing, imgui.ImVec2(2, style.item_spacing.y))
                euler_order_options = solver.EulerOrder._member_names_
                max_text_width = max([imgui.calc_text_size(text).x for text in euler_order_options])
                total_width = max_text_width + style.frame_padding.x * 2.0
                total_width+=imgui.get_frame_height() # for the arrow button todo: is it square for sure?
                imgui.set_next_item_width(total_width)
                # if imgui.begin_combo("##euler_order", solver.EulerOrder._member_names_[self.current_euler_order], imgui.ComboFlags_.no_arrow_button):
                #     for i, option in enumerate(euler_order_options):
                #         is_selected = (i == self.current_euler_order)
                #         _, selected_event =  imgui.selectable(option, is_selected)
                #         if selected_event:
                #             self.current_euler_order = i
                #         if is_selected:
                #             imgui.set_item_default_focus()
                #     imgui.end_combo()
                _, self.current_euler_order = imgui.combo("##euler_order", self.current_euler_order, solver.EulerOrder._member_names_)
                imgui.set_item_tooltip("Select the Euler angle rotation order used for decomposition.")
                imgui.same_line()
                imgui.set_next_item_width(-1)
                imgui.input_text("##euler", euler_text, flags=imgui.InputTextFlags_.read_only)
                imgui.set_item_tooltip("Euler angles in degrees (x,y,z).\nNote: Rotation is applied in order order: ZXY (Yaw, Pitch, Roll)")
                imgui.pop_style_var()
                ui.next_attribute("fovy")
                imgui.input_text("##fovy", f"{self.camera.fovy:.2f}°")
                ui.next_attribute("fovx")
                fovx = 2.0 * math.degrees(math.atan(math.tan(math.radians(self.camera.fovy) * 0.5) * (self.doc.content_size.x / self.doc.content_size.y)))
                imgui.input_text("##fovx", f"{fovx:.2f}°")

                ui.end_attribute_editor()

        if self.camera is not None:
            data = {
                "viewTransform": {
                    "rows": [[col for col in self.camera.viewMatrix()[j]] for j in range(4)]
                },
                "projectionTransform": {
                    "rows": [[col for col in self.camera.projectionMatrix()[j]] for j in range(4)]
                },
                "verticalFieldOfView": self.camera.fovy
            }
            # additional_data = {
            #     "principalPoint": {
            #         'x': self.doc.principal_point.x, 
            #         'y': self.doc.principal_point.y
            #     },
            #     "vanishingPoints": [
            #         {
            #             'x': self.first_vanishing_point.x, 
            #             'y': self.first_vanishing_point.y
            #         },
            #         {
            #             'x': self.second_vanishing_point.x, 
            #             'y': self.second_vanishing_point.y
            #         },
            #         "TODO:calculate third VP"
            #     ],
            #     "vanishingPointAxes": [
            #         solver.Axis._member_map_[self.doc.first_axis], 
            #         solver.Axis._member_map_[self.doc.second_axis],
            #         "TODO:thirdAxis"
            #     ],
            #     'focalLength': "todo: calculate from fov with the camera sensor size in mind",
            #     "imageWidth": int(self.doc.content_size.x),
            #     "imageHeight": int(self.doc.content_size.y)
            # }

            # import json
            # json_string = json.dumps(data, indent=4)
            # imgui.text(json_string)
            # if imgui.button("export camera parameters", imgui.ImVec2(-1,0)):
            #     ...

    def show_data(self):
        from textwrap import dedent
        if imgui.collapsing_header("Document as Python Code", imgui.TreeNodeFlags_.default_open):
            text = self.doc.document_to_python()
            imgui.text_unformatted(dedent(text).strip())

        if imgui.collapsing_header("Document as Dict", imgui.TreeNodeFlags_.default_open):
            imgui.text_unformatted("TODO. implement doc.to_dict()")

        if imgui.collapsing_header("Results Dictionary", imgui.TreeNodeFlags_.default_open):
            data = self.results_to_dict()
            text = pformat(data, indent=2, width=80, compact=False)
            # text = json.dumps(data, indent=4)
            imgui.text_unformatted(text)

        if imgui.collapsing_header("Blender Script", imgui.TreeNodeFlags_.default_open):
            data = self.results_to_blender_script()
            text = pformat(data, indent=2, width=80, compact=False)
            # text = json.dumps(data, indent=4)
            imgui.text_unformatted(text)
        # if imgui.collapsing_header("Parameters", imgui.TreeNodeFlags_.default_open):
        #     text = self.serialize()
        #     imgui.text_unformatted=(text)

        # if imgui.collapsing_header("Computed", imgui.TreeNodeFlags_.default_open):
        #     imgui.text("...")
       
    def show_emoji_test(self):
        imgui.text("Emoji Font Test")
        imgui.separator()
        
        # Calculate total emoji count
        total_sample_emojis = 0
        
        # Extended emoji categories with more comprehensive coverage
        emoji_categories = {
            "Smileys & Emotion (😀-😿)": [
                "😀", "😃", "😄", "😁", "😆", "😅", "🤣", "😂", "🙂", "🙃", "🫠",
                "😉", "😊", "😇", "🥰", "😍", "🤩", "😘", "😗", "☺", "😚", "😙",
                "🥲", "😋", "😛", "😜", "🤪", "😝", "🤑", "🤗", "🤭", "🫢", "🫣",
                "🤫", "🤔", "🫡", "🤐", "🤨", "😐", "😑", "😶", "🫥", "😶‍🌫", "😏",
                "😒", "🙄", "😬", "😮‍💨", "🤥", "😔", "😪", "🤤", "😴", "😷",
                "🤒", "🤕", "🤢", "🤮", "🤧", "🥵", "🥶", "🥴", "😵", "😵‍💫",
                "🤯", "🤠", "🥳", "🥸", "😎", "🤓", "🧐", "😕", "🫤", "😟",
                "🙁", "☹", "😮", "😯", "😲", "😳", "🥺", "🥹", "😦", "😧",
                "😨", "😰", "😥", "😢", "😭", "😱", "😖", "😣", "😞", "😓",
                "😩", "😫", "🥱", "😤", "😡", "😠", "🤬", "😈", "👿", "💀",
                "☠", "�", "🤡", "👹", "👺", "👻", "👽", "👾", "🤖", "😺",
                "😸", "😹", "😻", "😼", "😽", "🙀", "😿", "😾"
            ],
            "People & Body (�👋-🫶)": [
                "👋", "🤚", "🖐", "✋", "🖖", "🫱", "�", "🫳", "�", "👌",
                "�", "🤏", "✌", "🤞", "🫰", "🤟", "�🤘", "🤙", "👈", "👉",
                "👆", "🖕", "👇", "☝", "🫵", "👍", "👎", "👊", "✊", "🤛",
                "🤜", "👏", "🙌", "🫶", "👐", "🤲", "🤝", "🙏", "✍", "💅",
                "🤳", "💪", "🦾", "🦿", "🦵", "🦶", "👂", "🦻", "👃", "🧠",
                "🫀", "🫁", "🦷", "🦴", "👀", "👁", "👅", "👄", "🫦", "👶",
                "🧒", "👦", "👧", "🧑", "👱", "👨", "🧔", "👨‍🦰", "👨‍🦱", "👨‍🦳",
                "👨‍🦲", "👩", "👩‍🦰", "👩‍🦱", "👩‍🦳", "👩‍🦲", "🧓", "👴", "👵"
            ],
            "Animals & Nature (🐵-🦎)": [
                "🐵", "🐒", "🦍", "🦧", "🐶", "🐕", "🦮", "🐕‍🦺", "�", "🐺",
                "🦊", "🦝", "�🐱", "🐈", "🐈‍⬛", "🦁", "🐯", "🐅", "🐆", "🐴",
                "🐎", "🦄", "🦓", "🦌", "🦬", "🐮", "🐂", "🐃", "🐄", "🐷",
                "🐖", "�", "🐽", "🐏", "🐑", "🐐", "🐪", "🐫", "🦙", "🦒",
                "🐘", "🦣", "🦏", "🦛", "�🐭", "🐁", "🐀", "🐹", "🐰", "🐇",
                "🐿", "�", "🦔", "🦇", "🐻", "�‍❄", "🐨", "�", "🦥", "🦦",
                "�", "🦘", "🦡", "🐾", "🦃", "🐔", "�", "�", "�", "�",
                "�", "🐧", "🕊", "🦅", "🦆", "🦢", "🦉", "🦤", "🪶", "🦩",
                "🦚", "🦜", "�", "�", "�", "🦎", "🐍", "🐲", "🐉", "🦕",
                "🦖", "🐳", "🐋", "🐬", "🦭", "🐟", "🐠", "�", "🦈", "🐙"
            ],
            "Food & Drink (🍎-🍷)": [
                "🍎", "🍊", "🍋", "🍌", "🍉", "🍇", "🍓", "🫐", "🍈", "🍒",
                "🍑", "🥭", "🍍", "🥥", "🥝", "🍅", "🍆", "🥑", "🥦", "🥒",
                "🌶", "🫑", "🌽", "🥕", "🫒", "🧄", "🧅", "🥔", "🍠", "🫘",
                "🥐", "🍞", "🥖", "🥨", "🧀", "🥚", "🍳", "🧈", "🥞", "🧇",
                "🥓", "🥩", "🍗", "🍖", "🦴", "🌭", "🍔", "🍟", "🍕", "🫓",
                "🥙", "🧆", "🌮", "🌯", "🫔", "🥗", "🥘", "🫕", "🍝", "🍜",
                "🍲", "🍛", "🍣", "🍱", "🥟", "🦪", "🍤", "🍙", "🍚", "🍘",
                "🍥", "🥠", "🥮", "🍢", "🍡", "🍧", "🍨", "🍦", "🥧", "🧁",
                "🍰", "🎂", "🍮", "🍭", "🍬", "🍫", "🍿", "🍩", "🍪", "🌰",
                "🥜", "🍯", "🥛", "🍼", "🫖", "☕", "🍵", "🧃", "🥤", "🧋",
                "🍶", "🍺", "🍻", "🥂", "🍷", "🥃", "🍸", "🍹", "🧉", "🍾"
            ],
            "Travel & Places (🚗-🏰)": [
                "🚗", "🚕", "🚙", "🚌", "🚎", "🏎", "🚓", "🚑", "🚒", "🚐",
                "🛻", "🚚", "🚛", "🚜", "🏍", "🛵", "🚲", "🛴", "🛹", "🛼",
                "🚁", "🛸", "✈", "🛩", "🛫", "🛬", "🪂", "⛵", "🚤", "🛥",
                "🛳", "⛴", "🚢", "⚓", "🪝", "⛽", "🚧", "🚦", "🚥", "🗺",
                "🗿", "🗽", "🗼", "🏰", "🏯", "🏟", "🎡", "🎢", "🎠", "⛲",
                "⛱", "🏖", "🏝", "🏜", "🌋", "⛰", "🏔", "🗻", "🏕", "⛺"
            ],
            "Activities & Sports (⚽-🥇)": [
                "⚽", "🏀", "🏈", "⚾", "🥎", "🎾", "🏐", "🏉", "🥏", "🎱",
                "🪀", "🏓", "🏸", "🏒", "🏑", "🥍", "🏏", "🪃", "🥅", "⛳",
                "🪁", "🏹", "🎣", "🤿", "🥊", "🥋", "🎽", "🛹", "🛷", "⛸",
                "🥌", "🎿", "⛷", "🏂", "🪂", "🏋", "🤼", "🤸", "⛹", "🤺",
                "🏇", "🧘", "🏄", "🏊", "🤽", "🚣", "🧗", "🚵", "🚴", "🏆",
                "🥇", "🥈", "🥉", "🏅", "🎖", "🏵", "🎗", "🎫", "🎟", "🎪"
            ],
            "Objects & Technology (💻-📱)": [
                "💻", "🖥", "🖨", "⌨", "🖱", "🖲", "💽", "💾", "💿", "📀",
                "🧮", "📱", "📞", "☎", "📟", "📠", "📺", "📻", "🎙", "🎚",
                "🎛", "🧭", "⏱", "⏲", "⏰", "🕰", "⌛", "⏳", "📡", "🔋",
                "🪫", "🔌", "💡", "🔦", "🕯", "🪔", "🧯", "🛢", "💸", "💵",
                "💴", "💶", "💷", "🪙", "💰", "💳", "💎", "⚖", "🪜", "🧰"
            ],
            "Symbols & Flags (❤-🏁)": [
                "❤", "🧡", "💛", "💚", "💙", "💜", "🖤", "🤍", "🤎", "💔",
                "❣", "💕", "💞", "💓", "💗", "💖", "💘", "💝", "💟", "☮",
                "✝", "☪", "🕉", "☸", "✡", "🔯", "🕎", "☯", "☦", "🛐",
                "⛎", "♈", "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐",
                "♑", "♒", "♓", "🆔", "⚛", "🉑", "☢", "☣", "📴", "📳",
                "🈶", "🈚", "🈸", "🈺", "🈷", "✴", "🆚", "💮", "🉐", "㊙",
                "㊗", "🈴", "🈵", "🈹", "🈲", "🅰", "🅱", "🆎", "🆑", "🅾",
                "🆘", "❌", "⭕", "🛑", "⛔", "📛", "🚫", "💯", "💢", "♨",
                "🚷", "🚯", "🚳", "🚱", "🔞", "📵", "🚭", "❗", "❕", "❓",
                "❔", "‼", "⁉", "🔅", "🔆", "〽", "⚠", "🚸", "🔱", "⚜",
                "🔰", "♻", "✅", "🈯", "💹", "❇", "✳", "❎", "🌐", "💠",
                "Ⓜ", "🌀", "💤", "🏧", "🚾", "♿", "🅿", "🈳", "🈂", "🛂",
                "🛃", "🛄", "🛅", "🚹", "🚺", "🚼", "⚧", "🚻", "🚮", "🎦",
                "📶", "🈁", "🔣", "ℹ", "🔤", "🔡", "🔠", "🆖", "🆗", "🆙",
                "🆒", "🆕", "🆓", "0️⃣", "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣",
                "7️⃣", "8️⃣", "9️⃣", "🔟", "🔢", "#️⃣", "*️⃣", "⏏", "▶", "⏸",
                "⏯", "⏹", "⏺", "⏭", "⏮", "⏩", "⏪", "⏫", "⏬", "◀",
                "🔼", "🔽", "➡", "⬅", "⬆", "⬇", "↗", "↘", "↙", "↖",
                "↕", "↔", "↪", "↩", "⤴", "⤵", "🔀", "🔁", "🔂", "🔄",
                "🔃", "🎵", "🎶", "➕", "➖", "➗", "✖", "🟰", "♾", "💲",
                "💱", "™", "©", "®", "〰", "➰", "➿", "🔚", "🔙", "🔛",
                "🔝", "🔜", "✔", "☑", "🔘", "🔴", "🟠", "🟡", "🟢", "🔵",
                "🟣", "⚫", "⚪", "🟤", "🔺", "🔻", "🔸", "🔹", "🔶", "🔷",
                "🔳", "🔲", "▪", "▫", "◾", "◽", "◼", "◻", "🟥", "🟧",
                "🟨", "🟩", "🟦", "🟪", "⬛", "⬜", "🟫", "🔈", "🔇", "🔉",
                "🔊", "🔔", "🔕", "📣", "📢", "💬", "💭", "🗯", "♠", "♣",
                "♥", "♦", "🃏", "🎴", "🀄", "🕐", "🕑", "🕒", "🕓", "🕔",
                "🕕", "🕖", "🕗", "🕘", "🕙", "🕚", "🕛", "🕜", "🕝", "🕞",
                "🕟", "🕠", "🕡", "🕢", "🕣", "🕤", "🕥", "🕦", "🕧", "🏁"
            ]
        }
        
        # Count total emojis for statistics
        for category, emojis in emoji_categories.items():
            total_sample_emojis += len(emojis)
        
        # Show statistics
        imgui.text(f"Sample Coverage: {total_sample_emojis:,} emojis shown")
        imgui.text("📊 Unicode Emoji Statistics:")
        imgui.bullet_text("Total Unicode emojis: ~3,600+ (as of Unicode 15.1)")
        imgui.bullet_text("This sample shows major categories")
        imgui.bullet_text("Actual coverage depends on your system's emoji font")
        imgui.separator()
        
        # Show categories with emoji grids
        for category, emojis in emoji_categories.items():
            emoji_count = len(emojis)
            header_text = f"{category} ({emoji_count} emojis)"
            
            if imgui.collapsing_header(header_text):
                # Display emojis in a grid
                columns = 12  # More columns for better space usage
                for i, emoji in enumerate(emojis):
                    if i > 0 and i % columns != 0:
                        imgui.same_line()
                    
                    # Make emoji buttons for better interaction
                    if imgui.button(emoji, imgui.ImVec2(30, 30)):
                        # Copy emoji to clipboard (if supported)
                        pass
                    
                    if imgui.is_item_hovered():
                        # Try to get the actual Unicode codepoint(s)
                        try:
                            if len(emoji) == 1:
                                codepoint = ord(emoji)
                                imgui.set_tooltip(f"Unicode: U+{codepoint:04X}\nClick to copy")
                            else:
                                # Multi-codepoint emoji (like skin tones, ZWJ sequences)
                                codepoints = [f"U+{ord(c):04X}" for c in emoji]
                                imgui.set_tooltip(f"Unicode: {' '.join(codepoints)}\nClick to copy")
                        except:
                            imgui.set_tooltip(f"Emoji: {emoji}\nClick to copy")
                
                imgui.spacing()
        
        imgui.separator()
        imgui.text("🧪 Font Rendering Tests:")
        
        # Test different emoji types
        test_cases = [
            ("Basic Emojis", "😀 😃 😄 😁 😆 😅 🤣 😂"),
            ("Skin Tones", "👋 👋🏻 👋🏼 👋🏽 👋🏾 👋�"),
            ("Compound Emojis", "👨‍💻 👩‍🎓 🧑‍🚀 👩‍⚕️ 👨‍🍳"),
            ("Flags", "🏁 🏳️ 🏳️‍🌈 🏳️‍⚧️ 🏴‍☠️"),
            ("Recent Additions", "🫠 🫡 🫥 🫤 🫣 🫢 🫱 🫲"),
            ("Mixed Content", "Code: -> ≤ ≥ ≠ == /* */ // && || 🔥 💻"),
        ]
        
        for test_name, test_emoji in test_cases:
            imgui.text(f"{test_name}:")
            imgui.text(test_emoji)
            imgui.spacing()
        
        imgui.separator()
        imgui.text_colored((0.7, 0.7, 0.7, 1.0), "💡 Note: Emoji rendering depends on your system's emoji font.")
        imgui.text_colored((0.7, 0.7, 0.7, 1.0), "Some emojis may appear as □ if not supported.")

    def show_fontawesome_test(self):
        imgui.text("FontAwesome 4 Icons Test")
        imgui.separator()
        
        # Helper function to safely get FontAwesome icons
        def safe_icon(name, fallback=""):
            return getattr(icons_fontawesome_4, name, fallback)
        
        # FontAwesome icon categories with safe access
        icon_categories = {
            "Interface Icons": [
                (safe_icon('ICON_FA_HOME'), "Home"),
                (safe_icon('ICON_FA_USER'), "User"),
                (safe_icon('ICON_FA_SEARCH'), "Search"),
                (safe_icon('ICON_FA_COG', safe_icon('ICON_FA_GEAR')), "Settings"),
                (safe_icon('ICON_FA_BARS'), "Menu"),
                (safe_icon('ICON_FA_TIMES', safe_icon('ICON_FA_CLOSE')), "Close"),
                (safe_icon('ICON_FA_PLUS'), "Add"),
                (safe_icon('ICON_FA_MINUS'), "Remove"),
                (safe_icon('ICON_FA_EDIT', safe_icon('ICON_FA_PENCIL')), "Edit"),
                (safe_icon('ICON_FA_TRASH', safe_icon('ICON_FA_TRASH_O')), "Delete"),
                (safe_icon('ICON_FA_SAVE', safe_icon('ICON_FA_FLOPPY_O')), "Save"),
                (safe_icon('ICON_FA_UNDO'), "Undo"),
                (safe_icon('ICON_FA_REFRESH'), "Refresh"),
                (safe_icon('ICON_FA_DOWNLOAD'), "Download"),
                (safe_icon('ICON_FA_UPLOAD'), "Upload"),
            ],
            "Media & Files": [
                (safe_icon('ICON_FA_FILE', safe_icon('ICON_FA_FILE_O')), "File"),
                (safe_icon('ICON_FA_FOLDER', safe_icon('ICON_FA_FOLDER_O')), "Folder"),
                (safe_icon('ICON_FA_IMAGE', safe_icon('ICON_FA_PICTURE_O')), "Image"),
                (safe_icon('ICON_FA_VIDEO_CAMERA', safe_icon('ICON_FA_VIDEO')), "Video"),
                (safe_icon('ICON_FA_MUSIC'), "Music"),
                (safe_icon('ICON_FA_PLAY'), "Play"),
                (safe_icon('ICON_FA_PAUSE'), "Pause"),
                (safe_icon('ICON_FA_STOP'), "Stop"),
                (safe_icon('ICON_FA_VOLUME_UP'), "Volume Up"),
                (safe_icon('ICON_FA_VOLUME_DOWN'), "Volume Down"),
                (safe_icon('ICON_FA_VOLUME_OFF'), "Mute"),
            ],
            "Navigation": [
                (safe_icon('ICON_FA_ARROW_LEFT'), "Left"),
                (safe_icon('ICON_FA_ARROW_RIGHT'), "Right"),
                (safe_icon('ICON_FA_ARROW_UP'), "Up"),
                (safe_icon('ICON_FA_ARROW_DOWN'), "Down"),
                (safe_icon('ICON_FA_CHEVRON_LEFT'), "Chevron Left"),
                (safe_icon('ICON_FA_CHEVRON_RIGHT'), "Chevron Right"),
                (safe_icon('ICON_FA_CHEVRON_UP'), "Chevron Up"),
                (safe_icon('ICON_FA_CHEVRON_DOWN'), "Chevron Down"),
                (safe_icon('ICON_FA_ANGLE_LEFT'), "Angle Left"),
                (safe_icon('ICON_FA_ANGLE_RIGHT'), "Angle Right"),
            ],
            "Communication": [
                (safe_icon('ICON_FA_ENVELOPE', safe_icon('ICON_FA_ENVELOPE_O')), "Email"),
                (safe_icon('ICON_FA_PHONE'), "Phone"),
                (safe_icon('ICON_FA_COMMENT', safe_icon('ICON_FA_COMMENT_O')), "Comment"),
                (safe_icon('ICON_FA_COMMENTS', safe_icon('ICON_FA_COMMENTS_O')), "Comments"),
                (safe_icon('ICON_FA_BELL', safe_icon('ICON_FA_BELL_O')), "Bell"),
                (safe_icon('ICON_FA_HEART', safe_icon('ICON_FA_HEART_O')), "Heart"),
                (safe_icon('ICON_FA_STAR', safe_icon('ICON_FA_STAR_O')), "Star"),
                (safe_icon('ICON_FA_THUMBS_UP', safe_icon('ICON_FA_THUMBS_O_UP')), "Thumbs Up"),
                (safe_icon('ICON_FA_THUMBS_DOWN', safe_icon('ICON_FA_THUMBS_O_DOWN')), "Thumbs Down"),
            ],
            "Status & Indicators": [
                (safe_icon('ICON_FA_CHECK'), "Check"),
                (safe_icon('ICON_FA_TIMES'), "X/Cross"),
                (safe_icon('ICON_FA_EXCLAMATION'), "Exclamation"),
                (safe_icon('ICON_FA_QUESTION'), "Question"),
                (safe_icon('ICON_FA_INFO'), "Info"),
                (safe_icon('ICON_FA_WARNING', safe_icon('ICON_FA_EXCLAMATION_TRIANGLE')), "Warning"),
                (safe_icon('ICON_FA_BAN'), "Ban"),
                (safe_icon('ICON_FA_LOCK'), "Lock"),
                (safe_icon('ICON_FA_UNLOCK', safe_icon('ICON_FA_UNLOCK_ALT')), "Unlock"),
                (safe_icon('ICON_FA_EYE'), "Eye"),
                (safe_icon('ICON_FA_EYE_SLASH'), "Eye Slash"),
            ]
        }
        
        total_icons = sum(len(icons) for icons in icon_categories.values())
        imgui.text(f"FontAwesome 4 Sample: {total_icons} icons")
        imgui.text("Icons are vector-based and scale perfectly!")
        imgui.separator()
        
        for category, icons in icon_categories.items():
            if imgui.collapsing_header(category):
                columns = 5
                for i, (icon, name) in enumerate(icons):
                    if i > 0 and i % columns != 0:
                        imgui.same_line()
                    
                    # Create button with icon
                    button_size = imgui.ImVec2(80, 40)
                    if imgui.button(f"{icon}###{name}", button_size):
                        logger.info(f"Clicked {name} icon")
                    
                    if imgui.is_item_hovered():
                        imgui.set_tooltip(f"{name}\nIcon: {icon}")
                
                imgui.spacing()
        
        imgui.separator()
        imgui.text("Icon Integration Examples:")
        
        # Example usage in UI elements
        play_icon = safe_icon('ICON_FA_PLAY')
        pause_icon = safe_icon('ICON_FA_PAUSE')
        stop_icon = safe_icon('ICON_FA_STOP')
        info_icon = safe_icon('ICON_FA_INFO')
        home_icon = safe_icon('ICON_FA_HOME')
        chevron_icon = safe_icon('ICON_FA_CHEVRON_RIGHT')
        check_icon = safe_icon('ICON_FA_CHECK')
        
        if imgui.button(f"{play_icon} Play"):
            logger.info("Play button clicked")
        imgui.same_line()
        
        if imgui.button(f"{pause_icon} Pause"):
            logger.info("Pause button clicked")
        imgui.same_line()
        
        if imgui.button(f"{stop_icon} Stop"):
            logger.info("Stop button clicked")
        
        imgui.spacing()
        imgui.text(f"{info_icon} Mixed text with icons")
        imgui.text(f"{home_icon} Home {chevron_icon} Settings {chevron_icon} Display")
        
        imgui.separator()
        
        # Show available icons information
        available_icons = [attr for attr in dir(icons_fontawesome_4) if attr.startswith('ICON_FA_')]
        imgui.text(f"Available FontAwesome constants: {len(available_icons)}")
        
        # Debug: Show first few icon constants and their values
        imgui.separator()
        imgui.text("Debug: First 10 FontAwesome constants:")
        for i, icon_name in enumerate(available_icons[:10]):
            icon_value = getattr(icons_fontawesome_4, icon_name, "")
            # Show both the constant name and its Unicode value
            if icon_value:
                try:
                    unicode_val = ord(icon_value) if len(icon_value) == 1 else "multi-char"
                    imgui.text(f"{icon_name}: '{icon_value}' (U+{unicode_val:04X})" if unicode_val != "multi-char" else f"{icon_name}: '{icon_value}' (multi-char)")
                except:
                    imgui.text(f"{icon_name}: '{icon_value}' (unknown)")
            else:
                imgui.text(f"{icon_name}: (empty)")
        
        imgui.separator()
        imgui.text("Raw icon test (should show Unicode characters):")
        # Test some basic icons directly
        test_icons = ['ICON_FA_HOME', 'ICON_FA_USER', 'ICON_FA_SEARCH', 'ICON_FA_STAR']
        for icon_name in test_icons:
            if hasattr(icons_fontawesome_4, icon_name):
                icon_char = getattr(icons_fontawesome_4, icon_name)
                imgui.text(f"{icon_name}: -> {icon_char} <-")
                imgui.same_line()
                imgui.text_colored((0.7, 0.7, 0.7, 1.0), f"(should be an icon)")
            else:
                imgui.text(f"{icon_name}: NOT FOUND")
        
        imgui.separator()
        imgui.text_colored((1.0, 0.8, 0.3, 1.0), "If you see boxes □ or empty spaces, the FontAwesome font isn't loaded.")
        imgui.text_colored((0.7, 0.7, 0.7, 1.0), "The Unicode characters exist, but need the FontAwesome font to display properly.")
        
        imgui.separator()
        if check_icon:
            imgui.text_colored((0.3, 0.8, 0.3, 1.0), f"{check_icon} FontAwesome constants are loaded")
        else:
            imgui.text_colored((1.0, 0.7, 0.3, 1.0), "FontAwesome constants may be missing")
        
        imgui.text_colored((0.7, 0.7, 0.7, 1.0), "Note: Icons need proper font loading to render correctly")
        
    # Events
    def on_file_drop(self, window, paths):
        from pathlib import Path
        """GLFW drop callback - receives list of paths"""
        logger.info(f"Files dropped: {paths}")
        if len(paths) > 0:
            first_path = paths[0]
            self.load_image_file(first_path)

    # Actions
    def solve(self):
        """Solve for camera based on current document state
        throws exceptions on failure
        """
        # Solve for camera
        self.first_vanishing_point:glm.vec2|None = None
        self.second_vanishing_point:glm.vec2|None = None
        self.camera:Camera|None = None

        if self.doc.enable_auto_principal_point:
            self.doc.principal_point = glm.vec2(self.doc.content_size.x / 2, self.doc.content_size.y / 2)
        match self.doc.solver_mode:
            case SolverMode.OneVP:
                ###############################
                # 1. COMPUTE vanishing points #
                ###############################
                self.first_vanishing_point =  solver.least_squares_intersection_of_lines(self.doc.first_vanishing_lines)
                
                ###################
                # 2. Solve Camera #
                ###################
                fovy = math.radians(self.doc.fov_degrees)
                focal_length_pixel = solver.focal_length_from_fov(fovy, self.doc.content_size.y)
                self.solver_results:solver.SolverResults = solver.solve1vp(
                    width =                 self.doc.content_size.x, 
                    height =                self.doc.content_size.y, 
                    Fu=                     self.first_vanishing_point,
                    second_vanishing_line = self.doc.second_vanishing_lines[0],
                    f =                     focal_length_pixel,
                    P =                     self.doc.principal_point,
                    O =                     self.doc.origin,
                    first_axis =            self.doc.first_axis,
                    second_axis =           self.doc.second_axis,
                    scale =                 self.doc.scene_scale
                )

                # create camera
                self.camera = Camera()
                self.camera.setFoVY(math.degrees(self.solver_results.fovy))
                self.camera.transform = self.solver_results.transform
                self.camera.setAspectRatio(self.doc.content_size.x / self.doc.content_size.y)


            case SolverMode.TwoVP:
                # compute vanishing points
                self.first_vanishing_point =  solver.least_squares_intersection_of_lines(
                    self.doc.first_vanishing_lines)
                self.second_vanishing_point = solver.least_squares_intersection_of_lines(
                    self.doc.second_vanishing_lines)

                self.solver_results = solver.solve2vp(
                    self.doc.content_size.x, 
                    self.doc.content_size.y, 
                    self.first_vanishing_point,
                    self.second_vanishing_point,
                    self.doc.principal_point,
                    self.doc.origin,
                    self.doc.first_axis,
                    self.doc.second_axis,
                    self.doc.scene_scale
                )

                # create camera
                self.camera = Camera()
                self.camera.transform = self.solver_results.transform
                self.camera.setFoVY(math.degrees(self.solver_results.fovy))
                self.camera.setAspectRatio(self.doc.content_size.x / self.doc.content_size.y)
                self.camera.set_lens_shift(self.solver_results.shift_x, self.solver_results.shift_y)
                
    def load_image_file(self, path:str|None=None):
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

            self.doc.image_path = path

            # Load image with PIL
            img = Image.open(path)
            self.doc.image = img
            self.doc.content_size = imgui.ImVec2(img.width, img.height)
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

    def _upload_image_texture(self, img: Image):
        """Helper to upload PIL image to OpenGL texture."""
        # Convert to RGBA if needed
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        img_data = np.array(img, dtype=np.uint8)
        
        # Delete old texture if exists
        if self.image_texture_id is not None:
            gl.glDeleteTextures(1, [self.image_texture_id])
        
        # Generate new texture
        texture_id = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, texture_id)
        
        # Set texture parameters
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
        
        # Upload texture data
        gl.glTexImage2D(
            gl.GL_TEXTURE_2D,
            0,
            gl.GL_RGBA,
            img.width,
            img.height,
            0,
            gl.GL_RGBA,
            gl.GL_UNSIGNED_BYTE,
            img_data
        )
        
        self.image_texture_id = texture_id
        logger.info(f"✓ Uploaded texture (ID: {texture_id})")

    def _export_text_to_file(self, default_name: str, content: str, file_type: str, extension: str):
        """Helper to save text content to a file via dialog."""
        # open the file dialog
        file_dialog = pfd.save_file(
            title=f"Save {file_type}",
            default_path=default_name,
            filters=[f"{file_type} Files", f"*{extension}", "All Files", "*.*"],
            options=pfd.opt.none
        )

        save_path = file_dialog.result()
        if save_path is None:
            logger.info("Save cancelled by user.")
            return
        
        if not isinstance(save_path, str):
            logger.error(f"Invalid save path: {save_path}")
            return
        
        # save content to file
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"{file_type} saved to {save_path}")
        except Exception as e:
            logger.error(f"Failed to save {file_type} to {save_path}: {e}")
            import traceback
            traceback.print_exc()

    def results_to_dict(self) -> Dict[str, Any]:
        import document
        
        result:Dict[str, Any] = dict()
        if self.camera is not None:
            _, quat, translation, _, _ = solver.decompose(self.camera.transform)
            euler = solver.extract_euler(self.camera.transform, order=self.current_euler_order)
            camera_data = {
                "transform": self.camera.transform,
                "fov_degrees": self.camera.fovy,
                "position": self.camera.getPosition(),
                "quaternion_xyzw": quat,
                "euler_degrees_xyz": glm.vec3(euler[0], euler[1], euler[2]),
                "euler_order": solver.EulerOrder._member_names_[self.current_euler_order]
            }
            result["camera"] = camera_data

        vanishing_points_data:Dict[str, Any] = dict()
        if self.first_vanishing_point is not None:
            vanishing_points_data["first_vanishing_point"] = {
                "x": self.first_vanishing_point.x,
                "y": self.first_vanishing_point.y
            }
        if self.second_vanishing_point is not None:
            vanishing_points_data["second_vanishing_point"] = {
                "x": self.second_vanishing_point.x,
                "y": self.second_vanishing_point.y
            }
        result["vanishing_points"] = vanishing_points_data
        return result

    def results_to_blender_script(self) -> str:
        """Generate a Blender Python script to recreate the camera setup."""
        if self.camera is None:
            logger.error("No camera data to export.")
            return "# No camera data available."

        from textwrap import dedent
        blender_template_path = hello_imgui.asset_file_full_path("blender_camera_factory_template.py")
        script = Path(blender_template_path).read_text()

        fovx = 2.0 * math.degrees(math.atan(math.tan(math.radians(self.camera.fovy) * 0.5) * (self.doc.content_size.x / self.doc.content_size.y)))
        script = script.replace("<CAMERA_FOV>", str(math.radians(max(fovx, self.camera.fovy))))
        transform_list = [[v for v in row] for row in glm.transpose(self.camera.transform)]
        script = script.replace("<CAMERA_TRANSFORM>", str(transform_list))
        script = script.replace("<CAMERA_NAME>", "'PerspyCamera'")
        return script


if __name__ == "__main__":
    from imgui_bundle import immapp
    from imgui_bundle import hello_imgui
    from hello_imgui_config import create_my_runner_params
    app = PerspyApp()
    assets_folder = Path(__file__).parent / "assets"
    assert assets_folder.exists(), f"Assets folder not found: {assets_folder.absolute()}"
    print("setting assets folder:", assets_folder.absolute())
    hello_imgui.set_assets_folder(str(assets_folder.absolute()))
    hello_imgui.run(create_my_runner_params(app.gui, app.on_file_drop, "Perspy v0.5.0"))

