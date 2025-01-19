from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from pylive.NetworkXGraphEditor.nx_network_model import NXNetworkModel, _NodeId
from pylive.NetworkXGraphEditor.nx_network_scene_outlet_to_inlet import StandardNetworkDelegte, StandardNodeItem

from python_graph_model import PythonGraphModel

class PythonGraphDelegate(StandardNetworkDelegte):
    @override
    def createAttributeEditor(self, parent_node: QGraphicsItem, model: NXNetworkModel, node_id: _NodeId, attr: str)->QGraphicsItem|None:
        assert isinstance(model, PythonGraphModel)
        if func:=model.getNodeFunction(node_id):
            if func.__name__ == 'forEach':
                print("itr a foreach")
        return super().createPropertyEditor(parent_node, model, node_id, attr)

    def updateAttributeEditor(self, model: NXNetworkModel, node_id:Hashable, attr:str, editor: QGraphicsItem):
        # value = model.getNodeProperty(node_id, attr)
        # editor = cast(QGraphicsTextItem, editor)
        # editor.setPlainText(f"{prop}: {value}")
        if attr=="fn":
            fn = model.getNodeAttribute(node_id, attr)
            print(f"its a foreach with {fn}")

        super().updateAttributeEditor(model, node_id, attr, editor)

    # def setNodePropertyModel(self, model:NXNetworkModel, node_id:Hashable, prop:str, editor: QGraphicsItem):
    #     ...
