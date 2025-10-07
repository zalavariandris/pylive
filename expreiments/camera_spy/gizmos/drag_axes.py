from imgui_bundle import imgui
from typing import List, Tuple
from .drag_point import drag_point, window_to_screen

def drag_axes(axes:List[Tuple[imgui.ImVec2, imgui.ImVec2]], color)->Tuple[bool, List[Tuple[imgui.ImVec2, imgui.ImVec2]]]:
    changed = False
    for i, axis in enumerate(axes):
        start_point_changed, axis[0] = drag_point(f"y-start-{i} {axis[0]}###y-start-{i}", axis[0])
        end_point_changed, axis[1] = drag_point(f"y-end-{i} {axis[1]}###y-end-{i}", axis[1])
        if any([start_point_changed, end_point_changed]):
            changed = True

        p0 = axis[0]
        p1 = axis[1]
        imgui.get_window_draw_list().add_line(window_to_screen(p0), window_to_screen(p1), color, 1)

    return changed, axes