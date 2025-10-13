from imgui_bundle import imgui
from itertools import zip_longest

def points(points, labels: list[str] = None):
    draw_list = imgui.get_window_draw_list()
    screen_offset = imgui.get_cursor_screen_pos() - imgui.get_cursor_pos()
    for P, label in zip_longest(points, labels):
        draw_list.add_circle_filled(
            (P.x+screen_offset.x, P.y+screen_offset.y),
            5,
            imgui.color_convert_float4_to_u32((1, 1, 0, 0.3))
        )

        if label:
            draw_list.add_text(
                (P.x+screen_offset.x + 5, P.y+screen_offset.y - 5),
                imgui.color_convert_float4_to_u32((1, 1, 0, 0.8)),
                label
            )

from typing import List, Tuple
def lines(lines, labels: list[str] = None, colors:List[int]|int|None=None):
    match labels:
        case None:
            labels = []
        case str():
            labels = [labels] * len(lines)
        case list() | tuple():
            pass
        case _:
            assert len(labels) == len(lines), f"Expected {len(lines)} labels, got {len(labels)}"
    match colors:
        case None:
            colors = [imgui.color_convert_float4_to_u32((1, 1, 1, 1))]
        case str():
            colors = [colors] * len(lines)
        case list() | tuple():
            pass

    draw_list = imgui.get_window_draw_list()
    screen_offset = imgui.get_cursor_screen_pos() - imgui.get_cursor_pos()
    for line, label, color in zip_longest(lines, labels, colors):
        draw_list.add_line(
            (line[0].x+screen_offset.x, line[0].y+screen_offset.y),
            (line[1].x+screen_offset.x, line[1].y+screen_offset.y),
            color,
            2
        )

        if label:
            C = (line[0] + line[1]) * 0.5
            draw_list.add_text(
                (C.x+screen_offset.x + 5, C.y+screen_offset.y - 5),
                imgui.color_convert_float4_to_u32((1, 1, 0, 0.8)),
                label
            )