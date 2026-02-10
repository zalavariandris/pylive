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