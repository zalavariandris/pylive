import glm
import numpy as np
from typing import List, Tuple
from imgui_bundle import imgui
from itertools import zip_longest
from typing import List, Tuple, Literal


ShapeLiterals = Literal['o', 'x']
def draw_points(points:List[imgui.ImVec2], labels: list[str] = None, colors:List[int]|int|None=None, shapes:List[ShapeLiterals]|ShapeLiterals|None=None):
    match labels:
        case None:
            labels = []
        case str():
            labels = [labels] * len(points)
        case list() | tuple() if len(labels) in (0, len(points)):
            pass
        case _:
            assert len(labels) == len(points), f"Expected {len(points)} labels, got {len(labels)}"

    match colors:
        case None:
            colors = [imgui.color_convert_float4_to_u32((1, 1, 1, 1))]
        case int():
            colors = [colors] * len(points)
        case list() | tuple() if len(labels) in (0, len(points)):
            pass
        case _:
            ...

    match shapes:
        case None:
            shapes = ['o'] * len(points)
        case str():
            shapes = [shapes] * len(points)
        case list() | tuple() if len(shapes) in (0, len(points)):
            pass
        case _:
            ...

    draw_list = imgui.get_window_draw_list()
    screen_offset = imgui.get_cursor_screen_pos() - imgui.get_cursor_pos()
    for P, label, color, shape in zip_longest(points, labels, colors, shapes):
        match shape:
            case 'x':
                draw_list.add_line(
                    imgui.ImVec2(P.x-5+screen_offset.x, P.y-5+screen_offset.y),
                    imgui.ImVec2(P.x+5+screen_offset.x, P.y+5+screen_offset.y),
                    color,
                    2
                )
                draw_list.add_line(
                    imgui.ImVec2(P.x-5+screen_offset.x, P.y+5+screen_offset.y),
                    imgui.ImVec2(P.x+5+screen_offset.x, P.y-5+screen_offset.y),
                    color,
                    2
                )
            case _:
                draw_list.add_circle_filled(
                    (P.x+screen_offset.x, P.y+screen_offset.y),
                    5,
                    color
                )

    
        if label:
            draw_list.add_text(
                (P.x+screen_offset.x + 5, P.y+screen_offset.y - 5),
                imgui.color_convert_float4_to_u32((1, 1, 0, 0.8)),
                label
            )

def draw_lines(lines: List[Tuple[imgui.ImVec2, imgui.ImVec2]], labels: list[str]|str|None = None, colors:List[int]|int|None=None):
    match labels:
        case None:
            labels = []
        case str():
            labels = [labels] * len(lines)
        case list() | tuple() if len(labels) in (0, len(lines)):
            pass
        case _:
            assert len(labels) == len(lines), f"Expected {len(lines)} labels, got {len(labels)}"

    match colors:
        case None:
            colors = [imgui.color_convert_float4_to_u32((1, 1, 1, 1))]
        case int():
            colors = [colors] * len(lines)
        case list() | tuple() if len(labels) in (0, len(lines)):
            pass
        case _:
            ...

    draw_list = imgui.get_window_draw_list()
    screen_offset = imgui.get_cursor_screen_pos() - imgui.get_cursor_pos()
    for line, label, color in zip_longest(lines, labels, colors):
        draw_list.add_line(
            (line[0].x+screen_offset.x, line[0].y+screen_offset.y),
            (line[1].x+screen_offset.x, line[1].y+screen_offset.y),
            color,
            1
        )

        if label:
            C = (line[0] + line[1]) * 0.5
            draw_list.add_text(
                (C.x+screen_offset.x + 5, C.y+screen_offset.y - 5),
                color,
                label
            )

def draw_lines3D(view: glm.mat4, projection: glm.mat4, viewport: Tuple[int,int,int,int],
                 lines, labels=None, colors=None, near=0.1):
    """Draw 3D lines in the scene.
    Note: lines are clipped against the near plane before projection.
    """
    ###
    # the current implementation is a simple readable but a naive per-line processing.
    # TODO: Consider using numpy arrays and vectorized operations.
    ###
    # clip lines to near plane
    clipped_lines = []
    for A, B in lines:
        clipped = _clip_line_near_plane_world(A, B, view, near)
        if clipped is not None:
            clipped_lines.append(clipped)

    # project lines to screen
    projected_lines = []
    for A, B in clipped_lines:
        A_proj = glm.project(A, view, projection, viewport)
        B_proj = glm.project(B, view, projection, viewport)

        projected_lines.append((imgui.ImVec2(A_proj.x, A_proj.y), imgui.ImVec2(B_proj.x, B_proj.y)))

    # draw lines
    draw_lines(projected_lines, labels, colors)

def draw_grid3D(view: glm.mat4, projection: glm.mat4, viewport: Tuple[int,int,int,int],
                size: float = 10, step: float = 1, near: float = 0.1):
    # Compute number of steps from the center to edge
    n_steps = int(np.floor(size/2 / step))
    
    # Generate coordinates starting from 0
    xs = np.arange(-n_steps, n_steps + 1) * step
    zs = np.arange(-n_steps, n_steps + 1) * step
    
    # If size is not exact multiple of step, extend outer lines slightly
    # xs = np.clip(xs, -size, size)
    # zs = np.clip(zs, -size, size)
    
    lines = []
    
    # Vertical lines (constant X, varying Z)
    for x in xs:
        lines.append((glm.vec3(x, 0, -size/2), glm.vec3(x, 0, size/2)))
    
    # Horizontal lines (constant Z, varying X)
    for z in zs:
        lines.append((glm.vec3(-size/2, 0, z), glm.vec3(size/2, 0, z)))
    
    draw_lines3D(
        view,
        projection,
        viewport,
        lines,
        colors=imgui.color_convert_float4_to_u32((0.5, 0.5, 0.5, 1)),
        near=near
    )

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
    