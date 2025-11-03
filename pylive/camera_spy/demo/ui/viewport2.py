import math
from imgui_bundle import imgui
from typing import TypeVar, Tuple, List
import glm
import numpy as np
import colors
from typing import Tuple, Literal, Iterable

def flipy(point: glm.vec3, widget_screen_pos: imgui.ImVec2, widget_size: imgui.ImVec2) -> imgui.ImVec2:
    """Convert from OpenGL Y-up coordinates to ImGui Y-down coordinates."""
    return imgui.ImVec2(point.x, 2 * widget_screen_pos.y + widget_size.y - point.y)

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

def _project(point:Iterable[int|float], projection:glm.mat4, view:glm.mat4)->imgui.ImVec2Like:
    assert len(point) == 2 or len(point) == 3

    x, y = imgui.get_window_pos()
    w, h = imgui.get_window_size()
    widget_rect = (int(x), int(y), int(w), int(h))

    match len(point):
        case 2:
            P = glm.project(glm.vec3(*point,0), view, projection, widget_rect)
            return imgui.ImVec2(P.x, P.y)
        case 3:
            P = glm.project(glm.vec3(*point), view, projection, widget_rect)
            return imgui.ImVec2(P.x, P.y)
        case _:
            raise ValueError("point must be of length 2 or 3")
            
def _unproject(screen_point:imgui.ImVec2Like, projection:glm.mat4, view:glm.mat4)->imgui.ImVec2Like:
    x, y = imgui.get_window_pos()
    w, h = imgui.get_window_size()
    widget_rect = (int(x), int(y), int(w), int(h))
    P = glm.unProject(glm.vec3(screen_point.x, screen_point.y, 0), view, projection, widget_rect)
    return imgui.ImVec2(P.x, P.y)

def _get_world_space_mouse_drag_delta(
        projection:glm.mat4, 
        view:glm.mat4,
        button: imgui.MouseButton_=0, 
        lock_threshold: float=-1
    )->imgui.ImVec2Like:
    curr_mouse_pos = imgui.get_mouse_pos()
    prev_mouse_pos = imgui.get_mouse_pos() - imgui.get_mouse_drag_delta(button, lock_threshold)
    prev_world = _unproject(prev_mouse_pos, projection, view)
    curr_world = _unproject(curr_mouse_pos, projection, view)
    world_space_delta = curr_world - prev_world
    return world_space_delta

def pan_and_zoom(
        projection:glm.mat4,
        view:glm.mat4,
        zoom_speed:float=0.1,
        pan_speed:float=1.0
    )->Tuple[bool, glm.mat4]:
    """Handle panning and zooming of the view matrix based on mouse input.
    Returns (changed:bool, new_view:glm.mat4)
    Zoom is centered around the mouse position in world space.
    """
    changed = False
    translation = glm.vec3(0,0,0)
    scale = 1.0

    mouse_screen = imgui.get_mouse_pos()
    mouse_world_before = _unproject(mouse_screen, projection, view)

    # Zooming
    mouse_wheel = imgui.get_io().mouse_wheel
    if mouse_wheel != 0.0:
        scale_factor = 1.0 + mouse_wheel * zoom_speed
        scale *= scale_factor
        changed = True

    # Panning
    if imgui.is_mouse_dragging(imgui.MouseButton_.middle) or (imgui.is_key_down(imgui.Key.left_alt) and imgui.is_mouse_dragging(imgui.MouseButton_.left)):
        drag_delta = _get_world_space_mouse_drag_delta(projection, view, imgui.MouseButton_.middle if imgui.is_mouse_dragging(imgui.MouseButton_.middle) else imgui.MouseButton_.left)
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
            old_view = view
            view = new_view
            mouse_world_after = _unproject(mouse_screen, projection, view)
            view = old_view
            # Compute translation to keep mouse_world_before == mouse_world_after
            offset = glm.vec3(mouse_world_before.x - mouse_world_after.x, mouse_world_before.y - mouse_world_after.y, 0)
            new_view = glm.translate(new_view, -offset)
        return True, new_view

    return False, view

def make_perspective_projection(fovy, canvas_tl, canvas_br, widget_tl, widget_br, near=0.1, far=100.0)->glm.mat4:
    principal = canvas_tl/2 + canvas_br/2
    canvas_width = canvas_br.x - canvas_tl.x
    canvas_height = canvas_br.y - canvas_tl.y
    canvas_aspect = canvas_width / canvas_height
    widget_width = widget_br.x - widget_tl.x
    widget_height = widget_br.y - widget_tl.y
    widget_aspect = widget_width / widget_height

    # calculate ndc frustum for the canvas
    ndc_canvas_top = near * math.tan(fovy / 2)
    ndc_canvas_bottom = -ndc_canvas_top
    fovx = fovy * canvas_aspect
    ndc_canvas_left = - near * math.tan(fovx / 2)
    ndc_canvas_right = -ndc_canvas_left

    # imgui.text(f"{ndc_canvas_left:.2f} {ndc_canvas_right:.2f} {ndc_canvas_top:.2f} {ndc_canvas_bottom:.2f}")
    # return glm.frustum(ndc_canvas_left, ndc_canvas_right, ndc_canvas_bottom, ndc_canvas_top, near, far)

    # overscan frustrum for the widget
    ndc_widget_top =    ndc_canvas_top *    (widget_tl.y - principal.y) / (canvas_tl.y - principal.y)
    ndc_widget_bottom = ndc_canvas_bottom * (widget_br.y - principal.y) / (canvas_br.y - principal.y)
    ndc_widget_left =   ndc_canvas_left *   (widget_tl.x - principal.x) / (canvas_tl.x - principal.x)
    ndc_widget_right =  ndc_canvas_right *  (widget_br.x - principal.x) / (canvas_br.x - principal.x)

    return glm.frustum(ndc_widget_left, ndc_widget_right, ndc_widget_bottom, ndc_widget_top, near, far)

def make_grid_lines(size: float = 10, step: float = 1, near: float = 0.1):
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
class ViewportState:
    def __init__(self):
        self.pan_and_zoom_matrix = glm.identity(glm.mat4)
        self.camera = Camera().setPosition(glm.vec3(5,5,5)).lookAt(glm.vec3(0,0,0), glm.vec3(0,1,0))
        self.projection_2d = glm.identity(glm.mat4)

from collections import defaultdict
viewports = defaultdict(lambda: ViewportState())
current_viewport_name:str|None = None

def begin_viewport(name: str, size:imgui.ImVec2=imgui.ImVec2(128,128)):
    global viewports, current_viewport_name
    
    current_viewport_name = name

    # widget_screen_pos = imgui.get_window_pos()
    # widget_size = imgui.get_content_region_avail()
    # if widget_size.x < 16:
    #     widget_size.x = 16
    # if widget_size.y < 16:
    #     widget_size.y = 16

    imgui.begin_child(name, size, 
        imgui.ChildFlags_.borders,
        imgui.WindowFlags_.no_scrollbar
    )
    
    # create 2d projection
    CONTENT_SIZE = imgui.ImVec2(800,600)
    projection_2d, near, far = make_ortho(0,0,float(CONTENT_SIZE.x),float(CONTENT_SIZE.y))
    viewports[current_viewport_name].projection_2d = projection_2d
    _, viewports[current_viewport_name].pan_and_zoom_matrix = pan_and_zoom(projection_2d, viewports[current_viewport_name].pan_and_zoom_matrix)
    view_2d = viewports[current_viewport_name].pan_and_zoom_matrix

def end_viewport():
    imgui.end_child() # end viewport widget

def guide(A, B):
    global viewports, current_viewport_name
    projection_2d = viewports[current_viewport_name].projection_2d
    view_2d = viewports[current_viewport_name].pan_and_zoom_matrix

    A_screen = _project( (A.x, A.z), projection_2d, view_2d)
    B_screen = _project( (B.x, B.z), projection_2d, view_2d)

    draw_list = imgui.get_window_draw_list()
    draw_list.add_line(A_screen, B_screen, colors.YELLOW_DIMMED)

if __name__ == "__main__":
    from imgui_bundle import immapp
    
    def gui():
        global viewports
        imgui.begin("window")
        _, delta = touch_pad("Touch Pad")
        viewports["viewport1"].camera.orbit(-delta.x * 0.5, -delta.y * 0.5)
        if _:
            print(f"Touch pad delta: {delta.x}, {delta.y}")
        # begin viewport widget
        
        # widget_size = imgui.ImVec2(512,512)
        widget_screen_pos = imgui.get_window_pos()
        widget_size = imgui.get_content_region_avail()
        if widget_size.x < 16:
            widget_size.x = 16
        if widget_size.y < 16:
            widget_size.y = 16

        imgui.begin_child("viewport area", widget_size, 
            imgui.ChildFlags_.borders,
            imgui.WindowFlags_.no_scrollbar
        )
        
        # create 2d projection
        CONTENT_SIZE = imgui.ImVec2(800,600)
        projection_2d, near, far = make_ortho(0,0,float(CONTENT_SIZE.x),float(CONTENT_SIZE.y))
        _, viewports["viewport1"].pan_and_zoom_matrix = pan_and_zoom(projection_2d, viewports["viewport1"].pan_and_zoom_matrix)
        view_2d = viewports["viewport1"].pan_and_zoom_matrix

        # draw 2D in content pixelspace
        draw_list = imgui.get_window_draw_list()
        content_screen_tl = _project( (0,0), projection_2d, view_2d)
        content_screen_br = _project( (CONTENT_SIZE.x, CONTENT_SIZE.y), projection_2d, view_2d)
        draw_list.add_rect(content_screen_tl, content_screen_br, colors.YELLOW, thickness=5.0)

        # 2d grid        
        for line in make_grid_lines(step=100, size=512):
            A, B = line
            A_screen = _project( (A.x, A.z), projection_2d, view_2d)
            B_screen = _project( (B.x, B.z), projection_2d, view_2d)
            draw_list.add_line(A_screen, B_screen, colors.YELLOW_DIMMED)

        # create 3d projection
        projection_3d = make_perspective_projection(
            math.radians(60.0),
            glm.vec2(content_screen_tl.x, content_screen_tl.y),
            glm.vec2(content_screen_br.x, content_screen_br.y),
            widget_screen_pos,
            widget_screen_pos + widget_size,
            near,
            far
        )

        view_3d = viewports["viewport1"].camera.viewMatrix()
        # view_3d = glm.lookAt(glm.vec3(5,5,5), glm.vec3(0,0,0), glm.vec3(0,1,0))

        # draw 3d grid
        widget_rect = widget_screen_pos.x, widget_screen_pos.y, widget_size.x, widget_size.y
        for line in make_grid_lines(step=1, size=10):
            A, B = line
            A_proj = glm.project(A, view_3d, projection_3d, glm.vec4(widget_rect))
            B_proj = glm.project(B, view_3d, projection_3d, glm.vec4(widget_rect))
            A_imgui = flipy(A_proj, widget_screen_pos, widget_size)
            B_imgui = flipy(B_proj, widget_screen_pos, widget_size)
            draw_list.add_line(A_imgui, B_imgui, colors.YELLOW_DIMMED)

        # draw 3d axis
        axis_length = 1.5
        origin = glm.vec3(0,0,0)
        axes = [
            (origin, glm.vec3(axis_length,0,0), colors.RED),
            (origin, glm.vec3(0,axis_length,0), colors.GREEN),
            (origin, glm.vec3(0,0,axis_length), colors.BLUE),
        ]
        for line in axes:
            A, B, col = line
            A_proj = glm.project(A, view_3d, projection_3d, glm.vec4(widget_rect))
            B_proj = glm.project(B, view_3d, projection_3d, glm.vec4(widget_rect))
            A_imgui = flipy(A_proj, widget_screen_pos, widget_size)
            B_imgui = flipy(B_proj, widget_screen_pos, widget_size)
            draw_list.add_line(A_imgui, B_imgui, col, thickness=3.0)

        # render_margins(imgui.ImVec2(0,0), imgui.ImVec2(view_box[2],view_box[3]))
        imgui.end_child() # end viewport widget
        imgui.end()

        imgui.begin("Viewport Demo")
        begin_viewport("viewport_demo_1", size=imgui.ImVec2(256,256))
        for A, B in make_grid_lines(step=20, size=256):
            guide(A, B)
        end_viewport()

        begin_viewport("viewport_demo_2", size=imgui.ImVec2(256,128))

        end_viewport()
        imgui.end()


    
    immapp.run(gui, window_size=(1024,768), window_title="Viewport Demo")