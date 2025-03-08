from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

class PyNodeWidget(QGraphicsWidget):
    def __init__(self, key:str, parent:QGraphicsItem|None=None):
        super().__init__(parent=parent)

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges, True)

        self.kind_combo = QComboBox()
        self.kind_combo.insertItems(0, ["𝒇", "𝕍", "⅀"])
        self.kind_combo.setFrame(False)
        self.kind_combo.setAutoFillBackground(True)
        self.proxy_combo = QGraphicsProxyWidget()
        self.proxy_combo.setWidget(self.kind_combo)
        self.proxy_combo.setParentItem(self)

        self.expr_edit = QLineEdit()
        self.expr_edit.setFrame(False)
        self.expr_edit.setAutoFillBackground(True)
        self.proxy_expr = QGraphicsProxyWidget()
        self.proxy_expr.setWidget(self.expr_edit)
        self.proxy_expr.setParentItem(self)

        layout = QGraphicsLinearLayout()
        layout.addItem(self.proxy_combo)
        layout.addItem(self.proxy_expr)
        self.setLayout(layout)

    def headerText(self)->str:
        return self._header_text

    def setHeaderText(self, text:str):
        # print("set header text", text)
        self._header_text = text
        self.prepareGeometryChange()
        self.update()

    def paint(self, painter:QPainter, option:QStyleOptionGraphicsItem , widget:QWidget|None=None):
        painter.drawRoundedRect(option.rect, 4, 4)


if __name__ == "__main__":
    app = QApplication()
    view = QGraphicsView()
    scene = QGraphicsScene()
    view.setScene(scene)
    node_widget = PyNodeWidget("key")
    scene.addItem(node_widget)
    view.show()
    app.exec()
