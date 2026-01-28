from typing import Any, Callable, Protocol, Tuple, List, Dict, cast
from imgui_bundle import imgui, immapp
from imgui_bundle import imgui_node_editor as ed

from dataclasses import dataclass, field
from pathlib import Path
import inspect
import image_utils
import numpy as np

import numpy as np
from OpenGL.GL import *
import time
import networkx as nx

# --- TYPES ---
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



# # create_pipeline
# read_node = Read(r"./assets/SMPTE_Color_Bars_animation/SMPTE_Color_Bars_animation_%05d.png")
# transform_node = Transform(read_node, (100, 50))
# merge_node = Merge(transform_node, read_node, 0.5)
# cache_node = Cache(merge_node)
# viewer_node = Viewer(cache_node)



@dataclass
class Data:
    """ the data file describing the timeline"""
    ...


from functools import lru_cache

@lru_cache(maxsize=1) #TODO: this is a temporary fix to speed up the bake process during GUI interaction, but probably this si exaclt what we want, in a different place.
def bake(engine_graph: nx.MultiDiGraph, target_node: str) -> Callable:
    """Realize the graph into an actual callable Video pipeline for a specific node."""
    
    # 1. Get all nodes required for the target (ancestors + the node itself)
    required_nodes = nx.ancestors(engine_graph, target_node)
    required_nodes.add(target_node)
    
    # 2. Create a subgraph to ensure we only iterate over necessary nodes
    subgraph= cast(nx.MultiDiGraph, engine_graph.subgraph(required_nodes))
    
    instances = {}
    
    # 3. Process only the required nodes in topological order
    for node_id in nx.topological_sort(subgraph):
        node_data = subgraph.nodes[node_id]
        factory = node_data['factory']
        parameters = node_data.get('parameters', {})
        
        # 4. Gather the baked closures from predecessors
        inputs = {}
        for pred in subgraph.predecessors(node_id):
            edge_data = subgraph.get_edge_data(pred, node_id)
            for key_tuple, data in edge_data.items():
                from_pin, to_pin = key_tuple
                inputs[to_pin] = instances[pred]
        
        # 5. Bake the closure
        instance = factory(**inputs, **parameters)
        instances[node_id] = instance
        
    return instances[target_node]

print(f"working directory: {Path().cwd()}")




engine_graph = nx.MultiDiGraph()
engine_graph.add_node("read", factory=Read, inputs=[], parameters={"path": r"./assets/SMPTE_Color_Bars_animation/SMPTE_Color_Bars_animation_%05d.png"})
engine_graph.add_node("transform", factory=Transform, inputs=['source'], parameters={"translate": (100, 50)})
engine_graph.add_node("merge", factory=Merge, inputs=['foreground', 'background'], parameters={"mix": 0.5})
engine_graph.add_node("cache", factory=Cache, inputs=['source'])
engine_graph.add_node("viewer", factory=Viewer, inputs=['source'])

engine_graph.add_edge("read", "transform", key=("out", "source"))
engine_graph.add_edge("transform", "merge", key=("out", "foreground"))
engine_graph.add_edge("read", "merge", key=("out", "background"))
engine_graph.add_edge("merge", "cache", key=("out", "source"))
engine_graph.add_edge("cache", "viewer", key=("out", "source"))

@dataclass
class State:
    """the gui state"""
    graph:nx.MultiDiGraph
    frame:int = 0
    selection: List[str] = field(default_factory=list)
    status:str = ""
    error_msg:str = ""
    current: str|None = None
    current_result: Any=None

state = State(graph=engine_graph)

import hashlib
def string_to_int64(s: str) -> int:
    h = hashlib.blake2b(
        s.encode("utf-8"),
        digest_size=8  # 64 bits
    ).digest()
    return int.from_bytes(h, byteorder="little", signed=False)
    

def show_graph(state:State):
    imgui.begin("Pipeline Graph")
    ed.begin("Node Editor")

    # --- Create nodes ---
    mapping: Dict[int, str] = {}
    for n in engine_graph.nodes:
        mapping[string_to_int64(n)] = n
        ed.begin_node(ed.NodeId(string_to_int64(n)))
        factory = engine_graph.nodes[n]['factory']
        imgui.text(f"{n}")
        imgui.same_line()
        imgui.text(f"({engine_graph.nodes[n]['factory'].__name__})")

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

    for n1, n2, key, data in engine_graph.edges(keys=True, data=True):
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
    state.selection = [mapping[node_id.id()] for node_id in ed.get_selected_nodes()]
    state.current = state.selection[-1] if len(state.selection) > 0 else None
    ed.end()
    imgui.end()

def show_inspector(state:State):
    # --- Inspector ---
    imgui.begin("Inspector")
    for node_name in state.selection:
        imgui.text(f"Selected Node: {node_name}")
        engine_graph_node = engine_graph.nodes[node_name]
        factory = engine_graph_node['factory']
        imgui.text(f"Factory: {factory.__name__}")
        parameters = engine_graph_node.get('parameters', {})
        imgui.text("Parameters:")
        sig = inspect.signature(factory.__init__)
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            if param.annotation == Video:
                continue
            imgui.text(f"{param_name}: ")
            imgui.same_line()
            imgui.text(f"({param.annotation.__name__})")
            imgui.same_line()

            changed = False
            new_value = None

            value = parameters.get(param_name, "")
            match value:
                case int():
                    changed, new_value = imgui.input_int(param_name, int(value) if value != "" else 0)
                case float():
                    changed, new_value = imgui.input_float(param_name, float(value) if value != "" else 0.0)
                case str():
                    changed, new_value = imgui.input_text(param_name, str(value) if value != "" else "")
                case tuple():
                    changed, new_value = imgui.input_float2(param_name, value)
                    new_value = tuple(new_value)
                case _:
                    imgui.text(f"Unsupported parameter type: {type(value)}")

            if changed:
                engine_graph.nodes[node_name]["parameters"][param_name] = new_value

    imgui.end()

texture_id = 0
def show_viewer(state:State):
    global texture_id

    image = state.current_result
    imgui.begin("Viewer")

    match image:
        case np.ndarray():
            height, width, channels = image.shape
            if texture_id == 0:
                texture_id = glGenTextures(1)
                glBindTexture(GL_TEXTURE_2D, texture_id)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

            glBindTexture(GL_TEXTURE_2D, texture_id)
            glTexImage2D(
                GL_TEXTURE_2D, 0, GL_RGBA32F,
                width, height, 0,
                GL_RGBA, GL_FLOAT, np.ascontiguousarray(image, dtype=np.float32)
            )

            imgui.image(imgui.ImTextureRef(texture_id), imgui.ImVec2(128, 128))
        case _:
            imgui.text("No image to display")
    imgui.end()

def show_log(state:State):
    # show log
    imgui.begin("Log")
    imgui.text(f"Frame: {state.frame}")
    imgui.end()

def show_timeline(state:State):
    imgui.begin("Timeline")
    changed, new_frame = imgui.slider_int("Frame", state.frame, 0, 100)
    if changed:
        state.frame = new_frame
    imgui.end()

def gui():
    # get read_node input nodes from the by inspecting the class __init__ method, and check their values
    show_graph(state)
    show_inspector(state)

    # --- Render the Pipeline ---
    # bake the pipeline

    if state.current is not None:
        start_processing_time = time.time()
        pipeline = bake(engine_graph, state.current)
        end_processing_time = time.time()
        fps = 1.0 / (end_processing_time - start_processing_time)
        imgui.text(f"Bake time: {end_processing_time - start_processing_time:.4f} seconds / {fps:.2f} FPS")

        # run the pipeline
        try:
            start_processing_time = time.time()
            state.current_result = pipeline(frame=state.frame)
            end_processing_time = time.time()
            fps = 1.0 / (end_processing_time - start_processing_time)
            imgui.text(f"Processing time: {end_processing_time - start_processing_time:.4f} seconds / {fps:.2f} FPS")
            error_msg = ""
        except Exception as e:
            state.current_result = None
            state.error_msg = str(e)
            print("Error during running the pipeline", e)
    else:
        state.current_result = None
        state.error_msg = ""


    show_log(state)

    imgui.begin("status")
    imgui.text(f"current: {state.current}")
    imgui.end()

    # show pipeline output


    show_viewer(state)
    show_timeline(state)

if __name__ == "__main__":
    immapp.run(gui, with_node_editor=True)
