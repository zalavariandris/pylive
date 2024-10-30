from pylive.utils import getWidgetByName
import numpy as np
def random_image(width=8, height=8):
	img = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
	# Convert to QImage
	return QImage(img.data, width, height, 3 * width, QImage.Format_RGB888)

app_widget = getWidgetByName("PREVIEW_WINDOW_ID")
app_widget.display( random_image(128, 128) )

from PySide6.QtOpenGLWidgets import QOpenGLWidget
class Viewport3D(QOpenGLWidget):
	def __init__(self, parent=None):
		super().__init__(parent=parent)
		
	def initializeGL(self):
		print('gl initial')
		
	def cleanUpGl(self):
		pass
		
	def resizeGL(self, width: int, height: int):
		pass
		
	def paintGL(self):
		pass
		
glwidget = Viewport3D()
app_widget.display(glwidget)
print("hello")