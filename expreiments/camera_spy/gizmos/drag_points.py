from imgui_bundle import imgui
from core import Point2D

def drag_points(label: str, points: list[Point2D], selection:list[int], *, colors:list[tuple[float, float, float]]=[], labels:list[str]=[], size=(600, 400))->tuple[bool, list[Point2D], list[int]]:
    """
    Draw a draggable points widget inside the current ImGui window.

    Args:
        label: Unique label for the invisible button region.
        points_list: List of [x, y] coordinates to render and modify.
        size: (width, height) of the canvas.
    """
    RADIUS = 3.0


    io = imgui.get_io()
    mouse_pos = io.mouse_pos
    mouse_down = io.mouse_down[0]

    draw_list = imgui.get_window_draw_list()
    origin = imgui.get_cursor_pos()

    # Draw a canvas area (background)
    draw_list.add_rect_filled(
        origin,
        (origin.x + size[0], origin.y + size[1]),
        imgui.color_convert_float4_to_u32((0.1, 0.1, 0.1, 1.0)),
    )

    imgui.invisible_button(label, size)
    is_hovered = imgui.is_item_hovered()

    # Handle clicks
    def point_is_hovered(idx:int):
        x, y = points[idx]
        dx, dy = mouse_pos.x - (origin.x + x), mouse_pos.y - (origin.y + y)
        return dx * dx + dy * dy < (RADIUS * 2) ** 2

    if imgui.is_mouse_clicked(0) and is_hovered:
        for i, (x, y) in enumerate(points):
            if point_is_hovered(i):
                selection = [i]
                break

    # Handle dragging
    if mouse_down:
        for idx in selection:
            local_x = mouse_pos.x - origin.x
            local_y = mouse_pos.y - origin.y
            points[idx] = local_x, local_y

    if not mouse_down:
        selection = []

    # Draw points
    for i, (x, y) in enumerate(points):
        color = colors[i] if i < len(colors) else (1.0, 1.0, 1.0)
        label = labels[i] if i < len(labels) else str(i)
        radius = RADIUS
        if i in selection:
            color = (1.0, 1.0, 1.0)

        if point_is_hovered(i) and is_hovered:
            color = (1.0, 1.0, 1.0)
            radius+=2.0
        
        draw_list.add_circle_filled(
            (origin.x + x, origin.y + y),
            radius,
            imgui.color_convert_float4_to_u32(imgui.ImVec4(*color, 1.0)),
        )

        draw_list.add_text(
            (origin.x + x + 5, origin.y + y - 5),
            imgui.color_convert_float4_to_u32(imgui.ImVec4(*color, 1.0)),
            f"{label} ({int(x)},{int(y)})"
        )

    changed = mouse_down and len(selection) > 0
    return changed, points, selection