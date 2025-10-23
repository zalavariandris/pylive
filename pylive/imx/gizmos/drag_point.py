from imgui_bundle import imgui
from typing import Tuple, TypeVar, Generic


def window_to_screen(window_pos: imgui.ImVec2) -> imgui.ImVec2:
    """Convert window-relative coordinates to screen coordinates."""
    screen_offset = imgui.get_cursor_screen_pos() - imgui.get_cursor_pos()
    return imgui.ImVec2(window_pos.x, window_pos.y) + screen_offset

Vec2T = TypeVar('Vec2')
def drag_point(label:str, point:Vec2T, *,  color:int=None)->Tuple[bool, Vec2T]:
    if color is None:
        color = imgui.color_convert_float4_to_u32((1.0,1.0,1.0,0.9))

    change = False
    store_cursor_pos = imgui.get_cursor_pos()
    btn_size = imgui.ImVec2(28,28)
    imgui.set_cursor_pos(imgui.ImVec2(point.x-btn_size.x/2, point.y-btn_size.y/2))
    imgui.invisible_button(label, btn_size)

    # drawing
    draw_list = imgui.get_window_draw_list()
    radius=3
    
    text_offset = imgui.ImVec2(5, -5)
    if imgui.is_item_hovered() or imgui.is_item_active():
        draw_list.add_circle_filled(window_to_screen(point), radius+0.5, color, num_segments=0)
        text = f"{label}".split("##")[0]
        text += f"({point.x:.0f},{point.y:.0f})"
        draw_list.add_text(window_to_screen(point) + text_offset, color, text)
    else:
        r, g, b, a = imgui.color_convert_u32_to_float4(color)
        draw_list.add_circle_filled(window_to_screen(point), radius, color, num_segments=8)
        # text = f"{label}".split("##")[0]
        # text += f"({point.x:.0f},{point.y:.0f})"
        # draw_list.add_text(window_to_screen(point) + text_offset, color, text)
    

    new_point = type(point)(point.x, point.y)
    if imgui.is_item_active():
        delta = imgui.get_mouse_drag_delta()
        imgui.reset_mouse_drag_delta()
        new_point.x += delta.x
        new_point.y += delta.y
        change = True

    imgui.set_cursor_pos(store_cursor_pos)
    return change, new_point
