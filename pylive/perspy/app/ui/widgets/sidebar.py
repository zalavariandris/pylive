from imgui_bundle import imgui
from typing import Literal

sidebar_opacity = 0.8
def begin_sidebar(name:str, align:Literal['left', 'right']) -> bool:
    SIDEBAR_FLAGS = imgui.WindowFlags_.always_auto_resize | imgui.WindowFlags_.no_move | imgui.WindowFlags_.no_resize | imgui.WindowFlags_.no_collapse
    style = imgui.get_style()
    window_bg = style.color_(imgui.Col_.window_bg)
    title_bg = style.color_(imgui.Col_.title_bg)
    title_bg = style.color_(imgui.Col_.title_bg_active)
    border   = style.color_(imgui.Col_.border)
    imgui.push_style_color(imgui.Col_.window_bg, (*list(window_bg)[:3], sidebar_opacity))
    imgui.push_style_color(imgui.Col_.title_bg,  (*list(title_bg)[:3], sidebar_opacity))
    imgui.push_style_color(imgui.Col_.border,    (*list(border)[:3], sidebar_opacity))

    display_size = imgui.get_io().display_size
    match align:
        case 'left':
            imgui.set_next_window_pos(imgui.ImVec2(style.window_padding.x, display_size.y/2), imgui.Cond_.always, imgui.ImVec2(0.0, 0.5))
        case 'right':
            imgui.set_next_window_pos(imgui.ImVec2(display_size.x-style.window_padding.x, display_size.y/2), imgui.Cond_.always, imgui.ImVec2(1.0, 0.5))
    
    return imgui.begin(name, None, SIDEBAR_FLAGS)

def end_sidebar():
    imgui.end()
    imgui.pop_style_color(3)