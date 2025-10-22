import math
from imgui_bundle import imgui
from typing import TypeVar, Tuple
import glm


_view:glm.mat4 = glm.identity(glm.mat4)
_projection:glm.mat4 = glm.ortho(0,512,0,512,-1,1) # this is the rect of the input coordinate system, the image topleft, bottomright
_widget_rect:Tuple[int, int, int, int]=0, 0, 512, 512 # this is the rectangle of the target coord system, the widget pos and size

_region_br:imgui.ImVec2Like = imgui.ImVec2(0,0)
_region_tl:imgui.ImVec2Like = imgui.ImVec2(0,0)

_canvas_size:Tuple[float, float]=(512.0, 512.0)

def setup_orthographic(xmin:float, ymin:float, xmax:float, ymax:float, fit_viewport=True):
    global _projection, _view

    x, y = imgui.get_cursor_screen_pos()
    w, h = imgui.get_content_region_avail()
    _widget_rect = (int(x), int(y), int(w), int(h))
    widget_aspect = w/h
    content_width = xmax - xmin
    content_height = (ymax-ymin)
    content_aspect = content_width/content_height
    if fit_viewport:
        if widget_aspect < content_aspect:
            # viewport is narrower -> expand world height, center original canvas vertically
            proj_h = float(content_width) / float(widget_aspect)
            _projection = glm.ortho(0.0, float(content_width), 0.0, proj_h, -1.0, 1.0)
            extra_y = proj_h - float(content_height)
            _view = glm.translate(glm.identity(glm.mat4), glm.vec3(0.0, extra_y * 0.5, 0.0))
        else:
            # viewport is wider -> expand world width, center original canvas horizontally
            proj_w = float(content_height) * float(widget_aspect)
            _projection = glm.ortho(0.0, proj_w, 0.0, float(content_height), -1.0, 1.0)
            extra_x = proj_w - float(content_width)
            _view = glm.translate(glm.identity(glm.mat4), glm.vec3(extra_x * 0.5, 0.0, 0.0))
    else:
        _projection = glm.ortho(xmin, xmax, ymin, ymax, -1.0, 1.0)
        _view = glm.identity(glm.mat4)

def begin_plot(label:str, canvas_size:Tuple[float, float], size=imgui.ImVec2Like|None)->bool:
    global _widget_rect, _projection, _view, _region_tl, _region_br, _canvas_size
    _canvas_size = canvas_size
    imgui.begin_child(label, size, imgui.ChildFlags_.borders)
    x, y = imgui.get_cursor_screen_pos()
    w, h = imgui.get_content_region_avail()
    _widget_rect = (int(x), int(y), int(w), int(h))

    imgui.text(f"Widget screen: {_widget_rect[2]}x{_widget_rect[3]}")


    return True

def _project_point(point:imgui.ImVec2Like)->imgui.ImVec2Like:
    global _projection, _view, _widget_rect
    P = glm.project(glm.vec3(point.x,point.y,0), _view, _projection, _widget_rect)
    return imgui.ImVec2(P.x, P.y)

def _unproject_point(screen_point:imgui.ImVec2Like)->imgui.ImVec2Like:
    global _projection, _view, _widget_rect
    P = glm.unProject(glm.vec3(screen_point.x, screen_point.y, 0), _view, _projection, _widget_rect)
    return imgui.ImVec2(P.x, P.y)

def point_handle(label:str, point:imgui.ImVec2Like, color:int=None)->Tuple[bool, imgui.ImVec2Like]:
    global _projection, _view, _widget_rect

    if color is None:
        color = imgui.color_convert_float4_to_u32((1.0,1.0,1.0,0.9))

    # project the point to world coordinates
    P = _project_point(point)

    # invisible button
    btn_size = imgui.ImVec2(28,28)
    imgui.set_cursor_screen_pos(imgui.ImVec2(P.x, P.y)-btn_size/2)
    imgui.invisible_button(label, btn_size)

    # draw the point
    draw_list = imgui.get_window_draw_list()
    text_offset = imgui.ImVec2(5, -5)
    radius=3
    if imgui.is_item_hovered() or imgui.is_item_active():
        draw_list.add_circle_filled(P, radius+1, color, num_segments=0)
        text = f"{label}".split("##")[0]
        text += f"({point.x:.0f},{point.y:.0f})"
        draw_list.add_text(P + text_offset, color, text)
    else:
        r, g, b, a = imgui.color_convert_u32_to_float4(color)
        draw_list.add_circle_filled(P, radius, color, num_segments=8)

    if imgui.is_item_active():
        # Get mouse positions
        mouse_pos = imgui.get_mouse_pos()
        drag_delta = imgui.get_mouse_drag_delta()
        prev_mouse_pos = mouse_pos - drag_delta

        # Convert mouse positions to world coordinates
        prev_world = _unproject_point(prev_mouse_pos)
        curr_world = _unproject_point(mouse_pos)

        # Compute world-space movement
        move_delta = curr_world - prev_world

        # Apply movement to the point
        if math.fabs(move_delta.x) > 0.0 or math.fabs(move_delta.y) > 0.0:
            imgui.reset_mouse_drag_delta()
            new_point = type(point)(point.x, point.y)
            new_point.x += move_delta.x
            new_point.y += move_delta.y
            return True, new_point

    # imgui.set_cursor_pos(store_cursor_pos) # restore cursor pos?
    return False, point

def end_plot():
    # Color for the outside area (darker)
    outside_color = imgui.color_convert_float4_to_u32((0.05, 0.05, 0.05, 0.1))
    drawlist = imgui.get_window_draw_list()

    tl = _project_point(imgui.ImVec2(0, 0))
    br = _project_point(imgui.ImVec2(*_canvas_size))

    # widget coords
    widget_tl = imgui.ImVec2(_widget_rect[0], _widget_rect[1])
    widget_br = imgui.ImVec2(_widget_rect[0]+_widget_rect[2], _widget_rect[1]+_widget_rect[3])
    # left margin
    drawlist.add_rect_filled(widget_tl, imgui.ImVec2(tl.x, br.y), outside_color)
    # right margin
    drawlist.add_rect_filled(imgui.ImVec2(br.x, tl.y), widget_br, outside_color)
    # top margin
    drawlist.add_rect_filled(widget_tl, imgui.ImVec2(widget_br.x, tl.y), outside_color)
    # bottom margin
    drawlist.add_rect_filled(imgui.ImVec2(tl.x, br.y), imgui.ImVec2(widget_br.x, widget_br.y), outside_color)

    imgui.set_cursor_screen_pos(_region_br-imgui.ImVec2(100,20))
    imgui.text(f"{_canvas_size[0]:.0f}x{_canvas_size[1]:.0f}")
    imgui.end_child()
