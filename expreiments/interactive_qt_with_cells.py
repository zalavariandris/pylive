# run python file in interactive window

# %% open window
# %gui qt
from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
app = QApplication.instance() or QApplication()

view = QGraphicsView()
scene = QGraphicsScene()
view.setScene(scene)
view.show()

# %%
import ast
def parse_expression(expression:str):
    ...

import inspect

def format_type(annotation):
    """Helper function to format type annotations as readable strings."""

    print(annotation, annotation == inspect.Parameter.empty)
    if annotation == inspect.Parameter.empty:
        return ""

    if hasattr(annotation, '__name__'):  # For built-in types like int, float
        return annotation.__name__
    elif hasattr(annotation, '__origin__'):  # For generic types like List, Dict
        origin = annotation.__origin__
        args = ", ".join(format_type(arg) for arg in annotation.__args__) if annotation.__args__ else ""
        return f"{origin.__name__}[{args}]" if args else origin.__name__
    else:
        return str(annotation)  # Fallback for unusual cases

class ParamInlet(QGraphicsProxyWidget):
    def __init__(self, param:inspect.Parameter, parent=None):
        super().__init__(parent=parent)
        self._param = param

        label = QLabel("<function>")
        label.setStyleSheet(f"""
            border-radius: 25px;
            color: {self.color()};
        """)

        label.setSizePolicy(
            QSizePolicy.Policy.Maximum, 
            QSizePolicy.Policy.Minimum
        )

        self.setWidget(label)
        
        label.setText( "".join([
            self.text(), 
            self.annotation(), 
            f"={self.default()}" if self.default() else ""
        ]))

    def color(self)->str:
        if self._param.default is inspect.Parameter.empty:
            return "red"

        return "palette(text)"

    def text(self)->str:
        param = self._param
        text = param.name
        if param.kind == inspect.Parameter.VAR_POSITIONAL:
            text = "*" + text
        if param.kind == inspect.Parameter.VAR_KEYWORD:
            text = "**" + text
        return text
        
    def annotation(self)->str:
        return format_type(self._param.annotation)


    def default(self):
        if self._param.default == inspect.Parameter.empty:
            return ""
        return f"{repr(self._param.default)}"


class FunctionNodeWidget(QGraphicsWidget):
    def __init__(self, function:Callable, parent = None):
        super().__init__(parent)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)

        layout = QGraphicsLinearLayout(Qt.Orientation.Horizontal)
        self.setLayout(layout)

        self.setFunction(function)

    def addInlet(self, param:inspect.Parameter):
        inlet = ParamInlet(param)

        layout = cast(QGraphicsLinearLayout, self.layout())
        layout.addItem(inlet)

    def setFunction(self, function:Callable):
        layout = cast(QGraphicsLinearLayout, self.layout())
        while layout.count():
            item=layout.itemAt(0)
            layout.removeAt(0)
            item.deleteLater()

        # add header
        label = QLabel(function.__name__)
        label.setStyleSheet(f"""
            color: palette(text);
        """)

        label.setSizePolicy(
            QSizePolicy.Policy.Maximum, 
            QSizePolicy.Policy.Minimum
        )
        proxy = QGraphicsProxyWidget(self)
        proxy.setWidget(label)
        layout = cast(QGraphicsLinearLayout, self.layout())
        layout.addItem(proxy)

        # add inlets
        sig = inspect.signature(function)
        for name, param in sig.parameters.items():
            self.addInlet(param)

        self._function = function

    def paint(self, painter, option, widget=None):
        w, h = self.geometry().width(), self.geometry().height()

        painter.drawRoundedRect(0,0,w,h,5,5)


scene.clear()
widget = FunctionNodeWidget(print)
scene.addItem(widget)
expression = "print(msg)"

app.exec()

# %%
