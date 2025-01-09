

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
def hiearchical_layout_with_nx(G, scale=100):
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

