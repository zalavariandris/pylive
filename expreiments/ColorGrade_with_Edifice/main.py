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
import PyOpenColorIO as ocio
# 1. Load OCIO config (use built-in config)


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

import qimage2ndarray

from PySide6.QtGui import QPainter, QImage
from PySide6.QtCore import QRectF, QSize
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from OpenGL.GL import *
from PySide6.QtGui import QOpenGLContext

class OpenGLTextureItem(QGraphicsItem):
    def __init__(self, texture_id, texture_size):
        super().__init__()
        self._texture_id = texture_id
        self._texture_size = texture_size

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self._texture_size.width(), self._texture_size.height())
    
    def setTexture(self, texture_id: int, texture_size: QSize):
        """Set the OpenGL texture ID and size."""
        self._texture_id = texture_id
        self._texture_size = texture_size
        self.update()

    def paint(self, painter: QPainter, option, widget=None):
        if not QOpenGLContext.currentContext():
            return

        painter.beginNativePainting()

        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self._texture_id)

        glBegin(GL_QUADS)
        glTexCoord2f(0, 1); glVertex2f(0, 0)
        glTexCoord2f(1, 1); glVertex2f(self._texture_size.width(), 0)
        glTexCoord2f(1, 0); glVertex2f(self._texture_size.width(), self._texture_size.height())
        glTexCoord2f(0, 0); glVertex2f(0, self._texture_size.height())
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
    print("numpy_to_qimage")
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
                qimg = numpy_to_qimage(img)
                pixmap = QPixmap.fromImage(qimg)
                if not pixmap.isNull():
                    self.pixmap_item.setPixmap(pixmap)
                else:
                    print("TODO: Failed to convert numpy array to QImage") #TODO: Handle this case properly
                    print(f"Shape: {img.shape}, Dtype: {img.dtype}")
                


from splitview import SplitView
config = ocio.Config.CreateRaw()
srgb_to_linear_tf = ocio.ColorSpaceTransform(src='sRGB', dst='Linear')
linear_to_srgb_tf = ocio.ColorSpaceTransform(src='Linear', dst='sRGB')

def adjust_exposure(image, exposure_value):
    """
    Adjust exposure. exposure_value > 1 brightens the image,
    exposure_value < 1 darkens the image.
    """
    adjusted = image * (2 ** exposure_value)
    return np.clip(adjusted, 0, 1)  # Keep values in [0, 1] range

import colour

def apply_white_balance_linear(image, temperature=0.0, tint=0.0):
    """
    Apply temperature/tint in linear space using OCIO.
    
    - temperature: float in [-1, 1] (warm/cool)
    - tint: float in [-1, 1] (green/magenta)
    """

    # Convert sRGB → linear using OCIO
    processor_to_linear = config.getProcessor(srgb_to_linear_tf)
    linear = processor_to_linear.applyRGB(image.reshape(-1, 3)).reshape(image.shape)

    # Compute RGB gains based on temperature and tint
    # Temperature affects red/blue; Tint affects green
    r_gain = 1.0 + 0.1 * temperature
    g_gain = 1.0 - 0.1 * tint
    b_gain = 1.0 - 0.1 * temperature

    gains = np.array([r_gain, g_gain, b_gain]).reshape(1, 1, 3)
    balanced = linear * gains

    # Convert linear → sRGB
    processor_to_srgb = config.getProcessor(linear_to_srgb_tf)
    result = processor_to_srgb.applyRGB(balanced.reshape(-1, 3)).reshape(image.shape)

    return np.clip(result, 0, 1)

def adjust_exposure_ocio(image, exposure_value):
    # Normalize image to [0, 1]
    image = image.astype(np.float32) / 255.0

    # Convert sRGB → Linear
    processor_srgb_to_linear = config.getProcessor(srgb_to_linear_tf)
    linear = processor_srgb_to_linear.applyRGB(image.reshape(-1, 3)).reshape(image.shape)

    # Apply exposure in linear space
    linear *= 2 ** exposure_value

    # Convert Linear → sRGB
    processor_linear_to_srgb = config.getProcessor(linear_to_srgb_tf)
    corrected = processor_linear_to_srgb.applyRGB(linear.reshape(-1, 3)).reshape(image.shape)

    return np.clip(corrected, 0, 1)

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

    filename, set_filename = use_state(r"C:\dev\src\pylive\assets\colorchecker-classic_01.png")
    exposure, set_exposure = use_state(0)
    temperature, set_temperature = use_state(50)
    tint, set_tint = use_state(50)

    def read():
        img = cv2.imread(filename).astype(np.float32)/255
        img = cv2.resize(img, (1024, 576), interpolation=cv2.INTER_LINEAR, dst=img)
        return img
    
    img = use_memo(read, (filename,) )

    img = apply_temperature_tint(img, kelvin=temperature, tint_shift=tint/100)
    img = adjust_exposure(img, exposure/100)

    
    # cc = use_memo(lambda: process_color_correction(img, exposure), (img, exposure) )
    with Window(title="Color Grade", _size_open=(1024,576), full_screen=False):
        with SplitView(sizes=(500,200)):
            with VBoxView(style={'align': 'center'}):
                FileInput(path=filename, on_change=set_filename)
                NumpyImage(src=NumpyArray((img*255).astype(np.uint8)))
            with VBoxView(style={'align': 'top'}):
                Label(f"{img.shape} {img.dtype}")
                Label("temperature")
                Slider(
                    value=temperature,
                    min_value=1000,
                    max_value=40000,
                    on_change=set_temperature
                )
                Label("tint")
                Slider(
                    value=tint,
                    min_value=-100,
                    max_value=100,
                    on_change=set_tint
                )
                Label("exposure")
                Slider(
                    value=exposure,
                    min_value=-500,
                    max_value=500,
                    on_change=set_exposure
                )
                VBoxView()

if __name__ == "__main__":
    App(RootComponent()).start()