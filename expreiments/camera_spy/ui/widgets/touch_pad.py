from imgui_bundle import imgui

def touch_pad(label:str, size:imgui.ImVec2=imgui.ImVec2(200,200))->imgui.ImVec2:
    imgui.button(label, size)
    if imgui.is_item_active():
        delta = imgui.get_mouse_drag_delta()
        imgui.reset_mouse_drag_delta()

        return delta
    else:
        return imgui.ImVec2(0,0)