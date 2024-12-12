# run python file in interactive window

# %% open window
%gui qt
from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
app = QApplication.instance()

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
	if hasattr(annotation, '__name__'):  # For built-in types like int, float
		return annotation.__name__
	elif hasattr(annotation, '__origin__'):  # For generic types like List, Dict
		origin = annotation.__origin__
		args = ", ".join(format_type(arg) for arg in annotation.__args__) if annotation.__args__ else ""
		return f"{origin.__name__}[{args}]" if args else origin.__name__
	else:
		return str(annotation)  # Fallback for unusual cases

def format_param(param)->str:
	text = ""
	if param.kind == inspect.Parameter.VAR_POSITIONAL:
		text += "*"
	if param.kind == inspect.Parameter.VAR_KEYWORD:
		text += "**"
	text += f"{param.name}"
	
	# Add type annotation if available
	if param.annotation is not inspect.Parameter.empty:
		text += f":{format_type(param.annotation)}"
	
	# Add default value if available
	if param.default is not inspect.Parameter.empty:
		text += f"={repr(param.default)}"
	
	return text

def format_signature(fn:Callable):
	# Get the signature of the function
	sig = inspect.signature(fn)

	# Build the formatted signature text
	text = f"{fn.__name__}"
	text+="("
	text+=", ".join( [format_param(param) for param in sig.parameters.values()] )
	text+=")"
	
	# Output the return type annotation if present
	if sig.return_annotation is not inspect.Signature.empty:
		text += f"-> {format_type(sig.return_annotation)}"
	
	return text

class FunctionNodeWidget(QGraphicsWidget):
    def __init__(self, function:str, parent = None):
        super().__init__(parent)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)

        layout = QGraphicsLinearLayout(Qt.Orientation.Vertical)
        self.setLayout(layout)

        self._function = ""
        self.setExpression(function)

    def setExpression(self, function:str):
        layout = cast(QGraphicsLinearLayout, self.layout())
        while layout.count():
            item=layout.itemAt(0)
            layout.removeAt(0)
            item.deleteLater()

        sig = inspect.signature(function)

        def addLabel(text, color='orange'):
            label = QLabel("<function>")
            label.setStyleSheet(f"""
                border-radius: 25px;
                background: {color};
            """)
            label.setSizePolicy(
                QSizePolicy.Policy.Maximum, 
                QSizePolicy.Policy.Minimum
            )

            proxy = QGraphicsProxyWidget(self)
            proxy.setWidget(label)
            layout.addItem(proxy)
            label.setText(text)

        # add labels
        addLabel(function.__name__, 'orange')

        for name, param in sig.parameters.items():
            text = ""
            color = "grey"
            if param.kind == inspect.Parameter.VAR_POSITIONAL:
                text += "*"
            if param.kind == inspect.Parameter.VAR_KEYWORD:
                text += "**"
            text+=param.name
            
            # Add type annotation if available
            if param.annotation is not inspect.Parameter.empty:
                text += f":{format_type(param.annotation)}"
            
            # Add default value if available
            if param.default is not inspect.Parameter.empty:
                text += f"={repr(param.default)}"
                color='darkblue'
            else:
                color='red'

            addLabel(text, color)

        self._function = function

    def paint(self, painter, option, widget=None):
        w, h = self.geometry().width(), self.geometry().height()

        painter.drawRoundedRect(0,0,w,h,5,5)

def add_function_node(fn):
    widget = FunctionNodeWidget(fn)
    scene.addItem(widget)

scene.clear()
add_function_node(format_signature)
add_function_node(print)
expression = "print(msg)"

# %%
