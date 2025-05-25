from edifice import *
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
import cv2
from typing import *
import time
from functools import wraps
import numpy as np
import numpy.typing as npt

from PySide6.QtOpenGLWidgets import *

def timeit(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()  # more precise than time.time()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        print(f"Function '{func.__name__}' executed in {execution_time:.4f} seconds")
        return result
    return wrapper

T_My_Numpy_Array_co = TypeVar("T_My_Numpy_Array_co", bound=np.generic, covariant=True)

class MyNumpyArray(Generic[T_My_Numpy_Array_co]):
    """Wrapper for one `numpy.ndarray <https://numpy.org/doc/stable/reference/generated/numpy.ndarray.html>`_.

    This wrapper class provides the :code:`__eq__` relation for the wrapped
    :code:`numpy` array such that if two wrapped arrays are :code:`__eq__`,
    then one can be substituted for the other. This class may be used as a
    **prop** or a **state**.

    Args:
        np_array:
            A `numpy.ndarray <https://numpy.org/doc/stable/reference/generated/numpy.ndarray.html>`_.

    """

    np_array: npt.NDArray[T_My_Numpy_Array_co]

    def __init__(self, np_array: npt.NDArray[T_My_Numpy_Array_co]) -> None:
        super().__init__()
        self.dtype = np_array.dtype
        self.np_array = np_array

    def __eq__(self, other: Self) -> bool: # type: ignore  # noqa: PGH003
        return False
        return self.np_array is other.np_array
        return np.array_equal(self.np_array, other.np_array, equal_nan=True)

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


from typing import *
from edifice.extra.numpy_image import NumpyArray, NumpyArray_to_QImage, NumpyImage
from edifice.engine import _WidgetTree, _get_widget_children, CommandType
import qimage2ndarray

from PySide6.QtGui import QPainter, QImage
from PySide6.QtCore import QRectF, QSize
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from OpenGL.GL import *
from PySide6.QtGui import QOpenGLContext

class OpenGLTextureItem(QGraphicsItem):
    def __init__(self, texture_id, texture_size):
        super().__init__()
        self.texture_id = texture_id
        self.texture_size = texture_size

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self.texture_size.width(), self.texture_size.height())

    def paint(self, painter: QPainter, option, widget=None):
        if not QOpenGLContext.currentContext():
            return

        painter.beginNativePainting()

        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)

        glBegin(GL_QUADS)
        glTexCoord2f(0, 1); glVertex2f(0, 0)
        glTexCoord2f(1, 1); glVertex2f(self.texture_size.width(), 0)
        glTexCoord2f(1, 0); glVertex2f(self.texture_size.width(), self.texture_size.height())
        glTexCoord2f(0, 0); glVertex2f(0, self.texture_size.height())
        glEnd()

        glBindTexture(GL_TEXTURE_2D, 0)
        glDisable(GL_TEXTURE_2D)

        painter.endNativePainting()


def create_opengl_texture_from_image(image: QImage) -> (int, QSize):
    image = image.convertToFormat(QImage.Format_RGBA8888)
    width, height = image.width(), image.height()
    data = image.bits().asstring(image.sizeInBytes())

    texture_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture_id)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

    glTexImage2D(
        GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0,
        GL_RGBA, GL_UNSIGNED_BYTE, data
    )

    glBindTexture(GL_TEXTURE_2D, 0)
    return texture_id, QSize(width, height)


def numpy_to_qimage(image: np.ndarray) -> QImage:
    if image.dtype == np.float32 or image.dtype == np.float64:
        image = cv2.normalize(image, None, 0, 255, cv2.NORM_INF, cv2.CV_8U)
        # Normalize to [0, 255] and convert to uint8
        # image = np.clip(image, 0, 1)  # Assuming input is in [0, 1] range
        # image = (image * 255).astype(np.uint8)

    if image.ndim == 2:
        height, width = image.shape
        return QImage(image.data, width, height, width, QImage.Format_Grayscale8)
    elif image.ndim == 3:
        height, width, channels = image.shape
        if channels == 3:
            return QImage(image.data, width, height, width * 3, QImage.Format_RGB888)
        elif channels == 4:
            return QImage(image.data, width, height, width * 4, QImage.Format_RGBA8888)
    raise ValueError("Unsupported image shape")

def numpy_to_qimage_fast(image: np.ndarray) -> QImage:
    # if not img.flags['C_CONTIGUOUS']:
    #     img = np.ascontiguousarray(image)

    if image.dtype == np.float32 or image.dtype == np.float64:
        # image = cv2.normalize(image, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
        # print(image)
        image = np.clip(image, 0, 1)  # Ensure values are in [0, 255]
        # image = (image * 255).astype(np.uint8)  # Convert to float32
        pass

    # image = np.ascontiguousarray(image)
    assert image.dtype == np.uint8
    print("numpy_to_qimage_fast")
    if image.ndim == 2:
        h, w = image.shape
        return QImage(image.data, w, h, w, QImage.Format_Grayscale8)
    elif image.ndim == 3:
        h, w, ch = image.shape
        if ch == 3:
            return QImage(image.data, w, h, w * 3, QImage.Format_RGB888)
        elif ch == 4:
            return QImage(image.data, w, h, w * 4, QImage.Format_RGBA8888)
    
    raise ValueError("Unsupported shape or dtype")


class NumpyImageViewer(CustomWidget[PanAndZoomGraphicsView]):
    def __init__(self, src:MyNumpyArray, **kwargs):
        super().__init__(**kwargs)
        self._register_props(
            {
                "src": src,
            }
        )

    def create_widget(self):
        view = PanAndZoomGraphicsView()
        view.setViewport(QOpenGLWidget() )
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
                qimg = numpy_to_qimage_fast(img)
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
def RootComponent(self):
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
    def process_color_correction(img):
        try:
            cc = img*exposure
        except Exception:   
            cc = np.ones((32,32,3), np.float32)
        return cc
    cc = use_memo(lambda: process_color_correction(img), (img, exposure) )


    with Window(title="Color Grade", _size_open=(1024,576), full_screen=False):
        with SplitView(sizes=(500,200)):
            with VBoxView(style={'align': 'center'}):
                FileInput(path=filename, on_change=set_filename)
                NumpyImageViewer(src=MyNumpyArray(cc))
            with VBoxView(style={'align': 'top'}):
                Label(f"{cc.shape} {cc.dtype}")
                Label("exposure")
                Slider(
                    value=exposure,
                    min_value=-100,
                    max_value=100,
                    on_change=set_exposure
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
    App(RootComponent()).start()