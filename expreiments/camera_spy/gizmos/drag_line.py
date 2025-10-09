from imgui_bundle import imgui
from typing import List, Tuple
from .drag_point import drag_point, window_to_screen

def drag_line(label, line_segment:Tuple[imgui.ImVec2, imgui.ImVec2], color)->Tuple[bool, Tuple[imgui.ImVec2, imgui.ImVec2]]:
    start_point_changed, line_segment[0] = drag_point(f"{label}-start###{label}y-start", line_segment[0])
    end_point_changed, line_segment[1] = drag_point(f"{label}-end###{label}y-end", line_segment[1])
    


    p0 = line_segment[0]
    p1 = line_segment[1]
    imgui.get_window_draw_list().add_line(window_to_screen(p0), window_to_screen(p1), color, 1)

    changed = any([start_point_changed, end_point_changed])
    return changed, line_segment
