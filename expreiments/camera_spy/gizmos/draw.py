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

def lines(lines, labels: list[str] = None):
    draw_list = imgui.get_window_draw_list()
    screen_offset = imgui.get_cursor_screen_pos() - imgui.get_cursor_pos()
    for line, label in zip_longest(lines, labels):
        draw_list.add_line(
            (line[0].x+screen_offset.x, line[0].y+screen_offset.y),
            (line[1].x+screen_offset.x, line[1].y+screen_offset.y),
            imgui.color_convert_float4_to_u32((1, 0, 1, 1)),
            2
        )

        if label:
            C = (line[0] + line[1]) * 0.5
            draw_list.add_text(
                (C.x+screen_offset.x + 5, C.y+screen_offset.y - 5),
                imgui.color_convert_float4_to_u32((1, 1, 0, 0.8)),
                label
            )