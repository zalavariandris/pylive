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
        if self._param.default is inspect.Parameter.empty and\
            self._param.kind != inspect.Parameter.VAR_POSITIONAL and\
            self._param.kind != inspect.Parameter.VAR_KEYWORD:
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


class NodeWidget(QGraphicsWidget):
    def __init__(self, parent:QGraphicsItem|None= None):
        super().__init__(parent)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)

        layout = QGraphicsLinearLayout(Qt.Orientation.Horizontal)
        layout.setContentsMargins(6,4,10,4)
        self.setLayout(layout)
        palette = self.palette()
        self._pen:QPen = QPen(QBrush(palette.color(QPalette.ColorRole.Text)), 1)
        self._brush:QBrush = Qt.NoBrush

    def setPen(self, pen:QPen):
        self._pen = pen
        self.update()

    def pen(self):
        return self._pen

    def setBrush(self, brush:QBrush):
        self._brush = brush
        self.update()

    def brush(self):
        return self._brush

    def addInlet(self, pin:Pin):
        layout = cast(QGraphicsLinearLayout, self.layout())
        layout.addItem(pin)

    @override
    def paint(self, painter:QPainter, option:QStyleOptionGraphicsItem, widget:QWidget|None=None):
        painter.setPen( self.pen() )
        painter.setBrush( self.brush() )
        w, h = self.geometry().width(), self.geometry().height()
        painter.drawRoundedRect(QRectF(0,0,w,h),5.0,5.0)


class FunctionNodeWidget(NodeWidget):
    def __init__(self, function:Callable[..., object|None], parent:QGraphicsItem|None= None):
        super().__init__(parent)

        self._function:Callable[..., object|None]|None = None
        self.setFunction(function)
        self.setPen(QPen(QBrush("darkgrey"), 1))

    def addParam(self, param:inspect.Parameter):
        inlet = ParamInlet(param)
        super().addInlet(inlet)

    def setFunction(self, function:Callable[..., object|None]):
        layout = cast(QGraphicsLinearLayout, self.layout())
        while layout.count():
            # item=layout.itemAt(0)
            layout.removeAt(0)
            # item.deleteLater()

        # add header
        header = Pin(function.__name__)
        layout = cast(QGraphicsLinearLayout, self.layout())
        layout.addItem(header)

        # add inlets
        sig = inspect.signature(function)
        for name, param in sig.parameters.items():
            self.addParam(param)

        self._function = function

    @override
    def paint(self, painter:QPainter, option:QStyleOptionGraphicsItem, widget:QWidget|None=None):
        super().paint(painter, option, widget)

        if not self._function:
            return

        fm = painter.fontMetrics()
        x = fm.horizontalAdvance(self._function.__name__)
        rect = self.layout().contentsRect()
        painter.drawText(int(rect.x()+x), int(rect.y()+fm.ascent()-1),"(")
        painter.drawText(int(rect.right()),int(rect.y()+fm.ascent()-1),")")


import ast
def get_unbound_nodes(code: str) -> set[str]:
    # Parse the code into an AST
    tree = ast.parse(code)
    
    # Sets to store variable names
    assigned: set[str] = set()
    used: set[str] = set()

    # Function to traverse AST nodes
    names = []
    def visit_node(node: ast.AST):
        names.append(node)
        if isinstance(node, ast.Name):
            print(f"""
                {node.id}: load: {isinstance(node.ctx, ast.Load)}, store: {isinstance(node.ctx, ast.Store)}\
            """)
            print(node)
            # if isinstance(node.ctx, ast.Load):  # This is a variable being used
            #     if node.id not in assigned:
            #         used.add( (node.id, node.col_offset, node.end_col_offset))
            # elif isinstance(node.ctx, ast.Store):  # This is a variable being assigned
            #     assigned.add( (node.id, node.col_offset, node.end_col_offset))
        # Recursively visit all child nodes
        for child in ast.iter_child_nodes(node):
            visit_node(child)

    # Start visiting the nodes
    visit_node(tree)

    # Unbound variables are used variables that are not assigned
    unbound = used - assigned
    
    return unbound

class ExpressionWidget(NodeWidget):
    def __init__(self, expression:str, parent = None):
        super().__init__(parent)

        self._expression:str|None = None
        self.setExpression(expression)
        self.setPen(QPen(QBrush("green"), 1))

    def setExpression(self, expression:str):
        layout = cast(QGraphicsLinearLayout, self.layout())
        while layout.count():
            # item=layout.itemAt(0)
            layout.removeAt(0)
            # item.deleteLater()

        # add header
        if not expression:
            return

        # header = Pin(expression)
        layout = cast(QGraphicsLinearLayout, self.layout())
        # layout.addItem(header)

        # add inlets
        # def split_at_positions(s: str, positions: list[int]) -> list[str]:
        #     # Add the start and end positions to make sure the last part is included
        #     positions = [0] + positions + [len(s)]
        #     parts = [s[positions[i]:positions[i+1]] for i in range(len(positions)-1)]
        #     return parts
        # split_positions:List[int] = []

        unbound_nodes = get_unbound_nodes(expression)
        print([nod for nod in unbound_nodes])

        expression_parts:list[tuple[Literal['text', 'var'], str]] = []
        pos = 0
        for name, col_offset, end_col_offset in unbound_nodes:
            print(pos, col_offset, end_col_offset)
            expression_parts.append( (
                'text',
                expression[pos:col_offset]
            ))

            expression_parts.append( (
                'var',
                expression[col_offset:end_col_offset]
            ))
            pos = end_col_offset
        expression_parts.append( (
            'text',
            expression[pos:]
        ))

        for kind, text in expression_parts:
            match kind:
                case 'text':
                    label = QLabel(text)
                    label.setStyleSheet(f"""
                        border-radius: 25px;
                        color: palette(text);
                        background: transparent;
                    """)

                    label.setSizePolicy(
                        QSizePolicy.Policy.Maximum, 
                        QSizePolicy.Policy.Minimum
                    )

                    proxy = QGraphicsProxyWidget(self)
                    proxy.setWidget(label)
                    layout.addItem(proxy)

                case 'var':
                    header = Pin(text)
                    layout.addItem(header)
        self._expression = expression

### update here ###
scene.clear()

### add nodes for functions
from pathlib import Path
nodes:list[Callable[..., object|None]|str] = [
    print, 
    Path, 
    Path.read_text,
    "[item for item in the_list]",
    lambda x,y: x+y
]
for i, obj in enumerate( nodes ):
    match obj:
        case str():
            print(obj)
            widget = ExpressionWidget(obj)
            widget.setPos(0,i*40)
            scene.addItem(widget)
        case _ if callable(obj):
            widget = FunctionNodeWidget(obj)
            widget.setPos(0,i*40)
            scene.addItem(widget)
        case _:
            raise ValueError(f"{obj} is not supported")


expression = "print(msg)"
view.centerOn( 190, 90)
app.exec()






# %%
