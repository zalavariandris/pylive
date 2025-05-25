from edifice import *
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
import cv2

class FileInput(CustomWidget[QPushButton]):
    def __init__(self, path="", on_change=None, **kwargs):
        super().__init__(**kwargs)
        self._register_props(
            {
                "path": path,
                "on_change": on_change,
            }
        )

    def create_widget(self):
        button = QPushButton("Select File...")
        def on_click():
            file_path, _ = QFileDialog.getOpenFileName(button, "Select a file", self.props["path"])
            if file_path and self.props["on_change"]:
                self.props["on_change"](file_path)
        button.pressed.connect(on_click)
        return button

    def update(self, widget: QPushButton, diff_props: PropsDiff):
        # This function should update the widget
        match diff_props.get("path"):
            case _propold, propnew:
                widget.setText(propnew)

from pylive.qt_components.pan_and_zoom_graphicsview_not_optimized import PanAndZoomGraphicsView
class ImageViewer(CustomWidget[QLabel]):
    def __init__(self, src="", **kwargs):
        super().__init__(**kwargs)
        self._register_props(
            {
                "src": src,
            }
        )

    def create_widget(self):
        view = PanAndZoomGraphicsView()
        scene = QGraphicsScene()
        pixmap = QPixmap(self.props["src"])
        pixmap_item = QGraphicsPixmapItem(pixmap.scaled(400, 300, Qt.AspectRatioMode.KeepAspectRatio))
        scene.addItem(pixmap_item)
        view.setScene(scene)
        self.pixmap_item = pixmap_item
        view.setRenderHint(QPainter.RenderHint.Antialiasing)
        return view

    def update(self, widget: PanAndZoomGraphicsView, diff_props: PropsDiff):
        match diff_props.get("src"):
            case _propold, propnew:
                pixmap = QPixmap(propnew)
                if not pixmap.isNull():
                    self.pixmap_item.setPixmap(pixmap)
                else:
                    print(f"Failed to load image from {propnew}")

from typing import *
from edifice.extra.numpy_image import NumpyArray, NumpyArray_to_QImage, NumpyImage
from edifice.engine import _WidgetTree, _get_widget_children, CommandType
import qimage2ndarray
class NumpyImageViewer(CustomWidget[PanAndZoomGraphicsView]):
    def __init__(self, src:NumpyArray, **kwargs):
        super().__init__(**kwargs)
        self._register_props(
            {
                "src": src,
            }
        )

    def create_widget(self):
        view = PanAndZoomGraphicsView()
        scene = QGraphicsScene()
        pixmap_item = QGraphicsPixmapItem()
        scene.addItem(pixmap_item)
        view.setScene(scene)
        self.pixmap_item = pixmap_item
        pixmap = QPixmap.fromImage(qimage2ndarray.array2qimage(self.props["src"].np_array))
        self.pixmap_item.setPixmap(pixmap)
        view.setRenderHint(QPainter.RenderHint.Antialiasing)

        # scene.addPixmap()
        view.setScene(scene)

        return view

    def update(self, widget: PanAndZoomGraphicsView, diff_props: PropsDiff):
        match diff_props.get("src"):
            case _, new_image:
                img = new_image.np_array
                # print(img)
                qimg = qimage2ndarray.array2qimage( (img*255).astype(np.uint8) )
                pixmap = QPixmap.fromImage(qimg)
                if not pixmap.isNull():
                    self.pixmap_item.setPixmap(pixmap)
                else:
                    print(f"Failed to load image from {propnew}")
                


class SplitView(QtWidgetElement[QSplitter]):
    """
    A layout that splits its children and allows user-resizable panels.

    .. highlights::

        - Underlying Qt Widget: `QSplitter <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QSplitter.html>`_

    .. rubric:: Props

    All **props** from :class:`QtWidgetElement` plus:

    Args:
        orientation:
            Orientation of the splitter: `QtCore.Qt.Horizontal` or `QtCore.Qt.Vertical`.
        sizes:
            Optional list of initial sizes for each widget (in pixels).

    .. rubric:: Usage

    .. code-block:: python

        SplitView(orientation=QtCore.Qt.Horizontal)
    """

    def __init__(
        self,
        orientation: Qt.Orientation = Qt.Orientation.Horizontal,
        sizes: list[int] | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._register_props({
            "orientation": orientation,
            "sizes": sizes,
        })
        self._widget_children: list[QtWidgetElement] = []

    def _initialize(self):
        self.underlying = QSplitter(self.props["orientation"])
        self.underlying.setObjectName(str(id(self)))

    def _qt_update_commands(
        self,
        widget_trees: dict[Element, _WidgetTree],
        diff_props: PropsDiff,
    ):
        if self.underlying is None:
            self._initialize()

        assert self.underlying is not None
        commands = super()._qt_update_commands_super(widget_trees, diff_props, self.underlying)

        children = _get_widget_children(widget_trees, self)

        if children != self._widget_children:
            # Remove existing widgets
            for i in reversed(range(self.underlying.count())):
                widget = self.underlying.widget(i)
                self.underlying.widget(i).setParent(None)
                widget.deleteLater()

            # Add new children
            for child in children:
                assert child.underlying is not None
                self.underlying.addWidget(child.underlying)

            self._widget_children = children

            if self.props["sizes"]:
                commands.append(CommandType(self.underlying.setSizes, self.props["sizes"]))

        return commands

import cv2
import numpy as np
@component
def HelloWorld(self):
    def initializer():
        palette = palette_edifice_light() if theme_is_light() else palette_edifice_dark()
        palette = palette_edifice_dark()
        cast(QApplication, QApplication.instance()).setPalette(palette)
        return palette

    palette = use_memo(initializer)
    filename, set_filename = use_state(r"C:\dev\src\pylive\assets\IMG_0885.JPG")
    exposure, set_exposure = use_state(1)

    def read():
        return cv2.imread(filename).astype(np.float32)/255
    img = use_memo(read, (filename,) )
    try:
        cc = img*exposure
    except Exception:
        cc = np.ones((32,32,3), np.float32)

    def update_exposure(val):
        print("exposure was set to:", val)
        set_exposure(val)

    with Window(title="Color Grade", _size_open=(1024,576), full_screen=False):
        with SplitView(sizes=(500,200)):
            with VBoxView(style={'align': 'center'}):
                FileInput(path=filename, on_change=set_filename)
                NumpyImageViewer(src=NumpyArray(cc))
            with VBoxView(style={'align': 'top'}):
                Label("exposure")
                Slider(
                    value=exposure,
                    min_value=-10,
                    max_value=10,
                    on_change=update_exposure
                )
                Label("temperature")
                Slider(
                    value=50,
                    min_value=0,
                    max_value=100
                )
                Label("tint")
                Slider(
                    value=50,
                    min_value=0,
                    max_value=100
                )
                VBoxView()

if __name__ == "__main__":
    App(HelloWorld()).start()