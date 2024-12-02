from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *
# from PySide6.QtOpenGL import *
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

	def initializeGL(self) -> None:
		# fmt = QSurfaceFormat()
		# fmt.setDepthBufferSize(24);
		# fmt.setStencilBufferSize(8);
		# fmt.setSwapInterval(1)
		# fmt.setMajorVersion(4)
		# fmt.setMinorVersion(6)
		# self.setFormat(fmt)

		# print the current OpenGL context
		context = self.context()
		if context is not None and context.isValid():
			version = context.format().version()
			print(f"OpenGL Version Used by QOpenGLWindow: {version[0]}.{version[1]}")
		else:
			print("Failed to retrieve OpenGL context.")
		
	def resizeGL(self, w: int, h: int) -> None:
		# setup render layers
		ctx = moderngl.get_context()
		ctx.viewport = (0,0,w,h)
		return super().resizeGL(w, h)

	def paintGL(self) -> None:
		VERTEX_SHADER = dedent('''
			#version 330 core

			uniform mat4 view;
			uniform mat4 projection;


			layout(location = 0) in vec3 position;

			void main() {
				gl_Position = projection * view * vec4(position, 1.0);
			}
		''')

		FRAGMENT_SHADER = dedent('''
			#version 330 core

			layout (location = 0) out vec4 out_color;
			uniform vec4 color;
			void main() {
				out_color = color;
			}
		''')

		ctx = moderngl.get_context()
		ctx.gc_mode = 'context_gc' # MODERNGL CAN GARBAGE COLLECT its GLObjects!
		fbo = ctx.detect_framebuffer()
		fbo.use()
		program = ctx.program(VERTEX_SHADER, FRAGMENT_SHADER)
		program['projection'].write(glm.ortho(-1,1,-1,1,0,1))
		program['view'].write(glm.mat4(1))
		program['color'].write(glm.vec4(1.0, 1.0, 0.3, 1.0))

		# triangle
		vertices = np.array([
			[-1,  0, 0],    # Vertex 1
			[ 0, -1, 0],    # Vertex 2
			[+1, +1, 0]   # Vertex 3
		], dtype=np.float32)
		vbo = ctx.buffer(vertices.tobytes())

		vao = ctx.vertex_array(
			program,
			[
				(vbo, '3f', 'position'),
			],	
			mode=moderngl.TRIANGLES
		)

		ctx.clear(1,.3,1,1)
		vao.render()
		ctx.gc()


if __name__ == "__main__":
	import sys
	import math
	app = QApplication(sys.argv)

	glwidget = GLWidget()
	camera = Camera()
	camera.setPosition(glm.vec3(0, 1.5, 2.5))
	camera.lookAt(glm.vec3(0,0,0), glm.vec3(0.0, 0.0, 1.0))
	orbit_control = OrbitControl(glwidget, camera)
	
	glwidget.show()
	sys.exit(app.exec())
