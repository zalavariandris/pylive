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

from camera import Camera
from orbit_control import OrbitControl


class GLWidget(QOpenGLWidget):
	def __init__(self, parent=None):
		super().__init__(parent=parent)
		self.is_dragging = False

		### Start Animation Loop ###
		self.timer = QTimer()
		self.timer.timeout.connect(self.update)
		self.timer.start(1000//60)

	def sizeHint(self) -> QSize:
		return QSize(720, 576)

	def on_init(self, ctx:moderngl.Context):
		...

	def on_resize(self, ctx:moderngl.Context, w, h):
		...

	def on_render(self, ctx:moderngl.Context):
		...

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
		
		self.on_init(self.ctx)

	def resizeGL(self, w: int, h: int) -> None:
		self.on_resize(self.ctx, w, h)
		return super().resizeGL(w, h)

	def paintGL(self) -> None:
		# use the FBO that is currently bound by QT with moderngl
		fbo_id = self.defaultFramebufferObject() # get framebuffer id this is just for reference
		fbo = self.ctx.detect_framebuffer() 
		fbo.use()        
		
		self.ctx.clear(0.1, 0.2, 0.3, 1.0)  # Clear screen with a color

		self.on_render(self.ctx)
		

from textwrap import dedent
class RenderLayer:
	FLAT_VERTEX_SHADER = dedent('''
		#version 330 core

		uniform mat4 view;
		uniform mat4 projection;

		layout(location = 0) in vec3 position;

		void main() {
			gl_Position = projection * view * vec4(position, 1.0);
		}
	''')

	FLAT_FRAGMENT_SHADER = dedent('''
		#version 330 core

		layout (location = 0) out vec4 out_color;

		void main() {
			out_color = vec4(1.0, 1.0, 1.0, 1.0);
		}
	''')

	def setup(self, ctx):
		...

	def resize(self, ctx, w, h):
		...

	def render(self, ctx, camera):
		...

class BoxLayer(RenderLayer):
	@override
	def setup(self, ctx):
		# Setup shaders
		self.program = ctx.program(
			vertex_shader=self.FLAT_VERTEX_SHADER,
			fragment_shader=self.FLAT_FRAGMENT_SHADER
		)

		# Trimesh Cube
		box = trimesh.creation.box(extents=(1, 1, 1))

		vertices = box.vertices.flatten().astype(np.float32)
		indices = box.faces.flatten().astype(np.uint32)
		vbo = ctx.buffer(vertices)
		ibo = ctx.buffer(indices)

		self.vao = ctx.vertex_array(
			self.program,
			[
				(vbo, '3f', 'position'),
			],
			mode=moderngl.POINTS,
			index_buffer=ibo
		)

	def render(self, ctx, camera):
		# self.ctx.enable(self.ctx.DEPTH_TEST)
		self.program['view'].write(camera.viewMatrix())
		self.program['projection'].write(camera.projectionMatrix())
		
		self.vao.render()

class TriangleLayer(RenderLayer):
	@override
	def setup(self, ctx):
		self.program = ctx.program(
			vertex_shader=self.FLAT_VERTEX_SHADER,
			fragment_shader=self.FLAT_FRAGMENT_SHADER
		)

		# triangle
		vertices = np.array([
			 0.0, 0.0,  0.4,   # Vertex 1
			-0.4, 0.0, -0.3,   # Vertex 2
			 0.4, 0.0, -0.3    # Vertex 3
		], dtype=np.float32)

		vbo = ctx.buffer(vertices.tobytes())

		self.vao = ctx.vertex_array(
			self.program,
			[
				(vbo, '3f', 'position'),
			],
			mode=moderngl.TRIANGLES
		)

	@override
	def render(self, ctx, camera):
		# self.ctx.enable(self.ctx.DEPTH_TEST)
		self.program['view'].write(camera.viewMatrix())
		self.program['projection'].write(camera.projectionMatrix())
		self.vao.render()


if __name__ == "__main__":
	import sys
	app = QApplication(sys.argv)

	window = QWidget()
	mainLayout = QVBoxLayout()
	window.setLayout(mainLayout)

	glwidget = GLWidget()
	camera = Camera()
	camera.setPosition(glm.vec3(0, 1.5, 2.5))
	camera.lookAt(glm.vec3(0,0,0), glm.vec3(0.0, 0.0, 1.0))

	orbit_control = OrbitControl(glwidget, camera)
	triangle = TriangleLayer()
	box = BoxLayer()
	
	def init(ctx):
		triangle.setup(ctx)
		box.setup(ctx)

	def resize(ctx, w, h):
		triangle.resize(ctx, w, h)
		box.resize(ctx, w, h)
	
	def render(ctx):
		ctx.clear(0.03, 0.03, 0.1, 1.0)  # Clear screen with a color
		triangle.render(ctx, camera)
		box.render(ctx, camera)

	glwidget.on_init = init
	glwidget.on_resize = resize
	glwidget.on_render = render

	def render(ctx):
		ctx.clear(0.1, 0.11, 0.13, 1.0)  # Clear screen with a color
		triangle.render(ctx, camera)
		box.render(ctx, camera)
	glwidget.on_render = render

	mainLayout.addWidget(glwidget)
	window.show()
	sys.exit(app.exec())
