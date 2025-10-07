from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *
# from PySide6.QtOpenGL import *
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtOpenGL import *
from OpenGL.GL import *
import moderngl
import glm
import numpy as np
from textwrap import dedent


class GLCanvasWidget(QOpenGLWidget):
	painting = Signal()
	def __init__(self, parent=None):
		super().__init__(parent=parent)
		self.setWindowTitle("GLCanvasWidget with moderngl")
		self.setUpdateBehavior(QOpenGLWidget.UpdateBehavior.PartialUpdate)
		self.setAttribute(Qt.WA_OpaquePaintEvent, False) # see docs: https://doc.qt.io/qt-6/qt.html#WidgetAttribute-enum

		fmt = QSurfaceFormat()
		fmt.setDepthBufferSize(24)
		fmt.setStencilBufferSize(8)
		fmt.setSwapInterval(1)
		fmt.setMajorVersion(4)
		fmt.setMinorVersion(6)
		self.setFormat(fmt)

	@override
	def sizeHint(self) -> QSize:
		return QSize(720, 576)

	@override
	def initializeGL(self) -> None:
		# print the current OpenGL context
		context = self.context()
		if context is not None and context.isValid():
			version = context.format().version()
			print(f"OpenGL Version Used by QOpenGLWindow: {version[0]}.{version[1]}")
		else:
			print("Failed to retrieve OpenGL context.")
		
	@override
	def resizeGL(self, w: int, h: int) -> None:
		...

	@override
	def paintGL(self) -> None:
		...

	@override
	def paintEvent(self, e):
		# print("paint event")
		self.makeCurrent() # make the widget's opengl context active

		# Emit will call all connected slots within the current opengl context!
		self.painting.emit()

		# deactivate the window's opengl context 
		self.doneCurrent()


if __name__ == "__main__":
	import sys
	### create the app ###
	app = QApplication(sys.argv)

	### create the canvas ###
	glcanvas = GLCanvasWidget()
	glcanvas.show()

	### define render function ###
	from pylive.render_engine.utils import draw_triangle_with_moderngl
	ctx = None
	def paint():
		import time
		# QOpenGLWidget uses an internal FBO for drawing, use that with moderngl
		global ctx
		start_time = time.perf_counter_ns()
		if not ctx:
			ctx = moderngl.get_context()
			ctx.gc_mode = 'context_gc'
			print(time.perf_counter_ns()-start_time)
		fbo = ctx.detect_framebuffer()
		fbo.use()
		import math
		import time
		ctx.clear(0.5,.1,0.5,1)
		draw_triangle_with_moderngl(ctx, size=math.cos(time.time()))
		ctx.gc()
		
		# connect continously, and request update
		glcanvas.painting.connect(paint, Qt.ConnectionType.SingleShotConnection)
		glcanvas.update() #request repaint continously

	### set render function ###
	glcanvas.painting.connect(paint, Qt.ConnectionType.SingleShotConnection)

	
	# run app
	sys.exit(app.exec())
