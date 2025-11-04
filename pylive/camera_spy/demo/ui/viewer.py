import math
from imgui_bundle import imgui
from typing import TypeVar, Tuple, List
import glm
import numpy as np
import colors
from typing import Tuple, Literal, Iterable


def make_ortho(xmin:float, ymin:float, xmax:float, ymax:float, near:float=-1.0, far:float=1.0):
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
        projection = glm.ortho(0.0, float(content_width), 0.0-top_margin, proj_h-top_margin, near, far)
    else:
        # viewport is wider -> expand world width, center original canvas horizontally
        proj_w = float(content_height) * float(widget_aspect)
        left_margin = (proj_w - float(content_width)) * 0.5
        projection = glm.ortho(0.0-left_margin, proj_w-left_margin, 0.0, float(content_height), near, far)

    return projection, near, far

def make_perspective_projection(fovy, canvas_tl, canvas_br, widget_tl, widget_br, near=0.1, far=100.0)->glm.mat4:
    principal = canvas_tl/2 + canvas_br/2
    canvas_width = canvas_br.x - canvas_tl.x
    canvas_height = canvas_br.y - canvas_tl.y
    canvas_aspect = canvas_width / canvas_height
    widget_width = widget_br.x - widget_tl.x
    widget_height = widget_br.y - widget_tl.y
    # widget_aspect = widget_width / widget_height

    # calculate ndc frustum for the canvas
    projection = glm.perspective(fovy, canvas_aspect, near, far)
    # flip the projection Y to match imgui coords

    # ndc_canvas_top = near * math.tan(fovy / 2)
    # ndc_canvas_bottom = -ndc_canvas_top
    # fovx = fovy * canvas_aspect
    # ndc_canvas_left = - near * math.tan(fovx / 2)
    # ndc_canvas_right = -ndc_canvas_left

    # # imgui.text(f"{ndc_canvas_left:.2f} {ndc_canvas_right:.2f} {ndc_canvas_top:.2f} {ndc_canvas_bottom:.2f}")
    # # return glm.frustum(ndc_canvas_left, ndc_canvas_right, ndc_canvas_bottom, ndc_canvas_top, near, far)

    # # overscan frustrum for the widget
    # ndc_widget_top =    ndc_canvas_top *    (widget_tl.y - principal.y) / (canvas_tl.y - principal.y)
    # ndc_widget_bottom = ndc_canvas_bottom * (widget_br.y - principal.y) / (canvas_br.y - principal.y)
    # ndc_widget_left =   ndc_canvas_left *   (widget_tl.x - principal.x) / (canvas_tl.x - principal.x)
    # ndc_widget_right =  ndc_canvas_right *  (widget_br.x - principal.x) / (canvas_br.x - principal.x)

    # projection = glm.frustum(ndc_widget_left, ndc_widget_right, ndc_widget_bottom, ndc_widget_top, near, far)
    projection = overscan_projection(projection,
                                  glm.vec2(canvas_tl.x, canvas_tl.y),
                                  glm.vec2(canvas_br.x, canvas_br.y),
                                  glm.vec2(widget_tl.x, widget_br.y), # flip Y
                                  glm.vec2(widget_br.x, widget_tl.y),
                                  near, far)
    projection[1][1] *= -1
    return projection

def _project(point:Iterable[int|float], projection:glm.mat4, view:glm.mat4, widget_rect:Tuple[int, int, int, int])->imgui.ImVec2Like:
    assert len(point) == 2 or len(point) == 3

    match len(point):
        case 2:
            P = glm.project(glm.vec3(*point,0), view, projection, widget_rect)
            return imgui.ImVec2(P.x, P.y)
        case 3:
            P = glm.project(glm.vec3(*point), view, projection, widget_rect)
            return imgui.ImVec2(P.x, P.y)
        case _:
            raise ValueError("point must be of length 2 or 3")

def _unproject(screen_point:imgui.ImVec2Like, projection:glm.mat4, view:glm.mat4, widget_rect:Tuple[int, int, int, int])->imgui.ImVec2Like:
    P = glm.unProject(glm.vec3(screen_point.x, screen_point.y, 0), view, projection, widget_rect)
    return imgui.ImVec2(P.x, P.y)

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

from pylive.glrenderer.utils.camera import Camera
class ViewerWidget:
    def __init__(self, content_size:imgui.ImVec2):
        # canvas size in pixels (aka viewport?)
        self.content_size = content_size

        # 2D view
        self.view_2d = glm.identity(glm.mat4)
        self.projection_2d = glm.identity(glm.mat4)

        # 3D view
        self.use_camera:bool = False
        self.camera_view_matrix = glm.identity(glm.mat4)
        self.projection_view_matrix = glm.perspective(glm.radians(60.0), float(content_size.x)/float(content_size.y), 0.1, 100.0)
        
        # updated every frame on begin_viewport
        self.pos:imgui.ImVec2 = None
        self.size:imgui.ImVec2 = None

    def project(self, point: glm.vec3) -> glm.vec3:
        widget_rect = (self.pos.x, self.pos.y, self.size.x, self.size.y)
        # widget_rect = flip_widget_rect_y(widget_rect)
        if self.use_camera:
            return _project(point, 
                            self.projection_view_matrix, 
                            self.camera_view_matrix,
                             widget_rect=widget_rect
                            )
        else:
            return _project(point, 
                            self.projection_2d, 
                            self.view_2d,
                            widget_rect=widget_rect
                            )

    def unproject(self, point: glm.vec3) -> glm.vec3:
        widget_rect = (self.pos.x, self.pos.y, self.size.x, self.size.y)
        # widget_rect = flip_widget_rect_y(widget_rect)
        if self.use_camera:
            return _unproject(point, self.projection_view_matrix, self.camera_view_matrix, widget_rect)
        else:
            return _unproject(point, self.projection_2d, self.view_2d, widget_rect)
        
from collections import defaultdict
viewports:dict[int|str, ViewerWidget] = dict()
current_viewport_name:str|None = None

def begin_viewport(name: str, content_size: imgui.ImVec2, size:imgui.ImVec2=None, *, object_fit:Literal['none','contain', 'cover', 'fill']='none'):

    if size is None:
        size = imgui.ImVec2(-1,-1)

    # widget_screen_pos = imgui.get_window_pos()
    # widget_size = imgui.get_content_region_avail()
    # if widget_size.x < 16:
    #     widget_size.x = 16
    # if widget_size.y < 16:
    #     widget_size.y = 16

    imgui.begin_child(name, size, 
        imgui.ChildFlags_.borders,
        imgui.WindowFlags_.no_scrollbar | imgui.WindowFlags_.no_scroll_with_mouse
    )
    global viewports, current_viewport_name
    current_viewport_name = name
    if name not in viewports:
        viewports[name] = ViewerWidget(content_size)

    # update viewport info
    current_viewport = viewports[current_viewport_name]
    current_viewport.pos = imgui.get_window_pos()
    current_viewport.size = imgui.get_window_size()
    current_viewport.content_size = content_size

    # Setup 2D projection with overscan
    projection_2d = glm.ortho(
        0, #left
        current_viewport.content_size.x, #right
        0, #bottom
        current_viewport.content_size.y, #top
        -1.0, #near
        1.0 #far
    )

    x, y = current_viewport.pos.x, current_viewport.pos.y
    w, h = current_viewport.size.x, current_viewport.size.y
    projection_2d = overscan_projection(projection_2d,
        glm.vec2(0,0),
        glm.vec2(float(current_viewport.content_size.x), float(current_viewport.content_size.y)),
        glm.vec2(0, 0),
        glm.vec2(w, h),
    )
    current_viewport.projection_2d = projection_2d
    
    # Pan and Zoom handling
    imgui.set_cursor_screen_pos(imgui.get_window_pos())
    io = imgui.get_io()

    if imgui.is_key_down(imgui.Key.mod_alt):
        button_flags = imgui.ButtonFlags_.mouse_button_left
    else:
        button_flags = imgui.ButtonFlags_.mouse_button_middle
    imgui.invisible_button("viewport_button",
                           imgui.get_window_size(), 
                           button_flags)
    io = imgui.get_io()
    zoom_speed = 0.1
    
    if imgui.is_item_active():
        # Panning
        pan_speed = 1.0
        translation = glm.vec3(0,0,0)        
        prev_world = current_viewport.unproject(io.mouse_pos_prev)
        curr_world = current_viewport.unproject(io.mouse_pos)
        world_space_delta = curr_world - prev_world
        translation.x += world_space_delta.x * pan_speed
        translation.y += world_space_delta.y * pan_speed

        # Apply translationto the view matrix
        new_view = glm.translate(current_viewport.view_2d, translation)
        current_viewport.view_2d = new_view

    elif imgui.is_item_hovered() and math.fabs(imgui.get_io().mouse_wheel) > 0.0:
        # Zooming        
        scale = 1.0
        mouse_wheel = io.mouse_wheel
        scale_factor = 1.0 + mouse_wheel * zoom_speed
        scale *= scale_factor
        mouse_world_before = current_viewport.unproject(io.mouse_pos)
        current_viewport.view_2d = glm.scale(current_viewport.view_2d, glm.vec3(scale, scale, scale))
        # Keep mouse position fixed in world space
        mouse_world_after = current_viewport.unproject(io.mouse_pos) # Unproject mouse position after scaling
        offset = glm.vec3(mouse_world_before.x - mouse_world_after.x, mouse_world_before.y - mouse_world_after.y, 0)
        current_viewport.view_2d = glm.translate(current_viewport.view_2d, -offset)

def end_viewport():
    global viewports, current_viewport_name
    current_viewport = viewports[current_viewport_name]

    # draw content area margins
    draw_list = imgui.get_window_draw_list()
    content_screen_tl = current_viewport.project( (0,0))
    content_screen_br = current_viewport.project( (current_viewport.content_size.x, current_viewport.content_size.y))
    draw_list.add_rect(content_screen_tl, content_screen_br, colors.YELLOW_DIMMED, thickness=1.0)

    # display viewport info
    style = imgui.get_style()
    x, y = current_viewport.pos.x, current_viewport.pos.y
    w, h = current_viewport.size.x, current_viewport.size.y
    imgui.set_cursor_pos(style.window_padding)
    imgui.text(f"{current_viewport_name} — @({x:.0f}, {y:.0f}) — {w:.0f}×{h:.0f}px")

    screen_tl = current_viewport.project((0,0))  # force update of widget rect in project function
    screen_br = current_viewport.project((current_viewport.content_size.x, current_viewport.content_size.y))  # force update of widget rect in project function
    
    text = f"{current_viewport.content_size.x:.0f}×{current_viewport.content_size.y:.0f}px"
    text_size = imgui.calc_text_size(text)
    imgui.set_cursor_screen_pos(screen_br-text_size-style.window_padding)
    imgui.text(text)

    

    
    # end viewport widget
    current_viewport_name = None
    imgui.end_child()

def guide(A, B, color=colors.YELLOW_DIMMED):
    global viewports, current_viewport_name
    current_viewport = viewports[current_viewport_name]

    A_screen = current_viewport.project(A)
    B_screen = current_viewport.project(B)

    draw_list = imgui.get_window_draw_list()
    draw_list.add_line(A_screen, B_screen, color)

def axes(length:float=1.0):
    global viewports, current_viewport_name
    current_viewport = viewports[current_viewport_name]

    origin = glm.vec3(0,0,0)
    x_axis = glm.vec3(length,0,0)
    y_axis = glm.vec3(0,length,0)
    z_axis = glm.vec3(0,0,length)

    A_screen = current_viewport.project(origin)
    B_screen = current_viewport.project(x_axis)
    draw_list = imgui.get_window_draw_list()
    draw_list.add_line(A_screen, B_screen, colors.RED, 3.0)

    B_screen = current_viewport.project(y_axis)
    draw_list.add_line(A_screen, B_screen, colors.GREEN, 3.0)

    B_screen = current_viewport.project(z_axis)
    draw_list.add_line(A_screen, B_screen, colors.BLUE, 3.0)

def begin_scene_old(fovy:float, position:glm.vec3, target:glm.vec3, up:glm.vec3=glm.vec3(0,1,0), near=0.1, far=100.0):
    global viewports, current_viewport_name
    current_viewport = viewports[current_viewport_name]

    content_screen_tl = current_viewport.project( (0,0))
    content_screen_br = current_viewport.project( (current_viewport.content_size.x, current_viewport.content_size.y))
    viewport_tl = current_viewport.pos
    viewport_br = current_viewport.pos + current_viewport.size

    projection_3d = make_perspective_projection(
        fovy,
        glm.vec2(content_screen_tl.x, content_screen_tl.y),
        glm.vec2(content_screen_br.x, content_screen_br.y),
        glm.vec2(viewport_tl.x, viewport_br.y), # flip Y
        glm.vec2(viewport_br.x, viewport_tl.y),
        near,
        far
    )
    current_viewport.projection_view_matrix = projection_3d
    current_viewport.camera_view_matrix = glm.lookAt(position, target, up)
    assert current_viewport.use_camera is False
    current_viewport.use_camera = True

def begin_scene(projection:glm.mat4, view:glm.mat4):
    """
    Begin a 3D scene with given projection and view matrices.
    The projection and view matrices are adjusted to account for the viewport's overscan.
    example:
        begin_scene(glm.perspective(glm.radians(60.0), 1.0, 0.1, 100.0), glm.lookAt(glm.vec3(10,10,10), glm.vec3(0,0,0), glm.vec3(0,1,0)))

        camera.setAspectRatio(viewer_content_size.x / viewer_content_size.y)
        begin_scene(camera.projectionMatrix(), camera.viewMatrix())
    """
    global viewports, current_viewport_name
    current_viewport = viewports[current_viewport_name]

    content_screen_tl = current_viewport.project( (0,0))
    content_screen_br = current_viewport.project( (current_viewport.content_size.x, current_viewport.content_size.y))
    viewport_tl = current_viewport.pos
    viewport_br = current_viewport.pos + current_viewport.size

    # fli0p Y in projection to match imgui coords
    projection = glm.mat4(projection)
    projection[1][1] *= -1

    projection = overscan_projection(projection,
        glm.vec2(content_screen_tl.x, content_screen_tl.y),
        glm.vec2(content_screen_br.x, content_screen_br.y),
        glm.vec2(viewport_tl.x, viewport_tl.y),
        glm.vec2(viewport_br.x, viewport_br.y)
    )
    current_viewport.projection_view_matrix = projection
    current_viewport.camera_view_matrix = view
    assert current_viewport.use_camera is False
    current_viewport.use_camera = True

def end_scene():
    global viewports, current_viewport_name
    current_viewport = viewports[current_viewport_name]
    assert current_viewport.use_camera is True
    current_viewport.use_camera = False

if __name__ == "__main__":
    from imgui_bundle import immapp

    viewports["viewport1"] = ViewerWidget(imgui.ImVec2(800,600))
    camera = Camera().setPosition(glm.vec3(5,5,5)).lookAt(glm.vec3(0,0,0), glm.vec3(0,1,0))
    CONTENT_SIZE = [256,256]
    
    def gui():
        global CONTENT_SIZE
        imgui.begin("Window1")
        _, CONTENT_SIZE = imgui.slider_int2("Canvas Size", CONTENT_SIZE, 64, 512)
        _, delta = touch_pad("Orbit Camera", imgui.ImVec2(128,128))
        if _:
            speed = 0.25
            camera.orbit(-delta.x * speed, -delta.y * speed)
        if imgui.is_item_hovered() and math.fabs(imgui.get_io().mouse_wheel) > 0.0:
            zoom_speed = 0.2
            mouse_wheel = imgui.get_io().mouse_wheel
            camera.dolly(-mouse_wheel * zoom_speed, glm.vec3(0,0,0))
        begin_viewport("viewport1", content_size=imgui.ImVec2(CONTENT_SIZE[0], CONTENT_SIZE[1]), size=imgui.ImVec2(-1,256))
        # 2d grid
        for A, B in make_gridXY_lines(step=10, size=256):
            guide(A, B)
        axes(length=100.0)
        # 3d scene

        camera.setAspectRatio(float(CONTENT_SIZE[0])/float(CONTENT_SIZE[1]))
        begin_scene(camera.projectionMatrix(), camera.viewMatrix())
        for A, B in make_gridXZ_lines(step=1, size=10):
            guide(A, B)
        axes(length=1.0)
        end_scene()
        end_viewport()
        imgui.end()

    immapp.run(gui, window_size=(1024,768), window_title="Viewport Demo")