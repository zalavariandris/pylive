from typing import *

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from pylive.VisualCode_v4.py_fields_model import PyFieldsModel, PyFieldItem
from pylive.VisualCode_v4.py_nodes_model import PyNodesModel, UniqueFunctionItem
from pylive.VisualCode_v4.graph_editor.standard_edges_model import StandardEdgesModel, StandardEdgeItem

from pathlib import Path

class PyGraphItem(QObject):
    def __init__(self):
        ### document state
        self._is_modified = False
        self._filepath = "None"
        self._nodes_model = PyNodesModel()
        self._edges_model = StandardEdgesModel(self._nodes_model)

    


    def nodes(self)->PyNodesModel:
        return self._nodes_model

    def edges(self)->StandardEdgesModel:
        return self._edges_model

    def deserialize(self, text:str)->bool:
        import yaml
        data = yaml.load(text, Loader=yaml.SafeLoader)

        ### create node items
        _node_row_by_name = dict() # keep node name as references for the edge relations
        self._nodes_model.blockSignals(True)
        for row, node in enumerate(data['nodes']):
            if node['kind']!='UniqueFunction':
                raise NotImplementedError("for now, only 'UniqueFunction's are supported!")

            fields_model = PyFieldsModel()
            if fields:=node.get("fields", None):
                for row, (name, value) in enumerate(fields.items()):
                    field_item = PyFieldItem(name, value, editable=True)
                    fields_model.insertFieldItem(row, field_item)

            self._nodes_model.addNodeItem(
                UniqueFunctionItem(
                    node['source'], 
                    name=node.get('name', None),
                    fields=fields_model)
            )

            _node_row_by_name[node['name']] = row

        self._nodes_model.blockSignals(False)
        self._nodes_model.modelReset.emit()

        self._edges_model.blockSignals(True)
        if data.get('edges', None):
            for row, edge in enumerate(data['edges']):
                source_node_id = edge['source']
                target_node_id = edge['target']
                source_row = _node_row_by_name[source_node_id]
                target_row = _node_row_by_name[target_node_id]

                edge = StandardEdgeItem(
                    QPersistentModelIndex(self.nodes().index(source_row, 0)), 
                    QPersistentModelIndex(self.nodes().index(target_row, 0)), 
                    "out",
                    edge['inlet']
                )
                self._edges_model.appendEdgeItem(edge)

            self._edges_model.blockSignals(False)
        self._edges_model.modelReset.emit()

        return True

    def serialize(self)->str:
        import yaml
        return yaml.dump({
            'nodes': [],
            'edges': []
        })

    def load(self, path:Path|str):
        text = Path(path).read_text()
        self.deserialize(text)

    def save(self, path:Path|str):
        text = self.serialize()
        Path(path).write_text(text)

    def evaluateNode(self, node_index:QModelIndex|QPersistentModelIndex):
        from pylive.utils.evaluate_python import parse_python_function, call_function_with_stored_args
        node_item = self._nodes_model.nodeItem(node_index.row())
        assert node_item.kind() == "UniqueFunction", f"Only UniqueFunction kind is supported, got:{node_item.kind()}"
        node_item = cast(UniqueFunctionItem, node_item)
        """recursively evaluate nodes, from top to bottom"""
        ### load arguments achestors
        kwargs = dict()
        inputs = [_ for _ in self._edges_model.in_edges(node_index)]
        # print("in edges:", inputs)
        for edge_item in self._edges_model.in_edges(node_index):
            # print(f"EVALUATE SOURCE {edge_item.inlet}: {edge_item.source}")
            kwargs[edge_item.inlet] = self.evaluateNode(edge_item.source)
            

        ### load arguments from fields
        for row in range(node_item.fields().rowCount()):
            field_item = node_item.fields().fieldItem(row)
            if field_item.name in kwargs:
                continue # skip connected fields
            
            kwargs[field_item.name] = field_item.value

        # print("_evaluate", node_index, kwargs)
        # evaluate functions with 
        func = parse_python_function(node_item.source())
        result = call_function_with_stored_args(func, kwargs)
        return result

    