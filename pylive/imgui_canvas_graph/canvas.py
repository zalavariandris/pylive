import os
from pathlib import Path
from typing import Dict, Literal, Tuple, List
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

# --- Canvas State Registry ---
@dataclass
class CanvasWidget:
    pan_zoom: glm.mat4 = field(default_factory=lambda: glm.identity(glm.mat4))
    window_pos: imgui.ImVec2 = field(default_factory=lambda: imgui.ImVec2(0, 0))
    window_size: imgui.ImVec2 = field(default_factory=lambda: imgui.ImVec2(0, 0))
    
    # Internal state for transformation
    vtx0: int = 0
    cmd0: int = 0
    _mouse_backup: imgui.ImVec2 = field(default_factory=lambda: imgui.ImVec2(0, 0))
    _backup_window_pos: imgui.ImVec2 = field(default_factory=lambda: imgui.ImVec2(0, 0))
    
    # Hitbox backups (Corners)
    _backup_inner_min: imgui.ImVec2 = field(default_factory=lambda: imgui.ImVec2(0, 0))
    _backup_inner_max: imgui.ImVec2 = field(default_factory=lambda: imgui.ImVec2(0, 0))
    _backup_outer_min: imgui.ImVec2 = field(default_factory=lambda: imgui.ImVec2(0, 0))
    _backup_outer_max: imgui.ImVec2 = field(default_factory=lambda: imgui.ImVec2(0, 0))

_canvas_registry: Dict[str, CanvasWidget] = {}
_current_canvas_name: str | None = None

def get_current_canvas() -> CanvasWidget | None:
    return _canvas_registry.get(_current_canvas_name) if _current_canvas_name else None

# --- Coordinate Helpers ---
# origin is always window_pos — the top-left of the child window in screen space.
# pan_zoom transforms canvas-local coords to screen coords relative to that origin.

def screen_to_canvas_local(canvas: CanvasWidget, p: imgui.ImVec2) -> imgui.ImVec2:
    inv = glm.inverse(canvas.pan_zoom)
    # Offset by window_pos so we work in window-relative screen space
    v = glm.vec4(p.x - canvas.window_pos.x, p.y - canvas.window_pos.y, 0.0, 1.0)
    out = inv * v
    return imgui.ImVec2(out.x, out.y)

def get_canvas_zoom(canvas: CanvasWidget) -> float:
    return float(canvas.pan_zoom[0][0])

# --- Canvas Logic ---

def begin_canvas(name: str, size: imgui.ImVec2) -> bool:
    global _current_canvas_name
    if name not in _canvas_registry:
        _canvas_registry[name] = CanvasWidget()
    
    _current_canvas_name = name
    canvas = _canvas_registry[name]
    
    imgui.begin_child(name, size, imgui.ChildFlags_.borders,
                      imgui.WindowFlags_.no_scrollbar | imgui.WindowFlags_.no_scroll_with_mouse)

    # Capture window_pos immediately — this is our stable screen-space origin.
    canvas.window_pos = imgui.get_window_pos()
    canvas.window_size = imgui.get_window_size()

    # Pan: middle-mouse drag
    imgui.set_cursor_screen_pos(canvas.window_pos)
    imgui.invisible_button("##vport", canvas.window_size, imgui.ButtonFlags_.mouse_button_middle)
    
    io = imgui.get_io()
    if imgui.is_item_active() and (io.mouse_delta.x != 0 or io.mouse_delta.y != 0):
        zoom = get_canvas_zoom(canvas)
        # Pan in canvas-local units so it stays consistent with zoom level
        canvas.pan_zoom = glm.translate(canvas.pan_zoom,
                                        glm.vec3(io.mouse_delta.x / zoom,
                                                 io.mouse_delta.y / zoom, 0.0))

    # Zoom: scroll wheel, zooming toward the mouse cursor
    elif imgui.is_window_hovered() and io.mouse_wheel != 0:
        mouse_local = screen_to_canvas_local(canvas, io.mouse_pos)
        zoom_fact = 1.1 if io.mouse_wheel > 0 else 0.9
        # Compose: translate pivot to origin → scale → translate back
        # Order must match: pan_zoom is applied as (pan_zoom * local_point),
        # so new = pan_zoom * T2 * S * T1
        T1 = glm.translate(glm.mat4(1), glm.vec3(-mouse_local.x, -mouse_local.y, 0))
        S  = glm.scale(glm.mat4(1), glm.vec3(zoom_fact, zoom_fact, 1))
        T2 = glm.translate(glm.mat4(1), glm.vec3(mouse_local.x, mouse_local.y, 0))
        canvas.pan_zoom = canvas.pan_zoom * T2 * S * T1

    return True

def begin_canvas_content():
    canvas = get_current_canvas()
    window = imgui.internal.get_current_window()
    io = imgui.get_io()

    # 1. Backup mouse and window origin
    canvas._mouse_backup = imgui.ImVec2(io.mouse_pos.x, io.mouse_pos.y)
    canvas._backup_window_pos = imgui.ImVec2(window.pos.x, window.pos.y)

    # 2. Remap mouse from screen space → canvas-local space.
    #    Widgets inside will then receive canvas-local coords naturally.
    remapped = screen_to_canvas_local(canvas, io.mouse_pos)
    io.mouse_pos = remapped

    # 3. Zero the window origin so that set_cursor_screen_pos(local_pos)
    #    places items at their canvas-local position directly.
    window.pos = imgui.ImVec2(0, 0)

    # 4. Backup and expand all hitboxes to "infinite" so nothing gets culled
    canvas._backup_inner_min = imgui.ImVec2(window.inner_rect.min.x, window.inner_rect.min.y)
    canvas._backup_inner_max = imgui.ImVec2(window.inner_rect.max.x, window.inner_rect.max.y)
    canvas._backup_outer_min = imgui.ImVec2(window.outer_rect_clipped.min.x, window.outer_rect_clipped.min.y)
    canvas._backup_outer_max = imgui.ImVec2(window.outer_rect_clipped.max.x, window.outer_rect_clipped.max.y)

    huge_min = imgui.ImVec2(-100000, -100000)
    huge_max = imgui.ImVec2(100000, 100000)
    window.inner_rect.min, window.inner_rect.max = huge_min, huge_max
    window.outer_rect_clipped.min, window.outer_rect_clipped.max = huge_min, huge_max
    window.work_rect.min, window.work_rect.max = huge_min, huge_max
    window.clip_rect.min, window.clip_rect.max = huge_min, huge_max
    window.content_region_rect.min, window.content_region_rect.max = huge_min, huge_max
    window.skip_items = False

    # 5. Prepare draw list — record where our vertices start
    dl = imgui.get_window_draw_list()
    canvas.vtx0 = dl.vtx_buffer.size()
    canvas.cmd0 = dl.cmd_buffer.size()
    imgui.push_clip_rect(huge_min, huge_max, False)

def end_canvas_content():
    canvas = get_current_canvas()
    window = imgui.internal.get_current_window()
    dl = imgui.get_window_draw_list()

    # 1. Transform all new vertices: canvas-local → window-relative screen space.
    #    We add window_pos (the screen origin) after the pan_zoom transform.
    vtx1 = dl.vtx_buffer.size()
    for i in range(canvas.vtx0, vtx1):
        v = dl.vtx_buffer[i]
        local = glm.vec4(v.pos.x, v.pos.y, 0.0, 1.0)
        world = canvas.pan_zoom * local
        # Add window_pos to land in actual screen space
        v.pos.x = canvas.window_pos.x + world.x
        v.pos.y = canvas.window_pos.y + world.y

    # 2. Restore clipping rect for each draw command to the window bounds
    clip = imgui.ImVec4(canvas.window_pos.x, canvas.window_pos.y,
                        canvas.window_pos.x + canvas.window_size.x,
                        canvas.window_pos.y + canvas.window_size.y)
    for i in range(canvas.cmd0, dl.cmd_buffer.size()):
        dl.cmd_buffer[i].clip_rect = clip

    # 3. Restore everything
    imgui.pop_clip_rect()
    window.pos = canvas._backup_window_pos
    window.inner_rect.min, window.inner_rect.max = canvas._backup_inner_min, canvas._backup_inner_max
    window.outer_rect_clipped.min, window.outer_rect_clipped.max = canvas._backup_outer_min, canvas._backup_outer_max
    window.work_rect.min, window.work_rect.max = canvas._backup_inner_min, canvas._backup_inner_max
    imgui.get_io().mouse_pos = canvas._mouse_backup

def end_canvas():
    imgui.end_child()

# --- Node Interface ---

def begin_node(name: str, pos: imgui.ImVec2) -> Tuple[bool, imgui.ImVec2]:
    imgui.set_cursor_screen_pos(pos)
    imgui.begin_group()
    imgui.button(f"Node: {name}")
    imgui.text(f"Pos: {int(pos.x)}, {int(pos.y)}")
    imgui.end_group()

    if imgui.is_item_active() and imgui.is_mouse_dragging(imgui.MouseButton.left):
        io = imgui.get_io()
        zoom = get_canvas_zoom(get_current_canvas())
        return True, imgui.ImVec2(pos.x + io.mouse_delta.x / zoom,
                                  pos.y + io.mouse_delta.y / zoom)
    return False, pos

# --- Main App ---

state = {
    'nodes': {
        'A': imgui.ImVec2(100, 100),
        'B': imgui.ImVec2(-300, -300),
    }
}

def gui():
    imgui.text("Canvas Interaction: Positive and Negative Coordinates")
    
    if begin_canvas("MainCanvas", imgui.ImVec2(0, 0)):
        begin_canvas_content()

        dl = imgui.get_window_draw_list()

        # Grid
        for A, B in create_grid_lines(3000, 3000, step=100):
            dl.add_line(imgui.ImVec2(*A), imgui.ImVec2(*B),
                        imgui.get_color_u32(imgui.Col_.separator, 0.4))

        # Axes
        dl.add_line(imgui.ImVec2(-10000, 0), imgui.ImVec2(10000, 0),
                    imgui.get_color_u32((1, 0, 0, 0.5)), 2)
        dl.add_line(imgui.ImVec2(0, -10000), imgui.ImVec2(0, 10000),
                    imgui.get_color_u32((0, 1, 0, 0.5)), 2)

        # Nodes
        nodes = state['nodes']
        for node_id in list(nodes.keys()):
            imgui.push_id(node_id)
            _, nodes[node_id] = begin_node(node_id, nodes[node_id])
            imgui.pop_id()

        end_canvas_content()
        end_canvas()

if __name__ == "__main__":
    immapp.run(gui, window_size=(1280, 720))