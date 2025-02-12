from collections import deque
from typing import Generator, Hashable
import networkx as nx
from typing import *

def dependents(G:nx.MultiDiGraph, start_node:Hashable):
    queue = deque([start_node])
    visited = set()
    while queue:
        n = queue.popleft()
        if n not in visited:
            yield n
            visited.add(n)

            for _, v in G.out_edges(n):
                queue.append(v)

def dependencies(G:nx.MultiDiGraph, start_node:Hashable):
    queue = deque([start_node])
    visited = set()
    while queue:
        n = queue.popleft()
        if n not in visited:
            yield n
            visited.add(n)

            for u, _ in G.in_edges(n):
                queue.append(u)

def get_topological_successors(G:nx.MultiDiGraph, start_node):
    """
    Get all successors of a start node in topological order, traversing through out_edges.
    
    Parameters:
        G (nx.MultiDiGraph): Input directed multigraph
        start_node: Starting node to find successors from
        
    Returns:
        list: Successors in topological order
    """
    # Get subgraph reachable from start_node
    reachable = set()
    queue = deque([start_node])
    
    while queue:
        node = queue.popleft()
        if node not in reachable:
            reachable.add(node)
            # Use out_edges to get successors
            for u,v, k_ in G.out_edges(node, keys=True):
                queue.append(v)
    subgraph = G.subgraph(reachable)
    
    # Get topological sort of the subgraph
    try:
        topo_order = list(nx.topological_sort(subgraph))
        # Filter to only include successors (exclude start_node)
        return [node for node in topo_order]
    except nx.NetworkXUnfeasible:
        raise ValueError("Graph contains cycles, topological sort not possible")


def hiearchical_layout_with_grandalf(G, scale=1):
    import grandalf
    from grandalf.layouts import SugiyamaLayout

    g = grandalf.utils.convert_nextworkx_graph_to_grandalf(G)

    class defaultview(object):  # see README of grandalf's github
        w, h = scale, scale

    for v in g.C[0].sV:
        v.view = defaultview()
    sug = SugiyamaLayout(g.C[0])
    sug.init_all()  # roots=[V[0]])
    sug.draw()
    return {
        v.data: (v.view.xy[0], v.view.xy[1]) for v in g.C[0].sV
    }  # Extracts the positions


import networkx as nx
T = TypeVar('T')
def hiearchical_layout_with_nx(G:nx.DiGraph, scale=100)->dict[Any, tuple[float, float]]:
    for layer, nodes in enumerate(
        reversed(tuple(nx.topological_generations(G)))
    ):
        # `multipartite_layout` expects the layer as a node attribute, so add the
        # numeric layer value as a node attribute
        for node in nodes:
            G.nodes[node]["layer"] = -layer

    # Compute the multipartite_layout using the "layer" node attribute
    pos = nx.multipartite_layout(
        G, subset_key="layer", align="horizontal"
    )
    for n, p in pos.items():
        pos[n] = p[0] * scale, p[1] * scale
    return pos

