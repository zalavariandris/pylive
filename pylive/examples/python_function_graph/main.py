from ast import Call
from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from graph_model import GraphModel
from pylive.QtGraphEditor.NetrowkXGraphEditor.link_graphics_items import (
    makeLineBetweenShapes,
)
from pylive.QtGraphEditor.NetrowkXGraphEditor.qgraphics_arrow_item import (
    QGraphicsArrowItem,
)

from graph_view import GraphView, NodeDelegate

from pylive.utils.unique import make_unique_name

from function_widget import FunctionNodeWidget


class FnGraphDelegate(NodeDelegate):
    def _header_text(self, graph: GraphModel, n: Hashable):
        fn = graph.getNodeProperty(n, "fn")
        return f"{n}-{fn.__name__}"

    @override
    def sizeHint(
        self, option: QStyleOptionViewItem, graph: GraphModel, n: Hashable
    ) -> QSizeF:
        padding = 8
        fm = QFontMetrics(option.font)
        text_width = fm.horizontalAdvance(self._header_text(graph, n))
        return QSizeF(
            padding + text_width + padding, padding + fm.ascent() + padding
        )

    @override
    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionViewItem,
        graph: GraphModel,
        n: Hashable,
    ):
        padding = 8
        # draw outline
        painter.drawRoundedRect(option.rect, 4, 4)

        # draw header text
        fm = option.fontMetrics
        y = option.rect.height() - padding

        # draw node text
        painter.drawText(padding, y, self._header_text(graph, n))

        # painter.drawLine(0, y, option.rect.width(), y) # draw baseline


class FnGraphView(GraphView):
    def __init__(
        self, functions: List[Callable], parent: QWidget | None = None
    ):
        super().__init__(parent=parent)
        self._delegate = FnGraphDelegate()
        self.functions = functions

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        ...

    def contextMenuEvent(self, event: QContextMenuEvent):
        viewpos = self.mapFromGlobal(event.globalPos())
        scenepos = self.mapToScene(viewpos)

        def add_node(fn: Callable):
            if graphmodel := self.model():
                unique_node_name = make_unique_name(
                    fn.__name__, [n for n in graphmodel.nodes()]
                )
                graphmodel.addNode(unique_node_name, fn=fn)

        graphmodel = self.model()
        if graphmodel:
            add_menu: QMenu = QMenu("add")

            for fn in self.functions:
                action = QAction(self)

                action.setText(fn.__name__)
                action.triggered.connect(lambda checked, fn=fn: add_node(fn))
                add_menu.addAction(action)

            add_menu.exec(event.globalPos())


if __name__ == "__main__":
    app = QApplication()
    graph_model = GraphModel()
    from pathlib import Path

    cwd = Path.cwd()
    cwd.glob("*")

    graph_view = FnGraphView(
        [len, print, Path.cwd, Path.iterdir, Path.read_text]
    )
    graph_view.setModel(graph_model)
    graph_view.show()
    app.exec()
