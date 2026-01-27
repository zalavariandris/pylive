from typing import Callable, Protocol, Tuple
from imgui_bundle import imgui, immapp
from imgui_bundle import imgui_node_editor as ed

import image_utils
import numpy as np

import numpy as np
from OpenGL.GL import *

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
        return image_utils.read_image(self.path % frame)
    

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
    

class Cache(Video):
    def __init__(self, source:Video):
        self.source = source
        self.cache = {}

    def __call__(self, frame: Time) -> np.ndarray:
        if frame not in self.cache:
            self.cache[frame] = self.source(frame)
        return self.cache[frame]
    

class Viewer(Video):
    def __init__(self, source:Video):
        self.source = source

    def __call__(self, frame: Time) -> np.ndarray:
        # Placeholder implementation
        return self.source(frame)

from pathlib import Path
import inspect

# create_pipeline
read_node = Read(r"./assets/SMPTE_Color_Bars_animation/SMPTE_Color_Bars_animation_%05d.png")
transform_node = Transform(read_node, (100, 50))
merge_node = Merge(transform_node, read_node, 0.5)
cache_node = Cache(merge_node)
viewer_node = Viewer(cache_node)

import networkx as nx
G = nx.MultiDiGraph()

from typing import Type

G.add_node("read", factory=Read, inputs=[], parameters={"path": r"./assets/SMPTE_Color_Bars_animation/SMPTE_Color_Bars_animation_%05d.png"})
G.add_node("transform", factory=Transform, inputs=['source'], parameters={"translate": (100, 50)})
G.add_node("merge", factory=Merge, inputs=['foreground', 'background'], parameters={"mix": 0.5})
G.add_node("cache", factory=Cache, inputs=['source'])
G.add_node("viewer", factory=Viewer, inputs=['source'])

G.add_edge("read", "transform", key=("out", "source"))
G.add_edge("transform", "merge", key=("out", "foreground"))
G.add_edge("read", "merge", key=("out", "background"))
G.add_edge("merge", "cache", key=("out", "source"))
G.add_edge("cache", "viewer", key=("out", "source"))

def realize(G):
    instances = {}
    for node in nx.topological_sort(G):
        factory: Callable = G.nodes[node]['factory']
        inputs = {}
        for pred in G.predecessors(node):
            edge_data = G.get_edge_data(pred, node)
            for key in edge_data:
                to_pin = edge_data[key]['to_pin']
                from_pin = edge_data[key]['from_pin']
                inputs[to_pin] = instances[pred]
        parameters = G.nodes[node]['parameters']
        instance = factory(**inputs, **parameters)
        instances[node] = instance
    return instances

print(f"working directory: {Path().cwd()}")
links = []
next_link_id = 1
texture_id = 0

frame = 0

import hashlib

def string_to_int64(s: str) -> int:
    h = hashlib.blake2b(
        s.encode("utf-8"),
        digest_size=8  # 64 bits
    ).digest()
    return int.from_bytes(h, byteorder="little", signed=False)

def gui():
    global texture_id, frame

    # get read_node input nodes from the by inspecting the class __init__ method, and check their values
    ed.begin("Node Editor")

    # --- Create nodes ---
    mapping = {}
    for n in G.nodes:
        mapping[string_to_int64(n)] = n
        ed.begin_node(ed.NodeId(string_to_int64(n)))
        factory = G.nodes[n]['factory']
        imgui.text(f"{n}")
        imgui.same_line()
        imgui.text(f"({G.nodes[n]['factory'].__name__})")

        # imgui.same_line()

        imgui.begin_group()
        sig = inspect.signature(factory.__init__)
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            if param.annotation == Video:
                ed.begin_pin(ed.PinId(string_to_int64(f"{n}.{param_name}")), ed.PinKind.input)
                ed.pin_pivot_alignment(imgui.ImVec2(0.0, 0.5))
                imgui.text(param_name)
                ed.end_pin()
        imgui.end_group()

        imgui.same_line()
        imgui.dummy(imgui.ImVec2(20, 1)) # Horizontal gap between In and Out
        imgui.same_line()

        imgui.begin_group()
        ed.begin_pin(ed.PinId(string_to_int64(f"{n}->out")), ed.PinKind.output)
        ed.pin_pivot_alignment(imgui.ImVec2(1.0, 0.5))
        imgui.text('out')
        ed.end_pin()
        imgui.end_group()


        ed.end_node()

    for n1, n2, key, data in G.edges(keys=True, data=True):
        outlet, inlet = key
        from_pin = ed.PinId(string_to_int64(f"{n1}->{outlet}"))
        to_pin = ed.PinId(string_to_int64(f"{n2}.{inlet}"))
        link_id = ed.LinkId(string_to_int64(f"{n1}->{n2}:{outlet}->{inlet}"))
        ed.link(link_id, from_pin, to_pin)

    # --- Create links ---




    # # Draw existing links
    # for link_id, out_pin, in_pin in links:
    #     ed.link(link_id, out_pin, in_pin)

    # # --- Create links ---
    # if ed.begin_create():
    #     in_pin = ed.PinId()
    #     out_pin = ed.PinId()
    #     if ed.query_new_link(in_pin, out_pin):
    #         if in_pin and out_pin:
    #             ed.accept_new_item()
    #             links.append(
    #                 (ed.LinkId(next_link_id), out_pin, in_pin)
    #             )
    #             next_link_id += 1
    #     ed.end_create()

    # # --- Delete links ---
    # if ed.begin_delete():
    #     link_id = ed.LinkId()
    #     while ed.query_deleted_link(link_id):
    #         ed.accept_deleted_item()
    #         links[:] = [l for l in links if l[0] != link_id]
    #     ed.end_delete()
    ed.end()

    # create the texture
    if texture_id == 0:
        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

    try:
        image = viewer_node(frame=frame)
        error_msg = ""
    except FileNotFoundError:
        image = np.zeros((256, 256, 4), dtype=np.uint8)
        error_msg = "File Not Found"
    height, width, channels = image.shape
    # image = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
    glTexImage2D(
        GL_TEXTURE_2D, 0, GL_RGBA32F,
        width, height, 0,
        GL_RGBA, GL_FLOAT, np.ascontiguousarray(image, dtype=np.float32)
    )

    imgui.begin("Inspector")
    for node_id in ed.get_selected_nodes():
        node_name = mapping.get(node_id.id(), "-Unknown-")
        imgui.text(f"Selected Node: {node_name}")
    imgui.end()

    imgui.begin("Viewer")
    imgui.text("[Viewer]")
    imgui.image(imgui.ImTextureRef(texture_id), imgui.ImVec2(256, 256))
    _, frame = imgui.slider_int("Frame", frame, 0, 100)
    if error_msg:
        imgui.text_colored(imgui.ImVec4(1.0, 0.0, 0.0, 1.0), error_msg)
    imgui.end()

if __name__ == "__main__":
    immapp.run(gui, with_node_editor=True)
