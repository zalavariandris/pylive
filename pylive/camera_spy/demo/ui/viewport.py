import math
from imgui_bundle import imgui
from typing import TypeVar, Tuple, List
import glm
import numpy as np
from . import colors
from typing import Tuple
from typing import Literal

##############
# PROJECTION #
##############
_view:glm.mat4 = glm.identity(glm.mat4)
_projection:glm.mat4 = glm.ortho(0,512,0,512,-1,1) # this is the rect of the input coordinate system, the image topleft, bottomright
_near:float = 0.1
_far:float = 1000.0

from typing import Iterable
def _project(point:Iterable[int|float])->imgui.ImVec2Like:
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
            
def _unproject(screen_point:imgui.ImVec2Like)->imgui.ImVec2Like:
    global _projection, _view
    x, y = imgui.get_window_pos()
    w, h = imgui.get_window_size()
    widget_rect = (int(x), int(y), int(w), int(h))
    P = glm.unProject(glm.vec3(screen_point.x, screen_point.y, 0), _view, _projection, widget_rect)
    return imgui.ImVec2(P.x, P.y)

def ortho(xmin:float, ymin:float, xmax:float, ymax:float, near:float=-1.0, far:float=1.0):
    global _projection

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
        _projection = glm.ortho(0.0, float(content_width), 0.0-top_margin, proj_h-top_margin, near, far)
        _near, _far = near, far
    else:
        # viewport is wider -> expand world width, center original canvas horizontally
        proj_w = float(content_height) * float(widget_aspect)
        left_margin = (proj_w - float(content_width)) * 0.5
        _projection = glm.ortho(0.0-left_margin, proj_w-left_margin, 0.0, float(content_height), near, far)
        _near, _far = near, far

def perspective(fovy:float, aspect:float, near:float, far:float, pan_and_zoom:glm.mat4):
    global _projection, _near, _far
    # Step 1: canonical frustum bounds at near plane
    top = near * math.tan(fovy / 2)
    bottom = -top
    right = top * aspect
    left = -right

    # Step 2: extract translation and scale from pan_and_zoom
    # Extract scale from the matrix (assumes uniform scale in x and y)
    scale_x = glm.length(glm.vec3(pan_and_zoom[0]))
    scale_y = glm.length(glm.vec3(pan_and_zoom[1]))
    scale = (scale_x + scale_y) / 2.0  # average scale
    
    # Extract translation
    offset_x = pan_and_zoom[3][0]
    offset_y = pan_and_zoom[3][1]
    
    # Step 3: apply inverse transformations to frustum
    # Inverse scale: divide frustum bounds
    left /= scale
    right /= scale
    top /= scale
    bottom /= scale
    
    # Inverse translation: shift frustum
    left -= offset_x
    right -= offset_x
    top -= offset_y
    bottom -= offset_y

    # Step 4: create frustum with adjusted bounds
    _projection = glm.frustum(left, right, bottom, top, near, far)
    _near, _far = near, far

def frustum(left:float, right:float, bottom:float, top:float, near:float, far:float):
    global _projection
    _projection = glm.frustum(left, right, bottom, top, near, far)
    _near, _far = near, far

def setup_view(view:glm.mat4):
    global _view
    _view = view

def get_view_projection()->Tuple[glm.vec3, glm.vec3]:
    return _view, _projection

def pan_and_zoom(view:glm.mat4, zoom_speed:float=0.1, pan_speed:float=1.0)->Tuple[bool, glm.mat4]:
    """Handle panning and zooming of the view matrix based on mouse input.
    Returns (changed:bool, new_view:glm.mat4)
    Zoom is centered around the mouse position in world space.
    """
    changed = False
    translation = glm.vec3(0,0,0)
    scale = 1.0

    mouse_screen = imgui.get_mouse_pos()
    mouse_world_before = _unproject(mouse_screen)

    # Zooming
    mouse_wheel = imgui.get_io().mouse_wheel
    if mouse_wheel != 0.0:
        scale_factor = 1.0 + mouse_wheel * zoom_speed
        scale *= scale_factor
        changed = True

    # Panning
    if imgui.is_mouse_dragging(imgui.MouseButton_.middle) or (imgui.is_key_down(imgui.Key.left_alt) and imgui.is_mouse_dragging(imgui.MouseButton_.left)):
        drag_delta = _get_world_space_mouse_drag_delta(imgui.MouseButton_.middle if imgui.is_mouse_dragging(imgui.MouseButton_.middle) else imgui.MouseButton_.left)
        translation.x += drag_delta.x * pan_speed
        translation.y += drag_delta.y * pan_speed
        imgui.reset_mouse_drag_delta(imgui.MouseButton_.middle if imgui.is_mouse_dragging(imgui.MouseButton_.middle) else imgui.MouseButton_.left)
        changed = True

    if changed:
        # Apply translation and scaling to the view matrix
        new_view = glm.translate(view, translation)
        new_view = glm.scale(new_view, glm.vec3(scale, scale, scale))
        # If zooming, keep mouse position fixed in world space
        if mouse_wheel != 0.0:
            # Unproject mouse position after scaling
            # Use the new_view for unprojection
            global _view
            old_view = _view
            _view = new_view
            mouse_world_after = _unproject(mouse_screen)
            _view = old_view
            # Compute translation to keep mouse_world_before == mouse_world_after
            offset = glm.vec3(mouse_world_before.x - mouse_world_after.x, mouse_world_before.y - mouse_world_after.y, 0)
            new_view = glm.translate(new_view, -offset)
        return True, new_view

    return False, view


####################
# VIEWPORT CONTEXT #
####################
def begin_viewport(label:str, size=imgui.ImVec2Like|None, borders=True)->bool:
    imgui.begin_child(label, size, 
        imgui.ChildFlags_.borders if borders else imgui.ChildFlags_.none,
        imgui.WindowFlags_.no_scrollbar
    )

    # by default setup an orthographic projection matching the widget size
    w, h = imgui.get_content_region_avail()
    ortho(0,0,float(w),float(h))
    return True

def render_margins(tl:imgui.ImVec2Like, br:imgui.ImVec2Like):
    # draw margins
    margin_color = imgui.color_convert_float4_to_u32((0.1, 0.1, 0.1, 0.66))
    tl = _project(tl)
    br = _project(br)

    draw_list = imgui.get_window_draw_list()
    draw_list.add_circle(tl, 5, margin_color, 12, 2)
    draw_list.add_circle(br, 5, margin_color, 12, 2)

    window_tl = imgui.get_window_pos()
    window_br = window_tl + imgui.get_window_size()

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

def _clip_line(A: glm.vec3, B: glm.vec3, view: glm.mat4, near=None, far=None):
    """Clip a line against the near plane in camera space, return world-space endpoints.
    A, B: world-space endpoints of the line
    view: camera view matrix
    near, far: near and far plane distances
    """
    if near is None:
        near = _near
    if far is None:
        far = _far

    A_cam = glm.vec3(view * glm.vec4(A, 1.0))
    Az = A_cam.z
    B_cam = glm.vec3(view * glm.vec4(B, 1.0))
    Bz = B_cam.z

    # Both in front
    if Az <= -near and Bz <= -near:  # negative z is in front in OpenGL
        return A, B

    # Both behind → discard
    if Az > -near and Bz > -near:
        return None

    # Clip line to near plane
    t = (-near - Az) / (Bz - Az)
    intersection_cam = A_cam + t * (B_cam - A_cam)

    # Transform intersection back to world space
    inv_view = glm.inverse(view)
    intersection_world = glm.vec3(inv_view * glm.vec4(intersection_cam, 1.0))

    if Az > -near:
        return intersection_world, B
    else:
        return A, intersection_world
    
def _is_clipped(P: glm.vec3, view: glm.mat4, near=None, far=None)->bool:
    """Check if a point is clipped by the near/far planes in camera space."""
    if near is None:
        near = _near
    if far is None:
        far = _far

    P_cam = glm.vec3(view * glm.vec4(P, 1.0))
    z = P_cam.z

    if z > -near or z < -far:
        return True
    return False

def render_guide_line(p1, p2, color:int=imgui.color_convert_float4_to_u32((1,1,1,1)), thickness:float=1.0):
    """Draw a 2D line in the scene.
    Note: lines are clipped against the near plane before projection.
    It is essentally a wrapper over draw_list.add_line, with projection
    """
    # TODO: clip line to near plane
    if len(p1) == 3 and len(p2) == 3:
        clipped = _clip_line(glm.vec3(*p1), glm.vec3(*p2), _view, _near, _far)
        if clipped is None:
            return
        p1, p2 = clipped

    draw_list = imgui.get_window_draw_list()
    draw_list.add_line(
        _project(p1),
        _project(p2),
        color,
        thickness
    )

def render_grid_plane(size: float = 10, step: float = 1, near: float = 0.1):
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
        render_guide_line(line[0], line[1], color=imgui.color_convert_float4_to_u32((0.5, 0.5, 0.5, 1)))

def render_axes(length:float=1.0, thickness:float=2.0):
    """Draw XYZ axes at the origin."""
    origin = glm.vec3(0,0,0)
    x_axis = glm.vec3(length, 0, 0)
    y_axis = glm.vec3(0, length, 0)
    z_axis = glm.vec3(0, 0, length)

    render_guide_line(origin, x_axis, color=imgui.color_convert_float4_to_u32((1,0,0,0.5)), thickness=thickness) # X - red
    render_guide_line(origin, y_axis, color=imgui.color_convert_float4_to_u32((0,1,0,0.5)), thickness=thickness) # Y - green
    render_guide_line(origin, z_axis, color=imgui.color_convert_float4_to_u32((0,0,1,0.5)), thickness=thickness) # Z - blue

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

def _get_world_space_mouse_drag_delta(button: imgui.MouseButton_=0, lock_threshold: float=-1)->imgui.ImVec2Like:
    curr_mouse_pos = imgui.get_mouse_pos()
    prev_mouse_pos = imgui.get_mouse_pos() - imgui.get_mouse_drag_delta(button, lock_threshold)
    prev_world = _unproject(prev_mouse_pos)
    curr_world = _unproject(curr_mouse_pos)
    world_space_delta = curr_world - prev_world
    return world_space_delta

def control_point(label:str, point:imgui.ImVec2Like, *, color:int=colors.WHITE)->Tuple[bool, imgui.ImVec2Like]:
    # project the point to world coordinates
    P = _project(point)

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
        world_space_delta = _get_world_space_mouse_drag_delta()

        # Apply movement to the point
        if math.fabs(world_space_delta.x) > 0.0 or math.fabs(world_space_delta.y) > 0.0:
            imgui.reset_mouse_drag_delta()
            new_point = type(point)(point.x, point.y)
            new_point.x += world_space_delta.x
            new_point.y += world_space_delta.y
            return True, new_point

    # imgui.set_cursor_pos(store_cursor_pos) # restore cursor pos?
    return False, point
