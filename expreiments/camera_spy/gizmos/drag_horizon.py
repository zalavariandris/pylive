from imgui_bundle import imgui
from typing import List, Tuple
from .drag_point import drag_point, window_to_screen


def drag_horizon(y:float, color)->Tuple[bool, float]:
    x = imgui.get_content_region_avail().x
    p0 = imgui.ImVec2(x/2.0, y)

    changed, new_point = drag_point("horizon###horizon", p0)
    draw_list = imgui.get_window_draw_list()
    draw_list.add_line(window_to_screen((imgui.ImVec2(0, new_point.y))), window_to_screen(imgui.ImVec2(x, new_point.y)), color, 1)
    return changed, new_point.y