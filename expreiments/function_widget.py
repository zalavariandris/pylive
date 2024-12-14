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
scene.setSceneRect(-4500, -4500, 9000, 9000)
view.show()

# %%
import ast
def parse_expression(expression:str):
    ...


class Pin(QGraphicsProxyWidget):
    hoverEntered:Signal = Signal()
    hoverLeft:Signal = Signal()
    connectionInitiated:Signal = Signal()

    def __init__(self, text:str, parent=None):
        super().__init__(parent=parent)
        self._text = text

        label = QLabel("<function>")
        label.setStyleSheet(f"""
            border-radius: 25px;
            color: {self.color()};
            background: transparent;
        """)
        # label.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # label.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)


        label.setSizePolicy(
            QSizePolicy.Policy.Maximum, 
            QSizePolicy.Policy.Minimum
        )

        self.setWidget(label)
        
        self._label = label
        self.setText( self.text() )

    def setText(self, text:str):
        self._label.setText(text)

    def text(self):
        return self._label.text()

    def highlight(self):
        label = cast(QLabel, self.widget())
        label.setStyleSheet(f"""
            border-radius: 25px;
            color: orange;
            background: transparent;
        """)

    def unhighlight(self):
        label = cast(QLabel, self.widget())
        label.setStyleSheet(f"""
            border-radius: 25px;
            color: {self.color()};
            background: transparent;
        """)

    def color(self)->str:
        return "palette(text)"

    def text(self)->str:
        return self._text

    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        self.hoverEntered.emit()
        self.highlight()
        return super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        self.hoverLeft.emit()
        self.unhighlight()
        return super().hoverLeaveEvent(event)


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

class ParamInlet(Pin):
    hoverEntered:Signal = Signal()
    hoverLeft:Signal = Signal()
    connectionInitiated:Signal = Signal()

    def __init__(self, param:inspect.Parameter, parent=None):
        self._param = param
        super().__init__(text=self.text(), parent=parent)        

    @override
    def color(self)->str:
        if self._param.default is inspect.Parameter.empty:
            return "red"

        return "palette(text)"

    @override
    def text(self)->str:
        param = self._param
        text = param.name
        if param.kind == inspect.Parameter.VAR_POSITIONAL:
            text = "*" + text
        if param.kind == inspect.Parameter.VAR_KEYWORD:
            text = "**" + text

        return "".join([
            text, 
            self.annotation(), 
            f"={self.default()}" if self.default() else ""
        ])
        
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
        layout.setContentsMargins(6,4,10,4)
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
        header = Pin(function.__name__)

        layout = cast(QGraphicsLinearLayout, self.layout())
        layout.addItem(header)

        # add inlets
        sig = inspect.signature(function)
        for name, param in sig.parameters.items():
            self.addInlet(param)

        self._function = function

    def paint(self, painter, option, widget=None):
        w, h = self.geometry().width(), self.geometry().height()
        painter.drawRoundedRect(QRectF(0,0,w,h),5.0,5.0)

        fm = painter.fontMetrics()
        x = fm.horizontalAdvance(self._function.__name__)
        rect = self.layout().contentsRect()
        painter.drawText(rect.x()+x, rect.y()+fm.ascent()-1,"(")
        painter.drawText(rect.right(),rect.y()+fm.ascent()-1,")")


scene.clear()

from pathlib import Path
for i, fn in enumerate( [print, Path] ):
    widget = FunctionNodeWidget(fn)
    widget.setPos(0,i*40)
    scene.addItem(widget)
expression = "print(msg)"
view.centerOn( 190, 90)
app.exec()

# %%
