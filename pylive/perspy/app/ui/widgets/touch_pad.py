from imgui_bundle import imgui
from typing import Tuple
import math


def touch_pad(label:str, size:imgui.ImVec2=imgui.ImVec2(64,64))->Tuple[bool, imgui.ImVec2]:
    """A simple touch pad that returns the drag delta when active."""
    imgui.button(label, size)
    if imgui.is_item_active():
        delta = imgui.get_mouse_drag_delta(lock_threshold=0.0)
        imgui.reset_mouse_drag_delta()
        if math.fabs(delta.x) < 1e-6 and math.fabs(delta.y) < 1e-6:
            return False, imgui.ImVec2(0,0)

        return True, delta
    else:
        return False, imgui.ImVec2(0,0)