#####################
# The Network Scene #
#####################

#
# A Graph view that directly connects to PyDataModel
#


from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

import traceback
from collections import defaultdict
from textwrap import dedent
from itertools import chain

from bidict import bidict


from pylive.utils.unique import make_unique_name
from pylive.utils.diff import diff_set

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

from pylive.VisualCode_v4.py_data_model import PyDataModel, PyNodeItem


class PortItem(QGraphicsItem):
    def __init__(self, key:Hashable, parent:QGraphicsItem|None=None):
        super().__init__(parent=parent)
        self.key = key
        self.links:set[LinkItem] = set()
        self.label = QGraphicsTextItem(f"{self.key}")
        self.label.setPlainText
        self.label.setParentItem(self)
        self.label.setPos(0,-20)
        self.label.hide()
        self.setAcceptHoverEvents(True)

    def boundingRect(self) -> QRectF:
        r = 6
        return QRectF(-r,-r,r*2,r*2)

    def update(self, rect:QRect|QRectF=QRectF()):
        self.label.setPlainText(f"{self.key}")
        super().update()

    def shape(self):
        r = 3
        path = QPainterPath()
        path.addEllipse(QRectF(-r,-r,r*2,r*2))
        return path

    def paint(self, painter:QPainter, option:QStyleOption, widget:QWidget|None=None):
        r = 3
        palette = widget.palette() if widget else QApplication.palette()
        painter.setBrush(palette.text())
        painter.drawEllipse(QRectF(-r,-r,r*2,r*2))

    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        self.label.show()

    def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        self.label.hide()


class NodeItem(QGraphicsWidget):
    scenePositionChanged = Signal()
    def __init__(self, key:Hashable, parent:QGraphicsItem|None=None):
        super().__init__(parent=parent)
        self.key:Hashable = key
        self.in_links:set[LinkItem] = set()
        self.out_links:set[LinkItem] = set()

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges)

        self._inlet_widgets:bidict[Hashable, PortItem] = bidict()
        self._outlet = PortItem("out")
        self._outlet.label.setPos(-28,-5)
        self._outlet.setParentItem(self)
        
        self.setGeometry( QRectF(0,0,70,24) )
        self._outlet.setPos(self.rect().width()/2, self.rect().height()+2)

    def paint(self, painter: QPainter, option, widget=None):
        button_option = QStyleOptionButton()
        button_option.rect = self.boundingRect().toRect()
        button_option.text = f"{self.key}"
        button_option.state = QStyle.State_Enabled

        if False:#"PRESSED"
            button_option.state |= QStyle.State_Sunken
        else:
            button_option.state |= QStyle.State_Raised

        if QStyle.State_MouseOver in option.state:
            button_option.state = QStyle.State_MouseOver

        if self.isSelected():
            painter.drawRoundedRect(self.boundingRect(),5,5)


        if option.state & QStyle.State_MouseOver:
            button_option.state |= QStyle.State_MouseOver

        # Use the widget's style if available, otherwise use QApplication's style
        style = widget.style() if widget else QApplication.style()
        style.drawControl(QStyle.CE_PushButton, button_option, painter, widget)

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        if change == QGraphicsItem.GraphicsItemChange.ItemScenePositionHasChanged:
            self.scenePositionChanged.emit()
        return super().itemChange(change, value)


class LinkItem(QGraphicsLineItem):
    def __init__(self, key:tuple[str,str,str,str], parent:QGraphicsItem|None=None):
        super().__init__(parent=parent)
        self.key:tuple[str,str,str,str] = key


class _GraphEditorView(QGraphicsView):
    SourceRole = Qt.ItemDataRole.UserRole+1
    TargetRole = Qt.ItemDataRole.UserRole+2
    InletsRole = Qt.ItemDataRole.UserRole+3
    OutletsRole = Qt.ItemDataRole.UserRole+4

    nodesLinked = Signal(QModelIndex, QModelIndex, str, str)

    def __init__(self, parent:QWidget|None=None):
        super().__init__(parent=parent)
        self._model: PyDataModel | None = None
        self._model_connections = []

        # store model widget relations
        # map item index to widgets
        self._node_widgets:bidict[str, NodeItem] = bidict()
        self._link_widgets:bidict[Hashable, LinkItem] = bidict()

        # self._node_in_links:defaultdict[QPersistentModelIndex, list[QPersistentModelIndex]] = defaultdict(list) # Notes: store attached links, because the underlzing model has to find the relevant edges  and thats is O(n)
        # self._node_out_links:defaultdict[QPersistentModelIndex, list[QPersistentModelIndex]] = defaultdict(list) # Notes: store attached links, because the underlzing model has to find the relevant edges  and thats is O(n)

        self.setupUI()

    def setupUI(self):
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setCacheMode(QGraphicsView.CacheModeFlag.CacheNone)
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        scene = QGraphicsScene()
        scene.setSceneRect(QRectF(-9999,-9999,9999*2, 9999*2))
        self.setScene(scene)

    def setModel(self, model:PyDataModel|None):
        logger.debug(f"setModel {model}")
        if self._model:
            for signal, slot in self._model_connections:
                signal.disconnect(slot)

        if model:
            self._model_connections = [
                # Node Collection
                (model.modelReset, lambda: self.resetItems()),
                (model.nodesAdded, lambda nodes: self.addNodeItems([node_key for node_key in nodes])),
                (model.nodesAboutToBeRemoved, lambda nodes: self.removeNodeItems([node_key for node_key in nodes])),

                # Node Data
                (model.sourceChanged, lambda node: self.updateNodeItem(node, 'source')),
                (model.positionChanged, lambda node: self.updateNodeItem(node, 'position')),
                (model.compiledChanged, lambda node: self.updateNodeItem(node, 'compiled')),
                (model.evaluatedChanged, lambda node: self.updateNodeItem(node, 'evaluated')),
                (model.errorChanged, lambda node: self.updateNodeItem(node, 'error')),
                (model.resultChanged, lambda node: self.updateNodeItem(node, 'result')),

                # Node Parameters
                (model.parametersInserted, lambda node_key, first, last, model=model: 
                    self.insertInletItems(node_key, 0, [model.parameterName(node_key, i) for i in range(first, last)])
                ),
                (model.patametersChanged, lambda node_key, first, last, model=model: 
                    self.updateParameterItems(node_key, [model.parameterName(node_key, i) for i in range(first, last)])
                ),
                (model.parametersAboutToBeRemoved, lambda node_key, first, last, model=model:
                    self.removeInletItem(node_key, [model.parameterName(node_key, i) for i in range(first, last)])
                ),

                # Node Links
                (model.nodesLinked, lambda source, target, inlet:
                    self.addLinkItems([(source, target, "out", inlet)])
                    ),
                (model.nodesAboutToBeUnlinked, lambda source, target, inlet:
                    self.removeLinkItems([(source, target, "out", inlet)])
                    ),
                
            ]
            for signal, slot in self._model_connections:
                signal.connect(slot)
            
        self._model = model

        # populate initial scene
        self.resetItems()

    def model(self)->QAbstractItemModel|None:
        return self._tree

    ### Handle Model Signals
    def resetItems(self):
        assert self._model
        self.addNodeItems(self._model.nodes())
        for node_key in self._model.nodes():
            port_keys = [self._model.parameterName(node_key, i) for i in range(self._model.parameterCount(node_key))]
            self.insertInletItems(node_key, 0, port_keys)

        link_keys = set()
        for source, target, inlet in self._model.links():
            link_keys.add( (source, target, "out", inlet) )
        self.addLinkItems(link_keys)

    ### Node
    def addNodeItems(self, node_keys:Iterable[str]):
        for node_key in node_keys:
            node_widget = NodeItem(key=node_key)
            self._node_widgets[node_key] = node_widget
            self.scene().addItem(node_widget)

    def updateNodeItem(self, node_key:str, hint:Literal['source', 'position', 'compiled', 'evaluated', 'error', 'result']):
        node_widget = self._node_widgets[node_key]
        node_widget.update()

    def removeNodeItems(self, node_keys:list[str]):
        for key in node_keys:
            node_widget = self._node_widgets[key]
            del self._node_widgets[key]
            self.scene().removeItem(node_widget)

    ### Parameters
    def insertInletItems(self, node_key:str, index:int, port_keys:Iterable[str]):
        if index!=0:
            raise NotImplementedError("not yet implemented")
        node_widget = self._node_widgets[node_key]
        for port_key in port_keys:
            port_widget = PortItem(port_key)
            node_key = node_key
            node_widget._inlet_widgets[port_key] = port_widget
            port_widget.setParentItem(node_widget)

    def updateParameterItems(self, node_key:str, port_keys:Iterable[str], hints=None):
        assert self._model
        node_widget = self._node_widgets[node_key]
        for port_key in port_keys:
            port_widget = node_widget._inlet_widgets[port_key]
            port_widget.update()

    def removeInletItem(self, node_key:str, port_keys:Iterable[str]):
        assert self._model
        node_widget = self._node_widgets[node_key]
        for poet_key in port_keys:
            port_widget = node_widget._inlet_widgets[node_key]
            del node_widget._inlet_widgets[node_key]
            self.scene().removeItem(port_widget)

    ### Links
    def addLinkItems(self, link_keys:Iterable[tuple[str,str,str,str]]):
        for link_key in link_keys:
            source, target, outlet, inlet = link_key

            link_widget = LinkItem(link_key)
            self._link_widgets[link_key] = link_widget
            self.scene().addItem(link_widget)

    def removeLinkItems(self, link_keys:Iterable[tuple[str,str,str,str]]):
        for link_key in link_keys:
            source, target, outlet, inlet = link_key
            link_widget = self._link_widgets[link_key]
            del self._link_widgets[link_key]
            self.scene().removeItem(link_widget)

    ### CRUD WIDGETS
    def _moveAttachedLinks(self, node_key:str):
        node_widget = self._node_widgets[node_key]

        # move incoming links
        for inlet_item in node_widget._inlet_widgets.values():
            for link_item in inlet_item.links:
                link_item.update()

        # outgoing links
        for link_item in node_widget._outlet.links:
            link_item.update()

    ### Map widgets to model
    def itemWidgets(self)->Collection[NodeItem|PortItem]:
        return [item for item in self._item_widgets.values()]

    def linkWidgets(self)->Collection[LinkItem]:
        return [item for item in self._link_widgets.values()]

    def itemWidget(self, index: QModelIndex) -> NodeItem|PortItem:
        assert self._tree, "self._edges was not defined"
        assert index.isValid() and index.model() == self._tree, f"bad index, got: {index}"
        item_id = QPersistentModelIndex(index)
        item_widget = self._item_widgets[item_id]
        return item_widget

    def linkWidget(self, source_index: QModelIndex, target_index:QModelIndex) -> LinkItem:
        assert self._tree, "self._edges was not defined"
        if not source_index.isValid():
            raise ValueError(f"Source {source_index} is invalid!")
        if source_index.model()!=self._tree:
            raise ValueError(f"Source {source_index} is not in this model!")
        if not target_index.isValid():
            raise ValueError(f"Target {target_index} is invalid!")
        if target_index.model()!=self._tree:
            raise ValueError(f"Target {target_index} is not in this model!")

        source_id = QPersistentModelIndex(source_index)
        target_id = QPersistentModelIndex(target_index)
        link_id = (source_id, target_id)
        link_widget = self._link_widgets[link_id]
        return link_widget

    ### Widgets At Position
    def itemIndexAt(self, pos: QPoint) -> QModelIndex|None:
        """Returns the topmost node at position pos, which is in viewport coordinates."""
        assert self._tree, "self._nodes was not defined"
        for item in self.items(pos.x()-4,pos.y()-4,8,8):
            if item in self._item_widgets.values():
                assert isinstance(item, (NodeItem, PortItem))
                item_id:QPersistentModelIndex =  item.index
                item_index = self._tree.index(item_id.row(), 0, item_id.parent())
                return item_index

    def linkIndexesAt(self, pos: QPoint) -> tuple[QModelIndex, QModelIndex]|None:
        """Returns the topmost edge at position pos, which is in viewport coordinates."""
        assert self._tree, "_edges was not defined"
        for item in self.items(pos.x()-4,pos.y()-4,8,8):
            if item in self._link_widgets.values():
                assert isinstance(item, LinkItem)
                link_id =  item.index
                source_id, target_id = link_id
                source_index = self._tree.index(source_id.row(), 0, source_id.parent())
                target_index = self._tree.index(target_id.row(), 0, target_id.parent())
                return source_index, target_index

    def centerNodes(self):
        logger.debug("centerNodes")
        self.centerOn(self.scene().itemsBoundingRect().center())

from dataclasses import dataclass

@dataclass
class InternalDragController:
    mode: Literal['inlet', 'outlet', 'edge_source', 'edge_target']
    source_widget: QGraphicsItem
    draft: QGraphicsItem


class _InternalDragMixin(_GraphEditorView):
    def __init__(self, delegate=None, parent: QWidget | None = None):
        super().__init__(delegate, parent)
        self._drag_controller:InternalDragController|None = None

    def mousePressEvent(self, event: QMouseEvent) -> None:
        assert self._delegate
        for item in self.items(event.position().toPoint()):
            if item in self._outlet_widgets.values():
                draft_link_item = self._delegate.createEdgeWidget(QModelIndex())
                self._drag_controller = InternalDragController(
                    mode='outlet',
                    source_widget= item,
                    draft=draft_link_item
                )
                self.scene().addItem(self._drag_controller.draft)
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        assert self._delegate
        if self._drag_controller:
            match self._drag_controller.mode:
                case 'outlet':
                    if inlet_id := self.inletIndexAt(event.position().toPoint()):
                        node_index, inlet = inlet_id
                        drop_widget = self.inletWidget(node_index, inlet)

                        # self._drag_controller.draft.move(
                        #     self._drag_controller.source_widget, 
                        #     drop_widget
                        # )
                        self._delegate.updateEdgePosition(
                            self._drag_controller.draft,
                            self._drag_controller.source_widget, 
                            drop_widget
                        )
                        return
                    else:
                        # self._drag_controller.draft.move(
                        #     self._drag_controller.source_widget, 
                        #     self.mapToScene(event.position().toPoint())
                        # )
                        self._delegate.updateEdgePosition(
                            self._drag_controller.draft,
                            self._drag_controller.source_widget, 
                            self.mapToScene(event.position().toPoint())
                        )
                        return
                case  _:
                     ...

        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        assert self._delegate
        if self._drag_controller:
            match self._drag_controller.mode:
                case 'outlet':
                    if inlet_id := self.inletIndexAt(event.position().toPoint()):
                        source_node_index, source_outlet = self._outlet_widgets.inverse[self._drag_controller.source_widget]
                        drop_node_index, drop_inlet = inlet_id
                        self.nodesLinked.emit(
                            source_node_index,
                            drop_node_index,
                            source_outlet,
                            drop_inlet
                        )

                    else:
                        #cancel connection
                        ...
                case _:
                    ...

            self.scene().removeItem(self._drag_controller.draft)
            self._drag_controller = None
        else:
            super().mouseReleaseEvent(event)


class GraphEditorView(
    # _GraphDragAndDropMixin,
    # _InternalDragMixin,
    # _GraphSelectionMixin, 
    # _GraphLayoutMixin,
     _GraphEditorView
    ):
    ...


def main():
    app = QApplication()

    class Window(QWidget):
        def __init__(self, parent: QWidget | None = None) -> None:
            super().__init__(parent=parent)
            self._model=PyDataModel()
            self._model.load("./tests/math_script.yaml")

            self.setupUI()
            self.action_connections = []
            self.bindView()

        def setupUI(self):
            self.graphview = _GraphEditorView()
            self.graphview.setWindowTitle("NXNetworkScene")

            self.create_node_action = QPushButton("create node", self)
            self.delete_action = QPushButton("delete", self)
            self.link_selected_action = QPushButton("connect selected", self)
            self.layout_action = QPushButton("layout nodes", self)
            self.layout_action.setDisabled(True)

            buttons_layout = QVBoxLayout()
            buttons_layout.addWidget(self.create_node_action)
            buttons_layout.addWidget(self.delete_action)
            buttons_layout.addWidget(self.link_selected_action)
            buttons_layout.addWidget(self.layout_action)
            grid_layout = QGridLayout()
            grid_layout.addLayout(buttons_layout, 0, 0)
            grid_layout.addWidget(self.graphview, 0, 1, 3, 1)

            self.setLayout(grid_layout)

        def bindView(self):
            self.graphview.setModel(self._model)

            self.action_connections = [
                (self.create_node_action.clicked, lambda: self.create_node()),
                (self.delete_action.clicked, lambda: self.delete_selected()),
                (self.link_selected_action.clicked, lambda: self.link_selected()),
                # (self.layout_action.clicked, lambda: self.graphview.layoutNodes())
            ]
            for signal, slot in self.action_connections:
                signal.connect(slot)

        ### commands
        @Slot()
        def create_node(self):
            assert self._model
            unique_name = make_unique_name("node0", self._model.nodes())
            self._model.addNode(unique_name, PyNodeItem())


        @Slot()
        def link_selected(self):
            ...

        @Slot()
        def delete_selected(self):
            # either a node or an inlet
            ...        


    window = Window()
    window.show()
    app.exec()

if __name__ == "__main__":
    main()

