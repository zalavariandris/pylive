from imgui_bundle import imgui
from typing import List, Tuple

def radio_group(label:str, current_value:int, options:List[str]) -> Tuple[bool, int]:
    text, id = label.split("##") if "##" in label else (label, label)
    changed = False
    new_value = current_value
    imgui.push_id(label)
    for i, option in enumerate(options):
        changed = imgui.radio_button(option, current_value == i)
        if changed:
            new_value = i
        if i < len(options) - 1:
            imgui.same_line()
    imgui.pop_id()
    
    if label:
        imgui.same_line()
        imgui.text(f"{text}")
    
    return changed, new_value