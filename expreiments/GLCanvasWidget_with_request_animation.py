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
	def __init__(self, parent=None):
		super().__init__(parent=parent)
		self.setWindowTitle("GLCanvasWidget with moderngl")
		self.setUpdateBehavior(QOpenGLWidget.UpdateBehavior.PartialUpdate)
		self.setAttribute(Qt.WA_OpaquePaintEvent, False) # see docs: https://doc.qt.io/qt-6/qt.html#WidgetAttribute-enum

		fmt = QSurfaceFormat()
		fmt.setDepthBufferSize(24);
		fmt.setStencilBufferSize(8);
		fmt.setSwapInterval(1)
		fmt.setMajorVersion(4)
		fmt.setMinorVersion(6)
		self.setFormat(fmt)


		self._ctx = None
		self._animation_handlers = []

	def getContext(self)->moderngl.Context:
		if not self._ctx:
			raise RuntimeError("Context has not been initalized yet!")
		return self._ctx

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

		self._ctx = moderngl.get_context()
		
	@override
	def resizeGL(self, w: int, h: int) -> None:
		...
		assert self._ctx
		# setup render layers
		# ctx = moderngl.get_context()
		self._ctx.viewport = (0,0,w,h)
		# self.update()
		# return super().resizeGL(w, h)

	@override
	def paintGL(self) -> None:
		...

	@override
	def paintEvent(self, e):
		# print("paint event")
		self.handleAnimationRequests()

	def handleAnimationRequests(self):
		handlers = [handler for handler in self._animation_handlers]
		self._animation_handlers.clear()
		for handler in handlers:
			handler()

	def requestAnimationFrame(self, callback):
		assert self._ctx
		self._animation_handlers.append(callback)
		self.update()
		
	def paint(self, render_function):
		assert self._ctx
		"""sets up the opengl context for painting,
		then calls the render function"""
		self.makeCurrent()
		self._ctx.gc_mode = 'context_gc' # MODERNGL CAN GARBAGE COLLECT its GLObjects!
		fbo = self._ctx.detect_framebuffer()
		fbo.use()
		render_function(self._ctx)
		
		self._ctx.gc()
		self.doneCurrent()

if __name__ == "__main__":
	import sys
	
	format = QSurfaceFormat()
	format.setVersion(3, 3)  # OpenGL 3.3
	format.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)  # Use Core Profile
	format.setOption(QSurfaceFormat.FormatOption.DebugContext)  # Enable debugging for OpenGL (optional)
	QSurfaceFormat.setDefaultFormat(format)  # Set this format as default
	
	app = QApplication(sys.argv)

	glcanvas = GLCanvasWidget()
	glcanvas.show()
	# ctx = moderngl.get_context()

	from pylive.render_engine.utils import draw_triangle_with_moderngl
	def render(ctx):
		import math
		import time
		ctx.clear(0.5,.1,0.5,1)
		draw_triangle_with_moderngl(ctx, size=math.cos(time.time()))

	def animate():
		glcanvas.paint(lambda ctx: render(ctx))
		glcanvas.requestAnimationFrame(animate)

	glcanvas.requestAnimationFrame(animate)

	sys.exit(app.exec())
