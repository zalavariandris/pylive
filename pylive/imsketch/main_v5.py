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
from imgui_bundle import imgui

# Third-party imports
from PIL import Image
import OpenGL.GL as gl
import glfw
import glm
import sys

# Local application imports
from pylive.glrenderer.utils.camera import Camera
from pylive.perspy import solver

from imgui_bundle import icons_fontawesome_4 as fa


# Configure logging to see shader compilation logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from document.base_document import BaseDocument


def show_doc_menu(doc:BaseDocument):
    if imgui.menu_item_simple(f"{fa.ICON_FA_FILE} New", "Ctrl+N"):
        if doc.is_modified():
            """prompt if to save modifications"""
            doc.save()
        return True, BaseDocument()
    
    if imgui.menu_item_simple(f"{fa.ICON_FA_FOLDER_OPEN} Open", "Ctrl+O"):
        if doc.is_modified():
            """prompt if to save modifications"""
            doc.save()
        return True, BaseDocument()

    if imgui.menu_item_simple(f"{fa.ICON_FA_SAVE} Save", "Ctrl+S"):
        if doc is not None:
            doc.save()
            return True, doc
    
    if imgui.menu_item_simple(f"{fa.ICON_FA_SAVE} Save As...", "Ctrl+Shift+S"):
        if doc is not None:
            return True, doc.save_as()
        
    return False, doc

# ########### #
# Application #
# ########### #
class SketchAppBase():
    def __init__(self):
        super().__init__()

        # - manage windows
        self.show_about_popup: bool = False
        self.show_emoji_window: bool = False
        self.show_fontawesome_window: bool = False
        self.show_styleeditor_window: bool = False

        # - manage view
        self.view_grid: bool = True
        self.view_horizon: bool = True
        self.view_axes: bool = True

        # solver results
        self.camera:Camera|None = None
        
        # misc
        """
        Can be used to define inline variables, similarly how static vars used in C/C++ with imgui.
        
        Example:
        self.misc.setdefault('my_var', 0)
        _, self.misc['my_var'] = imgui.slider_float("my var", self.misc['my_var'], 0.0, 1.0)
        """
        self.misc:Dict[str, Any] = dict() # miscellaneous state variables for development.

    # Windows
    def setup_gui(self):
        self.update_os_window_title()
        import glfw
        glfw.window_hint(glfw.FLOATING, glfw.TRUE)

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

        # fullscreen viewer Window
        # style = imgui.get_style()
        display_size = imgui.get_io().display_size
        imgui.set_next_window_pos(imgui.ImVec2(0, menu_bar_height))
        imgui.set_next_window_size(imgui.ImVec2(display_size.x, display_size.y - menu_bar_height))       
        if imgui.begin("MainViewport", None, imgui.WindowFlags_.no_bring_to_front_on_focus | imgui.WindowFlags_.no_move | imgui.WindowFlags_.no_resize | imgui.WindowFlags_.no_collapse | imgui.WindowFlags_.no_title_bar):
            self.show_viewer()
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
                _, doc = show_doc_menu(None)
                # if imgui.menu_item_simple(f"{fa.ICON_FA_FILE} New", "Ctrl+N"):
                #     ...
                
                # if imgui.menu_item_simple(f"{fa.ICON_FA_FOLDER_OPEN} Open", "Ctrl+O"):
                #     ...

                # if imgui.menu_item_simple(f"{fa.ICON_FA_SAVE} Save", "Ctrl+S"):
                #     ...
                
                # if imgui.menu_item_simple(f"{fa.ICON_FA_SAVE} Save As...", "Ctrl+Shift+S"):
                #     ...            
                
                imgui.separator()

                if imgui.menu_item_simple(f"Quit", "Ctrl+Q"):
                    sys.exit(0)

                imgui.end_menu()

            if imgui.begin_menu("View"):
                if imgui.menu_item_simple(f"grid", None, self.view_grid):
                    self.view_grid = not self.view_grid

                if imgui.menu_item_simple(f"horizon", None, self.view_horizon):
                    self.view_horizon = not self.view_horizon

                if imgui.menu_item_simple(f"axes", None, self.view_axes):
                    self.view_axes = not self.view_axes

                imgui.end_menu()
            
            if imgui.begin_menu("Windows"):
                if imgui.menu_item_simple(f"{fa.ICON_FA_SMILE} Emoji Test", None, self.show_emoji_window):
                    self.show_emoji_window = not self.show_emoji_window

                if imgui.menu_item_simple(f"{fa.ICON_FA_STAR} FontAwesome Icons", None, self.show_fontawesome_window):
                    self.show_fontawesome_window = not self.show_fontawesome_window

                if imgui.menu_item_simple("Style Window", None, self.show_styleeditor_window):
                    self.show_styleeditor_window = not self.show_styleeditor_window

                imgui.end_menu()

            # alignt menu to right
            # right_cursor_pos = imgui.get_window_width() - style.window_padding.x*2 - imgui.calc_text_size("Help").x
            # if right_cursor_pos > imgui.get_cursor_pos_x():
            #     imgui.set_cursor_pos_x(right_cursor_pos)
            if imgui.begin_menu("Help"):
                if imgui.menu_item_simple(f"{fa.ICON_FA_BOOK} Manual"):
                    ...

                if imgui.menu_item_simple(f"{fa.ICON_FA_INFO} About"):
                    self.show_about_popup = True

                imgui.end_menu()

            imgui.end_main_menu_bar()

    def show_about(self):
        imgui.text("Camera Spy Demo")
        imgui.separator()
        imgui.text("Drop an image file (jpg, png, etc) into the window to load it as background.")
        imgui.text("Define vanishing lines by dragging the control points.")
        imgui.text("Adjust parameters in the sidebar to compute the camera.")
        imgui.separator()
        imgui.text("Developed with ❤ by András Zalavári")
        imgui.text_link_open_url("https://github.com/yourusername/camera-spy")
   
    def show_viewer(self):
        ...
        # if ui.viewer.begin_viewer("viewer1", content_size=self.doc.content_size, size=imgui.ImVec2(-1,-1)):
        #     # background image
        #     if self.image_texture_ref is not None:
        #         tl = ui.viewer._get_window_coords(imgui.ImVec2(0,0))
        #         br = ui.viewer._get_window_coords(imgui.ImVec2(self.doc.content_size.x, self.doc.content_size.y))

                
        #         image_size = br - tl
        #         # imgui.set_cursor_pos(tl)
        #         draw_list = imgui.get_window_draw_list()

        #         tint = (1.0, 1.0, 1.0, 1.0)
        #         if self.dim_background:
        #             tint = (0.33, 0.33, 0.33, 1.0)

        #         draw_list.add_image(
        #             self.image_texture_ref, 
        #             tl+imgui.get_window_pos(), 
        #             br+imgui.get_window_pos(), 
        #             imgui.ImVec2(0,1), 
        #             imgui.ImVec2(1,0), 
        #             imgui.color_convert_float4_to_u32(tint)
        #         )

        #     # control points
        #     _, self.doc.origin = ui.viewer.control_point("o", self.doc.origin)
        #     control_line = ui.comp(ui.viewer.control_point)
        #     control_lines = ui.comp(control_line)
        #     _, self.doc.first_vanishing_lines = control_lines("z", self.doc.first_vanishing_lines, color=get_axis_color(self.doc.first_axis) )
        #     for line in self.doc.first_vanishing_lines:
        #         ui.viewer.guide(line[0], line[1], get_axis_color(self.doc.first_axis), '>')

        #     ui.viewer.axes(length=10)

        #     match self.doc.solver_mode:
        #         case SolverMode.OneVP:
        #             _, self.doc.second_vanishing_lines[0] = control_line("x", self.doc.second_vanishing_lines[0], color=get_axis_color(self.doc.second_axis))  
        #             ui.viewer.guide(self.doc.second_vanishing_lines[0][0], self.doc.second_vanishing_lines[0][1], get_axis_color(self.doc.second_axis), '>')
                
        #         case SolverMode.TwoVP:
        #             _, self.doc.principal = ui.viewer.control_point("p", self.doc.principal)
        #             if self.doc.quad_mode:
        #                 z0, z1 = self.doc.first_vanishing_lines
        #                 self.doc.second_vanishing_lines = [
        #                     (z0[0], z1[0]),
        #                     (z0[1], z1[1])
        #                 ]
        #             else:
        #                 _, self.doc.second_vanishing_lines = control_lines("x", self.doc.second_vanishing_lines, color=get_axis_color(self.doc.second_axis) )
                    
        #             for line in self.doc.second_vanishing_lines:
        #                 ui.viewer.guide(line[0], line[1], get_axis_color(self.doc.second_axis), '>')

        #         case SolverMode.ThreeVP:
        #             _, self.doc.principal = ui.viewer.control_point("p", self.doc.principal)
        #             if self.doc.quad_mode:
        #                 z0, z1 = self.doc.first_vanishing_lines
        #                 self.doc.second_vanishing_lines = [
        #                     (z0[0], z1[0]),
        #                     (z0[1], z1[1])
        #                 ]
        #             else:
        #                 _, self.doc.second_vanishing_lines = control_lines("x", self.doc.second_vanishing_lines, color=get_axis_color(self.doc.second_axis) )
                    
        #             for line in self.doc.second_vanishing_lines:
        #                 ui.viewer.guide(line[0], line[1], get_axis_color(self.doc.second_axis), '>')

        #             _, self.doc.third_vanishing_lines = control_lines("y", self.doc.third_vanishing_lines, color=get_axis_color(self.doc.third_axis) )
        #             for line in self.doc.third_vanishing_lines:
        #                 ui.viewer.guide(line[0], line[1], get_axis_color(self.doc.third_axis), '>')

        #     # draw vanishing lines to vanishing points
        #     if self.first_vanishing_point is not None:
        #         for line in self.doc.first_vanishing_lines:
        #             P = sorted([line[0], line[1]], key=lambda P: glm.distance2(P, self.first_vanishing_point))[0]
        #             first_axis_color = get_axis_color(self.doc.first_axis)
        #             ui.viewer.guide(P, self.first_vanishing_point, imgui.ImVec4(first_axis_color[0], first_axis_color[1], first_axis_color[2], 0.4))

        #     if self.second_vanishing_point is not None:
        #         for line in self.doc.second_vanishing_lines:
        #             P = sorted([line[0], line[1]], key=lambda P: glm.distance2(P, self.second_vanishing_point))[0]
        #             second_axis_color = get_axis_color(self.doc.second_axis)
        #             ui.viewer.guide(P, self.second_vanishing_point, imgui.ImVec4(second_axis_color[0], second_axis_color[1], second_axis_color[2], 0.4))

        #     if self.camera is not None:
        #         if ui.viewer.begin_scene(glm.scale(self.camera.projectionMatrix(), glm.vec3(1.0, -1.0, 1.0)), self.camera.viewMatrix()):
        #             axes_name = {
        #                 solver.Axis.PositiveX: "X",
        #                 solver.Axis.NegativeX: "X",
        #                 solver.Axis.PositiveY: "Y",
        #                 solver.Axis.NegativeY: "Y",
        #                 solver.Axis.PositiveZ: "Z",
        #                 solver.Axis.NegativeZ: "Z"
        #             }
        #             ground_axes = set([axes_name[self.doc.first_axis], axes_name[self.doc.second_axis]])
        #             if self.view_grid:
        #                 # draw the grid
        #                 if ground_axes == {'X', 'Y'}:
        #                     for A, B in ui.viewer.make_gridXY_lines(step=1, size=10):
        #                         ui.viewer.guide(A, B)
        #                 elif ground_axes == {'X', 'Z'}:
        #                     for A, B in ui.viewer.make_gridXZ_lines(step=1, size=10):
        #                         ui.viewer.guide(A, B)
        #                 elif ground_axes == {'Y', 'Z'}:
        #                     for A, B in ui.viewer.make_gridYZ_lines(step=1, size=10):
        #                         ui.viewer.guide(A, B)
        #                 else:
        #                     logger.warning(f"Cannot draw grid for the selected axes. {solver.Axis(self.doc.first_axis).name}, {solver.Axis(self.doc.second_axis).name}")
                    
        #             if self.view_axes:
        #                 ui.viewer.axes(length=1.0)

        #             if self.view_horizon:
        #                 # draw the horizon line
        #                 if ground_axes == {'X', 'Y'}:
        #                     ui.viewer.horizon_line(ground='xy')
        #                 elif ground_axes == {'X', 'Z'}:
        #                     ui.viewer.horizon_line(ground='xz')
        #                 elif ground_axes == {'Y', 'Z'}:
        #                     ui.viewer.horizon_line(ground='yz')
        #                 else:
        #                     logger.warning(f"Cannot draw horizon line for the selected axes. {solver.Axis(self.doc.first_axis).name}, {solver.Axis(self.doc.second_axis).name}")
                    

        #         ui.viewer.end_scene()
        # ui.viewer.end_viewer()

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
            self.open_image(first_path)

    # update 
    def update_os_window_title(self):
        print("Updating OS window title...")
        # Change the window title at runtime
        try:
            import glfw
            glfw_window = glfw.get_current_context()
            title = f"{self.__class__.__name__}"
            # if self.doc._file_path:
            #     title += " - "
            #     if self.doc.isModified():
            #         title += " *"
            #     title += f"{Path(self.doc._file_path).stem}"
            #     title += f" [{self.doc._file_path}]"
            glfw.set_window_title(glfw_window, f"𝕊 {title}")
        except Exception as e:
            logger.warning(f"Could not set window title: {e}")


if __name__ == "__main__":
    from imgui_bundle import immapp
    from imgui_bundle import hello_imgui
    from hello_imgui_config import create_my_runner_params
    app = SketchAppBase()
    assets_folder = Path(__file__).parent / "assets"
    assert assets_folder.exists(), f"Assets folder not found: {assets_folder.absolute()}"
    print("setting assets folder:", assets_folder.absolute())
    hello_imgui.set_assets_folder(str(assets_folder.absolute()))
    runner_params = create_my_runner_params(app.draw_gui, app.setup_gui, app.on_file_drop, "𝕊Perspy v0.5.0")
    hello_imgui.run(runner_params)

