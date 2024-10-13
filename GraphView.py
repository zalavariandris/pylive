
from NodeGraphQt import NodeGraph, NodeObject, BaseNode, Port
import sys
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from typing import List, Tuple
from dataclasses import dataclass
@dataclass
class EdgeEditor:
    source:Port
    target:Port
    def __init__(self, source:Port, target:Port):
        self.source = source
        self.target = target
        self.data = None



class GraphView(QWidget):
    """A Qt View to present and editr the Graphmodel
    the current backend widget is the NodeGraphQt library
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.graph = NodeGraph()
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.graph.widget)

    def setModel(self, model):
        self._model = model

        # Utility functions for adding/removing/updating nodes, inlets, and outlets
        def createNodeEditor(parent: NodeGraph, option: QStyleOptionViewItem, index_id)->BaseNode:
            self.graph.blockSignals(True)


            unique_id = index_id.data()
            name =      index_id.siblingAtColumn(1).data()
            posx =      index_id.siblingAtColumn(2).data()
            posy =      index_id.siblingAtColumn(3).data()
            node = BaseNode()
            node.set_port_deletion_allowed(True)
            parent.add_node(node)
            node.set_name(f"{name}({unique_id})")
            node.set_x_pos(posx or 0)
            node.set_y_pos(posy or 0)
            self.graph.blockSignals(False)
            return node

        def createInletEditor(parent: BaseNode, option: QStyleOptionViewItem, index_id)->Port:
            self.graph.blockSignals(True)
            unique_id = index_id.data()
            owner = index_id.siblingAtColumn(1).data()
            name = index_id.siblingAtColumn(2).data()

            outletEditor = parent.add_input(f"{name}({unique_id})")
            self.graph.blockSignals(False)
            return outletEditor

        def createOutletEditor(parent: BaseNode, option: QStyleOptionViewItem, index_id)->Port:
            self.graph.blockSignals(True)
            unique_id = index_id.data()
            owner     = index_id.siblingAtColumn(1).data()
            name      = index_id.siblingAtColumn(2).data()

            outletEditor = parent.add_output(f"{name}({unique_id})", )
            self.graph.blockSignals(False)
            return outletEditor

        def createEdgeEditor(parent: Tuple[str,str], option: QStyleOptionViewItem, index_id)->Tuple[Port, Port]:
            self.graph.blockSignals(True)
            unique_id = index_id.data()
            owner     = index_id.siblingAtColumn(1).data()
            name      = index_id.siblingAtColumn(2).data()

            outlet_editor, inlet_editor = parent
            outlet_editor.connect_to(inlet_editor, push_undo=False)
            self.graph.blockSignals(False)
            return EdgeEditor(outlet_editor, inlet_editor)

        def getNodeParent(index_id:QModelIndex)->NodeGraph:
            return self.graph

        def getInletParent(index_id:QModelIndex)->BaseNode:
            owner_id = index_id.siblingAtColumn(1).data()
            return self.node_editor_by_id[owner_id]

        def getOutletParent(index_id:QModelIndex)->BaseNode:
            owner_id = index_id.siblingAtColumn(1).data()
            return self.node_editor_by_id[owner_id]

        def getEdgeParent(index_id:QModelIndex)->Tuple[Port, Port]:
            source_id = index_id.siblingAtColumn(1).data()
            target_id = index_id.siblingAtColumn(2).data()
            return self.outlet_editor_by_id[source_id], self.inlet_editor_by_id[target_id]

        def setNodeEditorData(parent:NodeGraph, editor:BaseNode, item:QStandardItem):
            # self.graph.blockSignals(True)
            # if item.column() == 1:
            #     editor.set_name(item.text())
            # elif item.column() == 2:
            #     editor.set_x_pos(item.data())
            # elif item.column() == 3:
            #     editor.set_y_pos(item.data())
            # self.graph.blockSignals(False)
            pass

        def setInletEditorData(parent:BaseNode, editor:Port, item:QStandardItem):
            self.graph.blockSignals(True)
            unique_id = item(row, 0).text()
            owner =     item(row, 1).text()
            name =      item(row, 2).text()

            raise NotImplementedError("NodeGraphQT does not allow changing the ports name. we need to delete, create a new one with the original edges")
            self.graph.blockSignals(False)

        def setOutletEditorData(parent:BaseNode, editor:Port, item:QStandardItem):
            self.graph.blockSignals(True)
            unique_id = item(row, 0).text()
            owner =     item(row, 1).text()
            name =      item(row, 2).text()

            raise NotImplementedError("NodeGraphQT does not allow changing the ports name. we need to delete, create a new one with the original edges")
            self.graph.blockSignals(False)

        def setEdgeEditorData(parent:Tuple[Port, Port], editor:Tuple[Port, Port], item:QStandardItem):
            self.graph.blockSignals(True)
            row, col = item.row(), item.column()
            unique_id = item(row, 0).text()
            owner =     item(row, 1).text()
            name =      item(row, 2).text()

            raise NotImplementedError("NodeGraphQT does not allow setting an edge: remove, and create a new one")
            self.graph.blockSignals(False)
            
        def destroyNodeEditor(parent: NodeGraph, editor:BaseNode, row: int):
            self.graph.blockSignals(True)
            parent.delete_node(editor)
            self.graph.blockSignals(False)
            print("DESTROY NodeEditor was called", parent, editor, row)

        def destroyInletEditor(parent:BaseNode, editor:Port, row: int):
            self.graph.blockSignals(True)
            parent.delete_input(editor)
            self.graph.blockSignals(False)

        def destroyOutletEditor(parent:BaseNode, editor:Port, row: int):
            self.graph.blockSignals(True)
            parent.delete_output(editor)
            self.graph.blockSignals(False)

        def destroyEdgeEditor(parent:Tuple[Port, Port], editor:EdgeEditor, row: int):
            self.graph.blockSignals(True)
            editor.source.disconnect_from(editor.target, push_undo=True)
            self.graph.blockSignals(False)

        # Initial setup
        self.node_editor_by_id = {}
        self.inlet_editor_by_id = {}
        self.outlet_editor_by_id = {}
        self.edge_editor_by_id = {}
        for row in range(model.nodes.rowCount()):
            index_id = model.nodes.indexFromItem(model.nodes.item(row, 0))
            node_editor = createNodeEditor(self.graph, QStyleOptionViewItem(), index_id)
            node_id = model.nodes.item(row, 0).text();

            self.node_editor_by_id[node_id] = node_editor
            node_editor.data = node_id

        for row in range(model.inlets.rowCount()):
            index_id = model.inlets.indexFromItem(model.inlets.item(row, 0)) 
            inlet_id = model.inlets.item(row, 0).text();
            owner_id = model.inlets.item(row, 1).text();
            nodeEditor = self.node_editor_by_id[owner_id]

            inlet_editor = createInletEditor(nodeEditor, QStyleOptionViewItem(), index_id)
            self.inlet_editor_by_id[inlet_id] = inlet_editor
            inlet_editor.data = inlet_id

        for row in range(model.outlets.rowCount()):
            index_id = model.outlets.indexFromItem(model.outlets.item(row, 0))
            outlet_id = model.outlets.item(row, 0).text();
            owner_id = model.outlets.item(row, 1).text();
            nodeEditor = self.node_editor_by_id[owner_id]

            outlet_editor = createOutletEditor(nodeEditor, QStyleOptionViewItem(), index_id)
            self.outlet_editor_by_id[outlet_id] = outlet_editor
            outlet_editor.data = outlet_id

        for row in range(model.edges.rowCount()):
            index_id = model.edges.indexFromItem(model.edges.item(row, 0))
            edge_id =          model.edges.item(row, 0).text()
            source_outlet_id = model.edges.item(row, 1).text()
            target_inlet_id =  model.edges.item(row, 2).text()

            outlet_editor = self.outlet_editor_by_id[source_outlet_id]
            oinlet_editor = self.inlet_editor_by_id[target_inlet_id]

            edge_editor = createEdgeEditor( (outlet_editor, inlet_editor), QStyleOptionViewItem(), index_id)
            self.edge_editor_by_id[edge_id] = edge_editor

        @model.nodesInserted.connect
        def nodesInserted(parent: QModelIndex, first: int, last: int):
            print("nodesInserted", parent, first, last)

        # ### BIND NodeGraphQT to model ###
        # def bind_model_signals(model, editor_by_id, createEditor, getParent, destroyEditor, setEditorData):
        #     @model.rowsInserted.connect
        #     def rowsInserted(parent: QModelIndex, first: int, last: int):
        #         for row in range(first, last + 1):
        #             row_indexes = [model.indexFromItem(model.item(row, i)) for i in range(model.columnCount()) ]
        #             unique_id = row_indexes[0].text()
        #             editor = createEditor(parent=getParent(row), option=QStyleOptionViewItem(), indexes=row_indexes)
        #             editor_by_id[unique_id] = editor
        #             editor.data = unique_id

        #     @model.rowsAboutToBeRemoved.connect
        #     def rowsAboutToBeRemoved(parent: QModelIndex, first: int, last: int):
        #         for row in range(first, last + 1):
        #             unique_id = model.item(row, 0).text()
        #             editor = editor_by_id[unique_id]
        #             destroyEditor(parent=getParent(row), editor=editor, row=row)

        #     @model.itemChanged.connect
        #     def itemChanged(item:QModelIndex):
        #         unique_id = model.item(item.row(), 0).text()
        #         editor = editor_by_id[unique_id]
        #         setEditorData(parent=getParent(row), editor=editor, item=item)

        # bind_model_signals(model.nodes,   self.node_editor_by_id,   createNodeEditor,   getNodeParent,   destroyNodeEditor,   setNodeEditorData)
        # bind_model_signals(model.inlets,  self.inlet_editor_by_id,  createInletEditor,  getInletParent,  destroyInletEditor,  setInletEditorData)
        # bind_model_signals(model.outlets, self.outlet_editor_by_id, createOutletEditor, getOutletParent, destroyOutletEditor, setOutletEditorData)
        # bind_model_signals(model.edges,   self.edge_editor_by_id,   createEdgeEditor,   getEdgeParent,   destroyEdgeEditor,   setEdgeEditorData)

        # bind CRUD signals
        def bindCRUD(submodel, editor_by_id, 
            createdSignal, getParent, createEditor, 
            updatedSignal, updateEditor, 
            deletedSignal, destroyEditor):
            @createdSignal.connect
            def rowsInserted(parent: QModelIndex, first: int, last: int):
                for row in range(first, last + 1):
                    index_id = submodel.indexFromItem(submodel.item(row, 0))
                    unique_id = index_id.data()
                    editor = createEditor(parent=getParent(index_id), option=QStyleOptionViewItem(), index_id=index_id)
                    editor_by_id[unique_id] = editor
                    editor.data = unique_id

            @deletedSignal.connect
            def rowsAboutToBeRemoved(parent: QModelIndex, first: int, last: int):
                for row in range(first, last + 1):
                    unique_id = submodel.item(row, 0).text()
                    editor = editor_by_id[unique_id]
                    destroyEditor(parent=getParent(index_id), editor=editor, row=row)

            @updatedSignal.connect
            def itemChanged(item:QModelIndex):
                unique_id = submodel.item(item.row(), 0).text()
                editor = editor_by_id[unique_id]
                updateEditor(parent=getParent(index_id), editor=editor, item=item)

        bindCRUD(self._model.nodes,
            self.node_editor_by_id,
            self._model.nodesInserted, getNodeParent, createNodeEditor,
            self._model.nodeChanged, setNodeEditorData,
            self._model.nodesAboutToBeRemoved, destroyNodeEditor)

        bindCRUD(self._model.outlets,
            self.outlet_editor_by_id,
            self._model.outletsInserted, getOutletParent, createOutletEditor,
            self._model.outletChanged, setOutletEditorData,
            self._model.outletsAboutToBeRemoved, destroyOutletEditor)

        bindCRUD(self._model.inlets,
            self.inlet_editor_by_id,
            self._model.inletsInserted, getInletParent, createInletEditor,
            self._model.inletChanged, setInletEditorData,
            self._model.inletsAboutToBeRemoved, destroyInletEditor)

        bindCRUD(self._model.edges,
            self.edge_editor_by_id,
            self._model.edgesInserted, getEdgeParent, createEdgeEditor,
            self._model.edgeChanged, setEdgeEditorData,
            self._model.edgesAboutToBeRemoved, destroyEdgeEditor)


        ### BIND NodeGraph Events to update the model ###
        @self.graph.node_created.connect
        def node_created(node:NodeObject):
            print("node_created", node)

        @self.graph.nodes_deleted.connect
        def nodes_deleted(node_ids:List[str]):
            print("nodes_deleted")

        # @self.graph.node_selection_changed.connect
        # def node_selection_changed(selected_nodes:List[NodeObject], deselected_nodes:List[NodeObject]):
        #     print("node_selection_changed", selected_nodes, deselected_nodes)

        @self.graph.node_double_clicked.connect
        def node_double_clicked(node:NodeObject):
            print("node_double_clicked", node)

        @self.graph.port_connected.connect
        def port_connected(input_port, output_port):
            print("port_connected", input_port, output_port)            
            self._model.addEdge(output_port.data, input_port.data)

        @self.graph.port_disconnected.connect
        def port_disconnected(input_port:Port, output_port:Port):
            print("port_disconnected", input_port.data, output_port.data)

            edge_rows_with_the_outlet = {index.row() for index in self._model.edges.findItems(output_port.data, Qt.MatchExactly, 1)}
            edge_rows_with_the_inlet  = {index.row() for index in self._model.edges.findItems(input_port.data, Qt.MatchExactly, 2)}
            print("edge_rows_with_the_outlet", edge_rows_with_the_outlet)
            print("edge_rows_with_the_inlet", edge_rows_with_the_inlet)

            found_edge_rows = edge_rows_with_the_outlet.intersection(edge_rows_with_the_inlet)
            
            self._model.removeEdges(found_edge_rows)
            print("found edges:", found_edge_rows)


        @self.graph.property_changed.connect
        def property_changed(triggered_node, property_name, property_value):
            pass
            # print("property_changed", triggered_node, property_name, property_value)

        @self.graph.data_dropped.connect
        def data_dropped(mime_data, node_graph_position):
            print("data_dropped", mime_data, node_graph_position)    

    def setNodeSelectionModel(self, nodes_selectionmodel):
        self._nodes_selectionmodel = nodes_selectionmodel

        # setup node selection
        self.graph.clear_selection()
        selected_rows = {index.row() for index in nodes_selectionmodel.selection().indexes()}
        for row in selected_rows:
            node_id = self._model.nodes.itemFromIndex(QModelIndex(row, 0))
            nodeEditor = self.node_editor_by_id[node_id]
            nodeEditor.setSelected(True)


        ### BIND MODEL ###
        @nodes_selectionmodel.modelChanged.connect
        def modelChanged(model: QAbstractItemModel):
            raise NotImplementedError("TODO: update graphview selection on model change")

        @nodes_selectionmodel.currentChanged.connect
        def currentChanged(current: QModelIndex, previous: QModelIndex):
            """TODO: kepp track of the current node item in the graphview?"""

        @nodes_selectionmodel.selectionChanged.connect
        def selectionChanged(selected:QItemSelection, deselected: QItemSelection):
            selected_rows = {index.row() for index in selected.indexes()}
            for row in selected_rows:
                node_id = self._model.nodes.item(row, 0).text()
                nodeEditor = self.node_editor_by_id[node_id]
                nodeEditor.set_selected(True)

            deselected_rows = {index.row() for index in deselected.indexes()}
            for row in deselected_rows:
                node_id = self._model.nodes.item(row, 0).text()
                nodeEditor = self.node_editor_by_id[node_id]
                nodeEditor.set_selected(False)
            # print("selectionChanged", selected, deselected)


        @self.graph.node_selection_changed.connect
        def node_selection_changed(selected_node_editors: List[BaseNode], deselected_node_editors: List[BaseNode]):
            # Collect the selected node indexes
            selected_indexes = [
                self._model.nodes.findItems(node_editor.data)[0].index()
                for node_editor in self.graph.selected_nodes()
            ]

            # Create a selection object
            item_selection = QItemSelection()
            for index in selected_indexes:
                item_selection.select(index, index)

            # Update the selection model
            self._nodes_selectionmodel.clearSelection()
            self._nodes_selectionmodel.select(
                item_selection, 
                QItemSelectionModel.ClearAndSelect | QItemSelectionModel.SelectCurrent | QItemSelectionModel.Rows
            )

            # Set the last selected index as the current one
            if selected_indexes:
                self._nodes_selectionmodel.setCurrentIndex(selected_indexes[-1], QItemSelectionModel.Current)



    def setEdgesSelectionModel(self, nodes_selectionmodel):
        raise NotImplementedError("NodeGraphQT does not seem to expose the edge selection model")