from pylive import unique
import sys
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from typing import *

class NodeFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, node_column, parent=None):
        super().__init__(parent)
        self.node_column = node_column
        self.node_name = ""

    def setNodeName(self, node_name):
        self.node_name = node_name
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        index = self.sourceModel().index(source_row, self.node_column, source_parent)
        return self.sourceModel().data(index) == self.node_name


class NodesItemModel(QStandardItemModel):
    def validate(self, index, value)->bool:
        if index.column() == 0:
            if value != index.data():
                msg = f"WARNING: changing the ID is not allowed, currentid: {index.data()}"
                # print(msg)
            return False
        return True

    def setData(self, index: QModelIndex, value, role: int = Qt.EditRole) -> bool:
        if role == Qt.EditRole:
            isValid = self.validate(index, value)
            if not isValid:
                return False

        # Call the base class's setData to actually set the data
        return super().setData(index, value, role)

class GraphModel(QObject):
    nodesInserted = Signal(QModelIndex, int, int)
    nodesRemoved = Signal(QModelIndex, int, int)
    nodesAboutToBeRemoved = Signal(QModelIndex, int, int)
    nodeChanged = Signal(QModelIndex)

    outletsInserted = Signal(QModelIndex, int, int)
    outletsRemoved = Signal(QModelIndex, int, int)
    outletsAboutToBeRemoved = Signal(QModelIndex, int, int)
    outletChanged = Signal(QModelIndex)

    inletsInserted = Signal(QModelIndex, int, int)
    inletsRemoved = Signal(QModelIndex, int, int)
    inletsAboutToBeRemoved = Signal(QModelIndex, int, int)
    inletChanged = Signal(QModelIndex)

    edgesInserted = Signal(QModelIndex, int, int)
    edgesRemoved = Signal(QModelIndex, int, int)
    edgesAboutToBeRemoved = Signal(QModelIndex, int, int)
    edgeChanged = Signal(QModelIndex)

    def __init__(self, parent=None):
        super().__init__(parent)
        ### CREATE QT MODELS ###

        ### Nodes Model ###
        self.nodes = NodesItemModel()
        self.nodes.setHorizontalHeaderLabels(['id', 'name', 'posx', 'posy', 'script'])
        self.nodes.rowsInserted.connect(self.nodesInserted.emit)
        self.nodes.rowsRemoved.connect(self.nodesRemoved.emit)
        self.nodes.rowsAboutToBeRemoved.connect(self.nodesAboutToBeRemoved.emit)
        self.nodes.itemChanged.connect(self.nodeChanged.emit)

        ### Inlets Model ###
        self.inlets = QStandardItemModel()
        self.inlets.setHorizontalHeaderLabels(['id', 'owner', "name"])
        self.inlets.rowsInserted.connect(self.inletsInserted.emit)
        self.inlets.rowsRemoved.connect(self.inletsRemoved.emit)
        self.inlets.rowsAboutToBeRemoved.connect(self.inletsAboutToBeRemoved.emit)
        self.inlets.itemChanged.connect(self.inletChanged.emit)

        ### Outlets Model ###
        self.outlets = QStandardItemModel()
        self.outlets.setHorizontalHeaderLabels(['id', 'owner', "name"])
        self.outlets.rowsInserted.connect(self.outletsInserted.emit)
        self.outlets.rowsRemoved.connect(self.outletsRemoved.emit)
        self.outlets.rowsAboutToBeRemoved.connect(self.outletsAboutToBeRemoved.emit)
        self.outlets.itemChanged.connect(self.outletChanged.emit)

        ### Edges Model ###
        self.edges = QStandardItemModel()
        self.edges.setHorizontalHeaderLabels(["id", "outlet_id", "inlet_id"])
        self.edges.rowsInserted.connect(self.edgesInserted.emit)
        self.edges.rowsRemoved.connect(self.edgesRemoved.emit)
        self.edges.rowsAboutToBeRemoved.connect(self.edgesAboutToBeRemoved.emit)
        self.edges.itemChanged.connect(self.edgeChanged.emit)

    def addNode(self, name:str, posx:int, posy:int, script:str)->QModelIndex:
        id_item =   QStandardItem(unique.make_unique_id())
        name_item = QStandardItem(name)
        posx_item = QStandardItem(str(posx))
        posy_item = QStandardItem(str(posy))
        script_item = QStandardItem(str(script))
        self.nodes.appendRow([id_item, name_item, posx_item, posy_item, script_item])

        return self.nodes.indexFromItem(id_item)

    def addInlet(self, node:QModelIndex, name:str)->QModelIndex:
        if not node.isValid():
            raise KeyError(f"Node {node.data()}, does not exist!")

        id_item =    QStandardItem(unique.make_unique_id())
        owner_item = QStandardItem(node.data())
        name_item =  QStandardItem(name)
        
        self.inlets.appendRow([id_item, owner_item, name_item])
        return self.inlets.indexFromItem(id_item)

    def addOutlet(self, node:QModelIndex, name:str)->QModelIndex:
        if not node.isValid():
            raise KeyError(f"Node {node.data()}, does not exist!")
        id_item =    QStandardItem(unique.make_unique_id())
        owner_item = QStandardItem(node.data())
        name_item =  QStandardItem(name)
        
        self.outlets.appendRow([id_item, owner_item, name_item])
        return self.outlets.indexFromItem(id_item)

    def addEdge(self, outlet:QModelIndex, inlet:QModelIndex)->QModelIndex:
        if not outlet.isValid():
            raise KeyError(f"outlet '{outlet}'' does not exist")
        if not inlet.isValid():
            raise KeyError(f"inlet {inlet} does not exist")

        id_item =        QStandardItem(unique.make_unique_id())
        outlet_id_item = QStandardItem(outlet.data())
        inlet_id_item =  QStandardItem(inlet.data())
        self.edges.appendRow([id_item, outlet_id_item, inlet_id_item])
        return self.edges.indexFromItem(id_item)

    def removeNodes(self, nodes:List[QModelIndex]):
        # Collect the rows to be removed
        rows_to_remove = sorted(set(index.row() for index in nodes), reverse=True)

        # collect inlets to be removed
        inlet_rows_to_remove = []
        for row in rows_to_remove:
            owner_id = self.nodes.item(row, 0).text()
            inlet_items = self.inlets.findItems(owner_id, Qt.MatchFlag.MatchExactly, 1)
            for inlet_item in inlet_items:
                inlet_rows_to_remove.append( inlet_item.index().row() )
        self.removeInlets(inlet_rows_to_remove)

        # collect outlets to be removed
        outlet_rows_to_remove = []
        for row in rows_to_remove:
            owner_id = self.nodes.item(row, 0).text()
            outlet_items = self.outlets.findItems(owner_id, Qt.MatchFlag.MatchExactly, 1)
            for outlet_item in outlet_items:
                outlet_rows_to_remove.append( outlet_item.index().row() )
        self.removeOutlets(outlet_rows_to_remove)

        # Remove the node rows from the GraphModel (starting from the last one, to avoid shifting indices)
        for row in reversed(rows_to_remove):
            self.nodes.removeRow(row)

    def removeOutlets(self, outlets_to_remove:List[QModelIndex]):
        # collect edges to be removed
        edges_to_remove = []
        for outlet in outlets_to_remove:
            edge_items = self.edges.findItems(outlet.data(), Qt.MatchFlag.MatchExactly, 2)
            for edge_item in edge_items:
                edges_to_remove.append( edge_item.index() )
        self.removeEdges(edges_to_remove)

        # Remove the rows from the GraphModel (starting from the last one, to avoid shifting indices)
        rows_to_remove = set([outlet.row() for outlet in outlets_to_remove]) # keep unique rows
        for row in sorted(rows_to_remove, reverse=True):
            self.outlets.removeRow(row)

    def removeInlets(self, inlets_to_remove:List[QModelIndex]):

        # collect edges to be removed
        edges_to_remove = []
        for inlet in inlets_to_remove:
            edge_items = self.edges.findItems(inlet.data(), Qt.MatchFlag.MatchExactly, 2)
            for edge_item in edge_items:
                edges_to_remove.append( edge_item.index() )
        self.removeEdges(edges_to_remove)

        # Remove the rows from the GraphModel (starting from the last one, to avoid shifting indices)
        rows_to_remove = set([inlet.row() for inlet in inlets_to_remove]) # keep unique rows
        for row in sorted(rows_to_remove, reverse=True):
            self.inlets.removeRow(row)

    def removeEdges(self, edges_to_remove:List[QModelIndex]):
        # Remove the rows from the GraphModel (starting from the last one, to avoid shifting indices)
        rows_to_remove = set([edge.row() for edge in edges_to_remove]) # keep unique rows
        for row in sorted(rows_to_remove, reverse=True):
            self.edges.removeRow(row)

    # def getNodeForInlet(self, inlet:QModelIndex)->QModelIndex:
    #     inlet.siblingAtColumn()

    # def getNodeForOutlet(self, outlet:QModelIndex)->QModelIndex:


    def findInlets(self, node:QModelIndex)->Iterable[QModelIndex]:
        items = self.inlets.findItems(node.data(), Qt.MatchFlag.MatchExactly, 1)
        for item in items:
            yield item.index().siblingAtColumn(0) # return the ndex at the id column

    def findOutlets(self, node)->Iterable[QModelIndex]:
        items = self.outlets.findItems(node.data(), Qt.MatchFlag.MatchExactly, 1)
        for item in items:
            yield item.index().siblingAtColumn(0) # return the ndex at the id column

    def findEdges(self, source_outlet:QModelIndex=None, target_inlet:QModelIndex=None)->Iterable[QModelIndex]:
        # find edges from source outlet
        edges_from_source = self.edges.findItems(source_outlet.data(), Qt.MatchFlag.MatchExactly, 1)

        # find edges to target inlet
        edges_to_target = self.edges.findItems(target_inlet.data(), Qt.MatchFlag.MatchExactly, 2)

        # return edges matching source and target:
        for edge in edges_from_source:
            if edge in edges_to_target:
                yield edge.index().siblingAtColumn(0) # return the ndex at the id column

    def findEdgesToInlet(self, target_inlet:QModelIndex)->Iterable[QModelIndex]:
        edges_to_target = self.edges.findItems(target_inlet.data(), Qt.MatchFlag.MatchExactly, 2)
        for edge in edges_to_target:
            yield edge.index().siblingAtColumn(0)

    def findSources(self, node:QModelIndex)->Iterable[QModelIndex]:
        inlets = self.findInlets(node.siblingAtColumn(0))
        for inlet in inlets:
            # find edges to inlet
            edges_to_target = self.edges.findItems(inlet.data(), Qt.MatchFlag.MatchExactly, 2)
            for edge in edges_to_target:
                source_outlet_id = edge.index().siblingAtColumn(1).data() # get the index of the source outlet
                outlet_items = self.outlets.findItems(source_outlet_id)
                for outlet_item in outlet_items:    
                    owner_node_id = outlet_item.index().siblingAtColumn(1).data()
                    for source_node_item in self.nodes.findItems(owner_node_id):
                        yield source_node_item.index()

    def findConnectedNodes(self, node:QModelIndex, direction:str)->Iterable[QModelIndex]:
        if direction == "SOURCE":
            findPorts = self.findInlets
            column = 2
        elif direction == "TARGET":
            findPorts = self.findOutlets
            column = 1
        else:
            raise ValueError("direction must be either SOURCE or TARGET!")
        
        ports = findPorts(node.siblingAtColumn(0))
        for port in ports:
            # find edges to inlet
            edges_to_target = self.edges.findItems(port.data(), Qt.MatchFlag.MatchExactly, column)
            for edge in edges_to_target:
                connected_id = edge.index().siblingAtColumn(1).data() # get the index of the source outlet
                connected_items = self.outlets.findItems(connected_id)
                for connected_item in connected_items:
                    owner_node_id = connected_item.index().siblingAtColumn(1).data()
                    for connected_node_item in self.nodes.findItems(owner_node_id):
                        yield connected_node_item.index()


    def rootRodes(self)->Iterable[QModelIndex]:
        """Yield all root nodes (nodes without outlets) in the graph."""
        for i in range(self.nodes.rowCount()):
            node = self.nodes.item(i, 0).index()
            target_nodes = list(self.findConnectedNodes(node, direction="TARGET"))
            if not target_nodes:
                yield node
            # print(list(sources))
            # if not sources:  # Check if the node has no outlets
            #   yield node  # Yield the root node

    def dfs(self)->Iterable[QModelIndex]:
        """Perform DFS starting from the root notes and yield each node."""

        start_nodes = self.rootRodes()
        visited = set()  # Set to track visited nodes

        def dfs_visit(node:QModelIndex):
            """Recursive helper function to perform DFS."""
            visited.add(node)
            yield node  # Yield the current node

            # Iterate through all adjacent edges from the current node
            for target_node in self.findSources(node):
                if target_node not in visited:  # Check if the target node has been visited
                    yield from dfs_visit(target_node)  # Recursive call

        for start_node in start_nodes:
            if start_node not in visited:  # Check if the start node has been visited
                yield from dfs_visit(start_node)  # Start DFS from the start node