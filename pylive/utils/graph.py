from collections import deque
from typing import Generator, Hashable
import networkx as nx

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