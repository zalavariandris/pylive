# Standard library imports
import math
from pathlib import Path
from pprint import pformat
from typing import Any, List, Tuple, Dict, cast, TypeVar
import json

# Third-party imports
from PIL import Image
import OpenGL.GL as gl
import glfw
from loguru import logger
import glm
import numpy as np
from imgui_bundle import imgui, icons_fontawesome_4
from imgui_bundle import icons_fontawesome_4 as fa
from imgui_bundle import portable_file_dialogs as pfd
import pyperclip

# Local application imports
from pylive.glrenderer.utils.camera import Camera
from pylive.perspy.core import solver_functional as solver
from pylive.perspy.core import utils
from pylive.perspy.core.types import *
import ui
from document import PerspyDocument

from pylive.perspy.app.hot_reloader import HotModuleReloader
HotModuleReloader([solver]).start_file_watchers()


class PerspyApp():
    def __init__(self):
        super().__init__()

        self.doc = PerspyDocument()

        # stored texture
        self.image_texture_ref:imgui.ImTextureRef|None = None
        self.image_texture_id: int|None = None

        # - manage windows
        self.show_about_popup: bool = False
        self.show_emoji_window: bool = False
        self.show_fontawesome_window: bool = False
        self.show_data_window: bool = False
        self.show_styleeditor_window: bool = False

        # - manage view
        self.dim_background: bool = True
        self.view_grid: bool = True
        self.view_horizon: bool = True
        self.view_axes: bool = True

        # solver results
        # self.camera:Camera|None = None
        self.view_matrix:glm.mat4|None = None
        self.projection_matrix:glm.mat4|None = None

        self.current_euler_order = solver.EulerOrder.ZXY
        self.solver_results:Dict|None = None
        
        # misc
        """
        Can be used to define inline variables, similarly how static vars used in C/C++ with imgui.
        
        Example:
        self.misc.setdefault('my_var', 0)
        _, self.misc['my_var'] = imgui.slider_float("my var", self.misc['my_var'], 0.0, 1.0)
        """
        self.misc:Dict[str, Any] = dict() # miscellaneous state variables for development. 

    @staticmethod
    def get_axis_color(axis:solver.Axis) -> imgui.ImVec4:
        match axis:
            case solver.Axis.PositiveX | solver.Axis.NegativeX:
                return ui.viewer.get_viewer_style().AXIS_COLOR_X
            case solver.Axis.PositiveY | solver.Axis.NegativeY:
                return ui.viewer.get_viewer_style().AXIS_COLOR_Y
            case solver.Axis.PositiveZ | solver.Axis.NegativeZ:
                return ui.viewer.get_viewer_style().AXIS_COLOR_Z
            case _:
                return imgui.ImVec4(1.0, 1.0, 1.0, 1.0)

    # Windows
    def setup_gui(self):
        if self.doc.image_path:
            # Create OpenGL texture
            self.update_texture()

    def draw_gui(self):
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

        # Parameters Window
        if ui.begin_sidebar("Parameters", align="left"):
            buttons_width = 150
            imgui.separator_text("Image")
            imgui.set_next_item_width(buttons_width)
            if self.image_texture_ref is None:
                if imgui.button("open image", size=imgui.ImVec2(-1,0)):
                    self.open_image()

            else:
                image_aspect = self.doc.content_size.x / self.doc.content_size.y
                width = imgui.get_content_region_avail().x-imgui.get_style().frame_padding.x*2
                if imgui.image_button("open", self.image_texture_ref, imgui.ImVec2(width, width/image_aspect)):
                    self.open_image()

            imgui.set_next_item_width(buttons_width)
            _, value = imgui.input_int2("image size", [int(self.doc.content_size.x), int(self.doc.content_size.y)])
            if _:
                self.doc.content_size = imgui.ImVec2(value[0], value[1])

            _, self.dim_background = imgui.checkbox("dim background", self.dim_background)

            # imgui.bullet_text("Warning: Font scaling will NOT be smooth, because\nImGuiBackendFlags_RendererHasTextures is not set!")
            imgui.separator_text("Solver Parameters")
            imgui.set_next_item_width(buttons_width)
            _, self.doc.solver_mode = ui.combo_enum("mode", self.doc.solver_mode, solver.SolverMode)
            # _, self.doc.solver_mode = imgui.combo("mode", self.doc.solver_mode, solver.SolverMode._member_names_)

            imgui.set_next_item_width(buttons_width)
            _, self.doc.reference_world_size = imgui.slider_float("scene scale", self.doc.reference_world_size, 1.0, 100.0, "%.2f")

            imgui.set_next_item_width(buttons_width)
            
            _, self.doc.reference_axis = ui.combo_enum("reference distance mode", self.doc.reference_axis, solver.ReferenceAxis)

            imgui.set_next_item_width(buttons_width)
            _, self.doc.reference_distance_offset = imgui.slider_float("reference distance offset", self.doc.reference_distance_offset, 0.0, 2000.0, "%.2f")
            
            imgui.set_next_item_width(buttons_width)
            _, self.doc.reference_distance_length = imgui.slider_float("reference distance length", self.doc.reference_distance_length, 1.0, 2000.0, "%.2f")

            # solver specific parameters
            match self.doc.solver_mode:
                case solver.SolverMode.OneVP:
                    _, self.doc.enable_auto_principal_point = imgui.checkbox("auto principal point", self.doc.enable_auto_principal_point)
                    imgui.set_next_item_width(buttons_width)
                    _, self.doc.fov_degrees = imgui.slider_float("fov°", self.doc.fov_degrees, 1.0, 179.0, "%.1f°")

                case solver.SolverMode.TwoVP:
                    _, self.doc.enable_auto_principal_point = imgui.checkbox("auto principal point", self.doc.enable_auto_principal_point)
                    _, self.doc.quad_mode = imgui.checkbox("quad", self.doc.quad_mode)

                case solver.SolverMode.ThreeVP:
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
        ui.end_sidebar()

        # fullscreen viewer Window
        # style = imgui.get_style()
        display_size = imgui.get_io().display_size
        imgui.set_next_window_pos(imgui.ImVec2(0, menu_bar_height))
        imgui.set_next_window_size(imgui.ImVec2(display_size.x, display_size.y - menu_bar_height))       
        if imgui.begin("MainViewport", None, imgui.WindowFlags_.no_bring_to_front_on_focus | imgui.WindowFlags_.no_move | imgui.WindowFlags_.no_resize | imgui.WindowFlags_.no_collapse | imgui.WindowFlags_.no_title_bar):
            self.misc.setdefault('viewer1_coord_sys', 1) # 0: top-left, 1: bottom-left
            coord_options = ["top-left", "bottom-left"]
            _, self.misc['viewer1_coord_sys'] = imgui.combo("coord-sys", self.misc['viewer1_coord_sys'], coord_options) # hack to prevent focusing this window when clicking on it

            if ui.viewer.begin_viewer("viewer1", content_size=self.doc.content_size, size=imgui.ImVec2(-1,-1), coordinate_system=coord_options[self.misc['viewer1_coord_sys']]):
                # background image
                if self.image_texture_ref is not None:
                    tl = ui.viewer._get_window_coords(imgui.ImVec2(0,0))
                    br = ui.viewer._get_window_coords(imgui.ImVec2(self.doc.content_size.x, self.doc.content_size.y))

                    
                    image_size = br - tl
                    # imgui.set_cursor_pos(tl)
                    draw_list = imgui.get_window_draw_list()

                    tint = (1.0, 1.0, 1.0, 1.0)
                    if self.dim_background:
                        tint = (0.33, 0.33, 0.33, 1.0)

                    draw_list.add_image(
                        self.image_texture_ref, 
                        tl+imgui.get_window_pos(), 
                        br+imgui.get_window_pos(), 
                        imgui.ImVec2(0,1), 
                        imgui.ImVec2(1,0), 
                        imgui.color_convert_float4_to_u32(tint)
                    )

                # Solve the camera
                try:
                    if self.doc.solver_mode in [solver.SolverMode.OneVP, solver.SolverMode.TwoVP] and self.doc.enable_auto_principal_point:
                        self.doc.principal = self.doc.content_size * 0.5 # TODO: set principal to center of image, consider using the solver viewport directly or stick to doc content size? the vieqwport is created from content size anyway

                    self.solver_results = solver.solve(
                        mode = self.doc.solver_mode,
                        viewport=Rect(0,0,self.doc.content_size.x, self.doc.content_size.y),
                        first_vanishing_lines =  self.doc.first_vanishing_lines,
                        second_vanishing_lines = self.doc.second_vanishing_lines,
                        third_vanishing_lines =  self.doc.third_vanishing_lines,
                        
                        f=utils.focal_length_from_fov(self.doc.fov_degrees, self.doc.content_size.y), # focal length (in height units)
                        P=glm.vec2(*self.doc.principal),
                        O=glm.vec2(*self.doc.origin),

                        # 5. adjust scene scale
                        reference_world_size=self.doc.reference_world_size,
                        reference_axis=self.doc.reference_axis,
                        reference_distance_segment=(self.doc.reference_distance_offset, self.doc.reference_distance_length), # 2D distance from origin to camera  
                        
                        # 6. adjust axes
                        first_axis=self.doc.first_axis,
                        second_axis=self.doc.second_axis,
                    )

                    # apply solver results to camera
                    # P, f, shift = solver.decompose_intrinsics(
                    #     self.solver_results['viewport'],
                    #     self.solver_results['projection']
                    # )

                    self.view_matrix = self.solver_results['view']
                    self.projection_matrix = self.solver_results['projection']

                    # update document parameters TODO: consider removing this and instead drawing the solver results only
                    # self.doc.principal = imgui.ImVec2(P.x, P.y)

                    error_msg = None
                except Exception as e:
                    # self.camera = None
                    self.view_matrix = None
                    self.projection_matrix = None
                    error_msg = e
                    import traceback
                    traceback.print_exc()

                # control points
                _, self.doc.origin = ui.viewer.control_point("o", self.doc.origin)
                _, self.doc.principal = ui.viewer.control_point("Principal", self.doc.principal)

                control_line = ui.comp(ui.viewer.control_point)
                control_lines = ui.comp(control_line)
                _, self.doc.first_vanishing_lines = control_lines("z", self.doc.first_vanishing_lines, color=self.get_axis_color(self.doc.first_axis) )
                for line in self.doc.first_vanishing_lines:
                    ui.viewer.guide(line[0], line[1], self.get_axis_color(self.doc.first_axis), head='>')

                ui.viewer.axes(length=10)

                match self.doc.solver_mode:
                    case solver.SolverMode.OneVP:
                        _, self.doc.second_vanishing_lines[0] = control_line("x", self.doc.second_vanishing_lines[0], color=self.get_axis_color(self.doc.second_axis))  
                        ui.viewer.guide(self.doc.second_vanishing_lines[0][0], self.doc.second_vanishing_lines[0][1], self.get_axis_color(self.doc.second_axis), head='>')
                    
                    case solver.SolverMode.TwoVP:
                        if self.doc.quad_mode:
                            z0, z1 = self.doc.first_vanishing_lines
                            self.doc.second_vanishing_lines = [
                                (z0[0], z1[0]),
                                (z0[1], z1[1])
                            ]
                        else:
                            _, self.doc.second_vanishing_lines = control_lines("x", self.doc.second_vanishing_lines, color=self.get_axis_color(self.doc.second_axis) )
                        
                        for line in self.doc.second_vanishing_lines:
                            ui.viewer.guide(line[0], line[1], self.get_axis_color(self.doc.second_axis), head='>')

                    case solver.SolverMode.ThreeVP:
                        if self.doc.quad_mode:
                            z0, z1 = self.doc.first_vanishing_lines
                            self.doc.second_vanishing_lines = [
                                (z0[0], z1[0]),
                                (z0[1], z1[1])
                            ]
                        else:
                            _, self.doc.second_vanishing_lines = control_lines("x", self.doc.second_vanishing_lines, color=self.get_axis_color(self.doc.second_axis) )
                        
                        for line in self.doc.second_vanishing_lines:
                            ui.viewer.guide(line[0], line[1], self.get_axis_color(self.doc.second_axis), head='>')

                        _, self.doc.third_vanishing_lines = control_lines("y", self.doc.third_vanishing_lines, color=self.get_axis_color(self.doc.third_axis) )
                        for line in self.doc.third_vanishing_lines:
                            ui.viewer.guide(line[0], line[1], self.get_axis_color(self.doc.third_axis), head='>')

                # adjust scale
                if self.solver_results is not None:
                    match self.doc.reference_axis:
                        case solver.ReferenceAxis.X_Axis:
                            reference_axis_vector = glm.vec3(1,0,0)
                        case solver.ReferenceAxis.Y_Axis:
                            reference_axis_vector = glm.vec3(0,1,0)
                        case solver.ReferenceAxis.Z_Axis:
                            reference_axis_vector = glm.vec3(0,0,1)
                        case solver.ReferenceAxis.Screen:
                            reference_axis_vector = glm.normalize(glm.vec3(glm.inverse(self.solver_results['view'])[0]))

                    reference_screen_dir = glm.normalize(
                            glm.vec2(
                                glm.project(reference_axis_vector, self.solver_results['view'], self.solver_results['projection'], glm.vec4(*self.solver_results['viewport']))
                            )
                         - glm.vec2(*self.doc.origin))
                    ORANGE = imgui.ImVec4(1.0, 0.5, 0.0, 1.0)

                    reference_segment_startpoint = self.doc.origin + imgui.ImVec2(*reference_screen_dir) * self.doc.reference_distance_offset
                    start_changed, reference_segment_startpoint = ui.viewer.control_point("E", reference_segment_startpoint, color=ORANGE)

                    reference_segment_endpoint = self.doc.origin + imgui.ImVec2(*reference_screen_dir) * (self.doc.reference_distance_offset+self.doc.reference_distance_length)
                    end_changed, reference_segment_endpoint = ui.viewer.control_point("S", reference_segment_endpoint, color=ORANGE)
                    
                    ui.viewer.guide(reference_segment_startpoint, reference_segment_endpoint, color=ORANGE, head='|', tail='|')
                    if start_changed or end_changed:
                        self.doc.reference_distance_offset = glm.distance(glm.vec2(*self.doc.origin), glm.vec2(*reference_segment_startpoint))
                        self.doc.reference_distance_length = glm.distance(glm.vec2(*reference_segment_startpoint), glm.vec2(*reference_segment_endpoint))

                # draw vanishing lines to vanishing points
                # if results:=self.solver_results:
                #     if results.first_vanishing_point:
                #         for line in self.doc.first_vanishing_lines:
                #             P = sorted([line[0], line[1]], key=lambda P: glm.distance2(P, results.first_vanishing_point))[0]
                #             first_axis_color = self.get_axis_color(self.doc.first_axis)
                #             ui.viewer.guide(P, imgui.ImVec2(*results.first_vanishing_point), ui.viewer.fade_color(first_axis_color))

                #     if results.second_vanishing_point:
                #         for line in self.doc.second_vanishing_lines:
                #             P = sorted([line[0], line[1]], key=lambda P: glm.distance2(P, results.second_vanishing_point))[0]
                #             second_axis_color = self.get_axis_color(self.doc.second_axis)
                #             ui.viewer.guide(P, imgui.ImVec2(*results.second_vanishing_point), ui.viewer.fade_color(second_axis_color))

                if self.view_matrix and self.projection_matrix:
                    # proj = glm.scale(self.projection_matrix, glm.vec3(1.0, -1.0, 1.0))
                    # view = glm.scale(self.view_matrix, glm.vec3(1.0, -1.0, 1.0))
                    if ui.viewer.begin_scene(self.projection_matrix, self.view_matrix):
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


        imgui.end()

        # Results Window
        if ui.begin_sidebar("Results", align="right"):
            if error_msg is not None:
                imgui.push_style_color(imgui.Col_.text, (1.0, 0.2, 0.2, 1.0))
                imgui.text_wrapped(f"{error_msg}")
                imgui.pop_style_color()
            else:
                if results:=self.solver_results:
                    imgui.separator_text("Camera Parameters")
                    imgui.input_float4("Viewport", [*self.solver_results['viewport']], format="%.0f", flags=imgui.InputTextFlags_.read_only)
                    

                    imgui.separator_text("Vanishing Points")
                    imgui.input_float2("1st VP", [*self.solver_results['first_vanishing_point']]  if self.solver_results.get('first_vanishing_point')  is not None else [0.0, 0.0], flags=imgui.InputTextFlags_.read_only)
                    imgui.input_float2("2nd VP", [*self.solver_results['second_vanishing_point']] if self.solver_results.get('second_vanishing_point') is not None else [0.0, 0.0], flags=imgui.InputTextFlags_.read_only)
                    imgui.input_float2("3rd VP", [*self.solver_results['third_vanishing_point']]  if self.solver_results.get('third_vanishing_point')  is not None else [0.0, 0.0], flags=imgui.InputTextFlags_.read_only)
                    
                    
                    # euler = glm.eulerAngles(quat)
                    # ui.next_attribute("Euler") #todo: set order
                    # imgui.set_next_item_width(260)
                    # imgui.input_text("##euler", f"{math.degrees(euler.x):.2f}, {math.degrees(euler.y):.2f}, {math.degrees(euler.z):.2f}" if self.solver_results.transform is not None else "N/A", flags=imgui.InputTextFlags_.read_only)


                    imgui.separator_text("Projection")
                    # P, f, shift = solver.decompose_intrinsics(self.solver_results['viewport'], self.solver_results['projection'])
                    # imgui.input_float2("Principal (decompose)", [*P], flags=imgui.InputTextFlags_.read_only)
                    # imgui.input_float2("Shift (decompose)", [*shift], flags=imgui.InputTextFlags_.read_only)
                    # imgui.input_float("Focal Length (decompose)", f, flags=imgui.InputTextFlags_.read_only)

                    # imgui.input_text("fovy", f"{math.degrees(self.solver_results.fovy):.2f}°")
                    # imgui.input_text("fovx", f"{math.degrees(self.solver_results.get_fovx()):.2f}°")
                    # imgui.input_text("shiftx", f"{self.solver_results.shift_x:.2f}")
                    # imgui.input_text("shifty", f"{self.solver_results.shift_y:.2f}")

                    imgui.separator_text("Transform")
                    # position, quat = solver.decompose_extrinsics(glm.inverse(self.solver_results['view']))
                    # imgui.input_float3("Position (decompose)", [*position] if self.solver_results['view'] is not None else [0.0, 0.0, 0.0], flags=imgui.InputTextFlags_.read_only)
                    # imgui.input_float4("Quaternion", [*quat] if self.solver_results['view'] is not None else [0.0, 0.0, 0.0, 0.0], flags=imgui.InputTextFlags_.read_only)

                    combo_width = max([imgui.calc_text_size(text).x for text in solver.EulerOrder._member_names_]) + style.frame_padding.x * 2.0 -10
                    combo_width+=imgui.get_frame_height() # add room for the dropdown arrow. (TODO: is it square for sure?)
                    imgui.set_next_item_width(imgui.calc_item_width()-combo_width - style.frame_padding.x*2)
                    view_matrix = self.solver_results['view']
                    match self.current_euler_order:
                        case solver.EulerOrder.XYZ:
                            euler = utils.extract_euler_XYZ(view_matrix)
                        case solver.EulerOrder.XZY:
                            euler = utils.extract_euler_XZY(view_matrix)
                        case solver.EulerOrder.YXZ:
                            euler = utils.extract_euler_YXZ(view_matrix)
                        case solver.EulerOrder.YZX:
                            euler = utils.extract_euler_YZX(view_matrix)
                        case solver.EulerOrder.ZXY:
                            euler = utils.extract_euler_ZXY(view_matrix)
                        case solver.EulerOrder.ZYX:
                            euler = utils.extract_euler_ZYX(view_matrix)
                            
                    imgui.input_float3("##euler_values", [math.degrees(radians) for radians in euler], flags=imgui.InputTextFlags_.read_only)
                    imgui.set_item_tooltip("Euler angles in degrees (x,y,z).\nNote: Rotation is applied in order order: ZXY (Yaw, Pitch, Roll)")

                    imgui.same_line()

                    imgui.set_next_item_width(combo_width)
                    _, self.current_euler_order = imgui.combo("euler##euler_order", self.current_euler_order, solver.EulerOrder._member_names_)
                    imgui.set_item_tooltip("Select the Euler angle rotation order used for decomposition.")
                else:
                    imgui.text("No results.")

        ui.end_sidebar()

        if self.show_data_window:
            expanded, self.show_data_window = imgui.begin("data window", self.show_data_window)
            if expanded:
                self.show_io()
            imgui.end()

        # Style Editor Window
        if self.show_styleeditor_window:
            expanded, self.show_styleeditor_window = imgui.begin("style editor", self.show_styleeditor_window)
            if expanded:
                imgui.show_style_editor()
            imgui.end()

    def show_main_menu_bar(self):
        style = imgui.get_style()
        if imgui.begin_main_menu_bar():
            if imgui.begin_menu("File"):
                if imgui.menu_item_simple(f"{fa.ICON_FA_FILE} New", "Ctrl+N"):
                    ...
                
                if imgui.menu_item_simple(f"{fa.ICON_FA_FOLDER_OPEN} Open", "Ctrl+O"):
                    self.doc.open()
                    if self.doc.image_path:
                        # Create OpenGL texture
                        self.update_texture()

                if imgui.begin_menu("Open Template"):
                    templates = {
                        "One VP (Famous)": solver.SolverMode.OneVP,
                        "Two VP (Building Corner)": solver.SolverMode.TwoVP,
                        "Three VP (Cubic Room)": solver.SolverMode.ThreeVP
                    }
                    for template_name, mode in templates.items():
                        if imgui.menu_item_simple(template_name):
                            ...
                            if self.doc.image_path:
                                # Create OpenGL texture
                                self.update_texture()
                    imgui.end_menu()

                if imgui.menu_item_simple(f"{fa.ICON_FA_SAVE} Save", "Ctrl+S"):
                    self.doc.save()
                
                if imgui.menu_item_simple(f"{fa.ICON_FA_SAVE} Save As...", "Ctrl+Shift+S"):
                    self.doc.save_as()

                imgui.separator()

                if imgui.menu_item_simple(f"{fa.ICON_FA_FOLDER_OPEN} Load Image", "Ctrl+O"):
                    self.open_image()

                

                imgui.separator()

                if imgui.begin_menu("Export results"):
                    if imgui.menu_item_simple("JSON"):
                        self.export(
                            default_name="perspy_camera_factory.py",
                            content=json.dumps(self.solver_results.as_dict(), indent=4),
                            file_type="JSON",
                            extension=".json"
                        )

                    if imgui.menu_item_simple("blender script"):
                        self.export(
                            default_name="perspy_camera_factory.py",
                            content=self.solver_results.as_blender_script(),
                            file_type="Blender Python Script",
                            extension=".py"
                        )

                    imgui.end_menu()
                
                if imgui.begin_menu("Copy results to clipboard"):
                    if imgui.menu_item_simple("JSON"):
                        pyperclip.copy(json.dumps(self.solver_results.as_dict(), indent=4))

                    if imgui.menu_item_simple("blender script"):
                        pyperclip.copy(self.solver_results.as_blender_script())

                    imgui.end_menu()

                if imgui.begin_menu("Copy document to clipboard"):
                    if imgui.menu_item_simple("Python code"):
                        pyperclip.copy(self.doc.as_python_script())

                    imgui.end_menu()
                
                
                imgui.separator()
                if imgui.menu_item_simple(f"Quit", "Ctrl+Q"):
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

    def show_io(self):
        from textwrap import dedent
        if imgui.collapsing_header("Document as Python Code", imgui.TreeNodeFlags_.default_open):
            text = self.doc.as_python_script()
            imgui.text_unformatted(dedent(text).strip())

        if imgui.collapsing_header("Document as Dict", imgui.TreeNodeFlags_.default_open):
            imgui.text_unformatted("TODO. implement doc.to_dict()")

        if imgui.collapsing_header("Results Dictionary", imgui.TreeNodeFlags_.default_open):
            data = self.solver_results.as_dict()
            text = pformat(data, indent=2, width=80, compact=False)
            imgui.text_unformatted(text)

        if imgui.collapsing_header("Blender Script", imgui.TreeNodeFlags_.default_open):
            data = self.results_to_blender_script()
            text = pformat(data, indent=2, width=80, compact=False)
            imgui.text_unformatted(text)

    # Events
    def on_file_drop(self, window, paths):
        from pathlib import Path
        """GLFW drop callback - receives list of paths"""
        logger.info(f"Files dropped: {paths}")
        if len(paths) > 0:
            first_path = paths[0]
            self.open_image(first_path)

    # Actions 
    def open_image(self, path:str|None=None):
        from pathlib import Path
        try:
            if path is None:
                filters = [
                    "Image Files", "*.png *.jpg *.jpeg *.bmp *.tiff *.tif *.gif", 
                    "All Files", "*.*"
                ]
                open_file_dialog = pfd.open_file("Select Image", "", filters, pfd.opt.none)
                paths = open_file_dialog.result()
                
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

            self.update_texture()
            
        except Exception as e:
            logger.error(f"Failed to load {path}: {e}")
            import traceback
            traceback.print_exc()

    def export(self, default_path: str, content: str, file_type: str, extension: str):
        """Helper to save text content to a file via dialog."""
        # open the file dialog
        file_dialog = pfd.save_file(
            title=f"Save {file_type}",
            default_path=default_path,
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

    def update_texture(self):
        # Load image with PIL
        path = self.doc.image_path
        try:
            from imgui_bundle import hello_imgui
             # to ensure asset exists
            img = Image.open(hello_imgui.asset_file_full_path(path) )
        except FileNotFoundError:
            logger.error(f"🚨|⚠️|💡|🔥 File not found: {path}")
            return
        logger.info(f"Update texture")
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
