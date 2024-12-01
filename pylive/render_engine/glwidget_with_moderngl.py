from typing import *
from collections import defaultdict
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from PySide6.QtOpenGL import *
from PySide6.QtOpenGLWidgets import QOpenGLWidget

import moderngl
import glm
import math
import time
import trimesh
import glm # or import pyrr !!!! TODO: checkout pyrr
import numpy as np
from OpenGL import GL as gl

from pylive.render_engine.camera import Camera
from pylive.render_engine.orbit_control import OrbitControl
from pylive.render_engine.render_layers import *


class GLWidget(QOpenGLWidget):
	def __init__(self, parent=None):
		super().__init__(parent=parent)
		self.is_dragging = False

		### Start Animation Loop ###
		self.timer = QTimer()
		self.timer.timeout.connect(self.update)
		self.timer.start(1000//60)
		self._layers = []

	def sizeHint(self) -> QSize:
		return QSize(720, 576)

	def renderLayers(self):
		return self._layers

	def setRenderLayers(self, layers:List[RenderLayer]):
		self._layers = layers

	def initializeGL(self) -> None:
		fmt = QSurfaceFormat()
		fmt.setDepthBufferSize(24);
		fmt.setStencilBufferSize(8);
		fmt.setSwapInterval(1)
		fmt.setMajorVersion(4)
		fmt.setMinorVersion(6)
		self.setFormat(fmt)

		# print the current OpenGL context
		context = self.context()
		if context is not None and context.isValid():
			version = context.format().version()
			print(f"OpenGL Version Used by QOpenGLWindow: {version[0]}.{version[1]}")
		else:
			print("Failed to retrieve OpenGL context.")

		# create the moderngl context
		self.ctx = moderngl.get_context()
		
		# setup render layers
		for layer in self._layers:
			layer.setup(self.ctx)

	def resizeGL(self, w: int, h: int) -> None:
		# setup render layers
		for layer in self._layers:
			layer.resize(self.ctx, w, h)
		return super().resizeGL(w, h)

	def paintGL(self) -> None:
		# use the FBO that is currently bound by QT with moderngl
		fbo_id = self.defaultFramebufferObject() # get framebuffer id this is just for reference
		fbo = self.ctx.detect_framebuffer() 
		fbo.use()

		self.ctx.enable(self.ctx.DEPTH_TEST)		
		self.ctx.clear(0.1, 0.2, 0.3, 1.0)  # Clear screen with a color

		# setup render layers
		self.ctx.clear(0.03, 0.03, 0.1, 1.0)  # Clear screen with a color
		for layer in self._layers:
			layer.render(self.ctx)


if __name__ == "__main__":
	import sys
	import math
	app = QApplication(sys.argv)

	glwidget = GLWidget()
	camera = Camera()
	camera.setPosition(glm.vec3(0, 1.5, 2.5))
	camera.lookAt(glm.vec3(0,0,0), glm.vec3(0.0, 0.0, 1.0))
	orbit_control = OrbitControl(glwidget, camera)

	glwidget.setRenderLayers([
		# TriangleLayer(camera),
		# BoxLayer(camera),
		
		ArrowLayer(camera,
			color=glm.vec4(0,1,0,1),
			model=glm.mat4(1)
		), # Y
		ArrowLayer(camera, 
			model=glm.rotate(90*math.pi/180, glm.vec3(0,0,1)),
			color=glm.vec4(0,0,1,1)
		), # Z
		ArrowLayer(camera, 
			model=glm.rotate(90*math.pi/180, glm.vec3(1,0,0)),
			color=glm.vec4(1,0,0,1)
		), # X
		GridLayer(camera)
	])
	
	glwidget.show()
	sys.exit(app.exec())
