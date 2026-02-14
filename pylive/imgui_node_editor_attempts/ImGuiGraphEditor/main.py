from typing import Any, Callable, Hashable, Protocol, Tuple, List, Dict, cast
from imgui_bundle import imgui, immapp
from imgui_bundle import imgui_node_editor as ed


def gui():
    ed.begin("My Editor")
    # ed.push_style_var(ed.StyleVar.node_padding, imgui.ImVec4(0,0,0,0))
    imgui.set_next_item_width(200)
    ed.begin_node(ed.NodeId(1))
    imgui.begin_horizontal("inputs")
    for i in range(3):
        ed.begin_pin(ed.PinId(i), ed.PinKind.input)
        imgui.dummy(imgui.ImVec2(8, 8))
        # imgui.text(f"Input {i}")
        ed.end_pin()
    imgui.end_horizontal()

    imgui.text("node")
    # imgui.begin_horizontal("outputs")
    # for i in range(3):
    #     ed.begin_pin(ed.PinId(i+10), ed.PinKind.output)
    #     imgui.text(f"Output {i}")
    #     ed.end_pin()
    # imgui.end_horizontal()
    ed.end_node()
    ed.pop_style_var()
    ed.end()


if __name__ == "__main__":
    immapp.run(gui, with_node_editor=True)
