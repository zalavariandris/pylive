from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from pylive.VisualCode_v4.graph_editor.standard_graph_delegate import StandardGraphDelegate
from pylive.VisualCode_v4.py_node_widget import PyNodeWidget

from pylive.VisualCode_v4.py_proxy_model import PyProxyNodeModel

from pylive.utils.evaluate_python import get_function_name



class PyGraphViewDelegate(StandardGraphDelegate):
    def createNodeWidget(self, parent:QGraphicsScene, index:QModelIndex)->QGraphicsItem:
        node_widget = PyNodeWidget()
        node_widget.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        node_widget.setHeading(f"{index.data(Qt.ItemDataRole.DisplayRole)}")
        node_widget.scenePositionChanged.connect(lambda node=node_widget: self.nodePositionChanged.emit(node))
        parent.addItem(node_widget)
        return node_widget

    def updateNodeWidget(self, index:QModelIndex, node_widget:QGraphicsItem)->None:
        node_widget = cast(PyNodeWidget, node_widget)
        for column, header in enumerate(PyProxyNodeModel._headers):
            column_index = index.siblingAtColumn(column)
            value = column_index.data(Qt.ItemDataRole.EditRole)
            match header:
                case 'name':
                    ...
                case 'source':
                    node_widget.setHeading( get_function_name(value) )
                case 'parameters':
                    ...
                case 'compiled':
                    node_widget.debug_widget.setCompiled(value)
                case 'evaluated':
                    node_widget.debug_widget.setEvaluated(value)
                case 'error':
                    if value:
                        node_widget.debug_widget.showError(value)
                    else:
                        node_widget.debug_widget.clearError()
                    
                case 'result':
                    ...
        node_widget.debug_widget.update()
