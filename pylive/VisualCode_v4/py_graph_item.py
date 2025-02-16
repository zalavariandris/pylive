from typing import *

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from pylive.VisualCode_v4.py_fields_model import PyFieldsModel, PyFieldItem
from pylive.VisualCode_v4.py_nodes_model import PyNodesModel, PyNodeItem
from pylive.VisualCode_v4.graph_editor.standard_edges_model import StandardEdgesModel, StandardEdgeItem

from pathlib import Path


class PyGraphItem(QObject):
    def __init__(self):
        ### document state
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
            print("deserialize node:", node.get('fields'))
            if node['kind']!='UniqueFunction':
                raise NotImplementedError("for now, only 'UniqueFunction's are supported!")

            fields = node.get('fields') or dict({'f': 1})
            node_item = PyNodeItem(
                name=node['name'],
                code=node['source'],
                fields=fields
            )
            self._nodes_model.insertNodeItem(row, node_item)

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
        """recursively evaluate nodes, from top to bottom"""
        from pylive.utils.evaluate_python import parse_python_function, call_function_with_stored_args
        node_item = self._nodes_model.nodeItem(node_index.row())

        ### load arguments from achestors
        kwargs = dict()
        for edge_item in self._edges_model.in_edges(node_index):
            # print(f"EVALUATE SOURCE {edge_item.inlet}: {edge_item.source}")
            kwargs[edge_item.inlet] = self.evaluateNode(edge_item.source)
            
        ### load arguments from fields
        for name, value in node_item.fields.items():
            if name in kwargs:
                continue # skip connected fields
            kwargs[name] = value

        # evaluate functions with 
        if not node_item.func:
            success = self._nodes_model.compileNode(node_index.row())
            if not success:
                return

        node_item = self._nodes_model.nodeItem(node_index.row())
        assert node_item.func
        try:
            result = call_function_with_stored_args(node_item.func, kwargs)
        except SyntaxError as err:
            ...
        except Exception as err:
            ...
        else:
            

            # set result
            row = node_index.row()
            headers = [self.nodes().headerData(section, Qt.Orientation.Horizontal) for section in range(self.nodes().columnCount())]
            assert "result" in headers
            column = headers.index("result")
            self.nodes().setData(self.nodes().index(row, column), result)
            return result

    