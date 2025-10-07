from imgui_bundle import imgui
import numpy as np
from typing import List, Tuple

def closest_point_line_segment(p:imgui.ImVec2, line:List[imgui.ImVec2])->imgui.ImVec2:

    a = np.array([line[0].x, line[0].y])
    b = np.array([line[1].x, line[1].y])
    p = np.array([p.x, p.y])
    ab = b - a
    t = np.dot(p - a, ab) / np.dot(ab, ab)
    t = np.clip(t, 0.0, 1.0)
    closest = a + t * ab
    return imgui.ImVec2(closest[0], closest[1])