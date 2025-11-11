import logging
import math
from imgui_bundle import imgui
from typing import TypeVar, Tuple, List
import glm
import numpy as np
from typing import Tuple, Literal, Iterable

import types

# ############ #
# Viewer Style #
# ############ #
def fade_color(color:imgui.ImVec4, amount:float=0.5) -> imgui.ImVec4:
        r, g, b, a = color
        return imgui.ImVec4(r, g, b, a * amount)

def get_viewer_style():
    style = imgui.get_style()
    return types.SimpleNamespace(
        BACKGROUND_COLOR = imgui.ImVec4(0.1, 0.1, 0.1, 1.0),
        GRID_COLOR =       imgui.ImVec4(0.3, 0.3, 0.3, 1.0),
        AXIS_COLOR_X =     imgui.ImVec4(1,0.1,0, 1.0),
        AXIS_COLOR_Y =     imgui.ImVec4(0,1,0, 1.0),
        AXIS_COLOR_Z =     imgui.ImVec4(0.0,0.5,1, 1.0),
        margin_stroke_color = fade_color(style.color_(imgui.Col_.border), 0.5),
        margin_fill_color = fade_color(style.color_(imgui.Col_.window_bg), 0.7),
        GUIDE_COLOR = style.color_(imgui.Col_.text_disabled),
        HORIZON_LINE_COLOR = style.color_(imgui.Col_.text_disabled),
        CONTROL_POINT_COLOR = style.color_(imgui.Col_.text)
    )

#######################
# STATELESS UTILITIES #
#######################
def overscan_projection(projection:glm.mat4, rect_tl, rect_br, overscan_tl, overscan_br)->glm.mat4:
    # Calculate canvas and widget dimensions
    canvas_width = rect_br.x - rect_tl.x
    canvas_height = rect_br.y - rect_tl.y
    widget_width = overscan_br.x - overscan_tl.x
    widget_height = overscan_br.y - overscan_tl.y
    
    # Calculate scale factors (how much bigger/smaller the widget is vs canvas)
    scale_x = canvas_width / widget_width
    scale_y = canvas_height / widget_height
    
    # Calculate translation factors (normalized)
    canvas_center_x = (rect_tl.x + rect_br.x) * 0.5
    canvas_center_y = (rect_tl.y + rect_br.y) * 0.5
    widget_center_x = (overscan_tl.x + overscan_br.x) * 0.5
    widget_center_y = (overscan_tl.y + overscan_br.y) * 0.5
    
    # Offset in normalized coordinates (-1 to 1)
    offset_x = 2.0 * (canvas_center_x - widget_center_x) / widget_width
    offset_y = 2.0 * (canvas_center_y - widget_center_y) / widget_height
    
    # Create transformation matrix
    # Scale first, then translate
    transform = glm.mat4(1.0)
    transform = glm.translate(transform, glm.vec3(offset_x, offset_y, 0.0))
    transform = glm.scale(transform, glm.vec3(scale_x, scale_y, 1.0))
    
    # Apply transformation to the projection matrix
    return transform * projection

def make_gridXZ_lines(size: float = 10, step: float = 1, near: float = 0.1):
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
    return lines

def make_gridXY_lines(size: float = 10, step: float = 1, near: float = 0.1):
    """Draw a grid on the XY plane centered at the origin."""

    # Generate grid coordinates
    n_steps = int(np.floor(size/2 / step)) # number of steps from the center to edge
    xs = np.arange(-n_steps, n_steps + 1) * step
    ys = np.arange(-n_steps, n_steps + 1) * step

    # Create grid lines along X and Y axes
    lines = []
    for x in xs:
        lines.append((glm.vec3(x, -size/2, 0), glm.vec3(x, size/2, 0)))
    for y in ys:
        lines.append((glm.vec3(-size/2, y, 0), glm.vec3(size/2, y, 0)))
    return lines

def make_gridYZ_lines(size: float = 10, step: float = 1, near: float = 0.1):
    """Draw a grid on the YZ plane centered at the origin."""

    # Generate grid coordinates
    n_steps = int(np.floor(size/2 / step)) # number of steps from the center to edge
    ys = np.arange(-n_steps, n_steps + 1) * step
    zs = np.arange(-n_steps, n_steps + 1) * step

    # Create grid lines along Y and Z axes
    lines = []
    for y in ys:
        lines.append((glm.vec3(0, y, -size/2), glm.vec3(0, y, size/2)))
    for z in zs:
        lines.append((glm.vec3(0, -size/2, z), glm.vec3(0, size/2, z)))
    return lines
############################
# Viewer Widget (stateful) #
############################
class ViewerWidget:
    def __init__(self, content_size:imgui.ImVec2, coordinate_system:Literal['top-left', 'bottom-left']='bottom-left'):
        # canvas size in pixels (aka viewport?)
        self.content_size = content_size
        self.coordinate_system = coordinate_system

        # 2D canvas pan and zoom
        self.interactive_pan_and_zoom = glm.identity(glm.mat4)
        # self.canvas_view = glm.identity(glm.mat4)  # updated every frame on begin_viewport, TODO: make computed property?
        # self.canvas_projection = glm.identity(glm.mat4) # same as above

        # 3D camera
        self.use_camera:bool = False
        self.camera_view_matrix = glm.identity(glm.mat4)
        self.camera_projection_matrix = glm.perspective(glm.radians(60.0), float(content_size.x)/float(content_size.y), 0.1, 100.0)

        # widget position and size (updated every frame on begin_viewport)
        self.pos:imgui.ImVec2 = None
        self.size:imgui.ImVec2 = None

    def get_canvas_projection(self)->glm.mat4:
        # Setup 2D projection with overscan
        left, right = 0.0, float(self.content_size.x)
        bottom, top = 0.0, float(self.content_size.y)

        match self.coordinate_system:
            case 'bottom-left':
                top, bottom = bottom, top
                projection_2d = glm.ortho(left, right, bottom, top,-1.0, 1.0)
            case 'top-left':
                projection_2d = glm.ortho(left, right, bottom, top,-1.0, 1.0)
        

        x, y = self.pos.x, self.pos.y
        w, h = self.size.x, self.size.y
        projection_2d = overscan_projection(projection_2d,
            glm.vec2(0, 0),
            glm.vec2(self.content_size.x, self.content_size.y),
            glm.vec2(0, 0),
            glm.vec2(w, h)
        )

        return projection_2d

    def content_fit_center_matrix(self)->glm.mat4:
        # Fit and center content according to widget
        content_fit_matrix = glm.identity(glm.mat4)
        # create a view  matrix that fits the content into the viewport
        widget_aspect = self.size.x / self.size.y
        content_aspect = self.content_size.x / self.content_size.y
        if widget_aspect > content_aspect:
            scale = self.size.y / self.content_size.y
            content_fit_matrix = glm.scale(content_fit_matrix, glm.vec3(scale, scale, 1))
        else:
            scale = self.size.x / self.content_size.x
            content_fit_matrix = glm.scale(content_fit_matrix, glm.vec3(scale, scale, 1))

        # center content
        content_screen_size = glm.vec2(self.content_size.x * scale, self.content_size.y * scale)
        offset_x = (self.size.x - content_screen_size.x) * 0.5
        offset_y = (self.size.y - content_screen_size.y) * 0.5
        center_content_matrix = glm.translate(glm.mat4(), glm.vec3(offset_x/scale, offset_y/scale, 0))

        content_fit_center_matrix = content_fit_matrix * center_content_matrix
        return content_fit_center_matrix

    def get_canvas_view(self)->glm.mat4:
        return self.content_fit_center_matrix() * self.interactive_pan_and_zoom # update view_2d

    def _project(self, point: glm.vec3) -> glm.vec3:
        assert len(point) in (2, 3), f"point must be of length 2 or 3, got {len(point)}"
        if len(point)==2:
            point = glm.vec3(*point, 0)
        else:
            point = glm.vec3(*point)
            
        widget_rect = (self.pos.x, self.pos.y, self.size.x, self.size.y)
        if self.use_camera:
            P1 = glm.project(point, self.camera_view_matrix, self.camera_projection_matrix, widget_rect)
            return imgui.ImVec2(P1.x, P1.y)
        else:
            P1 = glm.project(point, self.get_canvas_view(), self.get_canvas_projection(), widget_rect)
            return imgui.ImVec2(P1.x, P1.y)

    def _unproject(self, screen_point: glm.vec3) -> glm.vec3:
        assert len(screen_point) in (2,3), f"screen_point must be of length 2 or 3, got {len(screen_point)}"
        if len(screen_point)==2:
            screen_point = glm.vec3(*screen_point, 0)

        widget_rect = (self.pos.x, self.pos.y, self.size.x, self.size.y)
        if self.use_camera:
            P1 = glm.unProject(screen_point, self.camera_view_matrix, self.camera_projection_matrix, widget_rect)
            return P1
        else:
            P1 = glm.unProject(screen_point, self.get_canvas_view(), self.get_canvas_projection(), widget_rect)
            return P1


##########################
# viewer imgui interface #
##########################
# note: imgui itself is a stateful library.

from collections import defaultdict
viewers:dict[int|str, ViewerWidget] = dict()
current_viewer_name:str|None = None

def begin_viewer(name: str, 
                 content_size: imgui.ImVec2, 
                 size:imgui.ImVec2=None,
                 coordinate_system:Literal['top-left', 'bottom-left']='bottom-left'
                 )->bool:
    """
    note: call begin_scene after begin_viewer regardless of the return value. just like imgui.begin_child.
    """

    global viewers, current_viewer_name
    assert current_viewer_name is None, "Nested begin_viewer calls are not supported."
    if size is None:
        size = imgui.ImVec2(-1,-1)

    # TODO: implement object_fit modes

    # TODO: enforce minimum widget size?
    # widget_screen_pos = imgui.get_window_pos()
    # widget_size = imgui.get_content_region_avail()
    # if widget_size.x < 16:
    #     widget_size.x = 16
    # if widget_size.y < 16:
    #     widget_size.y = 16

    ret = imgui.begin_child(name, size, 
        imgui.ChildFlags_.borders,
        imgui.WindowFlags_.no_scrollbar | imgui.WindowFlags_.no_scroll_with_mouse
    )

    current_viewer_name = name
    if name not in viewers:
        viewers[name] = ViewerWidget(content_size, coordinate_system)

    # update viewport info
    current_viewport = viewers[current_viewer_name]
    current_viewport.pos = imgui.get_window_pos()
    current_viewport.size = imgui.get_window_size()
    current_viewport.content_size = content_size
    current_viewport.coordinate_system = coordinate_system

    # Pan and Zoom handling
    imgui.set_cursor_screen_pos(imgui.get_window_pos())
    io = imgui.get_io()

    if imgui.is_key_down(imgui.Key.mod_alt):
        button_flags = imgui.ButtonFlags_.mouse_button_left
    else:
        button_flags = imgui.ButtonFlags_.mouse_button_middle
    
    imgui.set_next_item_allow_overlap()
    imgui.invisible_button("viewport_button",
                        imgui.get_window_size(), 
                        button_flags)

    
    window_hovered = imgui.is_window_hovered(imgui.HoveredFlags_.child_windows)
    imgui.is_any_item_focused()
    if imgui.is_item_active():
        mouse_world_before = current_viewport._unproject(io.mouse_pos_prev)
        
        mouse_world_after = current_viewport._unproject(io.mouse_pos)
        offset = glm.vec3(mouse_world_before.x - mouse_world_after.x, mouse_world_before.y - mouse_world_after.y, 0)
        current_viewport.interactive_pan_and_zoom = glm.translate(current_viewport.interactive_pan_and_zoom, -offset)

    elif window_hovered and not imgui.is_any_item_active() and not imgui.is_any_item_focused() and math.fabs(imgui.get_io().mouse_wheel) > 0.0:
        # Zooming
        zoom_speed = 0.1
        scale = 1.0
        mouse_wheel = io.mouse_wheel
        scale_factor = 1.0 + mouse_wheel * zoom_speed
        scale *= scale_factor

        mouse_world_before = current_viewport._unproject(io.mouse_pos_prev)
        
        # Apply scale
        current_viewport.interactive_pan_and_zoom = glm.scale(current_viewport.interactive_pan_and_zoom, glm.vec3(scale_factor, scale_factor, 1.0))
        mouse_world_after = current_viewport._unproject(io.mouse_pos)

        # keep the mouse position fixed in world space during zoom
        offset = glm.vec3(mouse_world_before.x - mouse_world_after.x, mouse_world_before.y - mouse_world_after.y, 0)
        current_viewport.interactive_pan_and_zoom = glm.translate(current_viewport.interactive_pan_and_zoom, -offset)

    imgui.set_cursor_pos(imgui.get_style().window_padding)
    imgui.new_line() # let some room for the viewer name
    return ret

def end_viewer():
    global viewers, current_viewer_name
    current_viewport = viewers[current_viewer_name]

    # draw content area margins
    style = imgui.get_style()
    draw_list = imgui.get_window_draw_list()

    viewport_tl = current_viewport.pos
    viewport_br = current_viewport.pos + current_viewport.size
    
    content_screen_tl = current_viewport._project( (0,0,0))
    content_screen_br = current_viewport._project( (current_viewport.content_size.x, current_viewport.content_size.y, 0))
    if current_viewport.coordinate_system == 'bottom-left':
        # flip Y for margin drawing
        content_screen_tl.y, content_screen_br.y = content_screen_br.y, content_screen_tl.y

    draw_list.add_rect(content_screen_tl, content_screen_br, imgui.color_convert_float4_to_u32(get_viewer_style().margin_stroke_color), thickness=1.0)

    # Top rectangle
    draw_list.add_rect_filled(
        imgui.ImVec2(viewport_tl.x, viewport_tl.y),
        imgui.ImVec2(viewport_br.x, content_screen_tl.y),
        imgui.color_convert_float4_to_u32(get_viewer_style().margin_fill_color)
    )
    # Bottom rectangle
    draw_list.add_rect_filled(
        imgui.ImVec2(viewport_tl.x, content_screen_br.y),
        imgui.ImVec2(viewport_br.x, viewport_br.y),
        imgui.color_convert_float4_to_u32(get_viewer_style().margin_fill_color)
    )
    # Left rectangle
    draw_list.add_rect_filled(
        imgui.ImVec2(viewport_tl.x, content_screen_tl.y),
        imgui.ImVec2(content_screen_tl.x, content_screen_br.y),
        imgui.color_convert_float4_to_u32(get_viewer_style().margin_fill_color)
    )
    # Right rectangle
    draw_list.add_rect_filled(
        imgui.ImVec2(content_screen_br.x, content_screen_tl.y),
        imgui.ImVec2(viewport_br.x, content_screen_br.y),
        imgui.color_convert_float4_to_u32(get_viewer_style().margin_fill_color)
    )

    # display viewport info
    style = imgui.get_style()
    x, y = current_viewport.pos.x, current_viewport.pos.y
    w, h = current_viewport.size.x, current_viewport.size.y
    imgui.set_cursor_pos(style.window_padding)
    imgui.push_style_color(imgui.Col_.text, style.color_(imgui.Col_.text_disabled))
    imgui.text(f"{current_viewer_name} — @({x:.0f}, {y:.0f}) — {w:.0f}×{h:.0f}px")
    
    screen_tl = current_viewport._project((0,0,0))  # force update of widget rect in project function
    screen_br = current_viewport._project((current_viewport.content_size.x, current_viewport.content_size.y, 0))  # force update of widget rect in project function

    text = f"{current_viewport.content_size.x:.0f}×{current_viewport.content_size.y:.0f}px"
    text_size = imgui.calc_text_size(text)
    imgui.set_cursor_screen_pos(screen_br-text_size)
    imgui.text(text)
    imgui.pop_style_color()

    # end viewport widget
    current_viewer_name = None
    imgui.end_child()

def _clip_line(A: glm.vec3, B: glm.vec3, view: glm.mat4, near, far):
    """Clip a line against the near plane in camera space, return world-space endpoints.
    A, B: world-space endpoints of the line
    view: camera view matrix
    near, far: near and far plane distances
    """
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

def guide(P:imgui.ImVec2Like, Q:imgui.ImVec2Like, color:imgui.ImVec4=None, 
          front_head_shape:Literal['', '>', '<', 'o']='',
          back_head_shape:Literal['', '>', '<', 'o']=''
    ):
    if not isinstance(color, imgui.ImVec4) and color is not None:
        raise TypeError(f"color must be of type imgui.ImVec4 or None, got: {color}")
    
    if color is None:
        style = imgui.get_style()
        color = get_viewer_style().GUIDE_COLOR
    

    global viewers, current_viewer_name
    current_viewport = viewers[current_viewer_name]

    if len(P) not in (2,3):
        raise ValueError(f"A must be of length 2 or 3, got {len(P)}")
    if len(Q) not in (2,3):
        raise ValueError(f"B must be of length 2 or 3, got {len(Q)}")

    if len(Q) == 2:
        Q = glm.vec3(Q[0], Q[1], 0)
    else:
        Q = glm.vec3(Q[0], Q[1], Q[2])

    if len(P) == 2:
        P = glm.vec3(P[0], P[1], 0)
    else:
        P = glm.vec3(P[0], P[1], P[2])
    # clip line against near plane if using camera
    if current_viewport.use_camera:
        near = 0.1  # TODO: get from camera
        far = 100.0
        clipped = _clip_line(P, Q, current_viewport.camera_view_matrix, near, far)
        if clipped is None:
            return
        P, Q = clipped

    # project points
    P = current_viewport._project(P)
    Q = current_viewport._project(Q)

    # draw line
    draw_list = imgui.get_window_draw_list()
    draw_list.add_line(P, Q, imgui.color_convert_float4_to_u32(color))

    # draw line head front
    dir = glm.vec2(Q.x, Q.y) - glm.vec2(P.x, P.y)
    dir = glm.normalize(dir)
    head_size = 12.0
    perp = glm.vec2(-dir.y, dir.x) * (head_size * 0.5)

    match front_head_shape:
        case '>':
            A = imgui.ImVec2(Q.x - dir.x * head_size + perp.x, Q.y - dir.y * head_size + perp.y)
            B = imgui.ImVec2(Q.x, Q.y)
            C = imgui.ImVec2(Q.x - dir.x * head_size - perp.x, Q.y - dir.y * head_size - perp.y)
            draw_list.add_line(A,B,imgui.color_convert_float4_to_u32(color))
            draw_list.add_line(C,B,imgui.color_convert_float4_to_u32(color))
            draw_list.add_triangle_filled(A, B, C, imgui.color_convert_float4_to_u32(color))
        case _:
            pass


    # draw line head back (backwards arrow)
    match back_head_shape:
        case '>':
            draw_list.add_line(
                imgui.ImVec2(P.x - dir.x * head_size + perp.x, P.y - dir.y * head_size + perp.y),
                P,
                imgui.color_convert_float4_to_u32(color)
            )
            draw_list.add_line(
                imgui.ImVec2(P.x - dir.x * head_size - perp.x, P.y - dir.y * head_size - perp.y),
                P,
                imgui.color_convert_float4_to_u32(color)
            )

def axes(length:float=1.0, thickness:float=1.0):
    global viewers, current_viewer_name
    current_viewport = viewers[current_viewer_name]

    origin = glm.vec3(0,0,0)
    x_axis = glm.vec3(length,0,0)
    y_axis = glm.vec3(0,length,0)
    z_axis = glm.vec3(0,0,length)

    O_screen = current_viewport._project(origin)
    X_screen = current_viewport._project(x_axis)
    draw_list = imgui.get_window_draw_list()
    draw_list.add_line(O_screen, X_screen, imgui.color_convert_float4_to_u32(get_viewer_style().AXIS_COLOR_X), thickness)

    Y_screen = current_viewport._project(y_axis)
    draw_list.add_line(O_screen, Y_screen, imgui.color_convert_float4_to_u32(get_viewer_style().AXIS_COLOR_Y), thickness)

    Z_screen = current_viewport._project(z_axis)
    draw_list.add_line(O_screen, Z_screen, imgui.color_convert_float4_to_u32(get_viewer_style().AXIS_COLOR_Z), thickness)

    draw_list.add_circle(O_screen, 5.0, imgui.color_convert_float4_to_u32(get_viewer_style().CONTROL_POINT_COLOR))

def _cast_ray(
    pos: glm.vec2, 
    view_matrix: glm.mat4, 
    projection_matrix: glm.mat4, 
    viewport: glm.vec4
) -> Tuple[glm.vec3, glm.vec3]:
    """
    Cast a ray from the camera through a pixel in screen space.
    returns the ray origin and target.
    
    Args:
        screen_x: X coordinate in pixel space
        screen_y: Y coordinate in pixel space
        view_matrix: Camera view matrix
        projection_matrix: Camera projection matrix
        viewport: Viewport (x, y, width, height)
    """

    ray_origin = glm.unProject(
        glm.vec3(pos.x, pos.y, 0.0),
        view_matrix, projection_matrix, viewport
    )

    ray_target = glm.unProject(
        glm.vec3(pos.x, pos.y, 1.0),
        view_matrix, projection_matrix, viewport
    )

    ray_direction = glm.normalize(ray_target - ray_origin)

    return ray_origin, ray_direction

def horizon_line(color:int=None, ground:Literal['xz', 'xy', 'yz']='xz'):
    """Draw the horizon line in the current viewer scene.
    note: current implementation draws a line at a large (but not infinite) distance on the XZ plane.
    """
    #todo: draw infinite line by: eg.: intersecting with near plane, or by using the view direction and up vector to compute the line in screen space directly.
    at_distance:float=10000.0
    if color is None:
        style = imgui.get_style()
        color = imgui.ImVec4(get_viewer_style().HORIZON_LINE_COLOR)

    global viewers, current_viewer_name
    current_viewer = viewers[current_viewer_name]

    if current_viewer is None:
        logging.warning("horizon_line: no current viewer")
        return
    
    if current_viewer.use_camera is False:
        logging.warning("horizon_line: current viewer is not using a camera. Must call _begin_scene_ first")
        return
    
    view = current_viewer.camera_view_matrix
    projection = current_viewer.camera_projection_matrix

    # horizon
    left_origin, left_direction = _cast_ray(
        imgui.ImVec2(0, current_viewer.content_size.y/2), 
        view, 
        projection,
        (0,0,current_viewer.content_size.x, current_viewer.content_size.y)
    )
    right_origin, right_direction = _cast_ray(
        imgui.ImVec2(current_viewer.content_size.x, current_viewer.content_size.y/2), 
        view, 
        projection,
        (0,0,current_viewer.content_size.x, current_viewer.content_size.y)
    )

    match ground:
        case 'xz':
            left_direction.y = 0
            right_direction.y = 0
        case 'xy':
            left_direction.z = 0
            right_direction.z = 0
        case 'yz':
            left_direction.x = 0
            right_direction.x = 0
        case _:
            raise ValueError(f"ground must be one of 'xz', 'xy', 'yz', got: {ground}")
    left_direction = glm.normalize(left_direction) * at_distance
    right_direction = glm.normalize(right_direction) * at_distance

    guide(left_direction, right_direction, color)

def begin_scene(projection:glm.mat4, view:glm.mat4):
    """
    Begin a 3D scene with given projection and view matrices.
    The projection and view matrices are adjusted to account for the viewport's overscan.
    example:
        begin_scene(glm.perspective(glm.radians(60.0), 1.0, 0.1, 100.0), glm.lookAt(glm.vec3(10,10,10), glm.vec3(0,0,0), glm.vec3(0,1,0)))

        camera.setAspectRatio(viewer_content_size.x / viewer_content_size.y)
        begin_scene(camera.projectionMatrix(), camera.viewMatrix())
    """
    global viewers, current_viewer_name
    current_viewport = viewers[current_viewer_name]
    assert current_viewport.use_camera is False, "Nested begin_scene calls are not supported."

    content_screen_tl = current_viewport._project( (0, 0, 0))
    content_screen_br = current_viewport._project( (current_viewport.content_size.x, current_viewport.content_size.y, 0))
    if current_viewport.coordinate_system == 'bottom-left':
        # flip Y for margin drawing
        content_screen_tl.y, content_screen_br.y = content_screen_br.y, content_screen_tl.y

    viewport_tl = current_viewport.pos
    viewport_br = current_viewport.pos + current_viewport.size

    # flip Y
    projection = glm.mat4(projection)
    match current_viewport.coordinate_system:
        case 'bottom-left':
            pass
        case 'top-left':
            ...
            projection[1][1] *= -1

    projection = overscan_projection(projection,
        glm.vec2(content_screen_tl.x, content_screen_tl.y),
        glm.vec2(content_screen_br.x, content_screen_br.y),
        glm.vec2(viewport_tl.x, viewport_tl.y),
        glm.vec2(viewport_br.x, viewport_br.y)
    )
    current_viewport.camera_projection_matrix = projection
    current_viewport.camera_view_matrix = view
    assert current_viewport.use_camera is False
    current_viewport.use_camera = True

    return True

def end_scene():
    """End the current 3D scene."""
    global viewers, current_viewer_name
    current_viewport = viewers[current_viewer_name]
    assert current_viewport.use_camera is True
    current_viewport.use_camera = False

def _get_screen_coords(point: imgui.ImVec2Like | Tuple[float, float, float]) -> imgui.ImVec2:
    """Project a 3D point to 2D screen space in the current viewer."""
    if len(point) not in (2,3):
        raise ValueError(f"point must be of length 2 or 3, got {len(point)}")
    
    global viewers, current_viewer_name
    current_viewport = viewers[current_viewer_name]
    if len(point) == 2:
        point = (point[0], point[1], 0.0)
    return current_viewport._project(point)

def _get_window_coords(point: imgui.ImVec2Like | Tuple[float, float, float]) -> imgui.ImVec2:
    """Project a 3D point to 2D window space in the current viewer."""
    if len(point) not in (2,3):
        raise ValueError(f"point must be of length 2 or 3, got {len(point)}")
    global viewers, current_viewer_name
    current_viewport = viewers[current_viewer_name]
    if len(point) == 2:
        point = (point[0], point[1], 0.0)
    screen_pos = current_viewport._project(point)
    window_pos = imgui.get_window_pos()
    return imgui.ImVec2(screen_pos.x - window_pos.x, screen_pos.y - window_pos.y)

def control_point(label:str, point:imgui.ImVec2Like, *, color:int=None)->Tuple[bool, imgui.ImVec2Like]:
    if color is None:
        color = get_viewer_style().CONTROL_POINT_COLOR

    # project the point to world coordinates
    P = _get_screen_coords(point)  # ensure widget rect is updated

    # invisible button to handle interaction
    btn_size = imgui.ImVec2(28,28)
    store_cursor_pos = imgui.get_cursor_pos()
    imgui.set_cursor_screen_pos(imgui.ImVec2(P.x, P.y)-btn_size/2)
    imgui.invisible_button(label, btn_size)

    # draw the point
    draw_list = imgui.get_window_draw_list()
    text_offset = imgui.ImVec2(5, -5)
    radius=3
    if imgui.is_item_hovered() or imgui.is_item_active():
        draw_list.add_circle_filled(P, radius+1, imgui.color_convert_float4_to_u32(color), num_segments=0)
        text = f"{label}".split("##")[0]
        text += f"({point.x:.0f},{point.y:.0f})"
        draw_list.add_text(P + text_offset, imgui.color_convert_float4_to_u32(color), text)
    else:
        draw_list.add_circle_filled(P, radius, imgui.color_convert_float4_to_u32(color), num_segments=8)

    # handle dragging
    if imgui.is_item_active():
        # Compute world-space movement
        current_viewport = viewers[current_viewer_name]
        io = imgui.get_io()
        mouse_world_pos_prev = current_viewport._unproject(io.mouse_pos_prev)  # ensure widget rect is updated
        mouse_world_pos = current_viewport._unproject(io.mouse_pos)  # ensure widget rect is updated
        world_space_delta = mouse_world_pos - mouse_world_pos_prev

        # Apply movement to the point
        if math.fabs(world_space_delta.x) > 0.0 or math.fabs(world_space_delta.y) > 0.0:
            imgui.reset_mouse_drag_delta()
            new_point = type(point)(point.x, point.y)
            new_point.x += world_space_delta.x
            new_point.y += world_space_delta.y
            return True, new_point

    imgui.set_cursor_pos(store_cursor_pos)
    return False, point

def set_cursor_to_point(point: imgui.ImVec2Like | Tuple[float, float, float]):
    """Set the imgui cursor position to the projected position of the given 3D point in the current viewer."""
    P = _get_screen_coords(point)
    imgui.set_cursor_screen_pos(P)

if __name__ == "__main__":
    from imgui_bundle import immapp
    from pylive.glrenderer.utils.camera import Camera
    def touch_pad(label:str, size:imgui.ImVec2=imgui.ImVec2(64,64))->Tuple[bool, imgui.ImVec2]:
        """A simple touch pad that returns the drag delta when active."""
        imgui.button(label, size)
        if imgui.is_item_active():
            delta = imgui.get_mouse_drag_delta(lock_threshold=0.0)
            imgui.reset_mouse_drag_delta()
            if math.fabs(delta.x) < 1e-6 and math.fabs(delta.y) < 1e-6:
                return False, imgui.ImVec2(0,0)

            return True, delta
        else:
            return False, imgui.ImVec2(0,0)

    camera = Camera().setPosition(glm.vec3(1,1,5)).lookAt(glm.vec3(0,0,0), glm.vec3(0,1,0))
    CONTENT_SIZE = [256,256]

    from pathlib import Path
    CP_POS = glm.vec2(50,50)
    COORD_SYS_OPTIONS = ["top-left", "bottom-left"]
    CURRENT_SYS_INDEX = 0
    def gui():
        imgui.text(f"camera position: {camera.getPosition()}")
        global CONTENT_SIZE, CP_POS, CURRENT_SYS_INDEX
        _, CONTENT_SIZE = imgui.slider_int2("Canvas Size", CONTENT_SIZE, 64, 512)
        
        _, CURRENT_SYS_INDEX = imgui.combo("Projection", CURRENT_SYS_INDEX, COORD_SYS_OPTIONS)
        _, delta = touch_pad("Orbit Camera", imgui.ImVec2(128,128))
        if _:
            speed = 0.25
            camera.orbit(-delta.x * speed, -delta.y * speed)
        if imgui.is_item_hovered() and math.fabs(imgui.get_io().mouse_wheel) > 0.0:
            zoom_speed = 0.2
            mouse_wheel = imgui.get_io().mouse_wheel
            camera.dolly(-mouse_wheel * zoom_speed, glm.vec3(0,0,0))

        if begin_viewer("viewport1", 
                        content_size=imgui.ImVec2(CONTENT_SIZE[0], CONTENT_SIZE[1]), 
                        size=imgui.ImVec2(-1,-1),
                        coordinate_system=COORD_SYS_OPTIONS[CURRENT_SYS_INDEX]
                        ):
            # 2d grid
            for A, B in make_gridXY_lines(step=10, size=30):
                guide(A, B, imgui.ImVec4(1,1,1,0.3))
            axes(length=100.0)
            _, CP_POS = control_point("CP##1", CP_POS, color=imgui.ImVec4(1,1,0,1))
            set_cursor_to_point(CP_POS)
            imgui.button("imgui button positioned in the viewer")

            # 3d scene
            camera.setAspectRatio(float(CONTENT_SIZE[0])/float(CONTENT_SIZE[1]))
            if begin_scene(camera.projectionMatrix(), camera.viewMatrix()):
                for A, B in make_gridXZ_lines(step=1, size=10):
                    guide(A, B)
                axes(length=1.0)
                set_cursor_to_point((0,0,0))
                imgui.text("imgui.text at (0,0,0) in 3D space")
                end_scene()

        end_viewer()
        

    immapp.run(gui, window_size=(1024,768), window_title="Viewport Demo")

