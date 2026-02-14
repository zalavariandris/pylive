import os
from pathlib import Path
from typing import Dict, Tuple
from pyglm import glm
from imgui_bundle import imgui, immapp
from dataclasses import dataclass, field

# --- Utility: Grid Generation ---
def create_grid_lines(w, h, step=50.0):
    lines = []
    for x in range(int(-w), int(w), int(step)):
        lines.append(((x, -h), (x, h)))
    for y in range(int(-h), int(h), int(step)):
        lines.append(((-w, y), (w, y)))
    return lines

# --- Canvas State ---
@dataclass
class CanvasWidget:
    # pan_zoom encodes both translation (in canvas-local units) and scale.
    # Transform: screen_pos = window_pos + pan_zoom * canvas_local
    pan_zoom:    glm.mat4      = field(default_factory=lambda: glm.identity(glm.mat4))
    window_pos:  imgui.ImVec2  = field(default_factory=lambda: imgui.ImVec2(0, 0))
    window_size: imgui.ImVec2  = field(default_factory=lambda: imgui.ImVec2(0, 0))

_canvas_registry: Dict[str, CanvasWidget] = {}
_current_canvas_name: str | None = None

def get_current_canvas() -> CanvasWidget | None:
    return _canvas_registry.get(_current_canvas_name) if _current_canvas_name else None

# --- Coordinate Helpers ---

def canvas_to_screen(canvas: CanvasWidget, p: imgui.ImVec2) -> imgui.ImVec2:
    """Canvas-local -> screen space."""
    v = canvas.pan_zoom * glm.vec4(p.x, p.y, 0.0, 1.0)
    return imgui.ImVec2(canvas.window_pos.x + v.x, canvas.window_pos.y + v.y)

def screen_to_canvas(canvas: CanvasWidget, p: imgui.ImVec2) -> imgui.ImVec2:
    """Screen space -> canvas-local."""
    inv = glm.inverse(canvas.pan_zoom)
    v = inv * glm.vec4(p.x - canvas.window_pos.x, p.y - canvas.window_pos.y, 0.0, 1.0)
    return imgui.ImVec2(v.x, v.y)

def get_canvas_zoom(canvas: CanvasWidget) -> float:
    return float(canvas.pan_zoom[0][0])

# --- Canvas ---

def begin_canvas(name: str, size: imgui.ImVec2) -> bool:
    global _current_canvas_name
    if name not in _canvas_registry:
        _canvas_registry[name] = CanvasWidget()

    _current_canvas_name = name
    canvas = _canvas_registry[name]

    imgui.begin_child(name, size, imgui.ChildFlags_.borders,
                      imgui.WindowFlags_.no_scrollbar | imgui.WindowFlags_.no_scroll_with_mouse)

    canvas.window_pos  = imgui.get_window_pos()
    canvas.window_size = imgui.get_window_size()

    # --- Input: pan (middle drag) & zoom (scroll) ---
    # invisible_button covers the entire canvas; only responds to middle mouse.
    imgui.set_cursor_screen_pos(canvas.window_pos)
    imgui.invisible_button("##pan", canvas.window_size,
                           imgui.ButtonFlags_.mouse_button_middle)

    io = imgui.get_io()
    if imgui.is_item_active() and (io.mouse_delta.x != 0 or io.mouse_delta.y != 0):
        zoom = get_canvas_zoom(canvas)
        canvas.pan_zoom = glm.translate(
            canvas.pan_zoom,
            glm.vec3(io.mouse_delta.x / zoom, io.mouse_delta.y / zoom, 0.0))

    if imgui.is_window_hovered() and io.mouse_wheel != 0:
        mouse_local = screen_to_canvas(canvas, io.mouse_pos)
        zf = 1.1 if io.mouse_wheel > 0 else 0.9
        T1 = glm.translate(glm.mat4(1), glm.vec3(-mouse_local.x, -mouse_local.y, 0))
        S  = glm.scale(glm.mat4(1), glm.vec3(zf, zf, 1))
        T2 = glm.translate(glm.mat4(1), glm.vec3(mouse_local.x, mouse_local.y, 0))
        canvas.pan_zoom = canvas.pan_zoom * T2 * S * T1

    return True

def end_canvas():
    imgui.end_child()

# --- Drawing helpers ---

def canvas_draw_begin(canvas: CanvasWidget):
    """Push a clip rect matching the canvas window."""
    dl = imgui.get_window_draw_list()
    dl.push_clip_rect(
        canvas.window_pos,
        imgui.ImVec2(canvas.window_pos.x + canvas.window_size.x,
                     canvas.window_pos.y + canvas.window_size.y),
        True)
    return dl

def canvas_draw_end():
    imgui.get_window_draw_list().pop_clip_rect()

# --- Node ---

def begin_node(name: str, pos: imgui.ImVec2) -> Tuple[bool, imgui.ImVec2]:
    """
    Place a draggable node at canvas-local `pos`.
    Returns (was_moved, new_pos).

    Approach: convert canvas-local pos to screen space and call
    set_cursor_screen_pos so that ImGui's hit-testing stays in screen space.
    This avoids all mouse-remapping / internal-state hacking, and works
    correctly for nodes at any canvas coordinate (positive or negative).
    """
    canvas = get_current_canvas()
    screen_pos = canvas_to_screen(canvas, pos)

    imgui.set_cursor_screen_pos(screen_pos)
    imgui.begin_group()
    imgui.button(f"Node: {name}")
    imgui.text(f"({int(pos.x)}, {int(pos.y)})")
    imgui.end_group()

    # EndGroup propagates the inner button's ActiveId, so is_item_active() works.
    if imgui.is_item_active() and imgui.is_mouse_dragging(imgui.MouseButton.left):
        io   = imgui.get_io()
        zoom = get_canvas_zoom(canvas)
        # mouse_delta is screen-space pixels; divide by zoom -> canvas-local units.
        new_pos = imgui.ImVec2(pos.x + io.mouse_delta.x / zoom,
                               pos.y + io.mouse_delta.y / zoom)
        return True, new_pos

    return False, pos

# --- App ---

state = {
    'nodes': {
        'A': imgui.ImVec2( 100,  100),
        'B': imgui.ImVec2(-300, -300),
    }
}

def gui():
    imgui.text("Middle-drag: pan   |   Scroll: zoom   |   Left-drag: move nodes")

    if begin_canvas("MainCanvas", imgui.ImVec2(0, 0)):
        canvas = get_current_canvas()

        # ---- Draw list: grid + axes (canvas-local coords converted per-line) ----
        dl = canvas_draw_begin(canvas)

        for A, B in create_grid_lines(3000, 3000, step=100):
            dl.add_line(
                canvas_to_screen(canvas, imgui.ImVec2(*A)),
                canvas_to_screen(canvas, imgui.ImVec2(*B)),
                imgui.get_color_u32(imgui.Col_.separator, 0.4))

        dl.add_line(canvas_to_screen(canvas, imgui.ImVec2(-10000, 0)),
                    canvas_to_screen(canvas, imgui.ImVec2( 10000, 0)),
                    imgui.get_color_u32((1, 0, 0, 0.6)), 2.0)
        dl.add_line(canvas_to_screen(canvas, imgui.ImVec2(0, -10000)),
                    canvas_to_screen(canvas, imgui.ImVec2(0,  10000)),
                    imgui.get_color_u32((0, 1, 0, 0.6)), 2.0)

        canvas_draw_end()

        # ---- Nodes ----
        nodes = state['nodes']
        for node_id in list(nodes.keys()):
            imgui.push_id(node_id)
            _, nodes[node_id] = begin_node(node_id, nodes[node_id])
            imgui.pop_id()

        end_canvas()

if __name__ == "__main__":
    immapp.run(gui, window_size=(1280, 720))