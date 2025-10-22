import math
from imgui_bundle import imgui
from typing import TypeVar, Tuple
import glm


_view:glm.mat4 = glm.identity(glm.mat4)
_projection:glm.mat4 = glm.ortho(0,512,0,512,-1,1) # this is the rect of the input coordinate system, the image topleft, bottomright
_viewport:Tuple[int, int, int, int]=0, 0, 512, 512 # this is the rectangle of the target coord system, the widget pos and size

_region_br:imgui.ImVec2Like = imgui.ImVec2(0,0)
_region_tl:imgui.ImVec2Like = imgui.ImVec2(0,0)

_canvas_size:Tuple[float, float]=(512.0, 512.0)

def begin_plot(label:str, canvas_size:Tuple[float, float], size=imgui.ImVec2Like|None)->bool:
    global _viewport, _projection, _view, _region_tl, _region_br, _canvas_size
    _canvas_size = canvas_size
    imgui.begin_child(label, size, imgui.ChildFlags_.borders)
    x, y = imgui.get_cursor_screen_pos()
    w, h = imgui.get_content_region_avail()
    _viewport = (int(x), int(y), int(w), int(h)) # is this the target coordinate system, the widget pos and size

    # create projection matrix, fit to axes and keep aspect ratio
    viewport_aspect = w / h
    region_aspect = canvas_size[0] / canvas_size[1]

    # fit region to viewport while keeping aspect ratio
    if viewport_aspect < region_aspect:
        # viewport is narrower -> expand world height, center original canvas vertically
        proj_h = float(canvas_size[0]) / float(viewport_aspect)
        _projection = glm.ortho(0.0, float(canvas_size[0]), 0.0, proj_h, -1.0, 1.0)
        extra_y = proj_h - float(canvas_size[1])
        _view = glm.translate(glm.identity(glm.mat4), glm.vec3(0.0, extra_y * 0.5, 0.0))
    else:
        # viewport is wider -> expand world width, center original canvas horizontally
        proj_w = float(canvas_size[1]) * float(viewport_aspect)
        _projection = glm.ortho(0.0, proj_w, 0.0, float(canvas_size[1]), -1.0, 1.0)
        extra_x = proj_w - float(canvas_size[0])
        _view = glm.translate(glm.identity(glm.mat4), glm.vec3(extra_x * 0.5, 0.0, 0.0))

    drawlist = imgui.get_window_draw_list()
    _region_tl = _project_point(imgui.ImVec2(0, 0))
    _region_br = _project_point(imgui.ImVec2(*canvas_size))
    # draw the main region
    
    drawlist.add_rect_filled(
        _project_point(imgui.ImVec2(0,0)), 
        _project_point(imgui.ImVec2(*canvas_size)), 
        imgui.color_convert_float4_to_u32((0.1, 0.1, 0.1, 1.0))
    )

    imgui.text(f"{_viewport[2]}x{_viewport[3]}")
    return True

def _project_point(point:imgui.ImVec2Like)->imgui.ImVec2Like:
    global _projection, _view, _viewport
    P = glm.project(glm.vec3(point.x,point.y,0), _view, _projection, _viewport)
    return imgui.ImVec2(P.x, P.y)

def _unproject_point(screen_point:imgui.ImVec2Like)->imgui.ImVec2Like:
    global _projection, _view, _viewport
    P = glm.unProject(glm.vec3(screen_point.x, screen_point.y, 0), _view, _projection, _viewport)
    return imgui.ImVec2(P.x, P.y)

def point_handle(label:str, point:imgui.ImVec2Like, color:int=None)->Tuple[bool, imgui.ImVec2Like]:
    global _projection, _view, _viewport

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
    outside_color = imgui.color_convert_float4_to_u32((0.05, 0.05, 0.05, 0.7))
    drawlist = imgui.get_window_draw_list()
    x0, y0 = _viewport[0], _viewport[1]
    x1, y1 = _viewport[0] + _viewport[2], _viewport[1] + _viewport[3]
    # Top margin
    drawlist.add_rect_filled(
        imgui.ImVec2(x0, y0),
        imgui.ImVec2(x1, _region_tl.y),
        outside_color
    )
    # Bottom margin
    drawlist.add_rect_filled(
        imgui.ImVec2(x0, _region_br.y),
        imgui.ImVec2(x1, y1),
        outside_color
    )
    # Left margin
    drawlist.add_rect_filled(
        imgui.ImVec2(x0, _region_tl.y),
        imgui.ImVec2(_region_tl.x, _region_br.y),
        outside_color
    )
    # Right margin
    drawlist.add_rect_filled(
        imgui.ImVec2(_region_br.x, _region_tl.y),
        imgui.ImVec2(x1, _region_br.y),
        outside_color
    )

    imgui.set_cursor_screen_pos(_region_br-imgui.ImVec2(100,20))
    imgui.text(f"{_canvas_size[0]:.0f}x{_canvas_size[1]:.0f}")
    imgui.end_child()
