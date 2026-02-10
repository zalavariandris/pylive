# Standard library imports
import os


from pathlib import Path
from typing import Dict, Generic, Literal, Tuple, List, Iterable, Iterator, TypeVar, cast
import math
from pyglm import glm
# ########### #
# Application #
# ########### #
from imgui_bundle import imgui, immapp
from dataclasses import dataclass, field
from utils import create_grid_lines


# - Canvas Registry -
@dataclass
class CanvasWidget:
    content_size: imgui.ImVec2 = field(default_factory=lambda: imgui.ImVec2(400, 400))
    coordinate_system: Literal['top-left', 'bottom-left'] = 'bottom-left'
    pan_zoom: glm.mat4 = field(default_factory=lambda: glm.identity(glm.mat4))
    window_pos: imgui.ImVec2 = field(default_factory=lambda: imgui.ImVec2(0, 0))
    window_size: imgui.ImVec2 = field(default_factory=lambda: imgui.ImVec2(0, 0))
    origin_screen: imgui.ImVec2 = field(default_factory=lambda: imgui.ImVec2(0, 0))
    vtx0: int = 0
    idx0: int = 0
    cmd0: int = 0
    _mouse_backup: imgui.ImVec2 = field(default_factory=lambda: imgui.ImVec2(0, 0))


_canvas_registry:Dict[str, CanvasWidget] = {}
_current_canvas_name:str|None = None

def create_canvas(name:str) -> CanvasWidget:
    global _canvas_registry
    if name in _canvas_registry:
        raise ValueError(f"Canvas with name '{name}' already exists")
    
    canvas = CanvasWidget()
    _canvas_registry[name] = canvas
    return canvas

def get_current_canvas() -> CanvasWidget|None:
    global _canvas_registry, _current_canvas_name
    if _current_canvas_name is None:
        return None
    
    return _canvas_registry.get(_current_canvas_name, None)

def set_current_canvas(name:str|None):
    global _canvas_registry, _current_canvas_name
    _current_canvas_name = name


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

# ---------------------------
# Canvas widget
# ---------------------------

def begin_canvas(
        name:str, 
        size:imgui.ImVec2|None=None, 
        content_size:imgui.ImVec2|None = None, 
        coordinate_system:Literal['top-left', 'bottom-left']='bottom-left'
)->bool:
    global _canvas_registry, _current_canvas_name

    window = imgui.internal.get_current_window()
    window.skip_items = False

    if name not in _canvas_registry:
        print("create canvas", name)
        create_canvas(name)
    
    set_current_canvas(name)
    canvas = get_current_canvas()
    if canvas is None:
        raise RuntimeError("Canvas should have been created above")

    if size is None:
        size = imgui.ImVec2(-1, -1)

    # ret = imgui.begin_child(
    #     name, 
    #     size, 
    #     imgui.ChildFlags_.borders,
    #     imgui.WindowFlags_.no_scrollbar | imgui.WindowFlags_.no_scroll_with_mouse
    # )

    canvas.content_size = content_size
    canvas.coordinate_system = coordinate_system
    canvas.window_pos = imgui.get_window_pos()
    canvas.window_size = imgui.get_window_size()

    # This is the screen-space origin of our canvas-local (0,0)
    # We use cursor screen pos so padding is included.
    canvas.origin_screen = imgui.get_cursor_screen_pos()

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

    return True

_debug_frame = [0]

def begin_canvas_content():
    """
    Remap mouse into canvas-local space so ImGui widgets do correct hit-testing.
    Must be called AFTER begin_canvas() and BEFORE submitting widgets.
    """
    global _debug_frame
    _debug_frame[0] += 1
    
    canvas = get_current_canvas()
    if canvas is None:
        raise RuntimeError("begin_canvas_content called without begin_canvas")
    
    # Capture draw ranges *now*
    draw_list = imgui.get_window_draw_list()
    canvas.vtx0 = draw_list.vtx_buffer.size()
    canvas.idx0 = draw_list.idx_buffer.size()
    canvas.cmd0 = draw_list.cmd_buffer.size()
    
    # Backup mouse pos
    io = imgui.get_io()
    canvas._mouse_backup = imgui.ImVec2(io.mouse_pos.x, io.mouse_pos.y)

    # Remap
    mouse_local = screen_to_canvas_local(canvas, io.mouse_pos)
    io.mouse_pos = mouse_local

    imgui.push_item_width(250) # for demo purposes, so slider isn't super long

    canvas_pos = canvas.origin_screen
    canvas_size = canvas.content_size
    imgui.push_clip_rect(
        imgui.ImVec2(-999999, -999999),
        imgui.ImVec2(+999999, +999999),
        True
    )
    
    # Expand window's internal clip rects AFTER push_clip_rect to prevent ImGui
    # from skipping widgets at negative cursor positions. push_clip_rect with
    # intersect_with_current_clip_rect=True resets window.clip_rect, so we must
    # override it afterwards.
    window = imgui.internal.get_current_window()
    big = imgui.internal.ImRect(-100000, -100000, 100000, 100000)
    window.clip_rect = big
    window.inner_clip_rect = big
    window.work_rect = big
    window.content_region_rect = big
    window.inner_rect = big
    window.skip_items = False
    
    if _debug_frame[0] % 60 == 1:
        print(f"[begin_canvas_content] vtx0={canvas.vtx0}, clip_rect.min={window.clip_rect.min.x}")
 
def end_canvas_content():
    global _debug_frame
    draw_list = imgui.get_window_draw_list()
    canvas = get_current_canvas()
    if canvas is None:
        raise RuntimeError("end_canvas_content called without begin_canvas")
    
    # 1. Transform Vertices (Your existing code)
    vtx1 = draw_list.vtx_buffer.size()
    vtx_count = vtx1 - canvas.vtx0
    
    if _debug_frame[0] % 60 == 1:
        print(f"[end_canvas_content] vtx_count={vtx_count} (vtx0={canvas.vtx0}, vtx1={vtx1})")
    
    for i in range(canvas.vtx0, vtx1):
        vert = draw_list.vtx_buffer[i]
        local = glm.vec4(vert.pos.x, vert.pos.y, 0.0, 1.0)
        out = canvas.pan_zoom * local
        vert.pos.x = canvas.origin_screen.x + out.x
        vert.pos.y = canvas.origin_screen.y + out.y

    # 2. Set all canvas draw command clip_rects to the canvas window bounds.
    # Since we expanded the clip_rect to huge values to prevent widget skipping,
    # the original clip_rect values are meaningless. We just clip to the visible
    # canvas area in screen space.
    clip_min_x = canvas.window_pos.x
    clip_min_y = canvas.window_pos.y
    clip_max_x = canvas.window_pos.x + canvas.window_size.x
    clip_max_y = canvas.window_pos.y + canvas.window_size.y

    cmd1 = draw_list.cmd_buffer.size()
    for i in range(canvas.cmd0, cmd1):
        cmd = draw_list.cmd_buffer[i]
        cmd.clip_rect.x = clip_min_x
        cmd.clip_rect.y = clip_min_y
        cmd.clip_rect.z = clip_max_x
        cmd.clip_rect.w = clip_max_y

    imgui.pop_clip_rect()

    # 3. Restore Mouse/UI State
    imgui.pop_item_width()
    io = imgui.get_io()
    io.mouse_pos = canvas._mouse_backup

def end_canvas():
    canvas = get_current_canvas()
    if canvas is None:
        raise RuntimeError("end_canvas called without begin_canvas")

    draw_list = imgui.get_window_draw_list()

    # --- Draw grid in local space (it will be transformed by vertex transform) ---
    begin_canvas_content() # <-- important for input remapping
    for A, B in create_grid_lines(600, 600, origin=(0.0, 0.0), step=40.0):
        draw_list.add_line(
            imgui.ImVec2(A[0], A[1]),
            imgui.ImVec2(B[0], B[1]),
            imgui.color_convert_float4_to_u32((0.5, 0.5, 0.5, 1.0)),
            thickness=1.0,
        )
    end_canvas_content() # <-- important for input remapping
    set_current_canvas(None)
    # imgui.end_child()

def begin_node(name:str, pos:imgui.ImVec2) -> Tuple[bool, imgui.ImVec2]:
    imgui.set_cursor_screen_pos(pos)
    # imgui.begin_group()
    
    imgui.button(f"{name} ({pos.x},{pos.y}) ###{name}", imgui.ImVec2(200, 50))

    if imgui.is_item_active():
        io = imgui.get_io()
        return True, imgui.ImVec2(pos.x + io.mouse_delta.x, pos.y + io.mouse_delta.y)
    return False, pos

def end_node():
    ...
    # imgui.end_group()

state = {
    "my_value": 0.5,
    'nodes': {
        'Node1': imgui.ImVec2(50, 50),
        'Node2': imgui.ImVec2(50, 100),
    }
}
def gui():
    imgui.text("Hello, world!")
    # _, state['my_value'] = imgui.slider_float("slider1", state['my_value'], 0.0, 1.0)

    begin_canvas("MyCanvas", imgui.ImVec2(720, 540))

    # begin_canvas_content() # <-- important for input remapping
    # imgui.text("This is a canvas area.")
    # imgui.button("A Button")
    # _, state['my_value'] = imgui.slider_float("slider_canvas", state['my_value'], 0.0, 1.0)
    # end_canvas_content()

    begin_canvas_content() # <-- important for input remapping
    nodes = state['nodes']
    for node in nodes:
        _, nodes[node] = begin_node(node, nodes[node])
        end_node()
    end_canvas_content()


    imgui.text("Outside the canvas again, so it won't be transformed by the pan/zoom.")

    begin_canvas_content() # <-- important for input remapping
    imgui.text("This is also inside the canvas, so it will be transformed by pan/zoom.")
    end_canvas_content()

    end_canvas()

if __name__ == "__main__":
    immapp.run(gui)
