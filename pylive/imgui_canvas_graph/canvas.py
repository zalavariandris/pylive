# Standard library imports
import os


from pathlib import Path
from typing import Literal, Tuple, List, Iterable, Iterator, cast
import math
from pyglm import glm
# ########### #
# Application #
# ########### #
from imgui_bundle import imgui, immapp
from dataclasses import dataclass, field


global vtx0, idx0
vtx0 = 0
idx0 = 0

from typing import Iterator, Tuple

Point2 = Tuple[float, float]
Segment2 = Tuple[Point2, Point2]

def create_grid_lines(
    width: float,
    height: float,
    origin: Point2 = (0.0, 0.0),
    step: float = 1.0,
) -> Iterator[Segment2]:
    ox, oy = origin

    half_w = width / 2
    half_h = height / 2

    # Bounds
    x_min, x_max = ox - half_w, ox + half_w
    y_min, y_max = oy - half_h, oy + half_h

    # Vertical lines
    x = x_min
    while x <= x_max + 1e-9:
        yield (x, y_min), (x, y_max)
        x += step

    # Horizontal lines
    y = y_min
    while y <= y_max + 1e-9:
        yield (x_min, y), (x_max, y)
        y += step

@dataclass
class CanvasWidget:
    content_size: imgui.ImVec2
    coordinate_system: Literal['top-left', 'bottom-left']
    pan_zoom: glm.mat4 = field(default_factory=lambda: glm.identity(glm.mat4))
    window_pos: imgui.ImVec2 = field(default_factory=lambda: imgui.ImVec2(0, 0))
    window_size: imgui.ImVec2 = field(default_factory=lambda: imgui.ImVec2(0, 0))
    origin_screen: imgui.ImVec2 = field(default_factory=lambda: imgui.ImVec2(0, 0))
    vtx0: int = 0
    idx0: int = 0
    cmd0: int = 0
    _mouse_backup: imgui.ImVec2 = field(default_factory=lambda: imgui.ImVec2(0, 0))


class CanvasRegistry:
    def __init__(self):
        self.canvases:dict[int|str, CanvasWidget] = dict()
        self.current_canvas_name:str|None = None

def get_canvas_registry() -> CanvasRegistry:
    """Get the singleton CanvasRegistry instance."""
    #TODO: use better more pythonic singleton pattern
    import sys
    key = "pylive_canvas_registry"
    if key not in sys.modules:
        print("Creating CanvasRegistry singleton")
        sys.modules[key] = CanvasRegistry()
    return sys.modules[key]

def ensure_canvas(name:str, content_size:imgui.ImVec2, coordinate_system:Literal['top-left', 'bottom-left']='bottom-left'):
    if name not in get_canvas_registry().canvases:
        get_canvas_registry().canvases[name] = CanvasWidget(content_size, coordinate_system)
    get_canvas_registry().current_canvas_name = name

def get_current_canvas() -> CanvasWidget|None:
    registry = get_canvas_registry()
    if registry.current_canvas_name is None:
        return None
    
    return registry.canvases.get(registry.current_canvas_name, None)

def set_current_canvas(name:str|None):
    registry = get_canvas_registry()
    registry.current_canvas_name = name

# ---------------------------
# Transform helpers
# ---------------------------
def canvas_local_to_screen(canvas: CanvasWidget, p: imgui.ImVec2) -> imgui.ImVec2:
    v = glm.vec4(p.x, p.y, 0.0, 1.0)
    out = canvas.pan_zoom * v
    return imgui.ImVec2(canvas.origin_screen.x + out.x, canvas.origin_screen.y + out.y)

def screen_to_canvas_local(canvas: CanvasWidget, p: imgui.ImVec2) -> imgui.ImVec2:
    inv = glm.inverse(canvas.pan_zoom)
    v = glm.vec4(p.x - canvas.origin_screen.x, p.y - canvas.origin_screen.y, 0.0, 1.0)
    out = inv * v
    return imgui.ImVec2(out.x, out.y)

def get_canvas_zoom(canvas: CanvasWidget) -> float:
    # assuming uniform scale
    return float(canvas.pan_zoom[0][0])

# ---------------------------
# IO remap (the important part)
# ---------------------------

def begin_canvas_content():
    """
    Remap mouse into canvas-local space so ImGui widgets do correct hit-testing.
    Must be called AFTER begin_canvas() and BEFORE submitting widgets.
    """
    canvas = get_current_canvas()
    if canvas is None:
        return
    
    # Backup mouse pos
    io = imgui.get_io()
    canvas._mouse_backup = imgui.ImVec2(io.mouse_pos.x, io.mouse_pos.y)

    # Remap
    mouse_local = screen_to_canvas_local(canvas, io.mouse_pos)
    io.mouse_pos = mouse_local

    imgui.push_item_width(250) # for demo purposes, so slider isn't super long

def end_canvas_content():
    """Restore IO after begin_canvas_content()."""
    imgui.pop_item_width()
    canvas = get_current_canvas()
    if canvas is None:
        return

    # Restore mouse
    io = imgui.get_io()
    io.mouse_pos = canvas._mouse_backup


# ---------------------------
# Canvas widget
# ---------------------------

def begin_canvas(
        name:str, 
        content_size:imgui.ImVec2, 
        size:imgui.ImVec2|None=None, 
        coordinate_system:Literal['top-left', 'bottom-left']='bottom-left'
    )->bool:

    if size is None:
        size = imgui.ImVec2(-1, -1)

    ret = imgui.begin_child(
        name, 
        size, 
        imgui.ChildFlags_.borders,
        imgui.WindowFlags_.no_scrollbar | imgui.WindowFlags_.no_scroll_with_mouse
    )

    ensure_canvas(name, content_size, coordinate_system)
    canvas = get_current_canvas()
    if canvas is None:
        raise RuntimeError("begin_canvas: current_canvas is None after creation")
    
    canvas.window_pos = imgui.get_window_pos()
    canvas.window_size = imgui.get_window_size()

    # This is the screen-space origin of our canvas-local (0,0)
    # We use cursor screen pos so padding is included.
    canvas.origin_screen = imgui.get_cursor_screen_pos()
    
    # Capture draw ranges *now*
    draw_list = imgui.get_window_draw_list()
    canvas.vtx0 = draw_list.vtx_buffer.size()
    canvas.idx0 = draw_list.idx_buffer.size()
    canvas.cmd0 = draw_list.cmd_buffer.size()

    # ---------------------------
    # Input area for pan/zoom
    # ---------------------------

    # Put an invisible button covering the whole child window
    imgui.set_cursor_screen_pos(canvas.window_pos)
    imgui.set_next_item_allow_overlap()

    io = imgui.get_io()
    if imgui.is_key_down(imgui.Key.mod_alt):
        button_flags = imgui.ButtonFlags_.mouse_button_left
    else:
        button_flags = imgui.ButtonFlags_.mouse_button_middle

    imgui.invisible_button("##canvas_viewport", canvas.window_size, button_flags)

    # Pan
    if imgui.is_item_active() and (abs(io.mouse_delta.x) > 0.0 or abs(io.mouse_delta.y) > 0.0):
        zoom = get_canvas_zoom(canvas)
        # Convert screen mouse delta -> local delta
        local_dx = io.mouse_delta.x / zoom
        local_dy = io.mouse_delta.y / zoom
        canvas.pan_zoom = glm.translate(canvas.pan_zoom, glm.vec3(local_dx, local_dy, 0.0))

    # Zoom (only when hovered and nothing else is active)
    elif (
        imgui.is_window_hovered(imgui.HoveredFlags_.child_windows)
        and not imgui.is_any_item_active()
        and not imgui.is_any_item_focused()
        and abs(io.mouse_wheel) > 0.0
    ):
        zoom_speed = 0.12
        scale_factor = 1.0 + io.mouse_wheel * zoom_speed

        # Mouse in screen space (absolute)
        mouse_screen = imgui.get_mouse_pos()

        # Convert to canvas-local coordinates (before zoom)
        mouse_local = screen_to_canvas_local(canvas, mouse_screen)

        # Build translation matrices
        # 1. Translate so mouse_local is at origin
        T1 = glm.translate(glm.identity(glm.mat4), glm.vec3(-mouse_local.x, -mouse_local.y, 0.0))
        # 2. Scale around origin
        S = glm.scale(glm.identity(glm.mat4), glm.vec3(scale_factor, scale_factor, 1.0))
        # 3. Translate back
        T2 = glm.translate(glm.identity(glm.mat4), glm.vec3(mouse_local.x, mouse_local.y, 0.0))

        # Compose: zoom happens in canvas-local space, so multiply on the right
        # pan_zoom = pan_zoom * (T2 * S * T1)
        canvas.pan_zoom = cast(glm.mat4, canvas.pan_zoom * T2 * S * T1)

    # Restore cursor for content submission
    imgui.set_cursor_screen_pos(canvas.origin_screen)

    return ret


def end_canvas():
    canvas = get_current_canvas()
    if canvas is None:
        raise RuntimeError("end_canvas called without begin_canvas")

    draw_list = imgui.get_window_draw_list()

    # --- Draw grid in local space (it will be transformed by vertex transform) ---
    for A, B in create_grid_lines(600, 600, origin=(0.0, 0.0), step=40.0):
        draw_list.add_line(
            imgui.ImVec2(A[0], A[1]),
            imgui.ImVec2(B[0], B[1]),
            imgui.color_convert_float4_to_u32((0.5, 0.5, 0.5, 1.0)),
            thickness=1.0,
        )

    # --- Transform ONLY the vertices generated since begin_canvas() ---
    vtx1 = draw_list.vtx_buffer.size()

    for i in range(canvas.vtx0, vtx1):
        vert: imgui.ImDrawVert = draw_list.vtx_buffer[i]

        # Convert from "local" (where ImGui thought it was drawing) to screen
        local = glm.vec4(vert.pos.x, vert.pos.y, 0.0, 1.0)
        out = canvas.pan_zoom * local

        vert.pos.x = canvas.origin_screen.x + out.x
        vert.pos.y = canvas.origin_screen.y + out.y

    # Debug
    imgui.set_cursor_screen_pos(canvas.window_pos)
    imgui.text(f"zoom: {get_canvas_zoom(canvas):.3f}")
    imgui.text(f"pan_zoom:\n{canvas.pan_zoom}")

    imgui.end_child()
    set_current_canvas(None)

state = {
    "my_value": 0.5,
}
def gui():
    imgui.text("Hello, world!")
    _, state['my_value'] = imgui.slider_float("slider1", state['my_value'], 0.0, 1.0)
    begin_canvas("MyCanvas", imgui.ImVec2(400, 400))
    begin_canvas_content() # <-- important for input remapping
    imgui.text("This is a canvas area.")
    imgui.button("A Button")
    _, state['my_value'] = imgui.slider_float("slider_canvas", state['my_value'], 0.0, 1.0)
    end_canvas_content()
    end_canvas()

if __name__ == "__main__":
    immapp.run(gui)
