from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from typing import *
from pylive.utils import getWidgetByName
window = cast(QLabel, getWidgetByName("PREVIEW_WINDOW_ID"))
import numpy as np

# prin text to the widget by simply use the built in print.
# the snadard out i redirected to the preview widget
print("you can simply print to this widget")

# Create a random image with shape (height, width, channels)
def random_image():
	height, width = 256, 256  # You can adjust the size
	img = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)

	# Convert to QImage
	return QImage(img.data, width, height, 3 * width, QImage.Format_RGB888)

pix = QPixmap()
pix.convertFromImage(random_image())
window.display(pix)

class MyWidget(QLabel):
	def __init__(self, parent=None):
		super().__init__(parent=parent)
		self.setText("This is my custom Widget")


window.display(MyWidget())
