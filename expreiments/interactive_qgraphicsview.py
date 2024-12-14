# run python file in interactive window

# %% open window
%gui qt
from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
app = QApplication.instance() or QApplication()

view = QGraphicsView()
scene = QGraphicsScene()
view.setScene(scene)
scene.setSceneRect(-4500, -4500, 9000, 9000)
view.show()

# %%
scene.clear()
rect_item = QGraphicsRectItem()
rect_item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
rect_item.setBrush(QBrush("yellow"))
rect_item.setPen(QPen(QBrush("magenta"), 3))
rect_item.setRect(-30,-30,100,100)


scene.addItem(rect_item)

circle_item = QGraphicsEllipseItem(0,0,50,50)
circle_item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
circle_item.setBrush(QBrush("orange"))
circle_item.setPen(QPen(QBrush("blue"), 8))
circle_item.setRect(-30,-30,100,100)

scene.addItem(circle_item)

# app.exec()

# %%
