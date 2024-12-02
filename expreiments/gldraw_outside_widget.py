from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *
# from PySide6.QtOpenGL import *
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtOpenGL import *
import moderngl
import glm
import numpy as np
from textwrap import dedent

def draw_triangle(ctx):
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

class GLWidget(QOpenGLWidget):
	def __init__(self, parent=None):
		super().__init__(parent=parent)
		self.is_dragging = False

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

		self.ctx = moderngl.create_context()
		
	def resizeGL(self, w: int, h: int) -> None:
		# setup render layers
		# ctx = moderngl.get_context()
		self.ctx.viewport = (0,0,w,h)
		self.update()
		# return super().resizeGL(w, h)

	def paintGL(self) -> None:
		print("painGL")

	def paintTriangle(self):
		self.makeCurrent()
		fbo_handle = self.defaultFramebufferObject()
		fbo = self.ctx.detect_framebuffer()
		self.ctx.gc_mode = 'context_gc' # MODERNGL CAN GARBAGE COLLECT its GLObjects!
		# self.ctx.framebuffer_from_external(1)
		fbo.use()
		fbo.clear()
		print(fbo.glo)
		draw_triangle(self.ctx)
		self.ctx.gc()
		self.doneCurrent()
		self.update()


if __name__ == "__main__":
	import sys
	import math
	app = QApplication(sys.argv)

	glwidget = GLWidget()
	glwidget.show()
	glwidget.paintTriangle()

	sys.exit(app.exec())
