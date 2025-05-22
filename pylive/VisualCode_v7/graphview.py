#####################
# The Network Scene #
#####################

#
# A Graph view that directly connects to PyGraphmodel
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

class GraphView(QWidget):
    nodesLinked = Signal(QModelIndex, QModelIndex, str, str)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent=parent)
        self._nodes:QAbstractItemModel | None = None
        self._links:QAbstractItemModel | None = None
        self._model_connections = []

        # store model widget relations
        # map item index to widgets
        self._widgets: bidict[QPersistentModelIndex, NodeItem] = bidict()
        # self._inlet_widgets: bidict[QPersistentModelIndex, InletItem] = bidict()
        # self._outlet_widgets: bidict[QPersistentModelIndex, OutletItem] = bidict()
        self._link_widgets: bidict[tuple[QPersistentModelIndex, QPersistentModelIndex], LinkItem] = bidict()
        self._draft_link: QGraphicsLineItem | None = None

        self.setupUI()

    def setupUI(self):
        self.graphicsview = QGraphicsView(self)
        self.graphicsview.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.graphicsview.setCacheMode(QGraphicsView.CacheModeFlag.CacheNone)
        self.graphicsview.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.graphicsview.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        self.graphicsview.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        scene = QGraphicsScene()
        scene.setSceneRect(QRectF(-9999, -9999, 9999 * 2, 9999 * 2))
        self.graphicsview.setScene(scene)
        layout = QVBoxLayout()
        layout.addWidget(self.graphicsview)
        self.setLayout(layout)

    def setModel(self, nodes:QAbstractItemModel, links:QAbstractItemModel):
        if self._nodes or self._links:
            for signal, slot in self._model_connections:
                signal.disconnect(slot)

        assert isinstance(nodes, QAbstractItemModel)
        assert isinstance(links, QAbstractItemModel)


        if nodes and links:
            self._model_connections = []

            nodes.dataChanged.connect(self.onNodeDataChanged)

        self._nodes = nodes
        self._links = links

        # populate initial scene
        self.populate()

    @Slot()
    def onNodeDataChanged(self, topLeft:QModelIndex , bottomRight:QModelIndex , roles=[]):
        for row in range(topLeft.row(), bottomRight.row()+1):
            for col in range(topLeft.column(), bottomRight.column()+1):
                cell_index = self._nodes.index(row, col)
                widget = self._widgets[QPersistentModelIndex(cell_index)]
                proxy = cast(QGraphicsProxyWidget, widget)
                proxy.widget().setText(cell_index.data(Qt.ItemDataRole.DisplayRole))
            node_index = self._nodes.index(row, 0)
            node_widget = self._widgets[QPersistentModelIndex(node_index)]
            node_widget.resize(node_widget.layout().sizeHint(Qt.SizeHint.PreferredSize))
            # node_widget.updateGeometry()

    def model(self) -> Tuple[QAbstractItemModel, QAbstractItemModel] | None:
        return self._nodes, self._links
    #
    ### Handle Model Signals
    def populate(self):
        assert self._nodes and self._links
        ## clear
        self.graphicsview.scene().clear()

        self._link_widgets.clear()
        # self._inlet_widgets.clear()
        # self._outlet_widgets.clear()
        self._widgets.clear()

        ## populate
        ### nodes
        # create node_items from rows
        for row in range(self._nodes.rowCount()):
            node_index = self._nodes.index(row, 0)
            node_item = NodeItem()
            node_item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
            node_item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
            self.graphicsview.scene().addItem(node_item)
            self._widgets[QPersistentModelIndex(node_index)] = node_item

            # create labels from cells
            for col in range(self._nodes.columnCount()):
                cell_index = self._nodes.index(row, col)
                text = cell_index.data(Qt.ItemDataRole.DisplayRole)
                label = QLabel(text)
                proxy = QGraphicsProxyWidget()
                proxy.setWidget(label)
                node_item.layout().addItem(proxy)
                self._widgets[QPersistentModelIndex(cell_index)] = proxy

            # create inlets from children
            for child_row in range(self._nodes.rowCount(parent=node_index)):
                inlet_index = self._nodes.index(child_row, 0)
                inlet_item = InletItem()
                self._widgets[QPersistentModelIndex(inlet_index)] = inlet_item
                inlet_item.setParentItem(node_item)



class PortItem(QGraphicsItem):
    def __init__(self, parent: QGraphicsItem | None = None):
        super().__init__(parent=parent)
        self._label = QGraphicsTextItem(f"-port-")
        self._label.setParentItem(self)
        self._label.setPos(0, -25)
        self._label.hide()
        self.setAcceptHoverEvents(True)
        r = 3
        # self.setGeometry(QRectF(-r,-r,r*2,r*2))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges, True)
        self._view: PyGraphView | None = None

    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        self._label.show()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent, /) -> None:
        self._label.hide()
        super().hoverLeaveEvent(event)

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
        r = 3
        return QRectF(-r, -r, r * 2, r * 2).adjusted(-3, -3, 3, 3)

    def shape(self):
        r = 3
        path = QPainterPath()
        path.addEllipse(QRectF(-r, -r, r * 2, r * 2))
        return path

    def paint(self, painter: QPainter, option: QStyleOption, widget: QWidget | None = None):
        palette = widget.palette() if widget else QApplication.palette()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(palette.text())
        if QStyle.StateFlag.State_MouseOver in option.state:
            painter.setBrush(palette.accent())
        r = 3
        painter.drawEllipse(QRectF(-r, -r, r * 2, r * 2))


class InletItem(PortItem):
    def __init__(self, parent: QGraphicsItem | None = None):
        super().__init__(parent)
        self.setAcceptHoverEvents(True)
        self.setAcceptDrops(True)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
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
        if event.mimeData().hasFormat(GraphMimeData.OutletData):
            assert self._view
            assert self._view._model
            node_widget = self.parentItem()
            assert isinstance(node_widget, NodeItem)
            node_key = node_widget.key

            event.acceptProposedAction()
            return

        if event.mimeData().hasFormat(GraphMimeData.LinkSourceData):
            assert self._view
            assert self._view._model
            node_widget = self.parentItem()
            assert isinstance(node_widget, NodeItem)
            node_key = node_widget.key
            event.acceptProposedAction()
            return

    def dragMoveEvent(self, event: QGraphicsSceneDragDropEvent) -> None:
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

    def boundingRect(self) -> QRectF:
        flags = self.model.inletFlags(self.node, self.key)
        r = 3
        if 'multi' in flags:
            return QRectF(-r, -r, r * 4, r * 2).adjusted(-3, -3, 3, 3)
        else:
            return QRectF(-r, -r, r * 2, r * 2).adjusted(-3, -3, 3, 3)

    def shape(self):
        flags = self.model.inletFlags(self.node, self.key)
        path = QPainterPath()
        r = 3
        if 'multi' in flags:
            path.addRoundedRect(-r, -r, r * 4, r * 2, r, r)
        else:
            path.addEllipse(QRectF(-r, -r, r * 2, r * 2))

        return path

    def paint(self, painter: QPainter, option: QStyleOption, widget: QWidget | None = None):
        flags = self.model.inletFlags(self.node, self.key)
        palette = widget.palette() if widget else QApplication.palette()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(palette.text())

        if QStyle.StateFlag.State_MouseOver in option.state:
            painter.setBrush(palette.accent())

        if 'required' in flags and not self.model.isInletLinked(self.node, self.key):
            painter.setBrush(QBrush("red"))

        r = 3
        if 'multi' in flags:
            painter.drawRoundedRect(-r, -r, r * 4, r * 2, r, r)
        else:

            if 'extra' in flags:
                painter.setPen(QPen(palette.text(), 1))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawText(QRectF(-r + 2.45, -r - 0.1, r, r).adjusted(-2, -2, 2, 2), "+",
                                 QTextOption(Qt.AlignmentFlag.AlignCenter))
            else:
                painter.drawEllipse(QRectF(-r, -r, r * 2, r * 2))

    def refresh(self):
        self._label.setPlainText(f"{self.key}")
        self.prepareGeometryChange()
        self.update()


class OutletItem(PortItem):
    def __init__(self, model: QAbstractItemModel, node: str, key: str, parent: QGraphicsItem | None = None):
        super().__init__(parent)
        self.setAcceptHoverEvents(True)
        self.setAcceptDrops(True)
        self.model = model
        self.node = node
        self.key = key
        self._view: GraphView | None = None

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
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
        if event.mimeData().hasFormat(GraphMimeData.InletData):
            event.acceptProposedAction()  # Todo: set accepted action
            return

        if event.mimeData().hasFormat(GraphMimeData.LinkTargetData):
            event.acceptProposedAction()
            return

    def dragMoveEvent(self, event: QGraphicsSceneDragDropEvent) -> None:
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

    def refresh(self):
        self._label.setPlainText(f"{self.key}")
        self.update()

# class NodeCell(QGraphicsWidget):
#     def __init__(self, index: QPersistentModelIndex, parent: QGraphicsItem | None = None):
#         super().__init__(parent=parent)
#         self._index = index
#         self.setGeometry(QRectF(0, 0, 100, 10))
#
#     def paint(self, painter: QPainter, option: QStyleOption, widget=None):
#         rect = option.rect
#         pen = painter.pen()
#         pen.setBrush(self.palette().text())
#         if self.isSelected():
#             pen.setBrush(self.palette().accent())
#         painter.setPen(pen)
#         #
#         # fm = QFontMetrics(self.font())
#         # row = self._index.row()
#         # content = self._index.sibling(row, 2).data(Qt.ItemDataRole.DisplayRole)
#         # content_bbox = fm.boundingRect(f"{content}")
#         # content_bbox.adjust(-6, -2, 6, 2)
#         painter.drawRoundedRect(rect, 6, 6)


class NodeItem(QGraphicsWidget):
    # scenePositionChanged = Signal()
    def __init__(self, parent: QGraphicsItem | None = None):
        super().__init__(parent=parent)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges, True)

        layout = QGraphicsLinearLayout(Qt.Orientation.Vertical)
        self.setLayout(layout)

    def paint(self, painter: QPainter, option: QStyleOption, widget=None):
        rect = option.rect
        pen = painter.pen()
        pen.setBrush(self.palette().text())
        if self.isSelected():
            pen.setBrush(self.palette().accent())
        painter.setPen(pen)
        painter.drawRoundedRect(rect, 6, 6)


class LinkItem(QGraphicsLineItem):
    def __init__(self, model: QAbstractItemModel, key: tuple[str, str, str, str], parent: QGraphicsItem | None = None):
        super().__init__(parent=parent)
        self.model = model
        self.key: tuple[str, str, str, str] = key
        self.setLine(0, 0, 10, 10)
        self.setPen(QPen(self.palette().text(), 1))

        self.setAcceptHoverEvents(True)
        self._view: PyGraphView | None = None

    def move(self):
        assert self._view
        source, target, outlet, inlet = self.key
        source = self._view._node_widgets[source]._outlet_widgets[outlet]
        target = self._view._node_widgets[target]._inlet_widgets[inlet]

        self.setLine(makeLineBetweenShapes(source, target))

    def palette(self) -> QPalette:
        if widget := self.parentWidget():
            return widget.palette()

        if scene := self.scene():
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
        ...

    def paint(self, painter: QPainter, option: QStyleOption, widget: QWidget | None = None):
        painter.setPen(QPen(self.palette().text(), 1))
        if QStyle.StateFlag.State_MouseOver in option.state:
            painter.setPen(QPen(self.palette().accent(), 1))
        painter.drawLine(self.line())


def main():
    app = QApplication()

    class Window(QWidget):
        def __init__(self, parent: QWidget | None = None) -> None:
            super().__init__(parent=parent)
            self._model = PyGraphModel()
            self._model.fromData({
                'nodes': [
                    {
                        'name': "two",
                        'func_name': """def two():\n    return 2"""
                    },
                    {
                        'name': "three",
                        'source': """def three():\n    return 3"""
                    },
                    {
                        'name': "mult",
                        'source': """def mult(x, y):\n    return x*y""",
                        'fields': {
                            'x': "->two",
                            'y': "->three"
                        }
                    }
                ]
            })
            self.setupUI()
            self.action_connections = []
            self.bindView()

            self.graphview.layoutNodes()

        def setupUI(self):
            self.graphview = PyGraphView()
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
            self._model.addNode(unique_name)

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

