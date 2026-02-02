from typing import Any, Callable, Hashable, Protocol, Tuple, List, Dict, cast
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


available_factories = [
    Read,
    Transform,
    Merge,
    Cache,
    Viewer,
]

# # create_pipeline
# read_node = Read(r"./assets/SMPTE_Color_Bars_animation/SMPTE_Color_Bars_animation_%05d.png")
# transform_node = Transform(read_node, (100, 50))
# merge_node = Merge(transform_node, read_node, 0.5)
# cache_node = Cache(merge_node)
# viewer_node = Viewer(cache_node)

@dataclass
class Data:
    ...



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


from functools import lru_cache

@lru_cache(maxsize=1) #TODO: this is a temporary fix to speed up the bake process during GUI interaction, but probably this si exaclt what we want, in a different place.
def bake(engine_graph: nx.MultiDiGraph, target_node: str) -> Callable | None:
    """Realize the graph into an actual callable Video pipeline for a specific node."""
    
    # 1. Get all nodes required for the target (ancestors + the node itself)
    required_nodes = nx.ancestors(engine_graph, target_node)
    required_nodes.add(target_node)
    
    # 2. Create a subgraph to ensure we only iterate over necessary nodes
    subgraph= cast(nx.MultiDiGraph, state.graph.subgraph(required_nodes))
    
    instances = {}
    
    # 3. Process only the required nodes in topological order
    for node_id in nx.topological_sort(subgraph):
        node_data = subgraph.nodes[node_id]
        factory = node_data['factory']
        parameters = node_data.get('parameters', {})
        
        # 4. Gather the baked closures from predecessors
        inputs = {}
        for pred in subgraph.predecessors(node_id):
            edge_data:Dict[Hashable, Any] = subgraph.get_edge_data(pred, node_id)
            for key_tuple, data in edge_data.items():
                from_pin, to_pin = key_tuple
                inputs[to_pin] = instances[pred]
        
        # 5. Bake the closure
        try:
            instance = factory(**inputs, **parameters)
            instances[node_id] = instance
        except Exception as e:
            instances[node_id] = None
            print(f"Error creating instance for node {node_id}: {e}")
        
    return instances[target_node]


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

def show_node_style_editor():
    imgui.begin("Node Editor Style Editor")
    style = ed.get_style()

    changed, new_node_padding = imgui.input_float4("Node Padding", [style.node_padding.x, style.node_padding.y, style.node_padding.z, style.node_padding.w])
    if changed:
        style.node_padding = imgui.ImVec4(new_node_padding[0], new_node_padding[1], new_node_padding[2], new_node_padding[3])
    # style.node_padding = imgui.ImVec4(8.0, 0.0, 8.0, 0.0)

    changed, new_pin_radius = imgui.input_float("Pin Radius", style.pin_radius)
    if changed:
        style.pin_radius = new_pin_radius

    changed, new_link_strength = imgui.input_float("Link Strength", style.link_strength)
    if changed:
        style.link_strength = new_link_strength

    changed, new_pin_arrow_size = imgui.input_float("Pin Arrow Size", style.pin_arrow_size)
    if changed:
        style.pin_arrow_size = new_pin_arrow_size

    changed, new_pin_arrow_width = imgui.input_float("Pin Arrow Width", style.pin_arrow_width)
    if changed:
        style.pin_arrow_width = new_pin_arrow_width

    changed, new_pin_border_width = imgui.input_float("Pin Border Width", style.pin_border_width)
    if changed:
        style.pin_border_width = new_pin_border_width

    changed, new_pivot_size = imgui.input_float2("Pivot Size", [style.pivot_size.x, style.pivot_size.y])
    if changed:
        style.pivot_size = imgui.ImVec2(new_pivot_size[0], new_pivot_size[1])

    changed, new_pivot_scale = imgui.input_float2("Pivot Scale", [style.pivot_scale.x, style.pivot_scale.y])
    if changed:
        style.pivot_scale = imgui.ImVec2(new_pivot_scale[0], new_pivot_scale[1])

    change, new_pin_corners = imgui.input_float("Pivot Corners", style.pin_corners)
    if change:
        style.pin_corners = new_pin_corners

    # colors
    style.node_border_width = 0.0
    style.node_rounding = 0.0
    
    # style.set_color_(ed.StyleColor.pin_rect, imgui.ImVec4(1.0, 0.0, 1.0, 1.0))
    # style.set_color_(ed.StyleColor.pin_rect_border, imgui.ImVec4(0.0, 1.0, 1.0, 1.0))
    # style.set_color_(ed.StyleColor.pin_rect_border, imgui.ImVec4(0.0, 1.0, 1.0, 1.0))
    style.source_direction = imgui.ImVec2(0.0, 1.0)
    style.target_direction = imgui.ImVec2(0.0, -1.0)
    

    config = ed.get_config()


    imgui.end()

def show_graph(state:State):
    
    imgui.begin("Pipeline Graph")
    


    show_node_style_editor()

    ed.begin("Node Editor")
    imgui.push_style_var(imgui.StyleVar_.item_spacing, imgui.ImVec2(8.0, 0.0))
    ed.suspend()
    
    ed.resume()
    def show_inlet(node_name: str, param_name: str):
        ed.push_style_var(ed.StyleVar.pin_arrow_size, 10.0)
        ed.push_style_var(ed.StyleVar.pin_arrow_width, 10.0)
        ed.begin_pin(ed.PinId(string_to_int64(f"{node_name}-{param_name}")), ed.PinKind.input)
        ed.pin_pivot_alignment(imgui.ImVec2(0.5, 0.5))
        # imgui.text(param_name)
        pos = imgui.get_cursor_screen_pos()
        r = imgui.get_style().font_size_base / 4
        draw_list = imgui.get_window_draw_list()
        draw_list.add_circle_filled(pos+imgui.ImVec2(r-2, r-2), r-1, imgui.color_convert_float4_to_u32(imgui.ImVec4(1, 1, 1, 1)))
        imgui.dummy(imgui.ImVec2(r*2, r*2))
        # imgui.text(f"{param_name}")
        ed.end_pin()
        ed.pop_style_var(2)
        # imgui.set_tooltip(f"Inlet: {param_name}")
        if imgui.is_item_hovered():
            draw_list.add_text(pos+imgui.ImVec2(0,-14), imgui.color_convert_float4_to_u32(imgui.ImVec4(1, 1, 1, 1)), f"{param_name}")
    

    def show_outlet(node_name: str):
        ed.begin_pin(ed.PinId(string_to_int64(f"{node_name}->out")), ed.PinKind.output)
        ed.pin_pivot_alignment(imgui.ImVec2(0.5, 0.5))
        pos = imgui.get_cursor_screen_pos()
        r = imgui.get_style().font_size_base / 4
        imgui.get_window_draw_list().add_circle_filled(pos+imgui.ImVec2(r-2, r-2), r-1, imgui.color_convert_float4_to_u32(imgui.ImVec4(1, 1, 1, 1)))
        imgui.dummy(imgui.ImVec2(r*2, r*2))
        ed.end_pin()

    def show_node(node_name: str):
        ed.begin_node(ed.NodeId(string_to_int64(node_name)))
        factory = state.graph.nodes[node_name]['factory']
        sig = inspect.signature(factory.__init__)
        has_inlets = False
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue

            if param.annotation == Video:
                inlet_mapping[string_to_int64(f"{n}-{param_name}")] = (node_name, param_name)
                show_inlet(node_name, param_name)
                imgui.same_line()
                has_inlets = True
        
        if has_inlets:
            imgui.new_line()

        imgui.text(f"{n}")
        imgui.same_line()
        imgui.text(f"({state.graph.nodes[n]['factory'].__name__})")

        outlet_mapping[string_to_int64(f"{n}->out")] = (node_name, "out")
        show_outlet(node_name)


        ed.end_node()

    # --- Collect and Show Nodes ---
    node_mapping: Dict[int, str] = {}
    inlet_mapping:  Dict[int, Tuple[str, str]] = {}
    outlet_mapping: Dict[int, Tuple[str, str]] = {}
    for n in state.graph.nodes:
        node_mapping[string_to_int64(n)] = n
        show_node(n)

    # --- Show Edges ---
    link_id_to_edge = {}
    for n1, n2, key, data in state.graph.edges(keys=True, data=True):
        outlet, inlet = key
        from_pin = ed.PinId(string_to_int64(f"{n1}->{outlet}"))
        to_pin =   ed.PinId(string_to_int64(f"{n2}-{inlet}"))
        link_id =  ed.LinkId(string_to_int64(f"{n1}->{n2}:{outlet}->{inlet}"))
        link_id_to_edge[link_id.id()] = (n1, n2, key)
        # Highlight selected links
        selected_links = [l.id() for l in ed.get_selected_links()]
        if link_id.id() in selected_links:
            ed.link(link_id, from_pin, to_pin, color=(1.0, 1.0, 1.0, 1.0), thickness=3.0)
        else:
            ed.link(link_id, from_pin, to_pin)

    # --- Create links ---
    if ed.begin_create():
        end_pin = ed.PinId()
        start_pin = ed.PinId()
        if ed.query_new_link(start_pin, end_pin):
            if start_pin.id() == end_pin.id():
                ed.reject_new_item()

            print("Creating link from pin", start_pin.id(), "to pin", end_pin.id())

            if start_pin.id() in inlet_mapping and end_pin.id() in outlet_mapping:
                in_node, in_name = inlet_mapping[start_pin.id()]
                out_node, out_name = outlet_mapping[end_pin.id()]
                if ed.accept_new_item():
                    print(f"Creating link from {out_node}.{out_name} to {in_node}.{in_name}")
                    state.graph.add_edge(out_node, in_node, key=(out_name, in_name))
            elif end_pin.id() in inlet_mapping and start_pin.id() in outlet_mapping:

                in_node, in_name = inlet_mapping[end_pin.id()]
                out_node, out_name = outlet_mapping[start_pin.id()]
                if ed.accept_new_item():
                    print(f"Creating link from {out_node}.{out_name} to {in_node}.{in_name}")
                    state.graph.add_edge(out_node, in_node, key=(out_name, in_name))
            else:
                ed.reject_new_item()
        ed.end_create()

    # --- Update Selection ---
    state.selection = [node_mapping[node_id.id()] for node_id in ed.get_selected_nodes() if node_id.id() in node_mapping]
    state.current = state.selection[-1] if len(state.selection) > 0 else None

    imgui.pop_style_var()
    # --- Interaction & Context Menu ---
    ed.suspend()
    if ed.show_background_context_menu():
        imgui.open_popup("node_context_menu")
    
    from pylive.utils import unique
    popup_open = imgui.begin_popup("node_context_menu")
    if popup_open:
        # Example: Adding a node based on a specific factory
        if imgui.begin_menu("Add Node"):
            for factory in available_factories:
                selected = False
                clicked, selected = imgui.menu_item(f"{factory.__name__}", '', selected, True)
                if clicked:
                    new_id = unique.make_unique_name(factory.__name__.lower(), names=state.graph.nodes)
                    # Logic to update your backend graph:
                    state.graph.add_node(new_id, factory=factory)
            imgui.end_menu()
        clicked, selected = imgui.menu_item(f"Delete", '', False, True)
        if clicked:
            for link in ed.get_selected_links():
                edge = link_id_to_edge.get(link.id())
                if edge:
                    n1, n2, key = edge
                    if state.graph.has_edge(n1, n2, key=key):
                        state.graph.remove_edge(n1, n2, key=key)
            for node_name in state.selection:
                state.graph.remove_node(node_name)
                state.selection.remove(node_name)
                if state.current == node_name:
                    state.current = None
        imgui.end_popup()
    ed.resume()
    
    ed.end()
    imgui.end()

def show_nodes(state:State):
    imgui.begin("Nodes")
    for node_name in state.graph.nodes:
        imgui.text(f"Node: {node_name}")
    
    for source, target, key in state.graph.edges(keys=True):
        outlet, inlet = key
        imgui.text(f"Edge: {source}.{outlet} -> {target}.{inlet}")
    imgui.end()

def show_inspector(state:State):
    # --- Inspector ---
    imgui.begin("Inspector")
    for node_name in state.selection:
        imgui.text(f"Selected Node: {node_name}")
        engine_graph_node = state.graph.nodes.get(node_name)
        
        if engine_graph_node is None:
            imgui.text(f"Node '{node_name}' not found in graph.")
            continue
        
        factory = engine_graph_node['factory']
        imgui.same_line()
        imgui.text(f"Factory: {factory.__name__}")
        parameters = engine_graph_node.get('parameters', {})

        sig = inspect.signature(factory.__init__)
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            if param.annotation == Video:
                continue

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
                state.graph.nodes[node_name]["parameters"][param_name] = new_value

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
    show_nodes(state)

    # --- Render the Pipeline ---
    # bake the pipeline

    if state.current is not None:
        start_bake_time = time.perf_counter()
        pipeline = bake(engine_graph, state.current)
        end_bake_time = time.perf_counter()
        delta_bake_time = end_bake_time - start_bake_time
        imgui.text(f"Bake time: {delta_bake_time:.4f} seconds")

        # run the pipeline
        try:
            start_processing_time = time.perf_counter()
            state.current_result = pipeline(frame=state.frame)
            end_processing_time = time.perf_counter()
            delta_processing_time = end_processing_time - start_processing_time
            if delta_processing_time == 0:
                fps = float('inf')
            else:
                fps = 1.0 / delta_processing_time
            imgui.text(f"Processing time: {delta_processing_time:.4f} seconds / {fps if fps != float('inf') else 'inf'} FPS")
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
