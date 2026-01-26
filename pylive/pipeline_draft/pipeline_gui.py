from typing import Callable, Protocol, Tuple
from imgui_bundle import imgui, immapp
from imgui_bundle import imgui_node_editor as ed

import image_utils
import numpy as np

Time = int

# Video = Callable[[Time], image_utils.ImageRGBA]

class Video(Protocol):
    def __call__(self, frame: Time) -> np.ndarray:
        ...

class Read(Video):
    def __init__(self, path: str):
        self.path = path

    def __call__(self, frame: Time) -> np.ndarray:
        # Placeholder implementation
        return image_utils.read_image(self.path)
    

class Transform(Video):
    def __init__(self, source:Video, translate:Tuple[int, int]):
        self.source = source
        self.translate = translate

    def __call__(self, frame: Time) -> np.ndarray:
        # Placeholder implementation
        return image_utils.transform(self.source(frame), self.translate)
    

class Merge(Video):
    def __init__(self, foreground:Video, background:Video, mix:float):
        self.foreground = foreground
        self.background = background
        self.mix = mix

    def __call__(self, frame: Time) -> np.ndarray:
        # Placeholder implementation
        return image_utils.merge_over(self.foreground(frame), self.background(frame), self.mix)
    

class Viewer(Video):
    def __init__(self, source:Video):
        self.source = source

    def __call__(self, frame: Time) -> np.ndarray:
        # Placeholder implementation
        return self.source(frame)
    


import inspect
links = []
next_link_id = 1
def gui():
    read_node = Read("/path/to/image_%06d.png")
    transform_node = Transform(read_node, (100, 50))
    merge_node = Merge(transform_node, read_node, 0.5)
    viewer_node = Viewer(merge_node)
    nodes = [
        read_node,
        transform_node,
        merge_node,
        viewer_node
    ]

    # get read_node input nodes from the by inspecting the class __init__ method, and check their values
    sig = inspect.signature(read_node.__class__.__init__)
    print(sig)

    global next_link_id

    ed.begin("Node Editor")
    pin_id = 0
    node_id = 100
    for node in nodes:
        node_id += 1
        ed.begin_node(ed.NodeId(node_id))
        imgui.text(node.__class__.__name__)
        # # Inspect __init__ parameters to create pins
        sig = inspect.signature(node.__class__.__init__)
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            if param.annotation == Video:
                pin_id += 1
                ed.begin_pin(ed.PinId(pin_id), ed.PinKind.input)
                imgui.text(param_name)
                ed.end_pin()

        pin_id += 1
        ed.begin_pin(ed.PinId(pin_id), ed.PinKind.output)
        imgui.text('out')
        ed.end_pin()
        ed.end_node()

    # # Read
    # ed.begin_node(ed.NodeId(1))
    # imgui.text("Read")
    # ed.begin_pin(ed.PinId(101), ed.PinKind.output)
    # imgui.text("Out")
    # ed.end_pin()
    # ed.end_node()

    # # Transform
    # ed.begin_node(ed.NodeId(2))
    # imgui.text("Transform")
    # ed.begin_pin(ed.PinId(102), ed.PinKind.input)
    # imgui.text("In")
    # ed.end_pin()
    # ed.begin_pin(ed.PinId(103), ed.PinKind.output)
    # imgui.text("Out")
    # ed.end_pin()
    # ed.end_node()

    # # Merge
    # ed.begin_node(ed.NodeId(3))
    # imgui.text("Merge")
    # ed.begin_pin(ed.PinId(104), ed.PinKind.input)
    # imgui.text("Fg")
    # ed.end_pin()
    # ed.begin_pin(ed.PinId(105), ed.PinKind.input)
    # imgui.text("Bg")
    # ed.end_pin()
    # ed.begin_pin(ed.PinId(106), ed.PinKind.output)
    # imgui.text("Out")
    # ed.end_pin()
    # ed.end_node()

    # # Viewer
    # ed.begin_node(ed.NodeId(4))
    # imgui.text("Viewer")
    # ed.begin_pin(ed.PinId(107), ed.PinKind.input)
    # imgui.text("input")
    # ed.end_pin()
    # ed.end_node()

    # ed.link(ed.LinkId(1), ed.PinId(101), ed.PinId(102))
    # ed.link(ed.LinkId(2), ed.PinId(101), ed.PinId(104))
    # ed.link(ed.LinkId(3), ed.PinId(103), ed.PinId(105))
    # ed.link(ed.LinkId(4), ed.PinId(106), ed.PinId(107))

    # Draw existing links
    for link_id, out_pin, in_pin in links:
        ed.link(link_id, out_pin, in_pin)

    # --- Create links ---
    if ed.begin_create():
        in_pin = ed.PinId()
        out_pin = ed.PinId()
        if ed.query_new_link(in_pin, out_pin):
            if in_pin and out_pin:
                ed.accept_new_item()
                links.append(
                    (ed.LinkId(next_link_id), out_pin, in_pin)
                )
                next_link_id += 1
        ed.end_create()

    # --- Delete links ---
    if ed.begin_delete():
        link_id = ed.LinkId()
        while ed.query_deleted_link(link_id):
            ed.accept_deleted_item()
            links[:] = [l for l in links if l[0] != link_id]
        ed.end_delete()
    ed.end()

    imgui.begin_child()
    imgui.image(...)
    imgui.end_child()

if __name__ == "__main__":
    immapp.run(gui, with_node_editor=True)
