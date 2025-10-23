import math
from imgui_bundle import imgui
from typing import TypeVar, Tuple, List
import glm


_view:glm.mat4 = glm.identity(glm.mat4)
_projection:glm.mat4 = glm.ortho(0,512,0,512,-1,1) # this is the rect of the input coordinate system, the image topleft, bottomright
_widget_rect:Tuple[int, int, int, int]=0, 0, 512, 512 # this is the rectangle of the target coord system, the widget pos and size essentially the gl viewport

_region_br:imgui.ImVec2Like = imgui.ImVec2(0,0)
_region_tl:imgui.ImVec2Like = imgui.ImVec2(0,0)

_canvas_size:Tuple[float, float]=(512.0, 512.0)
def begin_viewport(label:str, size=imgui.ImVec2Like|None)->bool:
    global _widget_rect, _projection, _view, _region_tl, _region_br, _canvas_size
    imgui.begin_child(label, size, imgui.ChildFlags_.borders)
    x, y = imgui.get_cursor_screen_pos()
    w, h = imgui.get_content_region_avail()
    _widget_rect = (int(x), int(y), int(w), int(h))

    # by default setup an orthographic projection matching the widget size
    setup_orthographic(0,0,float(w),float(h))


    return True

def draw_margins(tl:imgui.ImVec2Like, br:imgui.ImVec2Like):
    # draw margins
    margin_color = imgui.color_convert_float4_to_u32((0.1, 0.1, 0.1, 0.95))
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
    # # left margin
    # draw_list.add_rect_filled(
    #     imgui.ImVec2(window_tl.x, window_tl.y),
    #     imgui.ImVec2(tl.x, window_br.y),
    #     margin_color
    # )
    # # right margin
    # draw_list.add_rect_filled(
    #     imgui.ImVec2(br.x, window_tl.y),
    #     imgui.ImVec2(window_br.x, window_br.y),
    #     margin_color
    # )
    # # top margin
    # draw_list.add_rect_filled(
    #     imgui.ImVec2(tl.x, window_tl.y),
    #     imgui.ImVec2(br.x, tl.y),
    #     margin_color
    # )
    # # bottom margin
    # draw_list.add_rect_filled(
    #     imgui.ImVec2(tl.x, br.y),
    #     imgui.ImVec2(br.x, window_br.y),
    #     margin_color
    # )

def end_viewport():
    # Color for the outside area (darker)
    # outside_color = imgui.color_convert_float4_to_u32((0.05, 0.05, 0.05, 0.1))
    # drawlist = imgui.get_window_draw_list()

    # tl = project(imgui.ImVec2(0, 0))
    # br = project(imgui.ImVec2(*_canvas_size))

    # # widget coords
    # widget_tl = imgui.ImVec2(_widget_rect[0], _widget_rect[1])
    # widget_br = imgui.ImVec2(_widget_rect[0]+_widget_rect[2], _widget_rect[1]+_widget_rect[3])
    # # left margin
    # drawlist.add_rect_filled(widget_tl, imgui.ImVec2(tl.x, br.y), outside_color)
    # # right margin
    # drawlist.add_rect_filled(imgui.ImVec2(br.x, tl.y), widget_br, outside_color)
    # # top margin
    # drawlist.add_rect_filled(widget_tl, imgui.ImVec2(widget_br.x, tl.y), outside_color)
    # # bottom margin
    # drawlist.add_rect_filled(imgui.ImVec2(tl.x, br.y), imgui.ImVec2(widget_br.x, widget_br.y), outside_color)

    # imgui.set_cursor_screen_pos(_region_br-imgui.ImVec2(100,20))
    # imgui.text(f"{_canvas_size[0]:.0f}x{_canvas_size[1]:.0f}")
    imgui.end_child()





##############
# PROJECTION #
##############
def project(point:imgui.ImVec2Like)->imgui.ImVec2Like:
    global _projection, _view, _widget_rect
    assert len(point) == 2
    P = glm.project(glm.vec3(*point,0), _view, _projection, _widget_rect)
    return imgui.ImVec2(P.x, P.y)

def unproject(screen_point:imgui.ImVec2Like)->imgui.ImVec2Like:
    global _projection, _view, _widget_rect
    P = glm.unProject(glm.vec3(screen_point.x, screen_point.y, 0), _view, _projection, _widget_rect)
    return imgui.ImVec2(P.x, P.y)

def _project_lines(lines:List[Tuple[imgui.ImVec2Like, imgui.ImVec2Like]])->List[Tuple[imgui.ImVec2Like, imgui.ImVec2Like]]:
    projected_lines = []
    for A, B in lines:
        A_proj = project(A)
        B_proj = project(B)

        projected_lines.append((A_proj, B_proj))
    return projected_lines

def setup_orthographic(xmin:float, ymin:float, xmax:float, ymax:float):
    global _projection, _view, _canvas_size

    x, y = imgui.get_cursor_screen_pos()
    w, h = imgui.get_content_region_avail()
    _widget_rect = (int(x), int(y), int(w), int(h))
    widget_aspect = w/h
    content_width = xmax - xmin
    content_height = ymax-ymin
    content_aspect = content_width/content_height
    _canvas_size = (content_width, content_height)
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


def setup_perspective(fovy:float, position=glm.vec3(5,5,5), target=glm.vec3(0, 0, 0), near=0.1, far=100.0):
    global _projection, _view, _canvas_size
    aspect = float(_widget_rect[2]) / float(_widget_rect[3])
    _projection = glm.perspective(math.radians(fovy), aspect, near, far)
    _view = glm.lookAt(position, target, glm.vec3(0, 1, 0))

def get_camera()->Tuple[glm.vec3, glm.vec3]:
    return _view, _projection


########
# DRAW #
########
import itertools

def _draw_annotations(centers:List[imgui.ImVec2Like], labels:List[str|None]):
    draw_list = imgui.get_window_draw_list()
    for C, label in zip(centers, labels):
        draw_list.add_text(
            (C.x, C.y),
            imgui.color_convert_float4_to_u32((1.0,1.0,1.0,1.0)),
            label
        )


def draw_lines(lines:List[Tuple[imgui.ImVec2Like, imgui.ImVec2Like]], color:int=None):
    """Draw 2D lines in the scene.
    Note: lines are clipped against the near plane before projection.
    """
    # clip lines to near plane
    # clipped_lines = []
    # for A, B in lines:
    #     clipped = _clip_line_near_plane_world(glm.vec3(A.x, A.y, 0), glm.vec3(B.x, B.y, 0), _view, near=-1.0)
    #     if clipped is not None:
    #         A_clipped, B_clipped = clipped
    #         clipped_lines.append(
    #             (imgui.ImVec2(A_clipped.x, A_clipped.y), imgui.ImVec2(B_clipped.x, B_clipped.y))
    #         )

    if color is None:
        color = imgui.color_convert_float4_to_u32((1, 1, 1, 1))
    # project lines to screen
    lines = _project_lines(lines)
    draw_list = imgui.get_window_draw_list()
    for line in lines:
        draw_list.add_line(
            imgui.ImVec2(line[0].x, line[0].y),
            imgui.ImVec2(line[1].x, line[1].y),
            color,
            1.0
        )

###########
# HANDLES #
###########
def point_handle(label:str, point:imgui.ImVec2Like, *, color:int=None)->Tuple[bool, imgui.ImVec2Like]:
    global _projection, _view, _widget_rect

    if color is None:
        color = imgui.color_convert_float4_to_u32((1.0,1.0,1.0,0.9))

    # project the point to world coordinates
    P = project(point)

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
        prev_world = unproject(prev_mouse_pos)
        curr_world = unproject(mouse_pos)

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
