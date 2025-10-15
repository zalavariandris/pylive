from imgui_bundle import imgui
from itertools import zip_longest
from typing import List, Tuple, Literal
ShapeLiterals = Literal['o', 'x']
def points(points:List[imgui.ImVec2], labels: list[str] = None, colors:List[int]|int|None=None, shapes:List[ShapeLiterals]|ShapeLiterals|None=None):
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

from typing import List, Tuple
def lines(lines, labels: list[str]|str|None = None, colors:List[int]|int|None=None):
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
                imgui.color_convert_float4_to_u32((1, 1, 0, 0.8)),
                label
            )