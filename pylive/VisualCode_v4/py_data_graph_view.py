#####################
# The Network Scene #
#####################

#
# A Graph view that directly connects to PyDataModel
#


from enum import Enum
from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

import traceback
from collections import defaultdict
from textwrap import dedent
from itertools import chain

from bidict import bidict


from pylive.utils.geo import makeLineBetweenShapes, makeLineToShape
from pylive.utils.qt import distribute_items_horizontal
from pylive.utils.unique import make_unique_name
from pylive.utils.diff import diff_set

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

from pylive.VisualCode_v4.py_data_model import PyDataModel, PyNodeItem


from enum import StrEnum
class GraphMimeData(StrEnum):
    OutletData = 'application/outlet'
    InletData = 'application/inlet'
    LinkSourceData = 'application/link/source'
    LinkTargetData = 'application/link/target'


class PyDataGraphEditorView(QGraphicsView):
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
        self._link_widgets:bidict[tuple[str,str,str,str], LinkItem] = bidict()
        self._draft_link:QGraphicsLineItem|None=None

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
                (model.sourceChanged, lambda node:    self.updateNodeItems([node], 'source')),
                (model.positionChanged, lambda node:  self.updateNodeItems([node], 'position')),
                (model.needsCompilationChanged, lambda node:  self.updateNodeItems([node], 'needs_compilation')),
                (model.needsEvaluationChanged, lambda node: self.updateNodeItems([node], 'needs_evaluation')),
                (model.errorChanged, lambda node:     self.updateNodeItems([node], 'error')),
                (model.resultChanged, lambda node:    self.updateNodeItems([node], 'result')),

                # Node Parameters
                (model.parametersInserted, lambda node_key, first, last, model=model: 
                    self.insertInletItems(node_key, 0, [model.parameterName(node_key, i) for i in range(first, last)])
                ),
                (model.patametersChanged, lambda node_key, first, last, model=model: 
                    self.updateInletItems(node_key, [model.parameterName(node_key, i) for i in range(first, last)])
                ),
                (model.parametersAboutToBeRemoved, lambda node_key, first, last, model=model:
                    self.removeInletItem(node_key, [model.parameterName(node_key, i) for i in range(first, last)])
                ),
                (model.parametersReset, lambda node_key, model=model:
                    self.resetInletItems(node_key)
                ),

                # Node Links
                (model.nodesLinked, lambda links:
                    self.addLinkItems([(source, target, outlet, inlet) for source, target, outlet, inlet in links])
                    ),
                (model.nodesAboutToBeUnlinked, lambda links:
                    self.removeLinkItems([(source, target, outlet, inlet) for source, target, outlet, inlet in links])
                    ),
                
            ]
            for signal, slot in self._model_connections:
                signal.connect(slot)
            
        self._model = model

        # populate initial scene
        self.resetItems()

    def model(self)->QAbstractItemModel|None:
        return self._model

    ### Handle Model Signals
    def resetItems(self):
        assert self._model
        ### clear
        self.scene().clear()
        self._node_widgets.clear()
        self._link_widgets.clear()

        ### populate
        self.addNodeItems(self._model.nodes())
        for node_key in self._model.nodes():
            port_keys = [self._model.parameterName(node_key, i) for i in range(self._model.parameterCount(node_key))]
            self.insertInletItems(node_key, 0, port_keys)

        link_keys = set()
        for source, target, outlet, inlet in self._model.links():
            link_keys.add( (source, target, outlet, inlet) )
        self.addLinkItems(link_keys)

        self.layoutNodes()        

    ### Node
    def addNodeItems(self, node_keys:Iterable[str]):
        for node_key in node_keys:
            if node_key not in self._node_widgets:
                node_widget = NodeItem(key=node_key)
                self._node_widgets[node_key] = node_widget
                self.scene().addItem(node_widget)
                node_widget._view = self
                self.insertOutletItems(node_key, 0, ["out"])
            else:
                self.updateNodeItems([node_key])

    def updateNodeItems(self, node_keys:Iterable[str], hint:Literal['source', 'position', 'needs_compilation', 'needs_compilation', 'error', 'result', None]=None):
        assert all(key in self._node_widgets for key in node_keys)
        for node_key in node_keys:
            node_widget = self._node_widgets[node_key]
            node_widget.update()

    def removeNodeItems(self, node_keys:list[str]):
        for key in node_keys:
            if key in self._node_widgets:
                node_widget = self._node_widgets[key]
                del self._node_widgets[key]
                self.scene().removeItem(node_widget)

    ### Ports
    def insertInletItems(self, node_key:str, index:int, inlet_keys:Iterable[str]):
        """insert inlet item for keys.
        if the item already exist, update it!"""
        assert not isinstance(inlet_keys, str)
        #TODO: index is not yet supported
        node_widget = self._node_widgets[node_key]
        for key in inlet_keys:
            if key not in node_widget._inlet_widgets:
                widget = InletItem(key)
                node_key = node_key
                node_widget._inlet_widgets[key] = widget
                widget.setY(-5)
                widget.setParentItem(node_widget)
                widget._view = self
                # widget.scenePositionChanged.connect(lambda n=node_key, p=key: self.moveInletLinks(n, p))
                # widget.scenePositionChanged.connect(lambda n=node_key, p=key: self.moveOutletLinks(n, p))

            else:
                self.updateInletItems(node_key, [key])
        distribute_items_horizontal([_ for _ in node_widget._inlet_widgets.values()], node_widget.boundingRect())

    def resetInletItems(self, node_key:str):
        assert self._model
        node_widget = self._node_widgets[node_key]
        # clear inlets
        for item in node_widget._inlet_widgets.values():
            self.scene().removeItem(item)
        node_widget._inlet_widgets.clear()

        # insert all
        inlet_keys = [self._model.parameterName(node_key, i) for i in range(self._model.parameterCount(node_key))]
        self.insertInletItems(node_key, 0, inlet_keys)

    def insertOutletItems(self, node_key:str, index:int, outlet_keys:Iterable[str]):
        """insert inlet item for keys.
        if the item already exist, update it!"""
        assert not isinstance(outlet_keys, str)
        #TODO: index is not yet supported
        node_widget = self._node_widgets[node_key]
        for key in outlet_keys:
            if key not in node_widget._inlet_widgets.keys():
                widget = OutletItem(key)
                node_key = node_key
                node_widget._outlet_widgets[key] = widget
                widget.setY(24)
                widget.setParentItem(node_widget)
                widget._view = self

            else:
                self.updateInletItems(node_key, [key])
        distribute_items_horizontal([_ for _ in node_widget._outlet_widgets.values()], node_widget.boundingRect())

    def updateInletItems(self, node_key:str, inlet_keys:Iterable[str], hints=[]):
        """update inlet item for keys.
        raise an exception if the item does not exist"""
        assert self._model
        node_widget = self._node_widgets[node_key]
        for key in inlet_keys:
            widget = node_widget._inlet_widgets[key]
            widget.update()

    def updateOutletItems(self, node_key:str, outlet_keys:Iterable[str], hints=None):
        """update inlet item for keys.
        raise an exception if the item does not exist"""
        assert self._model
        node_widget = self._node_widgets[node_key]
        for key in outlet_keys:
            widget = node_widget._outlet_widgets[key]
            widget.update()
            
            # move attached links
            link_keys = [link.key for link in widget.links]
            widget.scenePositionChanged.connect(self.updateLinkItems(link_keys))

    def removeInletItem(self, node_key:str, inlet_keys:Iterable[str]):
        """remove inlet item for keys.
        raise an exception if the item does not exist"""
        assert self._model
        node_widget = self._node_widgets[node_key]
        for key in inlet_keys:
            widget = node_widget._inlet_widgets[key]
            del node_widget._inlet_widgets[key]
            self.scene().removeItem(widget)
            #TODO: remove connected links

    def removeOutletItem(self, node_key:str, outlet_keys:Iterable[str]):
        """remove inlet item for keys.
        raise an exception if the item does not exist"""
        assert self._model
        node_widget = self._node_widgets[node_key]
        for key in outlet_keys:
            widget = node_widget._outlet_widgets[key]
            del node_widget._outlet_widgets[key]
            self.scene().removeItem(widget)
            #TODO: remove connected links

    ### Links
    def addLinkItems(self, link_keys:Iterable[tuple[str,str,str,str]]):
        """add link items connecting the ports.
        if inlets, outlets or nodes does not exist, create them"""

        for link_key in link_keys:
            source_key, target_key, outlet_key, inlet_key = link_key
            if source_key not in self._node_widgets:
                self.addNodeItems([source_key]) #TODO: consider createint missing nodes in one shot

            if outlet_key not in self._node_widgets[source_key]._outlet_widgets.keys():
                count = len(self._node_widgets[source_key]._outlet_widgets)
                self.insertOutletItems(source_key, count, [outlet_key])

            if target_key not in self._node_widgets.keys():
                self.addNodeItems([target_key])

            if inlet_key not in self._node_widgets[target_key]._inlet_widgets.keys():
                inlets_count = len(self._node_widgets[target_key]._inlet_widgets)
                self.insertInletItems(target_key, inlets_count, [inlet_key])


            inlet_item = self._node_widgets[target_key]._inlet_widgets[inlet_key]
            outlet_item = self._node_widgets[source_key]._outlet_widgets[outlet_key]

            link_widget = LinkItem(link_key)
            self._link_widgets[link_key] = link_widget
            self.scene().addItem(link_widget)
            link_widget._view = self
            link_widget.move()

    def updateLinkItems(self, link_keys:Iterable[tuple[str,str,str,str]], hint=None):
        """update link items.
        raise an exception if linkitem does not exist """
        assert all(key in self._link_widgets for key in link_keys), "link item does not exist"
        for link_key in link_keys:
            source_key, target_key, outlet_key, inlet_key = link_key
            link_widget = self._link_widgets[link_key]
            source_port_item = self._node_widgets[source_key]._outlet_widgets[outlet_key]
            target_port_item = self._node_widgets[target_key]._inlet_widgets[inlet_key]

            from pylive.utils.geo import makeLineBetweenShapes
            line = makeLineBetweenShapes(source_port_item, target_port_item)
            link_widget.setLine(line)

    def removeLinkItems(self, link_keys:Iterable[tuple[str,str,str,str]]):
        """remove link items.
        raise an exception if linkitem does not exist """
        assert all(key in self._link_widgets for key in link_keys), "link item does not exist"
        for link_key in link_keys:
            source, target, outlet, inlet = link_key
            link_widget = self._link_widgets[link_key]
            del self._link_widgets[link_key]
            self.scene().removeItem(link_widget)
    
    ### DRAG links and ports
    def _createDraftLink(self):
        """Safely create draft link with state tracking"""
        assert self._draft_link is None
            
        self._draft_link = QGraphicsLineItem()
        self._draft_link.setPen(QPen(self.palette().text(), 1))
        self.scene().addItem(self._draft_link)

    def _cleanupDraftLink(self):
        """Safely cleanup draft link"""
        assert self._draft_link
        self.scene().removeItem(self._draft_link)
        self._draft_link = None

    ### Layout
    def centerNodes(self):
        self.centerOn(self.scene().itemsBoundingRect().center())

    def layoutNodes(self, orientation=Qt.Orientation.Vertical, scale=100):
        assert self._model, f"bad _model, got: {self._model}"
        from pylive.utils.graph import hiearchical_layout_with_nx
        import networkx as nx
        G = nx.MultiDiGraph()
        for node_key in self._model.nodes():
            G.add_node(node_key)

        for source, target, outlet, inlet in self._model.links():
            G.add_edge(source, target, key=inlet)

        pos:dict[str, tuple[float, float]] = hiearchical_layout_with_nx(G, scale=scale)
        for node_key, (x, y) in pos.items():
            if node_widget := self._node_widgets[node_key]:
                match orientation:
                    case Qt.Orientation.Vertical:
                        node_widget.setPos(x, y)
                    case Qt.Orientation.Horizontal:
                        node_widget.setPos(y, x)

    ### Selection
    def selectedNodes(self)->list[str]:
        selected = []
        for node_key, node_item in self._node_widgets.items():
            if node_item.isSelected():
                selected.append(node_key)

        return selected

    def selectNodes(self, node_selection:Iterable[str]):
        next_node_selection = set(self._node_widgets[_] for _ in node_selection)
        prev_node_selection = set(_ for _ in self.scene().selectedItems())

        change = diff_set(prev_node_selection, next_node_selection)
        self.blockSignals(True)
        for item in change.removed:
            assert isinstance(item, NodeItem)
            item.setSelected(False)
        for item in change.added:
            assert isinstance(item, NodeItem)
            item.setSelected(True)
        self.blockSignals(False)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        print(f"View.dragEnter {event.mimeData().formats()}")
        super().dragEnterEvent(event)

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        super().dragMoveEvent(event)
        if event.isAccepted():
            return

        print(f"View.dragMove {event.mimeData().formats()}")
        if event.mimeData().hasFormat(GraphMimeData.OutletData):
            source_node, outlet = event.mimeData().data(GraphMimeData.OutletData).toStdString().split("/")
            source_item = self._node_widgets[source_node]._outlet_widgets[outlet]
            if self._draft_link:
                line = self._draft_link.line()
                mouse_scene_pos = self.mapToScene(event.position().toPoint())
                line = makeLineBetweenShapes(source_item, mouse_scene_pos)
                self._draft_link.setLine(line)


        if event.mimeData().hasFormat(GraphMimeData.InletData):
            target_node, inlet = event.mimeData().data(GraphMimeData.InletData).toStdString().split("/")
            target_item = self._node_widgets[target_node]._inlet_widgets[inlet]
            if self._draft_link:
                line = self._draft_link.line()
                mouse_scene_pos = self.mapToScene(event.position().toPoint())
                line = makeLineBetweenShapes(mouse_scene_pos, target_item)
                self._draft_link.setLine(line)

        if event.mimeData().hasFormat(GraphMimeData.LinkSourceData):
            link_key = event.mimeData().data(GraphMimeData.LinkSourceData).toStdString().split("/")
            source, target, outlet, inlet = link_key
            source_item = self._node_widgets[source]._outlet_widgets[outlet]
            target_item = self._node_widgets[target]._inlet_widgets[inlet]

            if self._draft_link:
                line = self._draft_link.line()
                mouse_scene_pos = self.mapToScene(event.position().toPoint())
                line = makeLineBetweenShapes(source_item, mouse_scene_pos)
                self._draft_link.setLine(line)
                event.acceptProposedAction() # Todo: accept delete action

        if event.mimeData().hasFormat(GraphMimeData.LinkTargetData):
            link_key = event.mimeData().data(GraphMimeData.LinkTargetData).toStdString().split("/")
            source, target, outlet, inlet = link_key
            source_item = self._node_widgets[source]._outlet_widgets[outlet]
            target_item = self._node_widgets[target]._inlet_widgets[inlet]

            if self._draft_link:
                line = self._draft_link.line()
                mouse_scene_pos = self.mapToScene(event.position().toPoint())
                line = makeLineBetweenShapes(mouse_scene_pos, target_item)
                self._draft_link.setLine(line)
                event.acceptProposedAction() # Todo: accept delete action

    def dropEvent(self, event: QDropEvent) -> None:
        super().dropEvent(event)
        # if event.isAccepted():
        #     return
        print(f"View.drop {event.mimeData().formats()}")
        if event.mimeData().hasFormat(GraphMimeData.LinkSourceData):
            assert self._model
            link_key = event.mimeData().data(GraphMimeData.LinkSourceData).toStdString().split("/")
            source, target, outlet, inlet = link_key
            self._model.unlinkNodes(source, target, outlet, inlet)

        if event.mimeData().hasFormat(GraphMimeData.LinkTargetData):
            assert self._model
            link_key = event.mimeData().data(GraphMimeData.LinkTargetData).toStdString().split("/")
            source, target, outlet, inlet = link_key
            self._model.unlinkNodes(source, target, outlet, inlet)


class PortItem(QGraphicsItem):
    def __init__(self, key:str, parent:QGraphicsItem|None=None):
        super().__init__(parent=parent)
        self.key = key
        self.label = QGraphicsTextItem(f"{self.key}")
        self.label.setParentItem(self)
        self.label.setPos(0,-20)
        self.label.hide()
        self.setAcceptHoverEvents(True)
        r = 3
        # self.setGeometry(QRectF(-r,-r,r*2,r*2))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges, True)
        self._view:PyDataGraphEditorView|None = None

    def view(self)->PyDataGraphEditorView|None:
        return self._view

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        if change == QGraphicsItem.GraphicsItemChange.ItemScenePositionHasChanged:
            assert self._view
            assert self._view._model
            node_widget = self.parentItem()
            assert isinstance(node_widget, NodeItem)
            inlink_keys = self._view._model.inLinks(node_widget.key)
            outlink_keys = self._view._model.outLinks(node_widget.key)
            link_keys = list(chain(inlink_keys, outlink_keys))

            for link_key in link_keys:
                if link_item := self._view._link_widgets.get(link_key):
                    link_item.move()
        return super().itemChange(change, value)

    def boundingRect(self) -> QRectF:
        r = 6
        return QRectF(-r,-r,r*2,r*2)

    def shape(self):
        r = 3
        path = QPainterPath()
        path.addEllipse(QRectF(-r,-r,r*2,r*2))
        return path

    def paint(self, painter:QPainter, option:QStyleOption, widget:QWidget|None=None):
        palette = widget.palette() if widget else QApplication.palette()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(palette.text())
        if QStyle.StateFlag.State_MouseOver in option.state:
            painter.setBrush(palette.accent())
        r = 3
        painter.drawEllipse(QRectF(-r,-r,r*2,r*2))


class InletItem(PortItem):
    def __init__(self, key: str, parent: QGraphicsItem | None = None):
        super().__init__(key, parent)
        self.setAcceptHoverEvents(True)
        self.setAcceptDrops(True)

    def paint(self, painter:QPainter, option:QStyleOption, widget:QWidget|None=None):
        assert self._view
        assert self._view._model
        node_widget = self.parentItem()
        assert isinstance(node_widget, NodeItem)
        node_key = node_widget.key

        if self._view._model.hasParameter(node_key, self.key):
            super().paint(painter, option, widget)
        else:
            r = 3
            palette = widget.palette() if widget else QApplication.palette()
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(palette.placeholderText())
            painter.drawEllipse(QRectF(-r,-r,r*2,r*2))

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        print("press inlet")
        # Setup new drag
        assert self._view
        node_widget = self.parentItem()
        assert isinstance(node_widget, NodeItem)

        mime = QMimeData()
        mime.setData(GraphMimeData.InletData, f"{node_widget.key}/{self.key}".encode("utf-8"))
        drag = QDrag(self._view)
        drag.setMimeData(mime)

        # Create visual feedback
        assert self._view
        self._view._createDraftLink()

        # Execute drag
        try:
            action = drag.exec(Qt.DropAction.CopyAction)
        except Exception as err:
            traceback.print_exc()
        finally:
            self._view._cleanupDraftLink()

    def dragEnterEvent(self, event: QGraphicsSceneDragDropEvent) -> None:
        print(f"Inlet.dragEnter {event.mimeData().formats()}")
        if event.mimeData().hasFormat(GraphMimeData.OutletData):
            assert self._view
            assert self._view._model
            node_widget = self.parentItem()
            assert isinstance(node_widget, NodeItem)
            node_key = node_widget.key
            if self._view._model.hasParameter(node_key, self.key):
                event.acceptProposedAction()
                return

        if event.mimeData().hasFormat(GraphMimeData.LinkSourceData):
            assert self._view
            assert self._view._model
            node_widget = self.parentItem()
            assert isinstance(node_widget, NodeItem)
            node_key = node_widget.key
            if self._view._model.hasParameter(node_key, self.key):
                event.acceptProposedAction()
                return

    def dragMoveEvent(self, event: QGraphicsSceneDragDropEvent) -> None:
        print(f"Inlet.dragMove {event.mimeData().formats()}")
        if event.mimeData().hasFormat(GraphMimeData.OutletData):
            assert self._view
            source_node, outlet = event.mimeData().data(GraphMimeData.OutletData).toStdString().split("/")
            source_item = self._view._node_widgets[source_node]._outlet_widgets[outlet]
            if self._view._draft_link:
                line = self._view._draft_link.line()
                line = makeLineBetweenShapes(source_item, self)
                self._view._draft_link.setLine(line)
                event.acceptProposedAction()
                return

        if event.mimeData().hasFormat(GraphMimeData.LinkSourceData):
            assert self._view
            link_key = event.mimeData().data(GraphMimeData.LinkSourceData).toStdString().split("/")
            source, target, outlet, inlet = link_key
            source_item = self._view._node_widgets[source]._outlet_widgets[outlet]
            if self._view._draft_link:
                line = self._view._draft_link.line()
                line = makeLineBetweenShapes(source_item, self)
                self._view._draft_link.setLine(line)
                event.acceptProposedAction()
                return
        return super().dragMoveEvent(event)

    def dropEvent(self, event: QGraphicsSceneDragDropEvent) -> None:
        print(f"Inlet.drop {event.mimeData().formats()}")
        if event.mimeData().hasFormat(GraphMimeData.OutletData):
            assert self._view
            assert self._view._model
            source_node, source_outlet = event.mimeData().data(GraphMimeData.OutletData).toStdString().split("/")
            
            node_widget = self.parentItem()
            assert isinstance(node_widget, NodeItem)
            target_node_key = node_widget.key
            target_inlet_key = self.key
            self._view._model.linkNodes(source_node, target_node_key, source_outlet, target_inlet_key)
            event.acceptProposedAction()
            return

        if event.mimeData().hasFormat(GraphMimeData.LinkSourceData):
            assert self._view
            assert self._view._model
            link_key = event.mimeData().data(GraphMimeData.LinkSourceData).toStdString().split("/")
            source, target, outlet, inlet = link_key
            # unlink current
            self._view._model.unlinkNodes(source, target, outlet, inlet)

            # link source with new target
            node_widget = self.parentItem()
            assert isinstance(node_widget, NodeItem)
            target_node_key = node_widget.key
            target_inlet_key = self.key
            self._view._model.linkNodes(source, target_node_key, outlet, target_inlet_key)
            event.acceptProposedAction()
            return

        return super().dragMoveEvent(event)


class OutletItem(PortItem):
    def __init__(self, key: str, parent: QGraphicsItem | None = None):
        super().__init__(key, parent)
        self.setAcceptHoverEvents(True)
        self.setAcceptDrops(True)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        print("press outlet")
        # Setup new drag
        assert self._view
        node_widget = self.parentItem()
        assert isinstance(node_widget, NodeItem)

        mime = QMimeData()
        mime.setData(GraphMimeData.OutletData, f"{node_widget.key}/{self.key}".encode("utf-8"))
        drag = QDrag(self._view)
        drag.setMimeData(mime)

        # Create visual feedback
        assert self._view
        self._view._createDraftLink()

        # Execute drag
        try:
            action = drag.exec(Qt.DropAction.CopyAction)
        except Exception as err:
            traceback.print_exc()
        finally:
            self._view._cleanupDraftLink()

    def dragEnterEvent(self, event: QGraphicsSceneDragDropEvent) -> None:
        print(f"Outlet.dragEnter {event.mimeData().formats()}")
        if event.mimeData().hasFormat(GraphMimeData.InletData):
            event.acceptProposedAction() # Todo: set accepted action
            return

        if event.mimeData().hasFormat(GraphMimeData.LinkTargetData):
            event.acceptProposedAction()
            return

    def dragMoveEvent(self, event: QGraphicsSceneDragDropEvent) -> None:
        print(f"Outlet.dragMove {event.mimeData().formats()}")
        if event.mimeData().hasFormat(GraphMimeData.InletData):
            assert self._view
            target_node, inlet = event.mimeData().data(GraphMimeData.InletData).toStdString().split("/")
            target_item = self._view._node_widgets[target_node]._inlet_widgets[inlet]
            if self._view._draft_link:
                line = self._view._draft_link.line()
                line = makeLineBetweenShapes(self, target_item)
                self._view._draft_link.setLine(line)
                event.acceptProposedAction()
                return

        if event.mimeData().hasFormat(GraphMimeData.LinkTargetData):
            assert self._view
            link_key = event.mimeData().data(GraphMimeData.LinkTargetData).toStdString().split("/")
            source, target, outlet, inlet = link_key
            source_item = self._view._node_widgets[source]._inlet_widgets[outlet]
            if self._view._draft_link:
                line = self._view._draft_link.line()
                line = makeLineBetweenShapes(source_item, self)
                self._view._draft_link.setLine(line)
                event.acceptProposedAction()
                return

        return super().dragMoveEvent(event)

    def dropEvent(self, event: QGraphicsSceneDragDropEvent) -> None:
        print(f"Inlet.drop {event.mimeData().formats()}")
        if event.mimeData().hasFormat(GraphMimeData.InletData):
            assert self._view
            assert self._view._model
            target_node, inlet = event.mimeData().data(GraphMimeData.InletData).toStdString().split("/")

            self._view._model.linkNodes(cast(NodeItem, self.parentItem()).key, target_node, self.key, inlet)
            event.acceptProposedAction()
            return

        if event.mimeData().hasFormat(GraphMimeData.LinkTargetData):
            assert self._view
            assert self._view._model
            link_key = event.mimeData().data(GraphMimeData.LinkTargetData).toStdString().split("/")
            source, target, outlet, inlet = link_key
            # unlink current
            self._view._model.unlinkNodes(source, target, outlet, inlet)

            # link source with new target
            self._view._model.linkNodes(source, cast(NodeItem, self.parentItem()).key, outlet, self.key)
            event.acceptProposedAction()
            return

        return super().dragMoveEvent(event)


class NodeItem(QGraphicsItem):
    # scenePositionChanged = Signal()
    def __init__(self, key:str, parent:QGraphicsItem|None=None):
        super().__init__(parent=parent)
        self.key:str = key

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges, True)

        self._inlet_widgets:bidict[str, InletItem] = bidict()
        self._outlet_widgets:bidict[str, OutletItem] = bidict()

        self._view:PyDataGraphEditorView|None = None

    def view(self)->PyDataGraphEditorView|None:
        return self._view

    def font(self):
        if widget:=self.parentWidget():
            return widget.font()

        if scene :=self.scene():
            return scene.font()

        app = QApplication.instance()
        if isinstance(app, QGuiApplication):
            return app.font()
        
        raise NotImplementedError()

    def palette(self)->QPalette:
        if widget:=self.parentWidget():
            return widget.palette()

        if scene :=self.scene():
            return scene.palette()

        app = QApplication.instance()
        if isinstance(app, QGuiApplication):
            return app.palette()
        
        raise NotImplementedError()

    def boundingRect(self) -> QRectF:
        # return QRectF(0,0,19,16)
        fm = QFontMetrics(self.font())
        size = fm.boundingRect(f"{self.key}").size().toSizeF()
        return QRectF(QPointF(), size+QSizeF(18,2))

    def paint(self, painter: QPainter, option, widget=None):
        rect = self.boundingRect().normalized()

        pen = painter.pen()
        pen.setBrush(self.palette().text())
        if self.isSelected():
            pen.setBrush(self.palette().accent())
        painter.setPen(pen)

        rect.moveTo(QPoint(0,0))
        painter.drawRoundedRect(rect, 6,6)
        painter.drawText(rect, f"{self.key}", QTextOption(Qt.AlignmentFlag.AlignCenter))
        # painter.drawText(QPoint(0,0), )


class LinkItem(QGraphicsLineItem):
    def __init__(self, key:tuple[str,str,str,str], parent:QGraphicsItem|None=None):
        super().__init__(parent=parent)
        self.key:tuple[str,str,str,str] = key
        self.setLine(0,0,10,10)
        self.setPen(QPen(self.palette().text(), 1))

        self.setAcceptHoverEvents(True)
        self._view:PyDataGraphEditorView|None = None

    def view(self)->PyDataGraphEditorView|None:
        return self._view

    def move(self):
        assert self._view
        source, target, outlet, inlet = self.key
        source = self._view._node_widgets[source]._outlet_widgets[outlet]
        target = self._view._node_widgets[target]._inlet_widgets[inlet]

        self.setLine( makeLineBetweenShapes(source, target) )

    def palette(self)->QPalette:
        if widget:=self.parentWidget():
            return widget.palette()

        if scene :=self.scene():
            return scene.palette()

        app = QApplication.instance()
        if isinstance(app, QGuiApplication):
            return app.palette()
        
        raise NotImplementedError()

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        assert self._view
        d1 = (event.scenePos() - self.line().p1()).manhattanLength()
        d2 = (event.scenePos() - self.line().p2()).manhattanLength()
        if d1 < d2:
            mime = QMimeData()
            source, target, outlet, inlet = self.key
            mime.setData(GraphMimeData.LinkTargetData, f"{source}/{target}/{outlet}/{inlet}".encode("utf-8"))
            drag = QDrag(self._view)
            drag.setMimeData(mime)
            
            # Execute drag
            self._view._draft_link = self
            try:
                action = drag.exec(Qt.DropAction.TargetMoveAction)
            except Exception as err:
                traceback.print_exc()
            finally:
                self._view._draft_link = None
                self.move()
        else:
            mime = QMimeData()
            source, target, outlet, inlet = self.key
            mime.setData(GraphMimeData.LinkSourceData, f"{source}/{target}/{outlet}/{inlet}".encode("utf-8"))
            drag = QDrag(self._view)
            drag.setMimeData(mime)
            
            # Execute drag
            self._view._draft_link = self
            try:
                action = drag.exec(Qt.DropAction.TargetMoveAction)
            except Exception as err:
                traceback.print_exc()
            finally:
                self._view._draft_link = None
                self.move()

    def mouseMoveEvent(self, event):
        print("link move")
            
    def paint(self, painter:QPainter, option:QStyleOption, widget:QWidget|None=None):
        painter.setPen( QPen(self.palette().text(), 1) )
        if QStyle.StateFlag.State_MouseOver in option.state:
            painter.setPen( QPen(self.palette().accent(), 1) )
        painter.drawLine(self.line())


def main():
    app = QApplication()


    class Window(QWidget):
        def __init__(self, parent: QWidget | None = None) -> None:
            super().__init__(parent=parent)
            self._model=PyDataModel()
            self._model.load("./tests/math_script.yaml")
            self._model.compileNodes(self._model.nodes())

            self.setupUI()
            self.action_connections = []
            self.bindView()

            self.graphview.layoutNodes()

        def setupUI(self):
            self.graphview = PyDataGraphEditorView()
            self.graphview.setWindowTitle("NXNetworkScene")

            self.create_node_action = QPushButton("create node", self)
            self.delete_action = QPushButton("delete", self)
            self.link_selected_action = QPushButton("connect selected", self)
            self.layout_action = QPushButton("layout nodes", self)
            self.layout_action.setDisabled(False)

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
                (self.layout_action.clicked, lambda: self.graphview.layoutNodes())
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

