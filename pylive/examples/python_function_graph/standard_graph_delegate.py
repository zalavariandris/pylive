from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from abstract_graph_deletage import AbstractGraphDelegate


from pylive.QtGraphEditor.NetrowkXGraphEditor.link_graphics_items import (
    makeLineBetweenShapes,
)
from pylive.QtGraphEditor.NetrowkXGraphEditor.qgraphics_arrow_item import (
    QGraphicsArrowItem,
)
from graph_model import GraphModel


class StandardNodeWidget(QGraphicsWidget):
    def __init__(self, parent: Optional[QGraphicsItem] = None) -> None:
        QGraphicsWidget.__init__(self, parent=parent)
        self.setGeometry(0, 0, 50, 50)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable, True)

    def paint(self, painter, option: QStyleOptionGraphicsItem, widget=None):
        palette = self.palette()

        pen = QPen(palette.color(QPalette.ColorRole.Text), 1)
        painter.setPen(pen)
        rect = QRectF(0, 0, self.geometry().width(), self.geometry().height())
        # painter.drawEllipse(rect)

        painter.drawRoundedRect(rect, 10, 10)

        if QStyle.StateFlag.State_Selected in option.state:
            pen = QPen(
                palette.color(QPalette.ColorRole.WindowText),
                1,
                Qt.PenStyle.DashLine,
            )
            painter.setPen(pen)
            painter.drawRoundedRect(rect, 1, 1)


class StandardLinkWidget(QGraphicsArrowItem):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        pen = QPen(QColor("white"), 2)
        self.setPen(pen)


class StandardGraphDelegate(AbstractGraphDelegate):
    def createNodeWidget(self, graph: GraphModel, n: Hashable) -> QGraphicsItem:
        """create and bind the widget"""
        widget = StandardNodeWidget()
        # widget.setGeometry(0,0,50,50)
        # palette = widget.palette()
        # palette.setColor(QPalette.ColorRole.Window, palette.color(QPalette.ColorRole.Base))
        # widget.setPalette(palette)
        # widget.setAutoFillBackground(True)

        return widget

    def setNodeWidgetProps(
        self, graph: GraphModel, n: Hashable, widget: QGraphicsWidget, **props
    ):
        ...
        """update iwdget props from model"""
        # if 'label' in props.keys():
        # 	widget.label.document().setPlainText(props['label'])

        # if 'inlets' in props.keys():
        # 	...

        # if 'outlets' in props.keys():
        # 	...

    def setNodeModelProps(
        self, graph: GraphModel, n: Hashable, widget: QGraphicsWidget, **props
    ):
        """update model props from widget"""
        graph.setNodeProperties(n, **props)

    def createEdgeWidget(
        self,
        graph: GraphModel,
        source: QGraphicsWidget,
        target: QGraphicsWidget,
    ) -> QGraphicsArrowItem:
        link = StandardLinkWidget()

        def update_link():
            link.setLine(
                makeLineBetweenShapes(source.geometry(), target.geometry())
            )

        update_link()

        source.geometryChanged.connect(update_link)
        target.geometryChanged.connect(update_link)

        return link

    def setEdgeWidgetProps(
        self,
        graph: GraphModel,
        e: Tuple[Hashable, Hashable],
        widget: QGraphicsArrowItem,
        **props
    ):
        ...

    def setEdgeModelProps(
        self,
        graph: GraphModel,
        e: Tuple[Hashable, Hashable],
        widget: QGraphicsArrowItem,
        **props
    ):
        ...
