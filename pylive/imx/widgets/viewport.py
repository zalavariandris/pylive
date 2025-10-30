import math
from imgui_bundle import imgui
from typing import TypeVar, Tuple, List
import glm
import numpy as np


##############
# PROJECTION #
##############
_view:glm.mat4 = glm.identity(glm.mat4)
_projection:glm.mat4 = glm.ortho(0,512,0,512,-1,1) # this is the rect of the input coordinate system, the image topleft, bottomright

from typing import Iterable
def project(point:Iterable[int|float])->imgui.ImVec2Like:
    global _projection, _view
    assert len(point) == 2 or len(point) == 3

    x, y = imgui.get_window_pos()
    w, h = imgui.get_window_size()
    widget_rect = (int(x), int(y), int(w), int(h))

    match len(point):
        case 2:
            P = glm.project(glm.vec3(*point,0), _view, _projection, widget_rect)
            return imgui.ImVec2(P.x, P.y)
        case 3:
            P = glm.project(glm.vec3(*point), _view, _projection, widget_rect)
            return imgui.ImVec2(P.x, P.y)
        case _:
            raise ValueError("point must be of length 2 or 3")
            
def unproject(screen_point:imgui.ImVec2Like)->imgui.ImVec2Like:
    global _projection, _view
    x, y = imgui.get_window_pos()
    w, h = imgui.get_window_size()
    widget_rect = (int(x), int(y), int(w), int(h))
    P = glm.unProject(glm.vec3(screen_point.x, screen_point.y, 0), _view, _projection, widget_rect)
    return imgui.ImVec2(P.x, P.y)

def setup_orthographic(xmin:float, ymin:float, xmax:float, ymax:float):
    global _projection, _view

    x, y = imgui.get_window_pos()
    w, h = imgui.get_window_size()
    widget_aspect = w/h
    content_width = xmax - xmin
    content_height = ymax-ymin
    content_aspect = content_width/content_height
    if widget_aspect < content_aspect:
        # viewport is narrower -> expand world height, center original canvas vertically
        proj_h = float(content_width) / float(widget_aspect)
        top_margin = ( proj_h - float(content_height) ) * 0.5
        _projection = glm.ortho(0.0, float(content_width), 0.0-top_margin, proj_h-top_margin, -1.0, 1.0)
    else:
        # viewport is wider -> expand world width, center original canvas horizontally
        proj_w = float(content_height) * float(widget_aspect)
        left_margin = (proj_w - float(content_width)) * 0.5
        _projection = glm.ortho(0.0-left_margin, proj_w-left_margin, 0.0, float(content_height), -1.0, 1.0)
    _view = glm.identity(glm.mat4)


def setup_view_projection(view:glm.mat4, projection:glm.mat4)->None:
    global _projection, _view
    _view = view
    _projection = projection

def get_view_projection()->Tuple[glm.vec3, glm.vec3]:
    return _view, _projection


####################
# VIEWPORT CONTEXT #
####################
def begin_viewport(label:str, size=imgui.ImVec2Like|None)->bool:
    imgui.begin_child(label, size, imgui.ChildFlags_.borders, imgui.WindowFlags_.no_scrollbar)
    w, h = imgui.get_content_region_avail()
    imgui.slider_float2("viewport size", imgui.ImVec2(float(w), float(h)), 100.0, 2000.0, "%.0f")
    # by default setup an orthographic projection matching the widget size
    setup_orthographic(0,0,float(w),float(h))
    return True

def draw_margins(tl:imgui.ImVec2Like, br:imgui.ImVec2Like):
    # draw margins
    margin_color = imgui.color_convert_float4_to_u32((0.1, 0.1, 0.1, 0.66))
    tl = project(tl)
    br = project(br)

    draw_list = imgui.get_window_draw_list()
    draw_list.add_circle(tl, 5, margin_color, 12, 2)
    draw_list.add_circle(br, 5, margin_color, 12, 2)

    window_tl = imgui.get_window_pos()
    window_br = window_tl + imgui.get_window_size()

    draw_list.add_line(
        imgui.ImVec2(tl.x, tl.y),
        imgui.ImVec2(br.x, br.y),
        margin_color, 2.0
    )
    # imgui.text(f"Viewport size: {window_tl.x:.0f},{window_tl.y:.0f} - {window_br.x:.0f},{window_br.y:.0f}")
    # left margin
    draw_list.add_rect_filled(
        imgui.ImVec2(window_tl.x, window_tl.y),
        imgui.ImVec2(tl.x, window_br.y),
        margin_color
    )
    # right margin
    draw_list.add_rect_filled(
        imgui.ImVec2(br.x, window_tl.y),
        imgui.ImVec2(window_br.x, window_br.y),
        margin_color
    )
    # top margin
    draw_list.add_rect_filled(
        imgui.ImVec2(tl.x, window_tl.y),
        imgui.ImVec2(br.x, tl.y),
        margin_color
    )
    # bottom margin
    draw_list.add_rect_filled(
        imgui.ImVec2(tl.x, br.y),
        imgui.ImVec2(br.x, window_br.y),
        margin_color
    )

def end_viewport():
    imgui.end_child()


########
# DRAW #
########

def _clip_line_near_plane_world(A: glm.vec3, B: glm.vec3, view: glm.mat4, near=0.1):
    """Clip a line against the near plane in camera space, return world-space endpoints."""
    A_cam = glm.vec3(view * glm.vec4(A, 1.0))
    B_cam = glm.vec3(view * glm.vec4(B, 1.0))

    zA, zB = A_cam.z, B_cam.z

    # Both in front
    if zA <= -near and zB <= -near:  # negative z is in front in OpenGL
        return A, B

    # Both behind → discard
    if zA > -near and zB > -near:
        return None

    # Clip line to near plane
    t = (-near - zA) / (zB - zA)
    intersection_cam = A_cam + t * (B_cam - A_cam)

    # Transform intersection back to world space
    inv_view = glm.inverse(view)
    intersection_world = glm.vec3(inv_view * glm.vec4(intersection_cam, 1.0))

    if zA > -near:
        return intersection_world, B
    else:
        return A, intersection_world
    

def _clip_point_near_plane_world(A: glm.vec3, view: glm.mat4, near=0.1):
    """Clip a line against the near plane in camera space, return world-space endpoints."""
    A_cam = glm.vec3(view * glm.vec4(A, 1.0))

    zA = A_cam.z

    # Both in front
    if zA <= -near:  # negative z is in front in OpenGL
        return A

    # Both behind → discard
    if zA > -near:
        return None
    
    else:
        return A

def draw_line(p1, p2, color:int=imgui.color_convert_float4_to_u32((1,1,1,1)), thickness:float=1.0):
    """Draw a 2D line in the scene.
    Note: lines are clipped against the near plane before projection.
    It is essentally a wrapper over draw_list.add_line, with projection
    """
    # TODO: clip line to near plane
    draw_list = imgui.get_window_draw_list()

    draw_list.add_line(
        project(p1),
        project(p2),
        color,
        thickness
    )

def draw_grid(size: float = 10, step: float = 1, near: float = 0.1):
    """Draw a grid on the XZ plane centered at the origin."""

    # Generate grid coordinates
    n_steps = int(np.floor(size/2 / step)) # number of steps from the center to edge
    xs = np.arange(-n_steps, n_steps + 1) * step
    zs = np.arange(-n_steps, n_steps + 1) * step

    # Create grid lines along X and Z axes
    lines = []
    for x in xs:
        lines.append((glm.vec3(x, 0, -size/2), glm.vec3(x, 0, size/2)))
    for z in zs:
        lines.append((glm.vec3(-size/2, 0, z), glm.vec3(size/2, 0, z)))
    
    # draw grid lines
    for line in lines:
        draw_line(line[0], line[1], color=imgui.color_convert_float4_to_u32((0.5, 0.5, 0.5, 1)))

def _draw_annotations(centers:List[imgui.ImVec2Like], labels:List[str|None]):
    draw_list = imgui.get_window_draw_list()
    for C, label in zip(centers, labels):
        draw_list.add_text(
            (C.x, C.y),
            imgui.color_convert_float4_to_u32((1.0,1.0,1.0,1.0)),
            label
        )


###########
# HANDLES #
###########
def point_handle(label:str, point:imgui.ImVec2Like, *, color:int=None)->Tuple[bool, imgui.ImVec2Like]:
    if color is None:
        color = imgui.color_convert_float4_to_u32((1.0,1.0,1.0,0.9))

    # project the point to world coordinates
    P = project(point)

    # invisible button to handle interaction
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

    # handle dragging
    if imgui.is_item_active():
        # Compute world-space movement
        curr_mouse_pos = imgui.get_mouse_pos()
        prev_mouse_pos = imgui.get_mouse_pos() - imgui.get_mouse_drag_delta()
        prev_world = unproject(prev_mouse_pos)
        curr_world = unproject(curr_mouse_pos)
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
