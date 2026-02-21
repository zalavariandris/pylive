from typing import Any, Callable, Hashable, Protocol, Tuple, List, Dict, cast
from imgui_bundle import imgui, immapp
from imgui_bundle import imgui_node_editor as ed

from dataclasses import dataclass, field

@dataclass
class Node:
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)

import networkx as nx

@dataclass
class State:
    _graph = nx.MultiDiGraph()
    current: str|None = None

    def add_node(self, name: str, pos:Tuple[float, float], inputs: List[str], outputs: List[str]):
        self._graph.add_node(name, pos=pos, inputs=inputs, outputs=outputs)

    def remove_node(self, name: str):
        self._graph.remove_node(name)

    def add_edge(self, source: str, target: str, outlet:str, inlet:str):
        key = (outlet, inlet)
        self._graph.add_edge(source, target, key=key)

    def remove_edge(self, source: str, target: str, outlet:str, inlet:str):
        key = (outlet, inlet)
        self._graph.remove_edge(source, target, key=key)


done_setup = False
def setup():
    global done_setup
    if done_setup:
        return
    print("Setting up the editor...")
    ctx = ed.default_node_editor_context_immapp()
    ed.set_current_editor(ctx)
    style = ed.get_style()
    style.set_color_(ed.StyleColor.node_border, imgui.ImVec4(1.0, 0.4, 0.4, 1.0))
    style.set_color_(ed.StyleColor.pin_rect, imgui.ImVec4(0.8, 0.8, 0.8, 1.0))
    done_setup = True

def show_graph(state: State):
    ed.begin("My Graph Editor")
    style = ed.get_style()
    style.source_direction = imgui.ImVec2(0.0, 1.0)  # Links go from right to left
    style.target_direction = imgui.ImVec2(0.0, -1.0)  # Links come into the left side of pins
    imgui.push_style_var(imgui.StyleVar_.item_spacing, imgui.ImVec2(8.0, 0.0))
    ed.push_style_var(ed.StyleVar.node_padding, imgui.ImVec4(8.0, 0.0, 8.0, 0.0))

    # -- Render Nodes --
    node_map = dict()
    pin_id_to_node_port = dict()
    node_port_to_pin_id = dict()  # (node_name, port_name, port_type) -> pin_id
    node_id_to_name = dict()  # node_id -> node_name
    item_id = 1
    for node_name, node in state._graph.nodes(data=True):
        node_map[node_name] = node
        node_id = item_id
        node_id_to_name[node_name] = node_id
        # Push state position to editor on first appearance


        ed.begin_node(ed.NodeId(item_id))
        item_id += 1
        imgui.begin_horizontal(f"node_content_{node_name}")
        imgui.spring(0.5)
        for input_name in node['inputs']:
            ed.begin_pin(ed.PinId(item_id), ed.PinKind.input)
            pin_id_to_node_port[item_id] = (node_name, input_name, "input")
            node_port_to_pin_id[(node_name, input_name, "input")] = item_id
            item_id += 1
            imgui.dummy(imgui.ImVec2(12, 6))
            if imgui.is_item_hovered():
                fg_dl = imgui.get_foreground_draw_list()
                rect_min_screen = ed.canvas_to_screen(imgui.get_item_rect_min())
                rect_max_screen = ed.canvas_to_screen(imgui.get_item_rect_max())
                fg_dl.push_clip_rect(rect_min_screen-imgui.ImVec2(40, 40), rect_max_screen+imgui.ImVec2(40, 40), False)
                fg_dl.add_text(rect_min_screen-imgui.ImVec2(0, 20), imgui.color_convert_float4_to_u32(imgui.ImVec4(1.0, 1.0, 1.0, 1.0)), f"{input_name}")
                fg_dl.pop_clip_rect()
            else:
                style = ed.get_style()
                color = style.color_(ed.StyleColor.node_border)
                dl = imgui.get_window_draw_list()
                dl.add_rect_filled(imgui.get_item_rect_min(), imgui.get_item_rect_max(), imgui.color_convert_float4_to_u32(color), rounding=4.0)
            ed.end_pin()
            imgui.spring(1.0)
        imgui.end_horizontal()

        imgui.begin_horizontal(f"node_title_{node_name}")
        imgui.spring(0.5)
        imgui.text(f"{node_name} ({node['pos'][0]:.1f}, {node['pos'][1]:.1f})")
        imgui.spring(0.5)
        imgui.end_horizontal()

        imgui.begin_horizontal(f"node_outputs_{node_name}")
        imgui.spring(0.5)
        for output_name in node['outputs']:
            ed.begin_pin(ed.PinId(item_id), ed.PinKind.output)
            pin_id_to_node_port[item_id] = (node_name, output_name, "output")
            node_port_to_pin_id[(node_name, output_name, "output")] = item_id
            item_id += 1
            imgui.dummy(imgui.ImVec2(12, 6))
            if imgui.is_item_hovered():
                fg_dl = imgui.get_foreground_draw_list()
                rect_min_screen = ed.canvas_to_screen(imgui.get_item_rect_min())
                rect_max_screen = ed.canvas_to_screen(imgui.get_item_rect_max())
                fg_dl.push_clip_rect(rect_min_screen-imgui.ImVec2(40, 40), rect_max_screen+imgui.ImVec2(100, 40), False)
                fg_dl.add_text(rect_max_screen-imgui.ImVec2(0, 0), imgui.color_convert_float4_to_u32(imgui.ImVec4(1.0, 1.0, 1.0, 1.0)), f"{output_name}")
                fg_dl.pop_clip_rect()
            else:
                style = ed.get_style()
                color = style.color_(ed.StyleColor.node_border)
                dl = imgui.get_window_draw_list()
                dl.add_rect_filled(imgui.get_item_rect_min(), imgui.get_item_rect_max(), imgui.color_convert_float4_to_u32(color), rounding=4.0)
            ed.end_pin()
            imgui.spring(1.0)
        imgui.end_horizontal()
        ed.end_node()

    # -- Render Links --
    link_id = 1000  # Start link IDs at a higher number to avoid conflicts
    link_id_to_edge = dict()  # link_id -> (source_node, target_node, edge_key)
    for source_node, target_node, edge_key in state._graph.edges(keys=True):
        output_pin_name, input_pin_name = edge_key
        # Get pin IDs for this link
        source_pin_id = node_port_to_pin_id.get((source_node, output_pin_name, "output"))
        target_pin_id = node_port_to_pin_id.get((target_node, input_pin_name, "input"))
        
        if source_pin_id and target_pin_id:
            ed.link(ed.LinkId(link_id), ed.PinId(source_pin_id), ed.PinId(target_pin_id))
            link_id_to_edge[link_id] = (source_node, target_node, edge_key)
            link_id += 1

    # Read editor positions back to state (keeps state in sync when user drags nodes)
    for node_name, node_id in node_id_to_name.items():
        pos = ed.get_node_position(ed.NodeId(node_id))
        state._graph.nodes[node_name]['pos'] = (pos.x, pos.y)

    # Handle link creation
    if ed.begin_create():
        start_pin_id = ed.PinId()
        end_pin_id = ed.PinId()

        if ed.query_new_link(start_pin_id, end_pin_id):
            start_id = start_pin_id.id()
            end_id = end_pin_id.id()
            
            # Check if both pins exist and are of different types
            if start_id in pin_id_to_node_port and end_id in pin_id_to_node_port:
                start_node, start_pin_name, start_type = pin_id_to_node_port[start_id]
                end_node, end_pin_name, end_type = pin_id_to_node_port[end_id]
                
                # Ensure one is input and one is output
                if start_type != end_type:
                    if ed.accept_new_item():
                        # Create the link (ensure start is output, end is input)
                        if start_type == "output":
                            state.add_edge(start_node, end_node, outlet=start_pin_name, inlet=end_pin_name)
                        else:
                            state.add_edge(end_node, start_node, outlet=end_pin_name, inlet=start_pin_name)
                else:
                    ed.reject_new_item()
            else:
                ed.reject_new_item()

        # Link Dragged to empty space -> create new node and link to it
        new_node_pin = ed.PinId()
        if ed.query_new_node(new_node_pin):
            if ed.accept_new_item():
                
                if new_node_pin.id() not in pin_id_to_node_port:
                    raise Exception("New node pin ID not found in mapping")
                
                source_node, source_pin_name, source_type = pin_id_to_node_port[new_node_pin.id()]
                new_node_name = f"Node{len(state._graph.nodes)}"
                pos = imgui.get_mouse_pos()
                pos = ed.screen_to_canvas(pos)
                if source_type == "output":
                    # Dragged from output -> create node with input and link to it
                    state.add_node(new_node_name, pos=(pos.x, pos.y), inputs=["in1"], outputs=["out1"])
                    state.add_edge(source_node, new_node_name, outlet=source_pin_name, inlet="in1")
                else:
                    # Dragged from input -> create node with output and link from it
                    state.add_node(new_node_name, pos=(pos.x, pos.y), inputs=["in1"], outputs=["out1"])
                    state.add_edge(new_node_name, source_node, outlet="out1", inlet=source_pin_name)

        ed.end_create()

    # Handle Delete selected nodes and links
    if ed.begin_delete():
        # Delete links
        deleted_link_id = ed.LinkId()
        while ed.query_deleted_link(deleted_link_id):
            if ed.accept_deleted_item():
                lid = deleted_link_id.id()
                if lid in link_id_to_edge:
                    src, tgt, key = link_id_to_edge[lid]
                    outlet, inlet = key
                    state.remove_edge(src, tgt, outlet=outlet, inlet=inlet)

        # Delete nodes
        deleted_node_id = ed.NodeId()
        while ed.query_deleted_node(deleted_node_id):
            if ed.accept_deleted_item():
                nid = deleted_node_id.id()
                # Find the node name from the node id
                for node_name, mapping_id in node_id_to_name.items():
                    if mapping_id == nid:
                        state.remove_node(node_name)
                        break
        ed.end_delete()

    imgui.pop_style_var()
    ed.end()

    # -- new node on background double-click --
    if ed.is_background_double_clicked():
        pos = imgui.get_mouse_pos()
        pos = ed.screen_to_canvas(pos)
        state.add_node(f"Node{len(state._graph.nodes)}", inputs=["in1"], outputs=["out1"], pos=(pos.x, pos.y))


state = State()
state.add_node("A", pos=(0, 0), inputs=["in1", "in2"], outputs=["out1"])
state.add_node("B", pos=(200, 0), inputs=["in1"], outputs=["out1", "out2"])

def gui():
    global state

    imgui.begin("Hello, world!")
    # # imgui.text("This is some useful text.")
    # zoom = ed.get_current_zoom()
    # ctx = ed.default_node_editor_context_immapp()
    # ed.set_current_editor(ctx)

    show_graph(state)

    imgui.end()


if __name__ == "__main__":
    from imgui_bundle import hello_imgui
    immapp.run(
        runner_params=hello_imgui.RunnerParams(
            callbacks=hello_imgui.RunnerCallbacks(
                show_gui=gui
            )
        ),
        add_ons_params=immapp.AddOnsParams(
            with_node_editor=True
        )
    )
