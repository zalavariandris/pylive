import networkx as nx
import numpy as np

class SugiyamaLayout:
    def __init__(self, graph):
        """
        Initialize Sugiyama layout for a directed acyclic graph
        
        :param graph: networkx DiGraph
        """
        self.G = graph
        self.layers = self._assign_layers()
        self.layer_positions = {}
        
    def _assign_layers(self):
        """
        Assign nodes to layers using longest path method
        
        :return: Dictionary of nodes mapped to their layer
        """
        # Use NetworkX's topological sort to help with layer assignment
        try:
            # Compute longest path to each node
            layers = {}
            for node in nx.topological_sort(self.G):
                # Find max layer of predecessors and add 1
                pred_layers = [layers.get(p, -1) for p in self.G.predecessors(node)]
                layers[node] = max(pred_layers) + 1 if pred_layers else 0
            
            return layers
        except nx.NetworkXUnfeasible:
            raise ValueError("Graph must be acyclic")
    
    def _minimize_crossings(self):
        """
        Reduce edge crossings within each layer
        
        Uses a barycenter heuristic to reduce crossings
        """
        # Group nodes by layer
        layers_by_level = {}
        for node, layer in self.layers.items():
            if layer not in layers_by_level:
                layers_by_level[layer] = []
            layers_by_level[layer].append(node)
        
        # Sort nodes in each layer by barycenter of connected nodes
        for layer, nodes in layers_by_level.items():
            # Calculate barycenter for each node
            def barycenter_key(node):
                # Predecessors and successors positions
                pred_pos = [self.layers.get(p, 0) for p in self.G.predecessors(node)]
                succ_pos = [self.layers.get(s, 0) for s in self.G.successors(node)]
                
                # Average position of connected nodes
                all_pos = pred_pos + succ_pos
                return np.mean(all_pos) if all_pos else 0
            
            # Sort nodes based on barycenter
            layers_by_level[layer] = sorted(nodes, key=barycenter_key)
        
        return layers_by_level
    
    def compute_layout(self, horizontal_spacing=1.0, vertical_spacing=1.0):
        """
        Compute node positions using Sugiyama layout algorithm
        
        :param horizontal_spacing: Space between nodes horizontally
        :param vertical_spacing: Space between layers vertically
        :return: Dictionary of node positions
        """
        # Minimize crossings
        optimized_layers = self._minimize_crossings()
        
        # Assign coordinates
        node_positions = {}
        for layer, nodes in optimized_layers.items():
            # Distribute nodes evenly in the layer
            for i, node in enumerate(nodes):
                node_positions[node] = (
                    i * horizontal_spacing,  # x-coordinate
                    layer * vertical_spacing  # y-coordinate
                )
        
        return node_positions

# Example usage
def create_example_dag():
    """Create a sample directed acyclic graph"""
    G = nx.DiGraph()
    
    # Add edges to create a sample DAG
    edges = [
        ('A', 'C'), ('A', 'D'),
        ('B', 'C'), ('B', 'E'),
        ('C', 'F'),
        ('D', 'F'), ('D', 'G'),
        ('E', 'G')
    ]
    G.add_edges_from(edges)
    
    return G

# Demonstration
def main():
    # Create a sample DAG
    G = create_example_dag()
    
    # Create Sugiyama layout
    layout = SugiyamaLayout(G)
    positions = layout.compute_layout()
    
    # Print node positions
    for node, (x, y) in positions.items():
        print(f"Node {node}: Position (x={x}, y={y})")
    
    # Optionally visualize with networkx and matplotlib
    import matplotlib.pyplot as plt
    
    plt.figure(figsize=(10, 6))
    nx.draw(G, pos=positions, with_labels=True, 
            node_color='lightblue', 
            node_size=500, 
            arrows=True)
    plt.title("Sugiyama Layout Visualization")
    plt.show()

if __name__ == "__main__":
    main()