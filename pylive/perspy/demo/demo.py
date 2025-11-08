# Standard library imports
import math
from pprint import pformat
from typing import Any, List, Tuple, Dict
from enum import IntEnum
import json
import base64
import logging

# Third-party imports
from PIL import Image
import OpenGL.GL as gl
import glm
import numpy as np
from imgui_bundle import imgui, icons_fontawesome_4
from imgui_bundle import portable_file_dialogs as pfd

# Local application imports
from pylive.glrenderer.utils.camera import Camera
from pylive.perspy import solver
import ui

# Configure logging to see shader compilation logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

sidebar_opacity = 0.8
def begin_sidebar(name:str, p_open:bool|None=None, flags:int=0) -> bool:
    SIDEBAR_FLAGS = imgui.WindowFlags_.always_auto_resize | imgui.WindowFlags_.no_move | imgui.WindowFlags_.no_resize | imgui.WindowFlags_.no_collapse
    style = imgui.get_style()
    window_bg = style.color_(imgui.Col_.window_bg)
    title_bg = style.color_(imgui.Col_.title_bg)
    title_bg = style.color_(imgui.Col_.title_bg_active)
    border   = style.color_(imgui.Col_.border)
    imgui.push_style_color(imgui.Col_.window_bg, (*list(window_bg)[:3], sidebar_opacity))
    imgui.push_style_color(imgui.Col_.title_bg,  (*list(title_bg)[:3], sidebar_opacity))
    imgui.push_style_color(imgui.Col_.border,    (*list(border)[:3], sidebar_opacity))
    return imgui.begin(name, None, SIDEBAR_FLAGS)

def end_sidebar():
    imgui.end()
    imgui.pop_style_color(3)
    # imgui.pop_style_var()

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

# ########### #
# Application #
# ########### #

class PerspyDocument:
    def __init__(self):
        # solver inputs
        # - content image
        self.image_path: str|None = None
        self.content_size = imgui.ImVec2(1280,720)
        self.image: Image = None
        self.image_texture_ref:imgui.ImTextureRef|None = None
        self.image_texture_id: int|None = None

        # - solver params
        self.solver_mode=SolverMode.OneVP
        self.scene_scale=5.0
        self.first_axis=solver.Axis.PositiveZ
        self.second_axis=solver.Axis.PositiveX
        self.fov_degrees=60.0 # only for OneVP mode
        self.quad_mode=False # only for TwoVP mode. is this a ui state?

        # - control points
        self.origin_pixel=self.content_size/2
        self.principal_point_pixel=self.content_size/2
        self.first_vanishing_lines_pixel = [
            (glm.vec2(296, 417), glm.vec2(633, 291)),
            (glm.vec2(654, 660), glm.vec2(826, 344))
        ]
        self.second_vanishing_lines_pixel = [
            [glm.vec2(381, 363), glm.vec2(884, 451)],
            [glm.vec2(511, 311), glm.vec2(879, 356)]
        ]

        # - manage view
        self.view_grid: bool = True
        self.view_horizon: bool = True

    # Document manager
    def serialize(self)->str:
        def serializer(obj):
            """Custom JSON serializer for glm types."""
            match obj:
                case glm.vec2():
                    return {'x': obj.x, 'y': obj.y}
                case glm.vec3():
                    return {'x': obj.x, 'y': obj.y, 'z': obj.z}
                case glm.vec4():
                    return {'x': obj.x, 'y': obj.y, 'z': obj.z, 'w': obj.w}
                case glm.mat4():
                    return {"rows": [
                        [obj[col][row] for col in range(4)]
                        for row in range(4)
                    ]}
                case imgui.ImVec2():
                    return {'x': obj.x, 'y': obj.y}
                case imgui.ImVec4():
                    return {'x': obj.x, 'y': obj.y, 'z': obj.z, 'w': obj.w}
                case Image():
                    image_embed_data = b''
                    import io
                    buffer = io.BytesIO()
                    self.image.save(buffer, format='PNG') # Save as PNG to preserve quality, consider using other image formats
                    image_embed_data = buffer.getvalue()
                    return base64.b64encode(obj).decode('ascii')
                case _:
                    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

        _, quat, _, _, _ = solver.decompose(self.camera.transform)
        euler = solver.extract_euler(self.camera.transform, order=self.current_euler_order)

        data = {
            'version': '0.5.0',
            'solver_params': {
                "mode": SolverMode(self.solver_mode).name,
                "first_axis": solver.Axis(self.first_axis).name,
                "second_axis": solver.Axis(self.second_axis).name,
                "scene_scale": self.scene_scale,
                "fov_degrees": 60.0,
                "quad_mode": False
            },

            'control_points': {
                "origin": self.origin_pixel,
                "principal_point": self.principal_point_pixel,
                "first_vanishing_lines": self.first_vanishing_lines_pixel,
                "second_vanishing_lines": self.second_vanishing_lines_pixel
            },

            'image_params': {
                "path": self.image_path,
                "width": int(self.content_size.x),
                "height": int(self.content_size.y)
            },

            'results': {
                "camera": {
                    "view": self.camera.viewMatrix(),
                    "projection": self.camera.projectionMatrix(),
                    "fovy_degrees": self.camera.fovy,
                    "position": self.camera.getPosition(),
                    "rotation_euler": {"x": euler[0], "y": euler[1], "z": euler[2], "order": solver.EulerOrder(self.current_euler_order).name},
                    "rotation_quaternion": {"x": quat.x, "y": quat.y, "z": quat.z, "w": quat.w}
                },
                "vanishing_points": {
                    "first": self.first_vanishing_point_pixel,
                    "second": self.second_vanishing_point_pixel
                }
            },

            'guides_params': {
                "show_grid": self.view_grid,
                "show_horizon": self.view_horizon
            },

            'ui_state': {
                "dim_background": self.dim_background,
                "windows": {
                    "show_data": self.show_data_window,
                    "show_style_editor": self.show_styleeditor_window
                }
            }
        }

        return json.dumps(data, indent=4, default=serializer)

    def deserialize(self, json_text: str):
        raise NotImplementedError("Deserialization from JSON is not implemented yet.")
    

class PerspyApp(PerspyDocument):
    def __init__(self):
        super().__init__()

        # solver results
        self.current_euler_order = solver.EulerOrder.ZXY
        self.first_vanishing_point_pixel:glm.vec2|None = None
        self.second_vanishing_point_pixel:glm.vec2|None = None
        self.camera:Camera|None = None

        # ui state
        self.pan_and_zoom_matrix = glm.identity(glm.mat4)
        self.dim_background: bool = True

        # - manage windows
        self.show_about_popup: bool = False
        self.show_emoji_window: bool = False
        self.show_fontawesome_window: bool = False
        self.show_data_window: bool = True
        self.show_styleeditor_window: bool = False

        # misc
        """
        Can be used to define inline variables, similarly how static vars used in C/C++ with imgui.
        
        Example:
        self.misc.setdefault('my_var', 0)
        _, self.misc['my_var'] = imgui.slider_float("my var", self.misc['my_var'], 0.0, 1.0)
        """
        self.misc:Dict[str, Any] = dict() # miscellaneous state variables for development. 

    def save(self, filepath: str|None):
        """
        Save the app state to a custom .perspy file format.
        
        File structure:
        - Magic number (4 bytes): b'prsp' (perspective spy)
        - Version (4 bytes): version number
        - JSON size (4 bytes): size of the state JSON
        - Image size (4 bytes): size of the image data
        - JSON data: serialized app state
        - Image data: raw image bytes (if available)
        """

        if filepath is None:
            """Prompt for file location"""
            save_dialog = pfd.save_file(
                title="Save Project As", 
                default_path="project.perspy", 
                file_types=["perspy files (*.perspy)"]
            )
            if path:=save_dialog.result():
                filepath = path

        import json
        from struct import pack
        
        # Get JSON state
        state_json = self.serialize().encode('utf-8')
        state_size = len(state_json)
        
        # Get image data
        image_data = b''
        if self.image is not None:
            import io
            buffer = io.BytesIO()
            # Save as PNG to preserve quality
            self.image.save(buffer, format='PNG')
            image_data = buffer.getvalue()
        image_size = len(image_data)
        
        # Write file
        magic = int.from_bytes(b'prsy', byteorder='little')  # 'prsy'
        version = 1
        
        with open(filepath, 'wb') as f:
            # Write header (16 bytes)
            f.write(pack('<I', magic))        # 4 bytes: magic number
            f.write(pack('<I', version))      # 4 bytes: version
            f.write(pack('<I', state_size))   # 4 bytes: JSON size
            f.write(pack('<I', image_size))   # 4 bytes: image size
            
            # Write data
            f.write(state_json)
            if image_data:
                f.write(image_data)
        
        logger.info(f"✓ Saved to {filepath}")
        logger.info(f"  State size: {state_size} bytes, Image size: {image_size} bytes")

    def open(self, filepath: str|None):
        """
        Load app state from a .perspy file.
        """
        import json
        from struct import unpack
        import io

        if filepath is None:
            """Prompt for file location"""
            open_file_dialog = pfd.open_file(
                title="Open Project", 
                default_path="", 
                file_types=["perspy files (*.perspy)"]
            )
            paths = open_file_dialog.result()
            if len(paths) > 0:
                filepath = paths[0]
            else:
                return
        
        with open(filepath, 'rb') as f:
            # Read header
            magic_bytes = f.read(4)
            if magic_bytes != b'prsp':
                raise ValueError(f"Not a valid .perspy file (got magic: {magic_bytes})")
            
            version = unpack('<I', f.read(4))[0]
            if version != 1:
                raise ValueError(f"Unsupported version: {version}")
            
            state_size = unpack('<I', f.read(4))[0]
            image_size = unpack('<I', f.read(4))[0]
            
            # Read state JSON
            state_json = f.read(state_size).decode('utf-8')
            
            # Read image data
            image_data = None
            if image_size > 0:
                image_data = f.read(image_size)
        
        # Use deserialize to restore state from JSON
        self.deserialize(state_json)
        
        # Load image
        if image_data:
            import io
            self.image = Image.open(io.BytesIO(image_data))
            self.content_size = imgui.ImVec2(float(self.image.width), float(self.image.height))
            
            # Create OpenGL texture
            self._upload_image_texture(self.image)
            
            logger.info(f"✓ Loaded from {filepath}")
            logger.info(f"  Image: {self.image.width}x{self.image.height}")
        else:
            logger.warning("No image data in file")
    
    # Windows
    def gui(self):        
        # Compute Camera
        self.camera = Camera()

        # Create main menu bar (independent of any window)
        self.show_main_menu_bar()
        menu_bar_height = imgui.get_frame_height()

        # Model About window
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
        style = imgui.get_style()
        display_size = imgui.get_io().display_size

        imgui.set_next_window_pos(imgui.ImVec2(style.window_padding.x, display_size.y/2), imgui.Cond_.always, imgui.ImVec2(0.0, 0.5))
        if begin_sidebar("Parameters", None):
            self.show_parameters()
        end_sidebar()

        # Solve the camera
        self.solve()

        # fullscreen viewer Window
        imgui.set_next_window_pos(imgui.ImVec2(0, menu_bar_height))
        imgui.set_next_window_size(imgui.ImVec2(display_size.x, display_size.y - menu_bar_height))       
        if imgui.begin("MainViewport", None, imgui.WindowFlags_.no_bring_to_front_on_focus | imgui.WindowFlags_.no_move | imgui.WindowFlags_.no_resize | imgui.WindowFlags_.no_collapse | imgui.WindowFlags_.no_title_bar):
            self.show_viewer()
        imgui.end()

        # Results Window
        imgui.set_next_window_pos(imgui.ImVec2(display_size.x-style.window_padding.x, display_size.y/2), imgui.Cond_.always, imgui.ImVec2(1.0, 0.5))
        if begin_sidebar("Results"):
            self.show_results()
        end_sidebar()

        if self.show_data_window:
            expanded, self.show_data_window = imgui.begin("data window", self.show_data_window)
            if expanded:
                self.show_file()
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
                    self.open_project_file()
                
                if imgui.menu_item_simple(f"{save_icon} Save", "Ctrl+S"):
                    self.save_project_file()
                
                if imgui.menu_item_simple(f"{save_icon} Save As...", "Ctrl+Shift+S"):
                    self.save_project_file_as()

                imgui.separator()

                if imgui.menu_item_simple(f"{folder_icon} Load Image", "Ctrl+O"):
                    self.load_image_file()
                
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

                global sidebar_opacity
                _, sidebar_opacity = imgui.slider_float("sidebar opacity", sidebar_opacity, 0.0, 1.0, "%.2f")

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

            if imgui.begin_menu("Help"):
                # Use safe icon access with fallback
                book_icon = getattr(icons_fontawesome_4, 'ICON_FA_BOOK', '')
                info_icon = getattr(icons_fontawesome_4, 'ICON_FA_INFO_CIRCLE', getattr(icons_fontawesome_4, 'ICON_FA_INFO', ''))
                
                if imgui.menu_item_simple(f"{book_icon} Manual"):
                    ...
                if imgui.menu_item_simple(f"{info_icon} About"):
                    self.show_about_popup = True

                
                imgui.end_menu()
            
            # Store the actual height of the menu bar
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
        imgui.separator_text("Image")
        imgui.set_next_item_width(150)
        if self.image_texture_ref is None:
            if imgui.button("open image", size=imgui.ImVec2(-1,0)):
                self.load_image_file()
            imgui.set_next_item_width(150)
            _, value = imgui.input_int2("image size", [int(self.content_size.x), int(self.content_size.y)])
            if _:
                self.content_size = imgui.ImVec2(value[0], value[1])
        else:
            image_aspect = self.content_size.x / self.content_size.y
            width = imgui.get_content_region_avail().x-imgui.get_style().frame_padding.x*2
            if imgui.image_button("open", self.image_texture_ref, imgui.ImVec2(width, width/image_aspect)):
                self.load_image_file()
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

    def show_viewer(self):
        if ui.viewer.begin_viewer("viewer1", content_size=self.content_size, size=imgui.ImVec2(-1,-1), coordinate_system="top-left"):
            if self.image_texture_ref is not None:
                tl = ui.viewer._get_window_coords(imgui.ImVec2(0,0))
                br = ui.viewer._get_window_coords(imgui.ImVec2(self.content_size.x, self.content_size.y))
                image_size = br - tl
                imgui.set_cursor_pos(tl)
                if self.dim_background:
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
                    if self.view_grid:
                        # draw the grid
                        for A, B in ui.viewer.make_gridXZ_lines(step=1, size=10):
                            ui.viewer.guide(A, B)
                    ui.viewer.axes(length=1.0)
                    if self.view_horizon:
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
            if not success:
                imgui.text("Error: Could not decompose camera transform matrix.")
                return
            pos = self.camera.getPosition()
            transform = [self.camera.transform[j][i] for i in range(4) for j in range(4)]
            euler = solver.extract_euler(self.camera.transform, order=self.current_euler_order)

            transform_text = pretty_matrix(np.array(transform).reshape(4,4), separator="\t")
            position_text = pretty_matrix(np.array(translation), separator="\t")
            quat_text = pretty_matrix(np.array([quat.x, quat.y, quat.z, quat.w]), separator="\t")
            euler_text = pretty_matrix(np.array(euler), separator="\t")

            if ui.begin_attribute_editor("res props"):
                ui.next_attribute("transform")
                style = imgui.get_style()
                transform_text_size = imgui.calc_text_size(transform_text) + style.frame_padding * 2
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
                ui.next_attribute("fov")
                imgui.input_text("##fov", f"{self.camera.fovy:.2f}°")

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
            #         'x': self.principal_point_pixel.x, 
            #         'y': self.principal_point_pixel.y
            #     },
            #     "vanishingPoints": [
            #         {
            #             'x': self.first_vanishing_point_pixel.x, 
            #             'y': self.first_vanishing_point_pixel.y
            #         },
            #         {
            #             'x': self.second_vanishing_point_pixel.x, 
            #             'y': self.second_vanishing_point_pixel.y
            #         },
            #         "TODO:calculate third VP"
            #     ],
            #     "vanishingPointAxes": [
            #         solver.Axis._member_map_[self.first_axis], 
            #         solver.Axis._member_map_[self.second_axis],
            #         "TODO:thirdAxis"
            #     ],
            #     'focalLength': "todo: calculate from fov with the camera sensor size in mind",
            #     "imageWidth": int(self.content_size.x),
            #     "imageHeight": int(self.content_size.y)
            # }

            # import json
            # json_string = json.dumps(data, indent=4)
            # imgui.text(json_string)
            # if imgui.button("export camera parameters", imgui.ImVec2(-1,0)):
            #     ...

    def show_file(self):
        from textwrap import dedent
        if imgui.collapsing_header("Serialized", imgui.TreeNodeFlags_.default_open):
            text = self.serialize()
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
        self.data = json.loads(self.serialize())
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

            self.image_path = path

            # Load image with PIL
            img = Image.open(path)
            self.image = img
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


if __name__ == "__main__":
    from imgui_bundle import hello_imgui
    app = PerspyApp()

    # Setup HelloImGui application parameters
    def create_fontawesome_assets_folder(self):
        """Create the proper assets folder structure for FontAwesome fonts"""
        from pathlib import Path
        
        # Create the assets/fonts directory structure
        demo_dir = Path(__file__).parent
        assets_fonts_dir = demo_dir / "assets" / "fonts"
        
        try:
            assets_fonts_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"✓ Created directory: {assets_fonts_dir}")
            
            # Create a README file with instructions
            readme_file = assets_fonts_dir / "README_FontAwesome.txt"
            readme_content = """FontAwesome Font Setup for ImGui Bundle

    This folder should contain: fontawesome-webfont.ttf

    HOW TO GET FontAwesome FONT:

    1. Download FontAwesome 4 Web Font:
    Visit: https://fontawesome.com/v4/get-started/
    Download the web font package
    Extract fontawesome-webfont.ttf from the fonts/ folder

    2. Download ImGui Bundle default assets (includes FontAwesome):
    Visit: https://traineq.org/ImGuiBundle/assets.zip
    Extract to get the complete assets folder with fonts

    3. Use wget/curl (if available):
    wget https://github.com/FortAwesome/Font-Awesome/raw/v4.7.0/fonts/fontawesome-webfont.ttf

    Once you have fontawesome-webfont.ttf, place it in this folder.
    Then restart your application to load FontAwesome icons!
    """
            
            with open(readme_file, 'w', encoding='utf-8') as f:
                f.write(readme_content)
            
            logger.info(f"✓ Created instructions: {readme_file}")
            logger.info("📁 Assets folder structure created!")
            logger.info("📋 Check README_FontAwesome.txt for detailed instructions")
            logger.info("")
            logger.info("🚀 Next steps:")
            logger.info("   1. Download fontawesome-webfont.ttf (see README)")
            logger.info(f"   2. Place it in: {assets_fonts_dir}/")
            logger.info("   3. Restart the application")
            
        except Exception as e:
            logger.error(f"Failed to create assets folder: {e}")
            import traceback
            traceback.print_exc()

    def load_additional_fonts():
        """Load FiraCode fonts with emoji support"""
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
                # Configure font to merge with system emoji font
                font_cfg = imgui.ImFontConfig()
                font_cfg.merge_mode = False  # First font, don't merge
                
                # Add FiraCode as primary font
                font = io.fonts.add_font_from_file_ttf(str(fira_regular), base_size, font_cfg)
                logger.info(f"✓ Loaded FiraCode Regular from {fira_regular} at {base_size}px")
                
                # Add FontAwesome icons as merged font
                # Try different FontAwesome loading methods based on imgui_bundle version
                fa_loaded = False
                
                try:
                    # Method 1: Check if immapp has FontAwesome functions
                    from imgui_bundle import immapp
                    if hasattr(immapp, 'add_font_awesome_to_font_atlas'):
                        immapp.add_font_awesome_to_font_atlas()
                        fa_loaded = True
                        logger.info("✓ Loaded FontAwesome via immapp.add_font_awesome_to_font_atlas()")
                    elif hasattr(immapp, 'load_font_awesome'):
                        immapp.load_font_awesome(base_size)
                        fa_loaded = True
                        logger.info("✓ Loaded FontAwesome via immapp.load_font_awesome()")
                except Exception as e1:
                    logger.warning(f"immapp FontAwesome loading failed: {e1}")
                
                if not fa_loaded:
                    try:
                        # Method 2: Try manual font file approach
                        import os
                        from pathlib import Path
                        
                        # Look for FontAwesome font file per imgui_bundle conventions
                        script_dir = Path(__file__).parent
                        possible_fa_paths = [
                            # imgui_bundle expects FontAwesome in assets/fonts/ folder
                            script_dir / "assets" / "fonts" / "fontawesome-webfont.ttf",
                            script_dir / "assets" / "fonts" / "fa-solid-900.ttf",  # FontAwesome 5/6
                            script_dir / "assets" / "fonts" / "FontAwesome.ttf",
                            # Also check the fonts/ folder you already have
                            script_dir / "fonts" / "fontawesome-webfont.ttf",
                            script_dir / "fonts" / "FontAwesome.ttf",
                            # Check parent directory assets (common pattern)
                            script_dir.parent / "assets" / "fonts" / "fontawesome-webfont.ttf",
                            # Try system fonts
                            Path("C:/Windows/Fonts/fontawesome-webfont.ttf"),
                        ]
                        
                        fa_font_loaded = False
                        for fa_path in possible_fa_paths:
                            if fa_path.exists():
                                try:
                                    # Method 1: Try with glyph ranges
                                    fa_config = imgui.ImFontConfig()
                                    fa_config.merge_mode = True
                                    
                                    # Create glyph ranges properly for imgui_bundle
                                    fa_ranges = imgui.GlyphRangesBuilder()
                                    fa_ranges.add_ranges(imgui.get_io().fonts.get_glyph_ranges_default())
                                    # Add FontAwesome range
                                    fa_ranges.add_char(ord(icons_fontawesome_4.ICON_MIN_FA))
                                    fa_ranges.add_char(ord(icons_fontawesome_4.ICON_MAX_FA))
                                    ranges = fa_ranges.build_ranges()
                                    
                                    font = io.fonts.add_font_from_file_ttf(str(fa_path), base_size, fa_config, ranges)
                                    if font:
                                        logger.info(f"✓ Loaded FontAwesome from file (with ranges): {fa_path}")
                                        fa_font_loaded = True
                                        fa_loaded = True
                                        break
                                except Exception as e3a:
                                    logger.warning(f"Failed to load FontAwesome with ranges from {fa_path}: {e3a}")
                                    try:
                                        # Method 2: Try without ranges (simpler)
                                        fa_config_simple = imgui.ImFontConfig()
                                        fa_config_simple.merge_mode = True
                                        font = io.fonts.add_font_from_file_ttf(str(fa_path), base_size, fa_config_simple)
                                        if font:
                                            logger.info(f"✓ Loaded FontAwesome from file (no ranges): {fa_path}")
                                            fa_font_loaded = True
                                            fa_loaded = True
                                            break
                                    except Exception as e3b:
                                        logger.warning(f"Failed to load FontAwesome without ranges from {fa_path}: {e3b}")
                                    try:
                                        # Method 3: Try with None config (most basic)
                                        font = io.fonts.add_font_from_file_ttf(str(fa_path), base_size)
                                        if font:
                                            logger.info(f"✓ Loaded FontAwesome from file (basic): {fa_path}")
                                            fa_font_loaded = True
                                            fa_loaded = True
                                            break
                                    except Exception as e3c:
                                        logger.warning(f"All FontAwesome loading methods failed for {fa_path}: {e3c}")
                        
                        if not fa_font_loaded and not fa_loaded:
                            logger.warning("No FontAwesome font loaded. Icons will appear as boxes or empty spaces.")
                            logger.info("FontAwesome constants are available but need the font file to render properly.")
                            logger.info("")
                            logger.info("📁 WHERE TO PLACE FontAwesome FONT:")
                            demo_dir = Path(__file__).parent
                            logger.info(f"   Create: {demo_dir}/assets/fonts/")
                            logger.info(f"   Place fontawesome-webfont.ttf in that folder")
                            logger.info("")
                            logger.info("📦 HOW TO GET FontAwesome FONT:")
                            logger.info("   1. Download from: https://fontawesome.com/v4/get-started/")
                            logger.info("   2. Or download default assets: https://traineq.org/ImGuiBundle/assets.zip")
                            logger.info("   3. Or pip install fonttools and get from CDN")
                            logger.info("")
                            logger.info("🔧 CHECKED THESE LOCATIONS:")
                            for path in possible_fa_paths:
                                exists_str = "✓" if path.exists() else "✗"
                                logger.info(f"   {exists_str} {path}")
                            logger.info("")
                            logger.info("💡 Alternative: Use Unicode symbols instead of FontAwesome icons")
                            
                    except Exception as e2:
                        logger.warning(f"Manual FontAwesome loading failed: {e2}")
                        logger.info("FontAwesome icons will not be available")
                
                # Try to add system emoji font as fallback
                try:
                    import platform
                    system = platform.system()
                    
                    emoji_font_cfg = imgui.ImFontConfig()
                    emoji_font_cfg.merge_mode = True  # Merge with previous font
                    emoji_font_cfg.pixel_snap_h = True
                    
                    emoji_font_path = None
                    if system == "Windows":
                        # Try Windows emoji fonts
                        for font_name in ["seguiemj.ttf", "NotoColorEmoji.ttf"]:
                            font_path = Path(f"C:/Windows/Fonts/{font_name}")
                            if font_path.exists():
                                emoji_font_path = str(font_path)
                                break
                    elif system == "Darwin":  # macOS
                        emoji_font_path = "/System/Library/Fonts/Apple Color Emoji.ttc"
                    elif system == "Linux":
                        # Try common Linux emoji fonts
                        for font_path in ["/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
                                        "/usr/share/fonts/TTF/NotoColorEmoji.ttf"]:
                            if Path(font_path).exists():
                                emoji_font_path = font_path
                                break
                    
                    if emoji_font_path and Path(emoji_font_path).exists():
                        # Try to load emoji font without specific ranges first (simpler approach)
                        try:
                            io.fonts.add_font_from_file_ttf(emoji_font_path, base_size, emoji_font_cfg)
                            logger.info(f"✓ Loaded emoji font: {emoji_font_path}")
                        except Exception as e:
                            logger.warning(f"Could not load emoji font {emoji_font_path}: {e}")
                            # Fallback: try with default glyph ranges
                            try:
                                emoji_font_cfg_simple = imgui.ImFontConfig()
                                emoji_font_cfg_simple.merge_mode = True
                                io.fonts.add_font_from_file_ttf(emoji_font_path, base_size, emoji_font_cfg_simple)
                                logger.info(f"✓ Loaded emoji font (fallback): {emoji_font_path}")
                            except Exception as e2:
                                logger.warning(f"Emoji font fallback also failed: {e2}")
                    else:
                        logger.warning(f"No emoji font found for {system}")
                        
                except Exception as e:
                    logger.warning(f"Could not load emoji font: {e}")
                
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

    def setup_imgui_config():
        """Setup ImGui configuration before initialization"""
        io = imgui.get_io()
        # Disable docking completely
        io.config_flags &= ~imgui.ConfigFlags_.docking_enable
        io.config_flags &= ~imgui.ConfigFlags_.viewports_enable  # Also disable viewports

    def setup_imgui_style():
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

        style.set_color_(imgui.Col_.text ,               windows_dark_text_color)
        style.set_color_(imgui.Col_.title_bg ,           imgui.ImVec4(*[levels[1]]*3,1.00))
        style.set_color_(imgui.Col_.title_bg_active ,    imgui.ImVec4(*[levels[1]]*3,1.00))
        style.set_color_(imgui.Col_.title_bg_collapsed , imgui.ImVec4(*[levels[1]]*3,1.00))
        style.set_color_(imgui.Col_.window_bg,           imgui.ImVec4(*[levels[1]]*3,1.00))
        style.set_color_(imgui.Col_.scrollbar_bg,         imgui.ImVec4(*[levels[1]]*3,1.00))


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

    def _setup_file_drop_callback_for_glfw(callback):
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
    
    def post_init():
        _setup_file_drop_callback_for_glfw(app.on_file_drop)
    
    def _set_dark_mode_on_windows(enable: bool | None = None):
        """Set dark mode on Windows for the application window
        
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

    def _set_titlebar_color_on_macos():
        """Set custom titlebar color for the application window macOS"""
        import platform
        if platform.system() != "Darwin":
            logger.info("macOS window styling only available on macOS")
            return
            
        try:
            import glfw
            
            # Get the GLFW window handle
            window = glfw.get_current_context()
            if not window:
                logger.warning("Could not get GLFW window for macOS styling")
                return
            
            # Access the native NSWindow through pyobjc
            try:
                from AppKit import NSApp, NSColor, NSWindowStyleMaskFullSizeContentView
                import objc
                
                
                def get_ns_window():
                    """Try multiple methods to get the NSWindow"""
                    # Method 1: Get main window
                    ns_window = NSApp.mainWindow()
                    if ns_window:
                        logger.info("Got NSWindow from NSApp mainWindow")
                        return ns_window
                    
                    # Method 2: Try key window if main window is None
                    ns_window = NSApp.keyWindow()
                    if ns_window:
                        logger.info("Got NSWindow from NSApp keyWindow")
                        return ns_window

                    # Method 3: Get from windows array
                    windows = NSApp.windows()
                    if windows and len(windows) > 0:
                        ns_window = windows[0]
                        if ns_window:
                            logger.info("Got NSWindow from NSApp windows array")
                            return ns_window
                    
                    # Method 4: Use GLFW's Cocoa window directly
                    try:
                        cocoa_window = glfw.get_cocoa_window(window)
                        if cocoa_window:
                            ns_window = objc.objc_object(c_void_p=cocoa_window)
                            if ns_window:
                                logger.info("Got NSWindow from GLFW Cocoa window")
                                return ns_window
                    except Exception as e:
                        logger.warning(f"Failed to get NSWindow from GLFW Cocoa window: {e}")
                    
                    if not ns_window:
                        logger.warning("Could not get NSWindow - window may not be fully initialized yet")
                        logger.info("Titlebar styling skipped - window will use default appearance")
                        return
                    
                ns_window = get_ns_window()
                if not ns_window:
                    logger.warning("NSWindow is None - cannot apply macOS styling")
                    return
                
                # Remove titlebar border and set custom color
                ns_window.setTitlebarAppearsTransparent_(True) # setting titlebar transparent removes the little border between titlebar and content
                dark_gray = NSColor.colorWithRed_green_blue_alpha_(32/255, 32/255, 32/255, 1.0) # we can also set our own color.
                ns_window.setBackgroundColor_(dark_gray)

                default_titlebar_color = NSColor.controlBackgroundColor() 
                
                # Set titlebar appearance (dark or light) - this affects text color
                # NSAppearance options: 
                # - NSAppearanceNameAqua (light mode - dark text)
                # - NSAppearanceNameDarkAqua (dark mode - light text)
                from AppKit import NSAppearance
                dark_appearance = NSAppearance.appearanceNamed_("NSAppearanceNameDarkAqua")
                ns_window.setAppearance_(dark_appearance)  # This makes titlebar text white/light
                
                # Alternative: Set title text color directly
                # Note: This requires accessing the titlebar's text field, which is more complex
                # The appearance setting above is the recommended approach
                
            except ImportError:
                logger.warning("pyobjc not available. Install with: pip install pyobjc-framework-Cocoa")
                logger.info("Basic window styling still applied via GLFW")
            except Exception as e:
                logger.warning(f"Advanced macOS styling failed: {e}")
                import traceback
                traceback.print_exc()
                
        except ImportError as e:
            logger.warning(f"GLFW not available: {e}")
        except Exception as e:
            logger.warning(f"Failed to setup macOS window styling: {e}")
            import traceback
            traceback.print_exc()

    def post_init_add_platform_backend_callbacks():
        """Called after platform backend is initialized - best time for native window customization"""
        import platform
        if platform.system() == "Darwin":
            _set_titlebar_color_on_macos()
        elif platform.system() == "Windows":
            _set_dark_mode_on_windows(True)

    runner_params = hello_imgui.RunnerParams(
        callbacks=hello_imgui.RunnerCallbacks(
            show_gui = lambda: app.gui(),
            # show_menus=None,
            # show_app_menu_items=None,
            # show_status=None,
            post_init_add_platform_backend_callbacks = post_init_add_platform_backend_callbacks,
            post_init = post_init,
            load_additional_fonts = load_additional_fonts,
            # default_icon_font=hello_imgui.DefaultIconFont.font_awesome4,
            setup_imgui_config = setup_imgui_config,
            setup_imgui_style = setup_imgui_style,
            # register_tests=None,
            # register_tests_called=False,
            # before_exit=None,
            # before_exit_post_cleanup=None,
            # pre_new_frame=None,
            # before_imgui_render=None,
            # after_swap=None,
            # custom_background=None,
            # post_render_dockable_windows=None,
            any_backend_event_callback=None
        ),
        app_window_params=hello_imgui.AppWindowParams(
            window_title="Perspy",
            # window_geometry=hello_imgui.WindowGeometry(
            #     position=(100, 100),
            #     size=(1200, 512),
            # ),
            restore_previous_geometry=True
            # repaint_during_resize_gotcha_reentrant_repaint=True,
            # borderless=True,
            # borderless_movable=True,
            # borderless_resizable=True,
            # borderless_closable=True,
        ),
        imgui_window_params=hello_imgui.ImGuiWindowParams(
            menu_app_title="Perspy Demo",
            background_color=[32/255, 32/255, 32/255, 1.0], # windows sytem titlebar color
            default_imgui_window_type=hello_imgui.DefaultImGuiWindowType.no_default_window,
        ),
        dpi_aware_params=hello_imgui.DpiAwareParams(
            dpi_window_size_factor=1.0 # Enable DPI awareness: 1.0 is Auto-detect?
        ),
        docking_params=hello_imgui.DockingParams(
            layout_condition=hello_imgui.DockingLayoutCondition.never # Completely disable docking at the hello_imgui level
        ),
    )

    hello_imgui.run(runner_params)

